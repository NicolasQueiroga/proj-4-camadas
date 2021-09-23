from enlace import *
import time


class Server:

    def __init__(self) -> None:
        '''
            Contrutor do servidor
        '''

        # Inicializando objeto "com1"
        self.serial_number = "/dev/ttyACM0"
        self.com1 = enlace(self.serial_number)

        # Inicializando atributos de "head"
        self.msg_type = b'' # h0
        self.sensor_id = b'' # h1
        self.server_id = b'' # h2
        self.pkgs_qty = b'' # h3
        self.pkg_id = b'' # h4
        self.pkg_id = b'' # h5
        self.payload_size = b'' # h6
        # h7

        # Inicializando atributo de EOP
        self.EOP = b'\x4C\x4F\x56\x55'

        # Inicializando atributos de apoio
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
                      'GOT_FILE_TYPE': False,
                      'CHECK_HEAD': False,
                      'SENT_HS_RESPONSE': False,
                      'HS_PAYLOAD': False,
                      'ERROR': False,
                      'GOT_PAYLOAD': False,
                      'GOT_EOP': False,
                      'END_OF_MSG': False,
                      'READ_ONCE': False,
                      'HS_RUN': True,
                      'PKG_ERROR': False}

        self.STATUS = {'activate_com_ok': 'Comunication activated',
                       'disable_com': 'Comunication disabled',
                       'read_pkg': 'Reading package', 'pkg_id_error': 'Package with ID ERROR',
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
        self.FLAGS['CHECK_HEAD'] = False
        self.FLAGS['GOT_PAYLOAD'] = False
        self.FLAGS['END_OF_MSG'] = False
        self.FLAGS['GOT_EOP'] = False
        self.FLAGS['PKG_ERROR'] = False

    def read_pkg(self):
        '''
            Main script to read file
        '''
        self.init()
        self.status('read_pkg')

        if self.FLAGS['ENABLED']:
            self.read_head()
            time.sleep(1)

        if not self.FLAGS['PKG_ERROR']:
            self.read_payload()

            if self.FLAGS['GOT_PAYLOAD']:
                self.check_eop()

        if self.FLAGS['PKG_ERROR'] or self.FLAGS['GOT_EOP']:
            time.sleep(1)
            now1 = time.time()
            if (now1 - self.timer2) > 20:
                self.FLAGS['TIMEOUT'] = True
                self.FLAGS['PKG_ERROR'] = False
            else:
                now2 = time.time()
                if (now2 - self.timer1) <= 2:
                    self.FLAGS['TIMEOUT'] = False
                    self.FLAGS['PKG_ERROR'] = False
            
        if self.FLAGS['GOT_HEAD'] or self.FLAGS['TIMEOUT'] or self.FLAGS['PKG_ERROR']:
            self.server_response()

        if self.FLAGS['END_OF_MSG']:
            self.disable_comunications()
            return False
        else:
            return True

    def read_head(self):
        try:
            head = self.com1.getData(self.head_size)[0]

            self.msg_type = head[0].to_bytes(1, 'big')           # h0
            self.sensor_id = head[1].to_bytes(1, 'big')          # h1
            self.server_id = head[2].to_bytes(1, 'big')          # h2
            self.pkgs_qty = head[3].to_bytes(1, 'big')           # h3
            self.pkg_id = head[4].to_bytes(1, 'big')             # h4
            if self.msg_type == b'\x01':
                self.msg_id = head[5].to_bytes(1, 'big')         # h5 (\x01)
            elif self.msg_type == b'\x03':
                self.pl_size = head[5].to_bytes(1, 'big')        # h5 (\x03)
            self.resend_pkg_id = head[6].to_bytes(1, 'big')      # h6
            self.last_pkg_id = head[7].to_bytes(1, 'big')        # h7

            if self.msg_type == b'\x01':
                self.pkg_counter = 1
                self.last_pkg_id = 0
                
            
            if self.msg_type == b'\x03':
                if self.pkg_id == self.last_pkg_id + 1:
                    self.self.msg_type == b'\x03'= True
                    self.FLAGS['GOT_HEAD'] = True
                    self.status('read_head_ok')
                else:
                    self.FLAGS['PKG_ERROR'] = True
                    self.status('pkg_id_error')

        except Exception as erro:
            self.status('read_head_!ok')

    def read_payload(self):
        try:
            if self.msg_type == b'\x01':
                self.status('no_pl')
            
            elif self.FLAGS['PKG_ID_0'] and self.msg_type == b'\x03':
                self.file_type = self.com1.getData(self.payload_size)[0].decode('ascii')
                self.FLAGS['PKG_ID_0'] = False
                self.status('got_filetype')

            elif self.msg_type == b'\x03':
                self.payload += self.com1.getData(self.payload_size)[0]
                self.status('got_pl')
                
            self.FLAGS['GOT_PAYLOAD'] = True

        except Exception as erro:
            self.status('read_payload_!ok')

    def check_eop(self):
        try:
            self.eop = self.com1.getData(self.eop_size)[0]
            if self.eop == self.EOP:
                self.FLAGS['GOT_EOP'] = True
                self.pkg_counter -= 1
                if self.pkg_counter > self.pkgs_qty:
                    self.FLAGS['END_OF_MSG'] = True
                    self.save_file()
                else:
                    self.timer1 = time.time()
                    self.timer2 = time.time()
            else:
                self.FLAGS['PKG_ERROR'] = True

        except Exception as erro:
            self.status('eop_error')

    def server_response(self):
        try:
            if self.FLAGS['PKG_ERROR']:
                # time.sleep(0.05)
                self.com1.rx.clearBuffer()
                head = [self.msg_type_dict['error'], self.cli_id, self.serv_id, self.msg_id, b'\x00', int(self.last_pkg_id+1).to_bytes(1, 'big'), b'\x00\x00\x00\x00']
                send_head = b''.join(head)
                self.com1.sendData(send_head)
                self.FLAGS['PKG_ERROR'] = False
                self.timer1 = time.time()
            
            elif self.FLAGS['TIMEOUT']:
                self.com1.rx.clearBuffer()
                head = [self.msg_type_dict['error'], self.cli_id, self.serv_id, self.msg_id, b'\x00', int(self.last_pkg_id+1).to_bytes(1, 'big'), b'\x00\x00\x00\x00']
                send_head = b''.join(head)
                self.com1.sendData(send_head)
                self.FLAGS['TIMEOUT'] = False

            else:
                if self.msg_type == b'\x01':
                    head_response_list = [self.msg_type_dict['handshake-response'], self.cli_id, self.serv_id, self.msg_id, b'\x00\x00\x00\x00\x00\x00\x00']
                    head_response = b''.join(head_response_list)
                    self.com1.rx.clearBuffer()
                    self.com1.sendData(head_response)
                    self.status('sent_hs')
                    self.FLAGS['HS_PAYLOAD'] = False
                    self.FLAGS['SENT_HS_RESPONSE'] = True

                elif self.msg_type == b'\x03':
                    self.status('got_data')
                    dataOK_response_list = [self.msg_type_dict['data-ok'], self.cli_id, self.serv_id, self.msg_id, b'\x00\x00\x00\x00\x00\x00']
                    dataOK_response = b''.join(dataOK_response_list)
                    self.com1.rx.clearBuffer()
                    self.com1.sendData(dataOK_response)
                    self.status('sent_dataOK')
                    self.last_pkg_id = self.pkg_id
                
                self.pkg_counter += 1

        except Exception as erro:
            self.status('check_head_!ok')

    def save_file(self):
        file = self.file_type
        with open("resources/" + file, "wb") as bin_file:
            bin_file.write(self.payload)


def main():
    try:
        while True:
            server = Server()
            server.activate_comunication()
            while (server.read_pkg()):
                print('---> pkg OK!\n\n')
            print('\nPress Control + c to shut down server')

    except Exception as erro:
        print("ops! :-\\")
        print(erro)
        server.disable()


if __name__ == "__main__":
    main()
