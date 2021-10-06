from enlace import *
import time
from datetime import datetime, timezone
from crccheck.crc import Crc16


class Server:

    def __init__(self) -> None:
        '''
            Contrutor do servidor
        '''

        # Inicializando objeto "com1"
        self.serial_number = "/dev/ttyACM0"
        self.com1 = enlace(self.serial_number)

        # Inicializando atributos de "head"
        self.msg_type = b''           # h0
        self.sensor_id = b''          # h1
        self.server_id = b''          # h2
        self.pkgs_qty = b''           # h3
        self.pkg_id = b''             # h4
        self.msg_id = b''             # h5 (\x01)
        self.pl_size = b''            # h5 (\x03)
        self.resend_pkg_id = b''      # h6
        self.last_pkg_id = b''        # h7
        self.crc = b''                # CRC

        # Inicializando atributo de EOP
        self.EOP = b'\xff\xaa\xff\xaa'

        # Inicializando atributos de apoio
        self.expected_id = 1
        self.timer = time.time()
        self.pkg_counter = 0
        self.eop_size = 4
        self.head_size = 10
        self.msg_id_list = []
        self.pkgs_qty_list = []
        self.pkg_id_list = []
        self.payload = b''

        self.msg_type_dict = {'handshake': b'\x01',
                              'handshake-response': b'\x02',
                              'data': b'\x03',
                              'data-ok': b'\x04',
                              'timeout': b'\x05',
                              'error': b'\x06'}

        self.FLAGS = {'ENABLED': False,
                      'GOT_HEAD': False,
                      'GOT_PAYLOAD': False,
                      'GOT_EOP': False,
                      'END_OF_MSG': False,
                      'PKG_ID_1': True,
                      'PKG_ERROR': False,
                      'TIMEOUT': False,
                      'SEND_T4': False,
                      'HS': True}

        self.STATUS = {'activate_com_ok': 'Comunication activated',
                       'disable_com': 'Comunication disabled',
                       'read_pkg': 'Reading package', 'pkg_error': 'Package with ERROR',
                       'read_head_ok': 'Head ok', 'read_head_!ok': 'Head NOT ok',
                       'got_hs': 'Handshake received', 'sent_hs': 'Handshake response sent', 'got_data': 'Data received', 'sent_dataOK': 'Sent data received confirmation', 'check_head_!ok': 'Problem with head',
                       'got_pl': 'Payload received', 'got_filetype': 'Filetype received', 'read_payload_!ok': 'Payload NOT received', 'no_pl': 'No payload from HS',
                       'eop_error': 'EOP error'}

    def status(self, msg):
        print(f'---> {self.STATUS[msg]}!')

    def activate_comunication(self):
        self.com1.enable()
        self.com1.rx.clearBuffer()
        self.status('activate_com_ok')
        self.FLAGS['ENABLED'] = True

    def disable_comunications(self):
        self.com1.disable()
        self.status('disable_com')
        self.FLAGS['ENABLED'] = False

    def init(self):
        self.FLAGS['GOT_HEAD'] = False
        self.FLAGS['GOT_PAYLOAD'] = False
        self.FLAGS['END_OF_MSG'] = False
        self.FLAGS['GOT_EOP'] = False
        self.FLAGS['PKG_ERROR'] = False
        self.FLAGS['TIMEOUT'] = False
        self.FLAGS['SEND_T4'] = False

    def read_pkg(self):
        '''
            Main script to read file
        '''
        self.init()
        self.status('read_pkg')

        if self.FLAGS['ENABLED']:
            self.read_head()
            if self.msg_type == b'\x01':
                time.sleep(1)

        if self.FLAGS['GOT_HEAD']:
            self.read_payload()

        if self.FLAGS['GOT_PAYLOAD']:
            self.check_eop()

        if self.FLAGS['GOT_HEAD'] or self.FLAGS['TIMEOUT'] or self.FLAGS['PKG_ERROR'] or self.FLAGS['SEND_T4']:
            self.server_response()

        if self.FLAGS['END_OF_MSG'] or self.FLAGS['TIMEOUT']:
            self.disable_comunications()
            return False
        else:
            self.com1.rx.clearBuffer()
            return True

    def read_head(self):
        head = self.com1.getData(
            self.head_size, self.timer, hs=self.FLAGS['HS'])[0]
        self.timer = time.time()
        if head[0] == 'RUNTIME':
            self.FLAGS['SEND_T4'] = True
        elif head[0] == 'TIME_OUT':
            self.FLAGS['TIMEOUT'] = True
        else:
            self.msg_type = head[0].to_bytes(1, 'big')           # h0
            self.sensor_id = head[1].to_bytes(1, 'big')          # h1
            self.server_id = head[2].to_bytes(1, 'big')          # h2
            self.pkgs_qty = head[3]                              # h3
            self.pkg_id = head[4]                                # h4
            if self.msg_type == b'\x01':
                self.msg_id = head[5].to_bytes(1, 'big')         # h5 (\x01)
                self.write_log('receb', msg_type=1)
            elif self.msg_type == b'\x03':
                self.pl_size = head[5]                           # h5 (\x03)
                self.write_log('receb', msg_type=3)
            self.resend_pkg_id = head[6].to_bytes(1, 'big')      # h6
            self.last_pkg_id = head[7]                           # h7
            self.h8 = head[8].to_bytes(1, 'big')                 # h8
            self.h9 = head[9].to_bytes(1, 'big')                 # h9
            self.crc = self.h8 + self.h9

            if self.msg_type == b'\x01' and self.FLAGS['HS']:
                self.FLAGS['GOT_HEAD'] = True
                self.status('got_hs')
                self.pkg_counter = 1
                self.last_pkg_id = 0
            elif self.msg_type == b'\x01' and not self.FLAGS['HS']:
                self.FLAGS['PKG_ERROR'] = True
                self.status('pkg_error')

            if self.msg_type == b'\x03':
                if self.pkg_id == self.expected_id:
                    self.expected_id = self.pkg_id + 1
                    self.FLAGS['GOT_HEAD'] = True
                    self.status('read_head_ok')
                else:
                    self.FLAGS['PKG_ERROR'] = True
                    self.status('pkg_error')

            if self.msg_type == b'\x05':
                self.write_log('receb', msg_type=5)
                self.FLAGS['TIMEOUT'] = True

    def read_payload(self):
        if self.msg_type == b'\x01':
            self.status('no_pl')

        elif self.FLAGS['PKG_ID_1'] and self.msg_type == b'\x03':
            self.file_type = self.com1.getData(
                self.pl_size, self.timer, hs=self.FLAGS['HS'])[0].decode('ascii')
            self.FLAGS['PKG_ID_1'] = False
            self.status('got_filetype')

        elif self.msg_type == b'\x03':
            pl = self.com1.getData(
                self.pl_size, self.timer, hs=self.FLAGS['HS'])[0]
            my_crc = self.CRC(pl)
            if my_crc == self.crc:
                self.payload += pl
                self.status('got_pl')
                self.FLAGS['GOT_PAYLOAD'] = True
            else:
                self.FLAGS['PKG_ERROR'] = True

    def check_eop(self):
        eop = self.com1.getData(
            self.eop_size, self.timer, hs=self.FLAGS['HS'])[0]
        if eop == self.EOP:
            self.FLAGS['GOT_EOP'] = True
            if self.pkg_counter > self.pkgs_qty:
                self.FLAGS['END_OF_MSG'] = True
                self.save_file()
            else:
                self.timer = time.time()
        else:
            self.FLAGS['PKG_ERROR'] = True

    def server_response(self):
        if self.FLAGS['PKG_ERROR']:
            self.com1.rx.clearBuffer()
            head = [self.msg_type_dict['error'], self.sensor_id, self.server_id, int(self.pkgs_qty).to_bytes(1, 'big'), b'\x00', self.msg_id, int(
                self.expected_id).to_bytes(1, 'big'), int(self.last_pkg_id).to_bytes(1, 'big'), b'\x00', b'\x00', self.EOP]
            send_head = b''.join(head)
            self.com1.sendData(send_head)
            self.FLAGS['PKG_ERROR'] = False
            self.write_log('envio', msg_type=6)

        elif self.FLAGS['TIMEOUT']:
            self.com1.rx.clearBuffer()
            head = [self.msg_type_dict['timeout'], self.sensor_id, self.server_id, int(self.pkgs_qty).to_bytes(1, 'big'), b'\x00', self.msg_id, int(
                self.last_pkg_id+1).to_bytes(1, 'big'), int(self.last_pkg_id).to_bytes(1, 'big'), b'\x00', b'\x00', self.EOP]
            send_head = b''.join(head)
            self.com1.sendData(send_head)
            self.write_log('envio', msg_type=5)

        elif self.FLAGS['SEND_T4']:
            self.com1.rx.clearBuffer()
            head = [self.msg_type_dict['data'], self.sensor_id, self.server_id, int(self.pkgs_qty).to_bytes(1, 'big'), b'\x00', self.msg_id, int(
                self.last_pkg_id+1).to_bytes(1, 'big'), int(self.last_pkg_id).to_bytes(1, 'big'), b'\x00', b'\x00', self.EOP]
            send_head = b''.join(head)
            self.com1.sendData(send_head)
            self.FLAGS['TIMEOUT'] = False
            self.write_log('envio', msg_type=4)
            self.timer = time.time()

        else:
            if self.msg_type == b'\x01' and self.FLAGS['HS']:
                self.FLAGS['HS'] = False
                head_response_list = [self.msg_type_dict['handshake-response'], self.sensor_id, self.server_id, int(self.pkgs_qty).to_bytes(
                    1, 'big'), b'\x00', self.msg_id, b'\x00', int(self.last_pkg_id).to_bytes(1, 'big'), b'\x00', b'\x00', self.EOP]
                head_response = b''.join(head_response_list)
                self.com1.rx.clearBuffer()
                self.com1.sendData(head_response)
                self.status('sent_hs')
                self.write_log('envio', msg_type=2)

            elif self.msg_type == b'\x03':
                self.status('got_data')
                dataOK_response_list = [self.msg_type_dict['data-ok'], self.sensor_id, self.server_id, int(self.pkgs_qty).to_bytes(
                    1, 'big'), b'\x00', self.msg_id, b'\x00', int(self.pkg_id).to_bytes(1, 'big'), b'\x00', b'\x00', self.EOP]
                dataOK_response = b''.join(dataOK_response_list)
                self.com1.rx.clearBuffer()
                self.com1.sendData(dataOK_response)
                self.status('sent_dataOK')
                self.last_pkg_id = self.pkg_id
                self.write_log('envio', msg_type=4)

            self.pkg_counter += 1

    def save_file(self):
        file = self.file_type
        with open("resources/server/" + file, "wb") as bin_file:
            bin_file.write(self.payload)

    def write_log(self, type, msg_type=0):
        now = datetime.now(tz=timezone.utc)
        if type == 'receb':
            if self.msg_type == b'\x03':
                log = f'{now} / {type} / {msg_type} / {int(self.pl_size) + 14} / {self.pkg_id} / {self.crc}\n'
            else:
                log = f'{now} / {type} / {msg_type} / {14}\n'
        elif type == 'envio':
            log = f'{now} / {type} / {msg_type} / {14}\n'

        f = open("logs/log.txt", "a")
        f.write(log)
        f.close()

    def CRC(self, data):
        crc_result = Crc16.calc(data)
        crc_ = crc_result.to_bytes(2, 'big')
        return crc_


def main():
    try:
        while True:
            server = Server()
            server.activate_comunication()
            while (server.read_pkg()):
                print('---> pkg OK!\n\n')
            time.sleep(0.5)
            print('\nPress Control + c to shut down server')

    except Exception as erro:
        print("ops! :-\\")
        print(erro)
        server.disable()


if __name__ == "__main__":
    main()
