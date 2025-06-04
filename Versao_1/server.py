import socket
#import os
#import hashlib
#from datetime import datetime
import threading
from con_config import obter_dados_conexao

IP, PORT, TAM_BUFFER, TAM_CABECALHO = obter_dados_conexao()

def iniciar_servidor(host=IP, port=PORT):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(5)
    print(f"Servidor escutando em {host}:{port}")

    try:
        while True:
            
                client_socket, addr = server_socket.accept()
                print(f"Conexão recebida de {addr}")
            
                # Inicia uma nova thread para lidar com o cliente
                thread = threading.Thread(target=lidar_cliente, args=(client_socket, addr))
                thread.daemon = True  # Permite que o programa principal termine mesmo com threads abertas
                thread.start()

                print(f"Nova thread iniciada para lidar com o cliente {addr}.")
            
    except KeyboardInterrupt:
        print("\nServidor sendo desligado (Ctrl+C detectado).")
    except Exception as e:
        print(f"❌ [Erro iniciar_servidor] Erro no loop principal do servidor: {e}")
    finally:
        server_socket.close()
        print("Servidor encerrado.")

def lidar_cliente(client_socket, addr):
    print(f"Iniciando tratamento para cliente {addr}...")

    try:
        
        while True:
            # Recebe o cabeçalho
            cabecalho = client_socket.recv(TAM_CABECALHO).strip()
            if not cabecalho:
                print("Conexão fechada pelo cliente.")
                break
            
            tamanho_dados = int(cabecalho.decode('utf-8'))
            print(f"Tamanho dos dados recebidos: {tamanho_dados}")

            # Recebe os dados
            dados = client_socket.recv(tamanho_dados)
            print(f"Dados recebidos: {dados}")

            # Prepara a resposta
            resposta = b"Dados recebidos com sucesso\n"
            cabecalho_resposta = f"{len(resposta):<{TAM_CABECALHO}}".encode('utf-8')

            # Envia o cabeçalho e a resposta
            client_socket.sendall(cabecalho_resposta)
            client_socket.sendall(resposta)

    except Exception as e:
        print(f"Erro ao lidar com o cliente: {e}")
    finally:
        client_socket.close()

if __name__ == "__main__":
    iniciar_servidor()