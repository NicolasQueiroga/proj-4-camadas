from tqdm import tqdm

def status(process, total_pkgs=0, VERBOSE = False):
    status_dict = {
        'read_msg' : 'Mensagem encontrada com sucesso',
        'msg_conv' : 'Mensagem convertida em pacotes',
    }
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

    


    if VERBOSE:
        print(f'---> {status_dict[process]}\n')
    else:
        pbar = tqdm(total=total_pkgs,unit='packages',desc='Pacotes Enviados:')
        if process == 'update_load_bar':
            pbar.update()
        elif process == 'close_load_bar':
            pbar.close()


