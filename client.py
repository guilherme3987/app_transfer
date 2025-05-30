import socket
import os
from con_config import obter_dados_conexao

_, PORT, TAM_BUFFER = obter_dados_conexao()

def enviar_arquivo(sock, caminho):
    """Envia um único arquivo"""
    nome = os.path.basename(caminho)
    tamanho = os.path.getsize(caminho)
    
    sock.sendall("FILE".encode())
    sock.sendall(nome.encode())
    sock.sendall(tamanho.to_bytes(8, byteorder='big'))
    
    with open(caminho, 'rb') as f:
        while True:
            dados = f.read(TAM_BUFFER)
            if not dados:
                break
            sock.sendall(dados)
    
    return sock.recv(TAM_BUFFER).decode() == "SUCESSO"

def enviar_pasta(sock, caminho_pasta):
    """Envia todos os arquivos de uma pasta"""
    nome_pasta = os.path.basename(caminho_pasta)
    sock.sendall("DIR".encode())
    sock.sendall(nome_pasta.encode())

    for raiz, _, arquivos in os.walk(caminho_pasta):
        for arquivo in arquivos:
            caminho_completo = os.path.join(raiz, arquivo)
            sock.sendall("FILE_IN_DIR".encode())
            if not enviar_arquivo(sock, caminho_completo):
                return False

    sock.sendall("FIM_DIR".encode())
    return True

def iniciar_cliente():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((input("IP do servidor: "), PORT))
    
    caminho = input("Caminho do arquivo/pasta: ")
    if os.path.isfile(caminho):
        enviar_arquivo(sock, caminho)
    elif os.path.isdir(caminho):
        enviar_pasta(sock, caminho)
    
    sock.sendall("FIM".encode())
    sock.close()

if __name__ == "__main__":
    iniciar_cliente()