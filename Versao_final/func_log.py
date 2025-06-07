import csv
import os
from datetime import datetime

def obter_config_log():
    print("#### <ENTROU EM obter_config_log> ####\n")

    NOME_ARQUIVO_LOG = "log.csv"
    CABECALHO_LOG = [
        'TIMESTAMP',
        'ID_CLIENTE',
        'IP_CLIENTE',
        'ARQUIVO',
        'TAMANHO_ARQUIVO_BYTES',
        'TIPO_ARQUIVO',
        'STATUS',
    ]
    print(f"NOME_ARQUIVO_LOG: {NOME_ARQUIVO_LOG}\nCABECALHO_LOG: {CABECALHO_LOG}\n")
    
    return NOME_ARQUIVO_LOG, CABECALHO_LOG

NOME_ARQUIVO_LOG, CABECALHO_LOG = obter_config_log()


def inicializar_log():##
    print("#### <ENTROU EM criar_log> ####\n") 

    if not os.path.exists(NOME_ARQUIVO_LOG):
        with open(NOME_ARQUIVO_LOG, 'w', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(CABECALHO_LOG)            
        print(f"Arquivo de log '{NOME_ARQUIVO_LOG}' criado com sucesso.\n")
    else:
        print(f"Arquivo de log '{NOME_ARQUIVO_LOG}' já existe.\n")

def registrar_log(cliente_id, ip_cliente, arquivo, tamanho_arquivo, tipo_arquivo, status):
    print("#### <ENTROU EM registra_log> ####\n")

    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    with open(NOME_ARQUIVO_LOG, 'a', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([ 
            timestamp,
            cliente_id,
            ip_cliente,
            arquivo,
            tamanho_arquivo,
            tipo_arquivo,
            status
        ])
    print(f"Log registrado para o cliente {cliente_id}.\n")