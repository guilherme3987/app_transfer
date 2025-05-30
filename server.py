import socket
import os
import csv
from datetime import datetime
from con_config import obter_dados_conexao

HOST, PORT, TAM_BUFFER = obter_dados_conexao()
BASE_DIR = "recebidos"

def iniciar_servidor():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind((HOST, PORT))
    sock.listen(1)
    print(f"🖥️ Servidor ouvindo em {HOST}:{PORT}")

    conn, addr = sock.accept()
    print(f"🔌 Conexão estabelecida com {addr}")

    try:
        while True:
            tipo = conn.recv(TAM_BUFFER).decode()
            if not tipo or tipo == "FIM":
                break

            if tipo == "FILE":
                receber_arquivo(conn, addr)
            elif tipo == "DIR":
                receber_pasta(conn, addr)

    except Exception as e:
        print(f"❌ Erro: {e}")
    finally:
        conn.close()
        sock.close()
        print("🛑 Servidor encerrado")

def receber_arquivo(conn, addr, caminho_relativo=""):
    """Recebe um arquivo com caminho relativo"""
    nome_arquivo = conn.recv(TAM_BUFFER).decode()
    caminho_completo = os.path.join(BASE_DIR, caminho_relativo, nome_arquivo)
    
    os.makedirs(os.path.dirname(caminho_completo), exist_ok=True)
    
    tamanho = int.from_bytes(conn.recv(8), byteorder='big')
    recebidos = 0
    inicio = datetime.now()

    with open(caminho_completo, 'wb') as f:
        while recebidos < tamanho:
            dados = conn.recv(min(TAM_BUFFER, tamanho - recebidos))
            if not dados:
                break
            f.write(dados)
            recebidos += len(dados)

    status = "SUCESSO" if recebidos == tamanho else "FALHA"
    conn.sendall(status.encode())
    
    print(f"📄 Arquivo recebido: {os.path.join(caminho_relativo, nome_arquivo)}")
    registrar_log(nome_arquivo, recebidos, inicio, datetime.now(), addr[0], status)

def receber_pasta(conn, addr):
    """Recebe uma pasta com estrutura completa"""
    nome_pasta = conn.recv(TAM_BUFFER).decode()
    print(f"📦 Recebendo pasta: {nome_pasta}")

    while True:
        tipo = conn.recv(TAM_BUFFER).decode()
        if tipo == "FIM_DIR":
            break
        
        if tipo == "FILE_IN_DIR":
            caminho_rel = conn.recv(TAM_BUFFER).decode()
            receber_arquivo(conn, addr, os.path.join(nome_pasta, caminho_rel))
        
        elif tipo == "SUB_DIR":
            subpasta = conn.recv(TAM_BUFFER).decode()
            os.makedirs(os.path.join(BASE_DIR, nome_pasta, subpasta), exist_ok=True)

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