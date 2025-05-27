import socket
import os
import datetime

HOST = '0.0.0.0'
PORT = 5051
UPLOAD_DIR = 'uploads'
LOG_FILE = 'transfer_log.txt'

# Cria diretório de upload se não existir
os.makedirs(UPLOAD_DIR, exist_ok=True)

def log_transfer(filename, client_address, status):
    """Registra logs da transferência."""
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(LOG_FILE, 'a') as f:
        f.write(f"[{timestamp}] Arquivo: {filename} | Cliente: {client_address[0]}:{client_address[1]} | Status: {status}\n")

def handle_single_client(conn, addr):
    """Recebe arquivo de um cliente."""
    print(f"\n--- Conexão estabelecida com {addr} ---")
    filename = None
    try:
        filename_size_bytes = conn.recv(4)
        if not filename_size_bytes:
            raise ValueError("Nome do arquivo não recebido.")
        
        filename_size = int.from_bytes(filename_size_bytes, 'big')
        filename_bytes = conn.recv(filename_size)
        filename = filename_bytes.decode('utf-8')
        filepath = os.path.join(UPLOAD_DIR, filename)

        file_size_bytes = conn.recv(8)
        if not file_size_bytes:
            raise ValueError("Tamanho do arquivo não recebido.")
        
        file_size = int.from_bytes(file_size_bytes, 'big')
        received_bytes = 0

        with open(filepath, 'wb') as f:
            while received_bytes < file_size:
                chunk = conn.recv(min(4096, file_size - received_bytes))
                if not chunk:
                    break
                f.write(chunk)
                received_bytes += len(chunk)

        if received_bytes == file_size:
            print(f"Arquivo '{filename}' recebido com sucesso.")
            log_transfer(filename, addr, "Sucesso")
        else:
            print(f"Falha: Recebido {received_bytes} de {file_size} bytes.")
            log_transfer(filename, addr, "Falha: Incompleto")
            os.remove(filepath) if os.path.exists(filepath) else None

    except Exception as e:
        print(f"Erro: {e}")
        log_transfer(filename if filename else "N/A", addr, f"Falha: {e}")
    finally:
        conn.close()
        print(f"--- Conexão encerrada com {addr} ---")

def start_server():
    """Inicia o servidor."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.bind((HOST, PORT))
        server_socket.listen(1)
        print(f"Servidor escutando em {HOST}:{PORT}")
        print(f"Uploads em: {os.path.abspath(UPLOAD_DIR)}")
        print(f"Log em: {os.path.abspath(LOG_FILE)}")

        while True:
            conn, addr = server_socket.accept()
            handle_single_client(conn, addr)

if __name__ == "__main__":
    start_server()
