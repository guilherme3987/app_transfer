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
        while True:
            # Recebe o tipo de transferência (FILE ou DIR)
            tipo = conn.recv(TAM_BUFFER).decode()
            if not tipo or tipo == "FIM":
                break

            if tipo == "FILE":
                receber_arquivo(conn, addr)
            elif tipo == "DIR":
                receber_pasta(conn, addr)

    except Exception as e:
        print(f"[Servidor] Erro: {e}")
    finally:
        conn.close()
        sock.close()
        print("[Servidor] Conexão encerrada.")

def receber_arquivo(conn, addr):
    """Recebe um único arquivo"""
    caminho = conn.recv(TAM_BUFFER).decode()
    nome_arquivo = os.path.basename(caminho)
    caminho_destino = os.path.join("recebidos", nome_arquivo)
    
    os.makedirs(os.path.dirname(caminho_destino), exist_ok=True)
    
    tamanho_arquivo = int.from_bytes(conn.recv(8), byteorder='big')
    tamanho_recebido = 0
    inicio = datetime.now()

    with open(caminho_destino, 'wb') as f:
        while tamanho_recebido < tamanho_arquivo:
            dados = conn.recv(min(TAM_BUFFER, tamanho_arquivo - tamanho_recebido))
            if not dados:
                break
            f.write(dados)
            tamanho_recebido += len(dados)

    status = "SUCESSO" if tamanho_recebido == tamanho_arquivo else "FALHA"
    conn.sendall(status.encode())
    
    registrar_log(nome_arquivo, tamanho_recebido, inicio, datetime.now(), addr[0], status)

def receber_pasta(conn, addr):
    """Recebe múltiplos arquivos de uma pasta"""
    nome_pasta = conn.recv(TAM_BUFFER).decode()
    caminho_destino = os.path.join("recebidos", nome_pasta)
    os.makedirs(caminho_destino, exist_ok=True)

    while True:
        tipo = conn.recv(TAM_BUFFER).decode()
        if tipo == "FIM_DIR":
            break
        
        if tipo == "FILE_IN_DIR":
            receber_arquivo(conn, addr)

def registrar_log(nome, tamanho, inicio, fim, ip, status):
    with open('log_transferencias.csv', 'a', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([
            nome,
            tamanho,
            inicio.isoformat(),
            fim.isoformat(),
            (fim - inicio).total_seconds(),
            ip,
            status
        ])

if __name__ == "__main__":
    iniciar_servidor()