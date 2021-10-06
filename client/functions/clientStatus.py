from datetime import datetime, timezone
from tqdm import tqdm


class Status:
    def __init__(self, VERBOSE):
        self.status_dict = {
            'msg_read': 'Mensagem encontrada com sucesso.',
            'msg_conv': 'Mensagem convertida em pacotes.',
            'com_enable': 'Comunicação Habilitada no Client!',
            'pkgs_encoded': 'Todos os pacotes foram montados.',
            'send_handshake': 'Enviando o Handshake...',
            'received_handshake': 'Handshake feito com SUCESSO!',
            'resend_handshake': 'Enviei o Handshake novamente :(',
            'handshake_timeout': 'Deu #TIMEOUT# no handshake :(',
            'handshake_runtime': '#RUNTIME# no handshake, enviando novamente :(',
            'timeout': 'Deu #TIMEOUT# no envio do pacote :(',
            'runtime': '#RUNTIME# no envio do pacote, enviando novamente :(',
            'send_pkg': 'Enviando o Pacote de id:',
            'update_load_bar': 'Pacote foi recebido! Update Bar.',
        }
        self.VERBOSE = VERBOSE
        self.logFile = open('client/logs/log.txt', 'a')

    def status(self, process, id=None, pbar=None):
        if self.VERBOSE:
            if id != None:
                print(f'---> {self.status_dict[process]} {str(id)}\n')
            else:
                print(f'---> {self.status_dict[process]}\n')
        else:
            if process == 'update_load_bar':
                pbar.update()
            elif process == 'close_load_bar':
                pbar.close()

    def log(self, type, msgType, totalBytes, sendPackNum=0, total_pkgs=0, CRC=b'\x00\x00'):
        """
        Informações para o LOG:
        -> Instante de Envio
        -> Envio ou Recebimento
        -> Tipo de Mensagem
        -> Tamanho de bytes total
        -> Pacote Enviado (caso tipo 3)
        -> Total de Pacotes (caso tipo 3)
        -> CRC do payload para mensagem tipo 3 (caso tenha implementado)

        EXEMPLO: 29/09/2020 13:34:23.089 / envio / 3 / 128 / 1 / 23/ F23F
        """
        now = datetime.now(tz=timezone.utc)
        logDATA = now.isoformat(' ') + ' / ' + str(type) + \
            ' / ' + str(msgType) + ' / ' + str(totalBytes)
        if msgType == 3:
            logDATA = logDATA + ' / ' + \
                str(sendPackNum) + ' / ' + \
                str(total_pkgs) + ' / ' + str(CRC) + '\n'
            self.logFile.write(logDATA)
        else:
            logDATA = logDATA + '\n'
            self.logFile.write(logDATA)

    def logClose(self):
        self.logFile.close()
