import socket
import os
import hashlib
from datetime import datetime
from con_config import obter_dados_conexao

IP, PORT, TAM_BUFFER, TAM_CABECALHO = obter_dados_conexao()

### Funções de Envio e Recebimento de Dados ###
def enviar_dados(sock, dados):
    '''
    Envia os dados com um cabeçalho fixo que informa o tamanho dos dados.
    '''
    try:
        cabecalho = f"{len(dados):<{TAM_CABECALHO}}".encode('utf-8')
        sock.sendall(cabecalho)
        sock.sendall(dados)
        return True
    except Exception as e:
        print(f"Erro ao enviar dados: {e}")
        return False

def receber_mensagem(sock):
    try:
        cabecalho = sock.recv(TAM_CABECALHO).strip()
        if not cabecalho:
            print("Conexão fechada pelo servidor.")
            return None
        tamanho_dados = int(cabecalho.decode('utf-8'))
        return tamanho_dados
    except Exception as e:
        print(f"Erro ao receber dados: {e}")
        return None

def receber_dados(sock, tamanho_dados):
    recebidos = []
    bytes_restantes = tamanho_dados

    while bytes_restantes > 0:
        try:
            dados = sock.recv(min(bytes_restantes, TAM_BUFFER))
            if not dados:
                print("Conexão fechada pelo servidor.")
                return None
            recebidos.append(dados)
            bytes_restantes -= len(dados)
        except Exception as e:
            print(f"Erro ao receber dados: {e}")
            return None
    return b''.join(recebidos)

### Funções para envio de arquivos e diretórios ###
def calcular_hash_arquivo(caminho_arquivo):
    hasher = hashlib.sha256()
    with open(caminho_arquivo, 'rb') as f:
        while True:
            dados = f.read(TAM_BUFFER)
            if not dados:
                break
            hasher.update(dados)
    return hasher.hexdigest()

def enviar_arquivo(sock, caminho_arquivo):
    try:
        # Verifica se o arquivo existe
        if not os.path.isfile(caminho_arquivo):
            print(f"Arquivo não encontrado: {caminho_arquivo}")
            return False
        
        # Obtém informações do arquivo
        tamanho = os.path.getsize(caminho_arquivo)
        nome_arquivo = os.path.basename(caminho_arquivo)
        data_modificacao = datetime.fromtimestamp(os.path.getmtime(caminho_arquivo)).isoformat()
        hash_arquivo = calcular_hash_arquivo(caminho_arquivo)
        
        # Envia metadados
        metadados = f"ARQUIVO|{nome_arquivo}|{tamanho}|{data_modificacao}|{hash_arquivo}"
        if not enviar_dados(sock, metadados.encode('utf-8')):
            return False
        
        # Espera confirmação do servidor
        tamanho_resposta = receber_mensagem(sock)
        if not tamanho_resposta:
            return False
        resposta = receber_dados(sock, tamanho_resposta)
        if resposta != b"OK":
            print("Servidor não está pronto para receber o arquivo")
            return False
        
        # Envia o arquivo em chunks
        with open(caminho_arquivo, 'rb') as f:
            total_enviado = 0
            while total_enviado < tamanho:
                dados = f.read(TAM_BUFFER)
                if not dados:
                    break
                sock.sendall(dados)
                total_enviado += len(dados)
        
        # Verifica confirmação final
        tamanho_resposta = receber_mensagem(sock)
        if not tamanho_resposta:
            return False
        resposta = receber_dados(sock, tamanho_resposta)
        print(f"Resposta do servidor: {resposta.decode('utf-8')}")
        return True
        
    except Exception as e:
        print(f"Erro ao enviar arquivo: {e}")
        return False

def enviar_diretorio(sock, caminho_diretorio):
    try:
        # Verifica se é um diretório válido
        if not os.path.isdir(caminho_diretorio):
            print(f"Diretório não encontrado: {caminho_diretorio}")
            return False
        
        nome_diretorio = os.path.basename(caminho_diretorio)
        
        # Envia metadados do diretório
        metadados = f"DIRETORIO|{nome_diretorio}"
        if not enviar_dados(sock, metadados.encode('utf-8')):
            return False
        
        # Espera confirmação do servidor
        tamanho_resposta = receber_mensagem(sock)
        if not tamanho_resposta:
            return False
        resposta = receber_dados(sock, tamanho_resposta)
        if resposta != b"OK":
            print("Servidor não está pronto para receber o diretório")
            return False
        
        # Percorre recursivamente o diretório
        for raiz, _, arquivos in os.walk(caminho_diretorio):
            for nome_arquivo in arquivos:
                caminho_completo = os.path.join(raiz, nome_arquivo)
                caminho_relativo = os.path.relpath(caminho_completo, caminho_diretorio)
                
                # Envia cada arquivo
                if not enviar_arquivo(sock, caminho_completo):
                    print(f"Falha ao enviar arquivo: {caminho_completo}")
                    return False
        
        # Envia sinal de término
        if not enviar_dados(sock, b"FIM_DIRETORIO"):
            return False
            
        return True
        
    except Exception as e:
        print(f"Erro ao enviar diretório: {e}")
        return False

def menu_cliente(sock):
    while True:
        print("\nOpções:")
        print("1. Enviar arquivo")
        print("2. Enviar diretório")
        print("3. Sair")
        opcao = input("Escolha uma opção: ")
        
        if opcao == "1":
            caminho = input("Digite o caminho do arquivo: ")
            if enviar_arquivo(sock, caminho):
                print("Arquivo enviado com sucesso!")
            else:
                print("Falha ao enviar arquivo")
        elif opcao == "2":
            caminho = input("Digite o caminho do diretório: ")
            if enviar_diretorio(sock, caminho):
                print("Diretório enviado com sucesso!")
            else:
                print("Falha ao enviar diretório")
        elif opcao == "3":
            break
        else:
            print("Opção inválida")

def iniciar_cliente():
    ip_servidor = input("Digite o IP do servidor: ")
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        try:
            sock.connect((ip_servidor, PORT))
            print(f"Conectado ao servidor {ip_servidor}:{PORT}")
            
            # Mostra menu de opções
            menu_cliente(sock)
        
        except Exception as e:
            print(f"Erro ao conectar ao servidor: {e}")

if __name__ == "__main__":
    iniciar_cliente()