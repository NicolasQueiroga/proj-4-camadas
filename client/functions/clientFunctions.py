TIPO_MENSAGEM = {'handshake':b'\x01','handshake-response':b'\x02','data':b'\x03','data-ok':b'\x04','timeout':b'\x05','error':b'\x06'}
EOP = b'\x4C\x4F\x56\x55'



def openMsg(fileName, Status):
    with open('resources/client/'+fileName, "rb") as image:
        f = image.read()
        Status.status('msg_read')
        return bytearray(f)

def construirPayloads(mensagem, Status, size=114):
    payloads = []
    payload = b''
    FLAG = size
    for byte in mensagem:
        #print(FLAG)
        if FLAG >= size:
            if payload != b'':
                payloads.append(payload)
                #print(payload)
            FLAG = 0
            payload = int(byte).to_bytes(1,'big')
        else:
            payload += int(byte).to_bytes(1,'big')
            FLAG += 1
    if payload != b'':
        payloads.append(payload)
    Status.status('msg_conv')
    return payloads
