import socket
import os
import struct
import hashlib
from datetime import datetime
from con_config import obter_dados_conexao

# Obtém as configurações de conexão do arquivo con_config.py
_, PORT, TAM_BUFFER = obter_dados_conexao()

# --- Funções Auxiliares para Comunicação Robusta ---

def _send_data(sock, data):
    """
    Envia dados com um cabeçalho de 4 bytes indicando o tamanho.
    Isso garante que o receptor saiba exatamente quantos bytes esperar.
    """
    try:
        data_len = len(data)
        # Empacota o tamanho dos dados como um inteiro sem sinal de 4 bytes (big-endian)
        sock.sendall(struct.pack('>I', data_len))
        sock.sendall(data)
    except Exception as e:
        print(f"❌ [Erro _send_data] Falha ao enviar dados: {e}")

def _receive_data(sock):
    """
    Recebe dados com um cabeçalho de 4 bytes indicando o tamanho.
    Primeiro lê o cabeçalho, depois lê a quantidade de bytes indicada.
    """
    try:
        # Tenta receber 4 bytes que representam o tamanho da próxima mensagem
        len_bytes = _recv_all(sock, 4)
        if not len_bytes:
            # Conexão fechada ou erro antes de receber o tamanho
            return None
        # Desempacota o tamanho dos dados
        data_len = struct.unpack('>I', len_bytes)[0]

        # Recebe os dados reais com base no tamanho lido
        data = _recv_all(sock, data_len)
        return data
    except Exception as e:
        print(f"❌ [Erro _receive_data] Falha ao receber dados: {e}")
        return
def _recv_all(sock, n):
    """
    Função auxiliar para garantir que todos os 'n' bytes sejam recebidos.
    Continua lendo até que a quantidade total de bytes esperada seja recebida.
    """
    data = b''
    while len(data) < n:
        packet = sock.recv(n - len(data))
        if not packet:
            # Conexão fechada pelo peer
            return None
        data += packet
    return data

# --- Função para Calcular Checksum ---

def calcular_checksum_md5(caminho_arquivo):
    """
    Calcula o checksum MD5 de um arquivo.
    Usado para verificar a integridade do arquivo após a transferência.
    """
    hasher = hashlib.md5()
    try:
        with open(caminho_arquivo, 'rb') as f:
            while True:
                # Lê o arquivo em chunks para não carregar tudo na memória de uma vez
                chunk = f.read(TAM_BUFFER)
                if not chunk:
                    break
                hasher.update(chunk)
        return hasher.hexdigest()
    except Exception as e:
        print(f"❌ [Erro] Não foi possível calcular o checksum para '{caminho_arquivo}': {e}")
        return None

# --- Funções de Envio ---

def enviar_arquivo(sock, caminho_arquivo, caminho_base_pasta=""):
    """
    Envia um único arquivo ao servidor.
    Inclui nome, tamanho, checksum e o conteúdo do arquivo.
    """
    # Obtém o nome base do arquivo e o caminho relativo se estiver dentro de uma pasta
    nome_arquivo = os.path.basename(caminho_arquivo)
    relative_path = os.path.relpath(caminho_arquivo, caminho_base_pasta) if caminho_base_pasta else nome_arquivo

    try:
        file_size = os.path.getsize(caminho_arquivo)
        checksum = calcular_checksum_md5(caminho_arquivo)
        if checksum is None:
            print(f"⚠️ [Cliente] Pulando envio de '{relative_path}' devido a falha no checksum.")
            return False

        print(f"⬆️ [Cliente] Enviando '{relative_path}' (Tamanho: {file_size} bytes, Checksum: {checksum})...")

        # Envia metadados (caminho relativo, tamanho, checksum)
        _send_data(sock, relative_path.encode('utf-8'))
        _send_data(sock, str(file_size).encode('utf-8'))
        _send_data(sock, checksum.encode('utf-8'))

        # Envia conteúdo do arquivo
        inicio = datetime.now()
        with open(caminho_arquivo, 'rb') as f:
            # Para simplificar o protocolo e evitar loops de recv adicionais no servidor,
            # lê o arquivo inteiro. Para arquivos muito grandes, considere enviar em chunks.
            file_content = f.read()
        _send_data(sock, file_content)
        fim = datetime.now()
        duracao = (fim - inicio).total_seconds()

        print(f"✅ [Cliente] Arquivo '{relative_path}' enviado. Duração: {duracao:.3f} segundos.")

        # Aguarda ACK (confirmação) do servidor
        ack = _receive_data(sock)
        if ack and ack.decode('utf-8') == "ACK_FILE_OK":
            print(f"👍 [Cliente] Servidor confirmou recebimento de '{relative_path}' com sucesso.")
            return True
        else:
            print(f"👎 [Cliente] Servidor reportou falha ou corrupção para '{relative_path}'. ACK: {ack.decode('utf-8') if ack else 'N/A'}")
            return False

    except Exception as e:
        print(f"❌ [Cliente] Erro ao enviar arquivo '{relative_path}': {e}")
        return False

def enviar_pasta(sock, caminho_pasta):
    """
    Percorre uma pasta recursivamente e envia cada arquivo individualmente.
    Cria a estrutura de diretórios no servidor.
    """
    base_dir_name = os.path.basename(caminho_pasta)
    print(f"📂 [Cliente] Iniciando envio da pasta: {base_dir_name}")
    try:
        # Envia o nome da pasta base para o servidor
        _send_data(sock, base_dir_name.encode('utf-8'))

        # Percorre a pasta e suas subpastas
        for root, _, files in os.walk(caminho_pasta):
            for file_name in files:
                full_path = os.path.join(root, file_name)
                # Sinaliza ao servidor que um novo arquivo está chegando
                _send_data(sock, b"NEXT_FILE")
                # Envia o arquivo, passando o caminho da pasta base para calcular o caminho relativo
                if not enviar_arquivo(sock, full_path, caminho_pasta):
                    print(f"⚠️ [Cliente] Falha no envio de '{full_path}'. Abortando pasta.")
                    # Se um arquivo falhar, podemos decidir abortar a transferência da pasta
                    _send_data(sock, b"ABORT_DIR") # Sinaliza ao servidor para abortar
                    return False

        # Sinaliza o fim da transferência da pasta
        _send_data(sock, b"END_DIR")
        ack = _receive_data(sock)
        if ack and ack.decode('utf-8') == "ACK_DIR_OK":
            print(f"🎉 [Cliente] Servidor confirmou recebimento da pasta '{base_dir_name}' com sucesso.")
            return True
        else:
            print(f"👎 [Cliente] Servidor reportou falha na transferência da pasta '{base_dir_name}'. ACK: {ack.decode('utf-8') if ack else 'N/A'}")
            return False

    except Exception as e:
        print(f"❌ [Cliente] Erro ao enviar pasta '{base_dir_name}': {e}")
        # Tenta sinalizar ao servidor que houve um erro grave na pasta
        try:
            _send_data(sock, b"ABORT_DIR")
        except:
            pass # Ignora se a conexão já estiver quebrada
        return False

# --- Função Principal de Inicialização do Cliente ---

def iniciar_cliente():
    """
    Função principal que inicia o cliente, conecta ao servidor
    e gerencia o envio de arquivos ou pastas.
    """
    try:
        ip_servidor = input("Digite o IP do servidor (VM Linux): ").strip()
        caminho_origem = input("Digite o caminho completo do arquivo ou pasta a ser enviado: ").strip()

        if not os.path.exists(caminho_origem):
            print("⚠️ [Cliente] Erro: Caminho não encontrado.")
            return

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((ip_servidor, PORT))
        print(f"🔌 [Cliente] Conectado ao servidor {ip_servidor}:{PORT}")

        if os.path.isfile(caminho_origem):
            # Sinaliza ao servidor que um arquivo individual será enviado
            _send_data(sock, b"FILE")
            if enviar_arquivo(sock, caminho_origem):
                print("✅ [Cliente] Transferência de arquivo concluída com sucesso!")
            else:
                print("❌ [Cliente] Transferência de arquivo falhou.")
        elif os.path.isdir(caminho_origem):
            # Sinaliza ao servidor que uma pasta será enviada
            _send_data(sock, b"DIR")
            if enviar_pasta(sock, caminho_origem):
                print("✅ [Cliente] Transferência de pasta concluída com sucesso!")
            else:
                print("❌ [Cliente] Transferência de pasta falhou.")
        else:
            print("⚠️ [Cliente] Erro: Caminho inválido (não é arquivo nem pasta).")

    except ConnectionError as e:
        print(f"🔌 [Cliente] Erro de conexão com o servidor: {e}")
    except Exception as e:
        print(f"❌ [Cliente] Erro inesperado durante a operação do cliente: {e}")
    finally:
        if 'sock' in locals() and sock.fileno() != -1: # Verifica se o socket está aberto antes de fechar
            sock.close()
            print("🛑 [Cliente] Conexão encerrada.")

if __name__ == "__main__":
    iniciar_cliente()
