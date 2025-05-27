# cliente.py
import socket
import os

# Altere para o IP real da sua VM Linux (ex: 192.168.0.100)
HOST = input("Digite o IP do servidor (VM Linux): ").strip()
PORT = 5001
TAM_BUFFER = 1024

def enviar_arquivo():
    caminho_arquivo = input("Digite o caminho completo do arquivo a ser enviado: ").strip()

    if not os.path.exists(caminho_arquivo):
        print("[Cliente] Arquivo não encontrado.")
        return

    nome_arquivo = os.path.basename(caminho_arquivo)

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((HOST, PORT))
        print(f"[Cliente] Conectado a {HOST}:{PORT}")

        # Envia nome do arquivo primeiro
        sock.sendall(nome_arquivo.encode())

        # Envia conteúdo do arquivo
        with open(caminho_arquivo, 'rb') as f:
            while True:
                dados = f.read(TAM_BUFFER)
                if not dados:
                    break
                sock.sendall(dados)

        print(f"[Cliente] Arquivo '{nome_arquivo}' enviado com sucesso.")
    except Exception as e:
        print(f"[Cliente] Erro: {e}")
    finally:
        sock.close()
        print("[Cliente] Conexão encerrada.")

if __name__ == "__main__":
    enviar_arquivo()
