import socket
import os

SERVER_HOST = '192.168.1.100'  # *** SUBSTITUA PELO ENDEREÇO IP DO SEU SERVIDOR ***
                               # Use '127.0.0.1' se o servidor estiver na mesma máquina
SERVER_PORT = 5050             # A mesma porta usada no servidor

def send_file(filepath):
    """Envia um arquivo para o servidor."""
    # Use os.path.normpath para normalizar o caminho de acordo com o SO
    # Isso ajuda a lidar com diferentes separadores de diretório (/, \)
    # e outras inconsistências no path digitado pelo usuário.
    normalized_filepath = os.path.normpath(filepath)

    if not os.path.exists(normalized_filepath):
        print(f"Erro: Arquivo ou diretório '{normalized_filepath}' não encontrado.")
        return

    if not os.path.isfile(normalized_filepath):
        print(f"Erro: '{normalized_filepath}' não é um arquivo. Por favor, forneça o caminho completo para um arquivo.")
        return

    filename = os.path.basename(normalized_filepath)
    file_size = os.path.getsize(normalized_filepath)

    try:
        print(f"Tentando conectar ao servidor em {SERVER_HOST}:{SERVER_PORT}...")
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((SERVER_HOST, SERVER_PORT))
        print(f"Conectado ao servidor.")

        # Envia o tamanho do nome do arquivo (4 bytes)
        filename_bytes = filename.encode('utf-8')
        client_socket.sendall(len(filename_bytes).to_bytes(4, 'big'))
        # Envia o nome do arquivo
        client_socket.sendall(filename_bytes)

        # Envia o tamanho do arquivo (8 bytes)
        client_socket.sendall(file_size.to_bytes(8, 'big'))

        # Envia o conteúdo do arquivo em chunks
        print(f"Enviando arquivo '{filename}' ({file_size} bytes)...")
        bytes_sent = 0
        with open(normalized_filepath, 'rb') as f: # Use o caminho normalizado aqui
            while True:
                bytes_read = f.read(4096)
                if not bytes_read:
                    break
                client_socket.sendall(bytes_read)
                bytes_sent += len(bytes_read)

        print(f"Arquivo '{filename}' enviado com sucesso. Total enviado: {bytes_sent} bytes.")

    except ConnectionRefusedError:
        print(f"Erro: Conexão recusada. Verifique se o servidor está rodando em {SERVER_HOST}:{SERVER_PORT} e se o firewall permite a conexão.")
    except Exception as e:
        print(f"Erro ao enviar arquivo: {e}")
    finally:
        if 'client_socket' in locals() and client_socket:
            client_socket.close()
            print("Conexão com o servidor encerrada.")

if __name__ == "__main__":
    file_to_send_raw = input("Digite o caminho completo do arquivo a ser enviado: ")
    send_file(file_to_send_raw)