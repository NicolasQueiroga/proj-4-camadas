import os
import random
import time
import numpy as np
from tqdm import tqdm
from functions.enlace import *
from functions.clientFunctions import *
from functions.clientStatus import Status


#   python -m serial.tools.list_ports
serialName = "/dev/cu.usbmodem1412401"

# Arquivo a enviar:
FILE = 'togepi.jpeg'

# Vriáveis de Teste
TEST_RUBRICA_2 = False
TEST_RUBRICA_4 = False

# Ativar Verbose:
VERBOSE = False


class Mensagem():
    def __init__(self, fileName, Status):
        self.Status = Status
        self.msg_id = random.randint(0, 255)
        self.mensagem = openMsg(fileName=fileName, Status=self.Status)
        self.payloads = construirPayloads(
            mensagem=self.mensagem, Status=self.Status, size=113)


class Client():
    def __init__(self, fileName, serialName=serialName):
        self.client_id = 20
        self.server_id = 21
        self.fileName = fileName
        self.serialName = serialName

        self.Status = Status(VERBOSE)

        self.mensagem = Mensagem(self.fileName, self.Status)
        self.msg_id = self.mensagem.msg_id
        self.payloads = self.mensagem.payloads

        self.crcs = []

        self.pbar = False

        self.EOP = b'\xFF\xAA\xFF\xAA'

    def generateHeader(self, msgType, numPacote, header5, header6=0, header7=0, CRC=b'\x00\x00'):
        """
        h0 -> tipo de mensagem;
        h1 -> id do client;
        h2 -> id do server;
        h3 -> nº total de pacotes do arquivo;
        h4 -> nº do pacote a ser enviado (começa em 1);
        h5 -> TIPO HANDSHAKE: id do arquivo // TIPO DADOS: tamanho do payload;
        h6 -> pacote solicitado para recomeço quando erro no envio;
        h7 -> último pacote recebido com sucesso;
        h8 & h9 -> CRC;
        """

        h0 = int(msgType).to_bytes(1, 'big')
        h1 = self.client_id.to_bytes(1, 'big')
        h2 = self.server_id.to_bytes(1, 'big')
        h3 = int(len(self.payloads)+1).to_bytes(1, 'big')
        h4 = int(numPacote).to_bytes(1, 'big')
        h5 = int(header5).to_bytes(1, 'big')
        h6 = int(header6).to_bytes(1, 'big')
        h7 = int(header7).to_bytes(1, 'big')
        h89 = CRC

        return h0+h1+h2+h3+h4+h5+h6+h7+h89

    def packageEncoder(self, first, id, last):
        if first:
            firstPkgPayload = FILE.encode()
            crc = CRC(firstPkgPayload)
            self.crcs.append(crc)
            firstPkgHead = self.generateHeader(
                3, 1, len(firstPkgPayload), CRC=crc)
            firstPkg = firstPkgHead + firstPkgPayload + self.EOP
            return firstPkg, crc
        else:
            crc = CRC(self.payloads[id-1])
            self.crcs.append(crc)
            header = self.generateHeader(
                3, id+1, len(self.payloads[id-1]), header7=last, CRC=crc)
            self.Status.status('pkg_encoded')
            return header+self.payloads[id-1]+self.EOP, crc

    def handshaking(self):
        HANDSHAKING = True
        head = self.generateHeader(1, 0, self.msg_id)
        handshake = head + self.EOP
        self.Status.status('send_handshake')

        start_handshake = time.time()
        while HANDSHAKING:
            self.com.sendData(handshake)
            self.Status.log('envio', 1, len(handshake))
            handshake_response, nRx = self.com.getData(
                14, start=start_handshake)

            if handshake_response[0] == 2:
                self.Status.log(
                    'receb', handshake_response[0], len(handshake_response))
                HANDSHAKING = False
                self.Status.status('received_handshake')
                return True
            elif handshake_response == 'TIME_OUT':
                HANDSHAKING = False
                timeout_head = self.generateHeader(5, 0, self.msg_id)
                timeout = timeout_head + self.EOP
                self.com.sendData(timeout)
                self.Status.log('envio', 5, len(timeout))
                self.Status.status('handshake_timeout')
                self.com.rx.clearBuffer()
                return False
            elif handshake_response[0] == 5:
                self.Status.log(
                    'receb', handshake_response[0], len(handshake_response))
                self.com.rx.clearBuffer()
                return False
            elif handshake_response == 'RUNTIME':
                self.com.rx.clearBuffer()
                self.Status.status('handshake_runtime')
            else:
                self.Status.log(
                    'receb', handshake_response[0], len(handshake_response))
                self.com.rx.clearBuffer()
                self.Status.status('resend_handshake')
        return False

    def sendPackages(self):
        i = 0
        TESTOU = False
        last = 0
        if not VERBOSE:
            self.pbar = tqdm(range(0, len(self.payloads)+1),
                             unit='packages', desc='Pacotes Enviados:')
        while i < len(self.payloads)+1:
            SENDING = True
            start_sending = time.time()
            if TEST_RUBRICA_2 and i == 10 and not TESTOU:
                i = 12
                TESTOU = True

            if i == 0:
                package, crc = self.packageEncoder(True, i, last)
            else:
                package, crc = self.packageEncoder(False, i, last)

            while SENDING:
                self.com.sendData(package)
                # print(self.packages[i])
                self.Status.log('envio', 3, len(package), i+1,
                                len(self.payloads)+1, CRC=crc)
                self.Status.status('send_pkg', id=i+1)

                response, nRx = self.com.getData(14, start=start_sending)

                if response[0] == 4:
                    self.Status.log('receb', response[0], len(response))
                    self.Status.status('update_load_bar', pbar=self.pbar)
                    last = response[7]
                    SENDING = False
                    i += 1
                elif response[0] == 6:
                    self.Status.log('receb', response[0], len(response))
                    i = response[6] - 1
                    last = response[7]
                    SENDING = False
                elif response[0] == 5:
                    self.Status.log('receb', response[0], len(response))
                    return False
                elif response == 'TIME_OUT':
                    timeout_head = self.generateHeader(5, 0, self.msg_id)
                    timeout = timeout_head + self.EOP
                    self.com.sendData(timeout)
                    self.Status.log('envio', 5, len(timeout))
                    self.Status.status('timeout')
                    time.sleep(0.3)
                    self.com.rx.clearBuffer()
                    return False
                elif response == 'RUNTIME':
                    self.com.rx.clearBuffer()
                    self.Status.status('runtime')
                else:
                    self.com.rx.clearBuffer()
        return True

    def streaming(self):
        handshakeSucsses = self.handshaking()
        if handshakeSucsses:
            sendingSuccess = self.sendPackages()
            if sendingSuccess:
                return True
            else:
                self.endCom(error=True)
                return False
        else:
            self.endCom(error=True)
            return False

    def endCom(self, error=False):
        if not self.pbar:
            print('Comunicação foi Finalizada.\n')
        else:
            self.Status.status('close_load_bar', pbar=self.pbar)
        if error:
            print('Ocorreu um problema.', end=' ')
        print('Comunicação foi Finalizada.')
        self.com.fisica.flush()
        self.com.disable()
        self.Status.logClose()

    def startCom(self):
        try:
            self.com = enlace(self.serialName)
            self.com.enable()
            self.com.fisica.flush()
            time.sleep(0.5)
            # self.com.sendData(b'\x00\x00')    # Sacrifício
            time.sleep(0.5)
            self.com.fisica.flush()
            self.Status.status('com_enable')

            streamingSuccess = self.streaming()
            if streamingSuccess:
                self.endCom()

        except Exception as erro:
            print("Ops! Erro no Client! :-(\\\n", erro)
            self.Status.logClose()
            self.com.disable()

        except KeyboardInterrupt:
            self.Status.logClose()
            self.com.disable()
            print(
                '\nClient Interrompido com Ctrl + C, desabilitando o contato e fechando o Log.\n')


def main():
    client = Client(fileName=FILE)
    client.startCom()


if __name__ == "__main__":
    main()
