from numpy import arange

class Mensagem():
    def __init__(self, data_path):
        with open('resources/client/'+data_path, "rb") as image:
            f = image.read()
            self.mensagem = bytearray(f)
            #print('\n---> Imagem convertida em bytes\n')
            #print(self.mensagem)

    def construir_payloads(self):
        lista_payloads=[]
        payload = b''
        FLAG = 100
        for byte in self.mensagem:
            #print(FLAG)
            if FLAG >= 114:
                if payload != b'':
                    lista_payloads.append(payload)
                    #print(payload)
                FLAG = 0
                payload = int(byte).to_bytes(1,'big')
            else:
                payload += int(byte).to_bytes(1,'big')
                FLAG += 1
        if payload != b'':
            lista_payloads.append(payload)
        return lista_payloads