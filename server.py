import socket
import os
import csv
import struct
import hashlib
from datetime import datetime
from con_config import obter_dados_conexao

HOST, PORT, TAM_BUFFER = obter_dados_conexao()
BASE_DIR = "recebidos" # Diretório base para salvar os arquivos recebidos

# --- Funções Auxiliares para Comunicação Robusta ---
def _send_data(conn, data):
    """
    Envia dados com um cabeçalho de 4 bytes indicando o tamanho.
    Isso garante que o receptor saiba exatamente quantos bytes esperar.
    """
    try:
        data_len = len(data)
        # Empacota o tamanho dos dados como um inteiro sem sinal de 4 bytes (big-endian)
        conn.sendall(struct.pack('>I', data_len))
        conn.sendall(data)
    except Exception as e:
        print(f"❌ [Erro _send_data] Falha ao enviar dados: {e}")
        raise # Re-lança a exceção para ser tratada em um nível superior

def _receive_data(conn):
    """
    Recebe dados com um cabeçalho de 4 bytes indicando o tamanho.
    Primeiro lê o cabeçalho, depois lê a quantidade de bytes indicada.
    """
    try:
        # Tenta receber 4 bytes que representam o tamanho da próxima mensagem
        len_bytes = _recv_all(conn, 4)
        if not len_bytes:
            # Conexão fechada ou erro antes de receber o tamanho
            return None
        # Desempacota o tamanho dos dados
        data_len = struct.unpack('>I', len_bytes)[0]

        # Recebe os dados reais com base no tamanho lido
        data = _recv_all(conn, data_len)
        return data
    except Exception as e:
        print(f"❌ [Erro _receive_data] Falha ao receber dados: {e}")
        raise # Re-lança a exceção

def _recv_all(conn, n):
    """
    Função auxiliar para garantir que todos os 'n' bytes sejam recebidos.
    Continua lendo até que a quantidade total de bytes esperada seja recebida.
    """
    data = b''
    while len(data) < n:
        packet = conn.recv(n - len(data))
        if not packet:
            # Conexão fechada pelo peer
            return None
        data += packet
    return data

# --- Funções de Log ---
def registrar_log(nome_arquivo, tamanho, inicio, fim, duracao, endereco_ip, status="SUCESSO", motivo_falha=""):
    """Registra os detalhes da transferência em um arquivo CSV."""
    log_csv = 'log_transferencias.csv'
    existe = os.path.exists(log_csv)

    taxa_transferencia = tamanho / duracao if duracao > 0 else 0

    with open(log_csv, 'a', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        if not existe:
            writer.writerow(['nome_arquivo', 'tamanho_bytes', 'inicio', 'fim', 'duracao_segundos', 'endereco_ip', 'taxa_transferencia_bytes_por_segundo', 'status', 'motivo_falha'])
        writer.writerow([
            nome_arquivo,
            tamanho,
            inicio.isoformat(),
            fim.isoformat(),
            f"{duracao:.3f}",
            endereco_ip,
            f"{taxa_transferencia:.3f}",
            status,
            motivo_falha
        ])

# --- Funções de Recebimento ---
def receber_arquivo(conn, addr, base_dir=""):
    """
    Recebe um único arquivo, verifica o checksum e o salva.
    `base_dir` é usado para recriar a estrutura de pastas para arquivos dentro de diretórios.
    """
    nome_arquivo_log = "N/A" # Nome para o log em caso de falha antes de obter o nome
    tamanho_recebido = 0
    inicio_transferencia = datetime.now()
    status = "SUCESSO"
    motivo_falha = ""

    try:
        # Recebe o caminho relativo do arquivo
        relative_path_bytes = _receive_data(conn)
        if relative_path_bytes is None: raise Exception("Caminho relativo do arquivo não recebido.")
        relative_path = relative_path_bytes.decode('utf-8')
        nome_arquivo_log = relative_path # Atualiza o nome para o log
        print(f"📄 [Servidor] Nome do arquivo: {relative_path}")

        # Recebe tamanho do arquivo esperado
        tamanho_str_bytes = _receive_data(conn)
        if tamanho_str_bytes is None: raise Exception("Tamanho do arquivo não recebido.")
        expected_size = int(tamanho_str_bytes.decode('utf-8'))
        print(f"📏 [Servidor] Tamanho esperado: {expected_size} bytes")

        # Recebe checksum esperado
        checksum_bytes = _receive_data(conn)
        if checksum_bytes is None: raise Exception("Checksum não recebido.")
        expected_checksum = checksum_bytes.decode('utf-8')
        print(f"🔍 [Servidor] Checksum esperado: {expected_checksum}")

        # Cria o caminho completo do arquivo no servidor, incluindo o diretório base 'recebidos'
        caminho_completo_arquivo = os.path.join(BASE_DIR, base_dir, relative_path)
        os.makedirs(os.path.dirname(caminho_completo_arquivo), exist_ok=True)

        # Recebe o conteúdo completo do arquivo
        file_content_bytes = _receive_data(conn)
        if file_content_bytes is None: raise Exception("Conteúdo do arquivo não recebido.")

        tamanho_recebido = len(file_content_bytes)

        if tamanho_recebido != expected_size:
            status = "FALHA"
            motivo_falha = f"Tamanho recebido ({tamanho_recebido}) difere do esperado ({expected_size})."
            print(f"❌ [Servidor] {motivo_falha}")
        else:
            # Calcula o checksum do arquivo recebido
            hasher = hashlib.md5()
            hasher.update(file_content_bytes)
            calculated_checksum = hasher.hexdigest()

            if calculated_checksum != expected_checksum:
                status = "CORROMPIDO"
                motivo_falha = f"Checksum não corresponde. Esperado: {expected_checksum}, Calculado: {calculated_checksum}"
                print(f"⚠️ [Servidor] {motivo_falha}")
            else:
                with open(caminho_completo_arquivo, 'wb') as f:
                    f.write(file_content_bytes)
                print(f"✅ [Servidor] Arquivo '{relative_path}' recebido com sucesso.")

        # Envia ACK (confirmação) de volta ao cliente
        _send_data(conn, b"ACK_FILE_OK" if status == "SUCESSO" else b"ACK_FILE_FAIL")

    except Exception as e:
        status = "FALHA"
        motivo_falha = f"Erro ao receber arquivo: {e}"
        print(f"❌ [Servidor] Erro ao receber arquivo '{nome_arquivo_log}': {e}")
        try:
            _send_data(conn, b"ACK_FILE_FAIL") # Tenta enviar ACK de falha
        except:
            pass # Ignora se a conexão já estiver quebrada
    finally:
        fim_transferencia = datetime.now()
        duracao = (fim_transferencia - inicio_transferencia).total_seconds()
        registrar_log(nome_arquivo_log, tamanho_recebido, inicio_transferencia, fim_transferencia, duracao, addr[0], status, motivo_falha)

def receber_pasta(conn, addr):
    """Recebe uma pasta, processando múltiplos arquivos e subpastas."""
    base_dir_name = "N/A"
    try:
        # Recebe o nome da pasta base
        base_dir_name_bytes = _receive_data(conn)
        if base_dir_name_bytes is None: raise Exception("Nome da pasta base não recebido.")
        base_dir_name = base_dir_name_bytes.decode('utf-8')
        print(f"📂 [Servidor] Recebendo pasta: {base_dir_name}")
        os.makedirs(os.path.join(BASE_DIR, base_dir_name), exist_ok=True)

        while True:
            # Recebe o sinal para o próximo arquivo ou fim da pasta
            signal_bytes = _receive_data(conn)
            if signal_bytes is None:
                print("⚠️ [Servidor] Conexão encerrada durante a transferência da pasta.")
                break # Conexão encerrada
            signal = signal_bytes.decode('utf-8')

            if signal == "NEXT_FILE":
                print("\n📄 [Servidor] Recebendo próximo arquivo na pasta...")
                receber_arquivo(conn, addr, base_dir=base_dir_name)
            elif signal == "END_DIR":
                print(f"🎉 [Servidor] Transferência da pasta '{base_dir_name}' concluída.")
                _send_data(conn, b"ACK_DIR_OK")
                break
            elif signal == "ABORT_DIR": # Sinal para abortar a transferência da pasta
                print(f"❌ [Servidor] Cliente sinalizou abortar transferência da pasta '{base_dir_name}'.")
                _send_data(conn, b"ACK_DIR_FAIL")
                break
            else:
                print(f"❓ [Servidor] Sinal desconhecido recebido durante transferência de pasta: {signal}")
                _send_data(conn, b"ACK_DIR_FAIL")
                break
    except Exception as e:
        print(f"❌ [Servidor] Erro ao receber pasta '{base_dir_name}': {e}")
        registrar_log(f"Pasta: {base_dir_name}", 0, datetime.now(), datetime.now(), 0, addr[0], status="FALHA", motivo_falha=f"Erro na transferência da pasta: {e}")
        try:
            _send_data(conn, b"ACK_DIR_FAIL")
        except:
            pass # Ignora se a conexão já estiver quebrada

# --- Função Principal do Servidor ---
def iniciar_servidor():
    """Inicia o servidor e aguarda por conexões para transferir arquivos/pastas."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind((HOST, PORT))
        sock.listen(1)
        print(f"🖥️ [Servidor] Escutando em {HOST}:{PORT}...")

        conn, addr = sock.accept()
        print(f"🔌 [Servidor] Conexão estabelecida com {addr}")

        try:
            # Recebe o tipo de transferência (FILE ou DIR)
            transfer_type_bytes = _receive_data(conn)
            if transfer_type_bytes is None:
                print("⚠️ [Servidor] Conexão encerrada prematuramente ao tentar receber tipo de transferência.")
                return

            transfer_type = transfer_type_bytes.decode('utf-8')
            print(f"📦 [Servidor] Tipo de transferência recebido: {transfer_type}")

            if transfer_type == "FILE":
                print("[Servidor] Preparando para receber um único arquivo...")
                receber_arquivo(conn, addr)
            elif transfer_type == "DIR":
                print("[Servidor] Preparando para receber uma pasta...")
                receber_pasta(conn, addr)
            else:
                print(f"❓ [Servidor] Tipo de transferência desconhecido: {transfer_type}")
                # Log de erro para tipo desconhecido
                registrar_log("N/A", 0, datetime.now(), datetime.now(), 0, addr[0], status="FALHA", motivo_falha=f"Tipo de transferência desconhecido: {transfer_type}")

        except Exception as e:
            print(f"❌ [Servidor] Erro grave durante a transferência: {e}")
            # Log de erro geral se a transferência falhar antes de um arquivo específico
            registrar_log("N/A", 0, datetime.now(), datetime.now(), 0, addr[0], status="FALHA", motivo_falha=f"Erro geral na transferência: {e}")
        finally:
            conn.close()
            print("🛑 [Servidor] Conexão encerrada.")
    except Exception as e:
        print(f"❌ [Servidor] Erro ao iniciar o servidor: {e}")
    finally:
        sock.close()
        print("🛑 [Servidor] Socket do servidor fechado.")

if __name__ == "__main__":
    iniciar_servidor()
