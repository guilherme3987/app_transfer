import os
import json #

from Funcoes_aux.con_config import obter_dados_conexao #
from Funcoes_aux.checksum import calcular_checksum_dados #


_,_,TAM_BUFFER, TAM_CABECALHO = obter_dados_conexao() #

def criar_cabecalho_arquivo(tipo, nome_arquivo, dados=b''): # Ensure dados has a default value
    print("\n##########################\n<ENTROU EM CRIAR_CABECALHO_ARQUIVO>\n############################")
    
    checksum = calcular_checksum_dados(dados) #
    tamanho = len(dados) #

    # Create a dictionary for the header
    header_dict = {
        'tipo': tipo,
        'tamanho': tamanho,
        'checksum': checksum,
        'nome': nome_arquivo
    }
    print(f"### Dicionario criado: {header_dict} ###") #
    
    # Convert the dictionary to a JSON string
    cabecalho_json = json.dumps(header_dict) #
    
    # Encode the JSON string to bytes
    cabecalho_bytes = cabecalho_json.encode('utf-8') #

    # Pad or truncate the header to fit TAM_CABECALHO
    if len(cabecalho_bytes) > TAM_CABECALHO:
        print(f"### AVISO: Cabeçalho JSON ({len(cabecalho_bytes)} bytes) é maior que TAM_CABECALHO ({TAM_CABECALHO} bytes). Será truncado! ###") #
        cabecalho_bytes = cabecalho_bytes[:TAM_CABECALHO] #
    elif len(cabecalho_bytes) < TAM_CABECALHO:
        cabecalho_bytes += b' ' * (TAM_CABECALHO - len(cabecalho_bytes)) #
    
    return cabecalho_bytes #

def enviar_cabecalho(sock, cabecalho):
    print("\n##########################\n<ENTROU EM ENVIAR_CABECALHO>\n############################")
    
    sock.sendall(cabecalho) #
    
    print(f"Cabecalho enviado: {cabecalho.decode('utf-8').strip()}") #

def receber_cabecalho(sock):
    print("\n##########################\n<ENTROU EM RECEBER_CABECALHO>\n############################")
    
    cabecalho_bytes = receber_dados(sock, TAM_CABECALHO) #

    if not cabecalho_bytes: #
        return None #

    cabecalho_str = cabecalho_bytes.decode('utf-8').strip() #
    print(f"Cabecalho recebido (RAW): {cabecalho_str}") #
    
    try:
        cabecalho_info = json.loads(cabecalho_str) #
    except json.JSONDecodeError as e: #
        print(f"\n### ERRO: Falha ao decodificar cabeçalho JSON: {e} ###") #
        print(f"Cabeçalho recebido: '{cabecalho_str}'") #
        return None #

    # Valida as chaves esperadas no dicionário
    chaves_esperadas = ['tipo', 'tamanho', 'checksum', 'nome'] #
    for chave in chaves_esperadas: #
        if chave not in cabecalho_info: #
            print(f"\n### ERRO: Cabeçalho JSON não contém a chave esperada: '{chave}'. ###") #
            print(f"Chaves esperadas: {chaves_esperadas}") #
            print(f"Chaves recebidas (Conteúdo do cabeçalho): {cabecalho_info}") #
            return None #
    
    # Valida o tipo de dados do tamanho
    if not isinstance(cabecalho_info['tamanho'], int): #
        print(f"\n### ERRO: O campo 'tamanho' no cabeçalho não é um inteiro. ###") #
        print(f"Valor de tamanho recebido: {cabecalho_info['tamanho']}") #
        return None #

    print(f"### Cabeçalho JSON decodificado: {cabecalho_info} ###") #
    return cabecalho_info # CRITICAL FIX: Ensure this line exists and is properly indented

def receber_dados(sock, tamanho_esperado):
    print("\n##########################\n<ENTROU EM RECEBER_DADOS>\n############################") #
    
    dados = b'' #
    bytes_recebidos = 0 #
    
    while bytes_recebidos < tamanho_esperado: #
        parte = sock.recv(min(TAM_BUFFER, tamanho_esperado - bytes_recebidos)) #
        if not parte: #
            break #
        dados += parte #
        bytes_recebidos += len(parte) #
    
    if bytes_recebidos == tamanho_esperado: #
        return dados #
    return None #

def receber_dados_com_cabecalho(sock):
    # This function is used for responses, not the main header.
    # It still uses the old fixed-size numeric header format for 'tamanho'.
    # If responses were also to use JSON headers, this function would need a JSON parser.
    cabecalho = receber_dados(sock, TAM_CABECALHO) #
    if not cabecalho: #
        return None #
    
    try: #
        tamanho = int(cabecalho.decode('utf-8').strip()) #
    except ValueError: #
        print(f"\n### ERRO: Cabeçalho de tamanho inválido em receber_dados_com_cabecalho: '{cabecalho.decode('utf-8').strip()}' ###") #
        return None #
        
    return receber_dados(sock, tamanho) #