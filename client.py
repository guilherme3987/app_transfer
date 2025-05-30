import socket
import os
from datetime import datetime
import time
from con_config import obter_dados_conexao  

_, PORT, TAM_BUFFER = obter_dados_conexao()  


def iniciar_cliente():
    ip_servidor = input("Digite o IP do servidor (VM Linux): ").strip()
    caminho_arquivo = input("Digite o caminho completo do arquivo a ser enviado: ").strip()

    if not os.path.exists(caminho_arquivo):
        print("[Cliente] Erro: Arquivo não encontrado.")
        return

    nome_arquivo = os.path.basename(caminho_arquivo)

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((ip_servidor, PORT))
        print(f"[Cliente] Conectado ao servidor {ip_servidor}:{PORT}")

        # Envia nome do arquivo
        sock.sendall(nome_arquivo.encode())

        # Aguarda um pequeno tempo para garantir que o nome foi enviado
        time.sleep(0.5)

        # Marca o início da transferência
        inicio = datetime.now()

        # Envia dados do arquivo
        with open(caminho_arquivo, 'rb') as f:
            while True:
                dados = f.read(TAM_BUFFER)
                if not dados:
                    break
                sock.sendall(dados)

        fim = datetime.now()
        duracao = (fim - inicio).total_seconds()

        print(f"[Cliente] Arquivo enviado com sucesso.")
        print(f"[Cliente] Início: {inicio}")
        print(f"[Cliente] Fim: {fim}")
        print(f"[Cliente] Duração: {duracao:.3f} segundos")

    except Exception as e:
        print(f"[Cliente] Erro: {e}")
    finally:
        sock.close()
        print("[Cliente] Conexão encerrada.")

if __name__ == "__main__":
    iniciar_cliente()