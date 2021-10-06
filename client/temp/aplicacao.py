#####################################################
# Camada Física da Computação
# Carareto
# 11/08/2020
# Aplicação
####################################################


# esta é a camada superior, de aplicação do seu software de comunicação serial UART.
# para acompanhar a execução e identificar erros, construa prints ao longo do código!


import random
from enlace import *
import time
import numpy as np
from PIL import Image
from io import BytesIO
from pacote import Mensagem
from clientFunctions import *
from tqdm import tqdm


#   python -m serial.tools.list_ports
serialName = "/dev/cu.usbmodem1412401"

def main():
    try:
        # Test declaration
        TEST_RUBRICA_3 = False
        TEST_RUBRICA_4 = False
        TESTOU_RUBRICA_4 = False
        # Declaração de Variáveis:
        com1 = enlace(serialName)

        id_client = b'\x14'
        id_server = b'\x15'
        id_mensagem = int(random.randint(0,255)).to_bytes(1,'big')

        headByteArray = b''
        payloadByteArray = b''

        FILE = 'sams.webp'

        mensagem = Mensagem(FILE)

        # Ativa comunicacao. Inicia os threads e a comunicação seiral
        com1.enable()

        # Se chegamos até aqui, a comunicação foi aberta com sucesso. Faça um print para informar.
        print('\n---> A comunicação foi aberta com sucesso!\n')

        # sacrificio:
        com1.sendData(b'\x00')
        time.sleep(0.1)

        # Handshake:
        handshake = generateHandshake(id_client,id_server,id_mensagem)
        HANDSHAKING = True
        com1.sendData(handshake)
        print('\n---> Enviei o Handshake!\n')

        while HANDSHAKING:
            handshake_response = com1.getData(10)
            #print(handshake_response)
            if handshake_response[0][0] == 2:
                HANDSHAKING = False
                print('\n---> Handshake feito com SUCESSO!\n')
            else:
                com1.sendData(handshake)
                com1.rx.clearBuffer()
                print('\n---> Enviei o Handshake novamente :(\n')

        # Converter a mensagem em bytes:
        lista_payloads = mensagem.construir_payloads()
        # print(lista_payloads)
        com1.rx.clearBuffer()

        FIRST_PACKAGE_RECEIVED = False
        first_pkg = generateFirstPkg(id_client,id_server,id_mensagem,int(len(lista_payloads)+1).to_bytes(1,'big'),FILE)
        #print(first_pkg)
        com1.sendData(first_pkg)

        while not FIRST_PACKAGE_RECEIVED:
            first_pkg_response = com1.getData(10)
            #print(first_pkg_response)
            if first_pkg_response[0][0] == 4:
                FIRST_PACKAGE_RECEIVED = True
                print('\n---> Primeiro Pacote foi recebido pelo server!\n')
            else:
                print('\n---> Enviei o primeiro pacote novamente :(\n')
                com1.rx.clearBuffer()
                com1.sendData(first_pkg)

        i = 0
        pbar = tqdm(total=len(lista_payloads),unit='packages',desc='Packages Enviados:')
        while i < len(lista_payloads):
            if TEST_RUBRICA_3:
                time.sleep(0.2)
            RECEIVED = False
            if TEST_RUBRICA_3 and i == 4:
                print('\n---> Alterei o id de um pacote!\n')
                i -= 1   
            #print(i)
            pkg_id = i+1
            if TEST_RUBRICA_4 and not TESTOU_RUBRICA_4 and i == 8:
                print('\n---> O tamanho do payload foi adulterado para erro!\n')
                pkg = generatePkg(id_client,id_server,id_mensagem,int(len(lista_payloads)+1).to_bytes(1,'big'),pkg_id,lista_payloads,TEST_RUBRICA_4)
            else:
                pkg = generatePkg(id_client,id_server,id_mensagem,int(len(lista_payloads)+1).to_bytes(1,'big'),pkg_id,lista_payloads)
            com1.tx.fisica.flush()
            com1.rx.clearBuffer()
            time.sleep(0.05)
            com1.sendData(pkg)
            while not RECEIVED:
                pkg_response = com1.getData(10)
                #print(pkg_response)
                if pkg_response[0][0] == 4:
                    RECEIVED = True
                    #print(f'\n---> {pkg_id}º pacote foi recebido pelo server!\n')
                    i += 1
                    pbar.update()

                elif pkg_response[0][0] == 6:
                    i = pkg_response[0][5] - 1
                    pkg_id = i+1
                    print(f'\n---> {pkg_id}º pacote foi recebido com ERRO no server, enviando novamente...\n')
                    pkg = generatePkg(id_client,id_server,id_mensagem,int(len(lista_payloads)+1).to_bytes(1,'big'),pkg_id,lista_payloads)
                    com1.tx.fisica.flush()
                    com1.rx.clearBuffer()
                    com1.sendData(pkg)

                elif pkg_response[0][0] == 5:
                    print(f'\n---> {pkg_id}º pacote não foi recebido pelo server, enviando novamente...\n')
                else:
                    print(f'\n---> Enviei o {pkg_id}º pacote novamente :(\n')
                    com1.rx.clearBuffer()
                    com1.tx.fisica.flush()
                    com1.rx.clearBuffer()
                    com1.sendData(pkg)

        # Encerra comunicação
        pbar.close()
        print("\n-----------------------------")
        print("---> Comunicação encerrada")
        print("-----------------------------\n")
        com1.disable()


    except Exception as erro:
        print("ops! :-\\")
        print(erro)
        com1.disable()


    # so roda o main quando for executado do terminal ... se for chamado dentro de outro modulo nao roda
if __name__ == "__main__":
    main()
