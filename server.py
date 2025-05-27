# servidor.py
import socket
import os

HOST = '0.0.0.0'  # Aceita conexões de qualquer IP
PORT = 5001
TAM_BUFFER = 1024

def iniciar_servidor():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind((HOST, PORT))
    sock.listen(1)
    print(f"[Servidor] Escutando em {HOST}:{PORT}...")

    conn, addr = sock.accept()
    print(f"[Servidor] Conexão estabelecida com {addr}")

    try:
        # Recebe o nome do arquivo
        nome_arquivo = conn.recv(TAM_BUFFER).decode()
        print(f"[Servidor] Nome do arquivo: {nome_arquivo}")

        # Abre arquivo para escrita binária
        with open(nome_arquivo, 'wb') as f:
            while True:
                dados = conn.recv(TAM_BUFFER)
                if not dados:
                    break
                f.write(dados)
        print(f"[Servidor] Arquivo '{nome_arquivo}' recebido com sucesso.")
    except Exception as e:
        print(f"[Servidor] Erro: {e}")
    finally:
        conn.close()
        sock.close()
        print("[Servidor] Conexão encerrada.")

if __name__ == "__main__":
    iniciar_servidor()
