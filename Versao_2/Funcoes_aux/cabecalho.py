'''
Cabeçalho do arquivo:
    tipo|tamanho|checksum|nome  -- Problemas com arquivos com | no nome

Resolver isso com JSON
'''

import os

from Funcoes_aux.con_config import obter_dados_conexao
from Funcoes_aux.checksum import calcular_checksum_dados


_,_,TAM_BUFFER, TAM_CABECALHO = obter_dados_conexao()

def criar_cabecalho_arquivo(tipo, nome_arquivo, dados):
    print("\n##########################\n<ENTROU EM CRIAR_CABECALHO_ARQUIVO>\n############################")
    
    checksum = calcular_checksum_dados(dados)

    tamanho = len(dados)

    cabecalho = f"{tipo}|{tamanho}|{checksum}|{nome_arquivo}"
    
    if len(cabecalho) > TAM_CABECALHO:
        cabecalho = cabecalho[:TAM_CABECALHO]
    elif len(cabecalho) < TAM_CABECALHO:
        cabecalho += ' ' * (TAM_CABECALHO - len(cabecalho))  # Preenche com espaços
    
    return cabecalho.encode('utf-8') 

'''
def criar_cabecalho_tamanho(tamanho):
    print("\n##########################\n<ENTROU EM CRIAR_CABECALHO_TAMANHO>\n############################")
    
    cabecalho = f"{tamanho}"
    
    if len(cabecalho) < TAM_CABECALHO:
        cabecalho += ' ' * (TAM_CABECALHO - len(cabecalho))  # Preenche com espaços
    
    return cabecalho.encode('utf-8')  # Converte para bytes

'''

def enviar_cabecalho(sock, cabecalho):
    print("\n##########################\n<ENTROU EM ENVIAR_CABECALHO>\n############################")
    
    sock.sendall(cabecalho)  # Envia o cabeçalho do arquivo
    
    print(f"Cabecalho enviado: {cabecalho.decode('utf-8').strip()}")

def receber_cabecalho(sock):
    print("\n##########################\n<ENTROU EM RECEBER_CABECALHO>\n############################")
    
    cabecalho_bytes = receber_dados(sock, TAM_CABECALHO)  # Recebe o cabeçalho do arquivo

    if not cabecalho_bytes:
        return None

    cabecalho = cabecalho_bytes.decode('utf-8').strip()  # Decodifica o cabeçalho para string
    print(f"Cabecalho recebido: {cabecalho}")
    partes = cabecalho.split('|')  # Divide o cabeçalho em partes

    if len(partes) != 4:
        print("\n### ERRO: Cabeçalho deve ter 4 partes separadas por '|' ###")
        print(f"Formato esperado: tipo|tamanho|checksum|nome")
        print(f"Formato recebido: {cabecalho}")
        return None
    else:
        print(f"### Formato do cabeçalho válido: {partes} ###")
        return {
            'tipo': partes[0],
            'tamanho': int(partes[1]),
            'checksum': partes[2],
            'nome': partes[3]
        }

    '''
    cabecalho = sock.recv(TAM_CABECALHO)  # Recebe o cabeçalho do arquivo
    
    if not cabecalho:
        return None
    
    print(f"Cabecalho recebido: {cabecalho.decode('utf-8').strip()}")
    
    return cabecalho.decode('utf-8').strip()  # Retorna o cabeçalho como string'''

def receber_dados(sock, tamanho_esperado):
    print("\n##########################\n<ENTROU EM RECEBER_DADOS>\n############################")
    
    dados = b''
    bytes_recebidos = 0
    
    while bytes_recebidos < tamanho_esperado:
        parte = sock.recv(min(TAM_BUFFER, tamanho_esperado - bytes_recebidos))
        if not parte:
            break
        dados += parte
        bytes_recebidos += len(parte)
    
    if bytes_recebidos == tamanho_esperado:
        return dados
    return None

def receber_dados_com_cabecalho(sock):
    cabecalho = receber_dados(sock, TAM_CABECALHO)
    if not cabecalho:
        return None
    
    tamanho = int(cabecalho.decode('utf-8').strip())
    return receber_dados(sock, tamanho)
