import csv
import os
from datetime import datetime
# 192.168.41.213 WSL
#Constantes para criar arquivo de log
NOME_ARQUIVO_LOG = "log.csv"
    
CABECALHO_LOG = [
    'TIMESTAMP',
    'ID_CLIENTE',
    'IP_CLIENTE',
    'ARQUIVO',
    'TAMANHO_ARQUIVO_BYTES',
    'TAMANHO_ARQUIVO_MB', 
    'TIPO_ARQUIVO',
    'STATUS',
    'TEMPO_TRANSFERENCIA_SEGUNDOS', 
    'TAXA_TRANSFERENCIA_MBPS' 
]

def obter_config_log(): 
    print("#### <ENTROU EM obter_config_log> ####\n")

    print(f"NOME_ARQUIVO_LOG: {NOME_ARQUIVO_LOG}\nCABECALHO_LOG: {CABECALHO_LOG}\n")
    
    return NOME_ARQUIVO_LOG, CABECALHO_LOG

#NOME_ARQUIVO_LOG, CABECALHO_LOG = obter_config_log()

def inicializar_log():
    print("#### <ENTROU EM inicializar_log> ####\n") 

    if not os.path.exists(NOME_ARQUIVO_LOG):
        
        with open(NOME_ARQUIVO_LOG, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(CABECALHO_LOG)            
        print(f"INFO: Arquivo de log '{NOME_ARQUIVO_LOG}' criado com sucesso.\n")
    else:
        print(f"INFO: Arquivo de log '{NOME_ARQUIVO_LOG}' já existe.\n")

def registrar_log(id_cliente, ip_cliente, arquivo, tamanho_arquivo, tipo_arquivo, status, 
                   tempo_transferencia_segundos=None, taxa_transferencia_mbps=None): 
    print("#### <ENTROU EM registrar_log> ####\n")

    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Calcular tamanho em MB
    if tamanho_arquivo is not None and tamanho_arquivo > 0:
        tamanho_arquivo_mb = round(tamanho_arquivo / (1024 * 1024), 2)
    else:
        tamanho_arquivo_mb = 0
    
    # Formatar taxa para exibição
    if taxa_transferencia_mbps is not None:
        taxa_transferencia_mbps_formatada = round(taxa_transferencia_mbps, 2)
    else:
        taxa_transferencia_mbps_formatada = None

    try:
        with open(NOME_ARQUIVO_LOG, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                timestamp,
                id_cliente,
                ip_cliente,
                arquivo,
                tamanho_arquivo,
                tamanho_arquivo_mb, 
                tipo_arquivo,
                status,
                tempo_transferencia_segundos, 
                taxa_transferencia_mbps_formatada 
            ])
        print(f"INFO: Log registrado para o cliente {id_cliente}.\n")
    except Exception as e:
        print(f"ERRO: Falha ao escrever no arquivo de log '{NOME_ARQUIVO_LOG}': {e}\n")