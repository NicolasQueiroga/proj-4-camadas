from enlace import *


class Server:

    def __init__(self) -> None:
        '''
            Contrutor do servidor
        '''

        # Inicializando objeto "com1"
        self.serial_number = "/dev/cu.usbmodem1412301"
        self.com1 = enlace(self.serial_number)

        # Inicializando atributos de "head"
        self.msg_type = b''
        self.cli_id = b''
        self.serv_id = b''
        self.msg_id = b''
        self.pkgs_qty = b''
        self.pkg_id = b''
        self.payload_size = b''

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
            Main script to read N packages
        '''
        self.init()
        self.status('read_pkg')

        if not self.FLAGS['PKG_ERROR']:

            if self.FLAGS['ENABLED'] and not self.FLAGS['ERROR']:
                self.read_head()

            if self.FLAGS['GOT_HEAD'] and not self.FLAGS['ERROR']:
                self.read_payload()

            if self.FLAGS['GOT_PAYLOAD'] and not self.FLAGS['ERROR']:
                self.check_eop()

        if self.FLAGS['PKG_ERROR'] or (self.FLAGS['GOT_EOP'] and not self.FLAGS['ERROR']):
            self.server_response()

        if self.FLAGS['END_OF_MSG'] and not self.FLAGS['ERROR']:
            self.disable_comunications()
            return False
        else:
            return True

    def read_head(self):
        try:
            self.head = self.com1.getData(self.head_size)[0]
            self.msg_type = self.head[0].to_bytes(1, 'big')
            self.cli_id = self.head[1].to_bytes(1, 'big')
            self.serv_id = self.head[2].to_bytes(1, 'big')
            self.pkgs_qty = self.head[4].to_bytes(1, 'big')
            self.pkg_id = self.head[5]
            self.payload_size = self.head[6]

            # mudar para dicio {pkg_id: {}}
            self.msg_id_list.append(self.msg_id)
            self.pkgs_qty_list.append(self.pkgs_qty)
            self.pkg_id_list.append(self.pkg_id)
            # ---

            if self.FLAGS['READ_ONCE']:
                self.pkg_counter = int.from_bytes(self.pkgs_qty, 'big')
                self.msg_id = self.head[3].to_bytes(1, 'big')

            if self.msg_type == b'\x01' and self.FLAGS['HS_RUN']:
                self.pkg_counter += 2
                self.FLAGS['HS_PAYLOAD'] = True
                self.last_pkg_id = -1
                self.FLAGS['GOT_HEAD'] = True
                self.status('read_head_ok')

            if self.msg_type == b'\x03':
                if self.pkg_id == self.last_pkg_id + 1:
                    self.FLAGS['GOT_HEAD'] = True
                    self.status('read_head_ok')
                else:
                    self.FLAGS['PKG_ERROR'] = True
                    self.status('pkg_id_error')

        except Exception as erro:
            self.FLAGS['ERROR'] = True
            self.status('read_head_!ok')

    def read_payload(self):
        try:
            if self.FLAGS['HS_PAYLOAD']:
                self.status('no_pl')
                self.FLAGS['READ_ONCE'] = True
                self.FLAGS['HS_RUN'] = False

            elif self.pkg_id == 0 and not self.FLAGS['GOT_FILE_TYPE']:
                self.file_type = self.com1.getData(self.payload_size)[0].decode('ascii')
                self.FLAGS['GOT_FILE_TYPE'] = True
                self.FLAGS['READ_ONCE'] = False
                self.status('got_filetype')

            else:
                self.payload += self.com1.getData(self.payload_size)[0]
                self.status('got_pl')
            self.FLAGS['GOT_PAYLOAD'] = True

        except Exception as erro:
            self.status('read_payload_!ok')
            self.FLAGS['ERROR'] = True

    def check_eop(self):
        try:
            self.eop = self.com1.getData(self.eop_size)[0]

            if self.eop == self.EOP:
                self.FLAGS['GOT_EOP'] = True
                self.pkg_counter -= 1

                if self.pkg_counter == 0:
                    self.FLAGS['END_OF_MSG'] = True
                    self.save_file()
            else:
                self.FLAGS['PKG_ERROR'] = True

        except Exception as erro:
            self.status('eop_error')
            self.FLAGS['ERROR'] = True

    def server_response(self):
        try:
            if self.FLAGS['PKG_ERROR']:
                time.sleep(0.05)
                self.com1.rx.clearBuffer()
                head = [self.msg_type_dict['error'],
                        self.cli_id, self.serv_id, self.msg_id, b'\x00', int(self.last_pkg_id+1).to_bytes(1, 'big'), b'\x00\x00\x00\x00']
                send_head = b''.join(head)
                self.com1.sendData(send_head)
                self.FLAGS['PKG_ERROR'] = False

            else:
                if self.msg_type == b'\x01' and not self.FLAGS['SENT_HS_RESPONSE']:
                    self.status('got_hs')
                    head_response_list = [self.msg_type_dict['handshake-response'],
                                          self.cli_id, self.serv_id, self.msg_id, b'\x00\x00\x00\x00\x00\x00\x00']
                    head_response = b''.join(head_response_list)

                    self.com1.rx.clearBuffer()
                    self.com1.sendData(head_response)
                    self.status('sent_hs')
                    self.FLAGS['HS_PAYLOAD'] = False
                    self.FLAGS['SENT_HS_RESPONSE'] = True

                elif self.msg_type == b'\x03' and self.FLAGS['SENT_HS_RESPONSE']:
                    self.status('got_data')
                    dataOK_response_list = [self.msg_type_dict['data-ok'], self.cli_id,
                                            self.serv_id, self.msg_id, b'\x00\x00\x00\x00\x00\x00']
                    dataOK_response = b''.join(dataOK_response_list)

                    self.com1.rx.clearBuffer()
                    self.com1.sendData(dataOK_response)
                    self.status('sent_dataOK')
                    self.last_pkg_id = self.pkg_id

        except Exception as erro:
            self.status('check_head_!ok')
            self.FLAGS['ERROR'] = True

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
