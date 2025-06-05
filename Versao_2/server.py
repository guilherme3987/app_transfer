import socket
import os
import hashlib
from datetime import datetime
import threading
from con_config import obter_dados_conexao

IP, PORT, TAM_BUFFER, TAM_CABECALHO = obter_dados_conexao()

def calcular_hash_dados(dados):
    hasher = hashlib.sha256()
    hasher.update(dados)
    return hasher.hexdigest()

def receber_arquivo(sock, nome_arquivo, tamanho, hash_esperado, diretorio_destino='.'):
    try:
        caminho_completo = os.path.join(diretorio_destino, nome_arquivo)
        
        # Cria diretório de destino se não existir
        os.makedirs(os.path.dirname(caminho_completo), exist_ok=True)
        
        # Envia confirmação para o cliente
        enviar_dados(sock, b"OK")
        
        # Recebe o arquivo em chunks
        dados_recebidos = bytearray()
        bytes_recebidos = 0
        
        while bytes_recebidos < tamanho:
            dados = sock.recv(min(TAM_BUFFER, tamanho - bytes_recebidos))
            if not dados:
                break
            dados_recebidos.extend(dados)
            bytes_recebidos += len(dados)
        
        # Verifica integridade
        hash_recebido = calcular_hash_dados(dados_recebidos)
        if hash_recebido != hash_esperado:
            enviar_dados(sock, "ERRO: Hash do arquivo não corresponde".encode('utf-8'))
            return False
        
        # Salva o arquivo
        with open(caminho_completo, 'wb') as f:
            f.write(dados_recebidos)
        
        enviar_dados(sock, b"Arquivo recebido com sucesso")
        return True
        
    except Exception as e:
        print(f"Erro ao receber arquivo: {e}")
        enviar_dados(sock, f"ERRO: {str(e)}".encode('utf-8'))
        return False

def enviar_dados(sock, dados):
    try:
        cabecalho = f"{len(dados):<{TAM_CABECALHO}}".encode('utf-8')
        sock.sendall(cabecalho)
        sock.sendall(dados)
        return True
    except Exception as e:
        print(f"Erro ao enviar dados: {e}")
        return False

def lidar_cliente(client_socket, addr):
    print(f"Iniciando tratamento para cliente {addr}...")
    diretorio_atual = None

    try:
        while True:
            # Recebe o cabeçalho
            tamanho_dados = receber_mensagem(client_socket)
            if tamanho_dados is None:
                break
            
            # Recebe os dados
            dados = receber_dados(client_socket, tamanho_dados)
            if dados is None:
                break
            
            # Verifica se é um comando especial
            if dados.startswith(b"ARQUIVO|"):
                partes = dados.decode('utf-8').split('|')
                if len(partes) == 5:
                    _, nome_arquivo, str_tamanho, data_modificacao, hash_arquivo = partes
                    tamanho_arquivo = int(str_tamanho)
                    
                    print(f"Preparando para receber arquivo: {nome_arquivo} ({tamanho_arquivo} bytes)")
                    
                    if diretorio_atual:
                        sucesso = receber_arquivo(client_socket, nome_arquivo, tamanho_arquivo, hash_arquivo, diretorio_atual)
                    else:
                        sucesso = receber_arquivo(client_socket, nome_arquivo, tamanho_arquivo, hash_arquivo)
                    
                    if not sucesso:
                        print(f"Falha ao receber arquivo {nome_arquivo}")
            
            elif dados.startswith(b"DIRETORIO|"):
                nome_diretorio = dados.decode('utf-8').split('|')[1]
                diretorio_atual = os.path.join("recebidos", nome_diretorio)
                os.makedirs(diretorio_atual, exist_ok=True)
                print(f"Preparando para receber diretório: {nome_diretorio}")
                enviar_dados(client_socket, b"OK")
            
            elif dados == b"FIM_DIRETORIO":
                print("Diretório recebido com sucesso!")
                diretorio_atual = None
            
            else:
                print(f"Dados recebidos: {dados}")
                resposta = b"Dados recebidos com sucesso\n"
                enviar_dados(client_socket, resposta)

    except Exception as e:
        print(f"Erro ao lidar com o cliente: {e}")
    finally:
        client_socket.close()

def receber_mensagem(sock):
    try:
        cabecalho = sock.recv(TAM_CABECALHO).strip()
        if not cabecalho:
            return None
        return int(cabecalho.decode('utf-8'))
    except Exception as e:
        print(f"Erro ao receber mensagem: {e}")
        return None

def receber_dados(sock, tamanho_dados):
    recebidos = []
    bytes_restantes = tamanho_dados

    while bytes_restantes > 0:
        try:
            dados = sock.recv(min(bytes_restantes, TAM_BUFFER))
            if not dados:
                return None
            recebidos.append(dados)
            bytes_restantes -= len(dados)
        except Exception as e:
            print(f"Erro ao receber dados: {e}")
            return None
    return b''.join(recebidos)

def iniciar_servidor(host=IP, port=PORT):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(5)
    print(f"Servidor escutando em {host}:{port}")

    try:
        while True:
            client_socket, addr = server_socket.accept()
            print(f"Conexão recebida de {addr}")

            thread = threading.Thread(target=lidar_cliente, args=(client_socket, addr))
            thread.daemon = True
            thread.start()

    except KeyboardInterrupt:
        print("\nServidor sendo desligado (Ctrl+C detectado).")
    except Exception as e:
        print(f"Erro no loop principal do servidor: {e}")
    finally:
        server_socket.close()
        print("Servidor encerrado.")

if __name__ == "__main__":
    # Cria diretório para arquivos recebidos se não existir
    os.makedirs("recebidos", exist_ok=True)
    iniciar_servidor()