import csv
import os
from datetime import datetime

def log():
    print("#### <ENTROU EM log> ####\n")

    LOG_FILE = "log.csv"
    LOG_CABECALHO = [
        'TIMESTAMP',
        'CLIENTE_ID',
        'IP_CLIENTE',
        'ARQUIVO',
        'TAMANHO_ARQUIVO_BYTES',
        'TIPO_ARQUIVO',
        'STATUS',
    ]
    print(f"LOG_FILE: {LOG_FILE}\nLOG_CABECALHO: {LOG_CABECALHO}\n")
    
    return LOG_FILE, LOG_CABECALHO

LOG_FILE, LOG_CABECALHO = log()

def criar_log():##
    print("#### <ENTROU EM criar_log> ####\n") 

    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, 'w', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(LOG_CABECALHO)            
        print(f"Arquivo de log '{LOG_FILE}' criado com sucesso.\n")

def registra_log(cliente_id, ip_cliente, arquivo, tamanho_arquivo, tipo_arquivo, status):
    print("#### <ENTROU EM registra_log> ####\n")

    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
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