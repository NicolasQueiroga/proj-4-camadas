from tqdm import tqdm

def status(process, total_pkgs=0, VERBOSE = False):
    status_dict = {
        'read_msg' : 'Mensagem lida com sucesso',
        'msg_conv' : 'Mensagem convertida em pacotes',
    }
    if VERBOSE:
        print(f'---> {status_dict[process]}')
    else:
        pbar = tqdm(total=total_pkgs,unit='packages',desc='Pacotes Enviados:')
        if process == 'update_load_bar':
            pbar.update()
        elif process == 'close_load_bar':
            pbar.close()


