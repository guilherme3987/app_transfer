import socket
import os
from con_config import obter_dados_conexao

_, PORT, TAM_BUFFER = obter_dados_conexao()

def enviar_arquivo(sock, caminho_arquivo, caminho_relativo=""):
    """Envia um arquivo com caminho relativo"""
    nome = os.path.basename(caminho_arquivo)
    tamanho = os.path.getsize(caminho_arquivo)
    
    sock.sendall(nome.encode())
    sock.sendall(tamanho.to_bytes(8, byteorder='big'))
    
    with open(caminho_arquivo, 'rb') as f:
        while True:
            dados = f.read(TAM_BUFFER)
            if not dados:
                break
            sock.sendall(dados)
    
    return sock.recv(TAM_BUFFER).decode() == "SUCESSO"

def enviar_pasta(sock, caminho_pasta):
    """Envia pasta com estrutura completa"""
    nome_pasta = os.path.basename(caminho_pasta)
    sock.sendall("DIR".encode())
    sock.sendall(nome_pasta.encode())

    for raiz, subpastas, arquivos in os.walk(caminho_pasta):
        # Envia subpastas primeiro
        rel_path = os.path.relpath(raiz, caminho_pasta)
        if rel_path != ".":
            sock.sendall("SUB_DIR".encode())
            sock.sendall(rel_path.encode())
        
        # Envia arquivos
        for arquivo in arquivos:
            sock.sendall("FILE_IN_DIR".encode())
            caminho_rel = os.path.relpath(raiz, caminho_pasta)
            sock.sendall(caminho_rel.encode())
            if not enviar_arquivo(sock, os.path.join(raiz, arquivo)):
                return False

    sock.sendall("FIM_DIR".encode())
    return True

def iniciar_cliente():
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        ip = input("IP do servidor: ").strip()
        sock.connect((ip, PORT))
        
        caminho = input("Caminho do arquivo/pasta: ").strip()
        
        if os.path.isfile(caminho):
            sock.sendall("FILE".encode())
            if enviar_arquivo(sock, caminho):
                print("✅ Arquivo enviado com sucesso!")
            else:
                print("❌ Falha no envio do arquivo")
        elif os.path.isdir(caminho):
            sock.sendall("DIR".encode())
            if enviar_pasta(sock, caminho):
                print("✅ Pasta enviada com sucesso!")
            else:
                print("❌ Falha no envio da pasta")
        else:
            print("⚠️ Caminho inválido")
        
        sock.sendall("FIM".encode())
    except ConnectionError as e:
        print(f"🔌 Erro de conexão: {e}")
    except Exception as e:
        print(f"⚠️ Erro inesperado: {e}")
    finally:
        sock.close()
        print("🛑 Cliente encerrado")

if __name__ == "__main__":
    iniciar_cliente()