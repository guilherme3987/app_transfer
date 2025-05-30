import socket
import os
import csv
from datetime import datetime
from con_config import obter_dados_conexao  

HOST, PORT, TAM_BUFFER = obter_dados_conexao()


def iniciar_servidor():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind((HOST, PORT))
    sock.listen(1)
    print(f"[Servidor] Escutando em {HOST}:{PORT}...")

    conn, addr = sock.accept()
    print(f"[Servidor] Conexão estabelecida com {addr}")

    try:
        nome_arquivo = conn.recv(TAM_BUFFER).decode().strip()
        print(f"[Servidor] Nome do arquivo: {nome_arquivo}")

        inicio = datetime.now()
        tamanho_recebido = 0

        with open(nome_arquivo, 'wb') as f:
            while True:
                dados = conn.recv(TAM_BUFFER)
                if not dados:
                    break
                f.write(dados)
                tamanho_recebido += len(dados)

        fim = datetime.now()
        duracao = (fim - inicio).total_seconds()

        print(f"[Servidor] Arquivo '{nome_arquivo}' recebido com sucesso.")
        print(f"[Servidor] Tamanho: {tamanho_recebido} bytes")
        print(f"[Servidor] Início: {inicio}")
        print(f"[Servidor] Fim: {fim}")
        print(f"[Servidor] Duração: {duracao:.3f} segundos")

        registrar_log(nome_arquivo, tamanho_recebido, inicio, fim, duracao)

    except Exception as e:
        print(f"[Servidor] Erro: {e}")
    finally:
        conn.close()
        sock.close()
        print("[Servidor] Conexão encerrada.")

def registrar_log(nome_arquivo, tamanho, inicio, fim, duracao):
    log_csv = 'log_transferencias.csv'
    existe = os.path.exists(log_csv)

    with open(log_csv, 'a', newline='') as csvfile:
        writer = csv.writer(csvfile)
        if not existe:
            writer.writerow(['nome_arquivo', 'tamanho_bytes', 'inicio', 'fim', 'duracao_segundos'])
        writer.writerow([
            nome_arquivo,
            tamanho,
            inicio.isoformat(),
            fim.isoformat(),
            f"{duracao:.3f}"
        ])

if __name__ == "__main__":
    iniciar_servidor()