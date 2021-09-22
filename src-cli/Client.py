import os
import random
from enlace import *
import time
import numpy as np
from clientFunctions import *
from tqdm import tqdm


#   python -m serial.tools.list_ports
serialName = "/dev/cu.usbmodem1412401"

# Arquivo a enviar:
FILE = 'sams.webp'

# Vriáveis de Teste
TEST_RUBRICA_3 = False
TEST_RUBRICA_4 = False

# Ativar Verbose:
VERBOSE = False


class Mensagem():
    def __init__(self, fileName):
        self.msg_id = random.randint(0,255)
        self.mensagem = openMsg(fileName=fileName,verbose=VERBOSE)
        self.payloads = construirPayloads(mensagem=self.mensagem, size=114, verbose=VERBOSE)

class Client():
    def __init__(self, fileName, serialName=serialName):
        self.client_id = 20
        self.client_server = 21
        self.fileName = fileName
        self.serialName = serialName

        self.mensagem = Mensagem(self.fileName)
        self.msg_id = self.mensagem.msg_id
        self.payloads = self.mensagem.payloads
        




def main():
    client = Client(fileName=FILE)
    client.startSending()

if __name__ == "__main__":
    main()