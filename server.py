import socket
import os
import datetime

HOST = '0.0.0.0'  # Escuta em todas as interfaces de rede disponíveis
PORT = 5050       # Porta para a conexão
UPLOAD_DIR = 'uploads' # Diretório para salvar os arquivos recebidos
LOG_FILE = 'transfer_log.txt' # Arquivo de log

# Garante que o diretório de uploads exista
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

def log_transfer(filename, client_address, status):
    """Registra informações da transferência no arquivo de log."""
    with open(LOG_FILE, 'a') as f:
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        f.write(f"[{timestamp}] Arquivo: {filename} | Cliente: {client_address[0]}:{client_address[1]} | Status: {status}\n")

def handle_single_client(conn, addr):
    """Lida com a conexão de um único cliente para receber um arquivo."""
    print(f"\n--- Conexão estabelecida com {addr} ---")
    filename = None
    try:
        # Recebe o tamanho do nome do arquivo (4 bytes)
        filename_size_bytes = conn.recv(4)
        if not filename_size_bytes:
            print(f"Cliente {addr} desconectou antes de enviar o nome do arquivo.")
            log_transfer("N/A", addr, "Falha: Desconexão antes do nome do arquivo")
            return

        filename_size = int.from_bytes(filename_size_bytes, 'big')
        filename_bytes = conn.recv(filename_size)
        filename = filename_bytes.decode('utf-8')
        filepath = os.path.join(UPLOAD_DIR, filename)

        print(f"Recebendo arquivo: {filename} de {addr}")

        # Recebe o tamanho total do arquivo
        file_size_bytes = conn.recv(8)
        if not file_size_bytes:
            print(f"Cliente {addr} desconectou antes de enviar o tamanho do arquivo.")
            log_transfer(filename, addr, "Falha: Desconexão antes do tamanho do arquivo")
            return
        file_size = int.from_bytes(file_size_bytes, 'big')

        received_bytes = 0
        with open(filepath, 'wb') as f:
            while received_bytes < file_size:
                bytes_read = conn.recv(4096)
                if not bytes_read:
                    break
                f.write(bytes_read)
                received_bytes += len(bytes_read)

        if received_bytes == file_size:
            print(f"Arquivo '{filename}' recebido com sucesso de {addr}")
            log_transfer(filename, addr, "Sucesso")
        else:
            print(f"Erro ao receber '{filename}' de {addr}: tamanho esperado {file_size}, recebido {received_bytes}")
            log_transfer(filename, addr, "Falha: Recebimento incompleto")
            if os.path.exists(filepath): # Remove arquivo parcial se a transferência falhar
                os.remove(filepath)

    except Exception as e:
        print(f"Erro ao lidar com o cliente {addr}: {e}")
        log_transfer(filename if filename else "N/A", addr, f"Falha: {e}")
    finally:
        conn.close()
        print(f"--- Conexão com {addr} encerrada. Aguardando próxima conexão... ---\n")

def start_server():
    """Inicia o servidor para escutar por conexões (um cliente por vez)."""
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((HOST, PORT))
    server_socket.listen(1) # Permite apenas 1 conexão pendente
    print(f"Servidor escutando em {HOST}:{PORT}")
    print(f"Arquivos serão salvos em: {os.path.abspath(UPLOAD_DIR)}")
    print(f"Logs em: {os.path.abspath(LOG_FILE)}")
    print("\nAguardando conexão de um cliente...")

    while True:
        conn, addr = server_socket.accept()
        handle_single_client(conn, addr)

if __name__ == "__main__":
    start_server()