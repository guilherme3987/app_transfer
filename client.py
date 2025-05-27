import socket
import os

SERVER_HOST = '192.168.1.100'  # *** SUBSTITUA PELO ENDEREÇO IP DO SEU SERVIDOR ***
                               # Use '127.0.0.1' se o servidor estiver na mesma máquina
SERVER_PORT = 12345            # A mesma porta usada no servidor

def send_file(filepath):
    """Envia um arquivo para o servidor."""
    if not os.path.exists(filepath):
        print(f"Erro: Arquivo '{filepath}' não encontrado.")
        return

    filename = os.path.basename(filepath)
    file_size = os.path.getsize(filepath)

    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((SERVER_HOST, SERVER_PORT))
        print(f"Conectado ao servidor em {SERVER_HOST}:{SERVER_PORT}")

        # Envia o tamanho do nome do arquivo (4 bytes)
        filename_bytes = filename.encode('utf-8')
        client_socket.sendall(len(filename_bytes).to_bytes(4, 'big'))
        # Envia o nome do arquivo
        client_socket.sendall(filename_bytes)

        # Envia o tamanho do arquivo (8 bytes)
        client_socket.sendall(file_size.to_bytes(8, 'big'))

        # Envia o conteúdo do arquivo em chunks
        with open(filepath, 'rb') as f:
            while True:
                bytes_read = f.read(4096) # Lê em chunks de 4KB
                if not bytes_read:
                    break # Fim do arquivo
                client_socket.sendall(bytes_read)

        print(f"Arquivo '{filename}' enviado com sucesso.")

    except ConnectionRefusedError:
        print(f"Erro: Conexão recusada. Verifique se o servidor está rodando em {SERVER_HOST}:{SERVER_PORT} e se o firewall permite a conexão.")
    except Exception as e:
        print(f"Erro ao enviar arquivo: {e}")
    finally:
        if 'client_socket' in locals() and client_socket:
            client_socket.close()
            print("Conexão com o servidor encerrada.")

if __name__ == "__main__":
    # Exemplo de uso:
    # Crie um arquivo de teste para enviar
    test_file_name = "teste.txt"
    with open(test_file_name, "w") as f:
        f.write("Este é um arquivo de teste para transferência.\n")
        f.write("Ele contém algumas linhas de texto.\n")
        f.write("Espero que seja transferido com sucesso!\n")

    print(f"Arquivo de teste '{test_file_name}' criado.")
    
    # Você pode pedir ao usuário para digitar o nome do arquivo
    # file_to_send = input("Digite o caminho do arquivo a ser enviado: ")
    
    # Ou usar o arquivo de teste criado
    file_to_send = test_file_name
    
    send_file(file_to_send)