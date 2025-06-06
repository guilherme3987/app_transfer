import socket
import os

from threading import Thread

from Funcoes_aux.con_config import obter_dados_conexao 
from Funcoes_aux.checksum import calcular_checksum_dados

from Funcoes_aux.cabecalho import criar_cabecalho_arquivo, receber_cabecalho, enviar_cabecalho, receber_dados, receber_dados_com_cabecalho 

IP, PORT, TAM_BUFFER, TAM_CABECALHO = obter_dados_conexao()

DIRETORIO_DESTINO = "arquivos_recebidos"

def iniciar_servidor():
    print("\n##########################\n<ENTROU EM INICIAR_SERVIDOR>\n############################")

    if not os.path.exists(DIRETORIO_DESTINO):
        os.makedirs(DIRETORIO_DESTINO)
    
    servidor_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servidor_socket.bind((IP, PORT))
    servidor_socket.listen()  
    
    print(f"\n### Servidor iniciado em {IP}:{PORT} ###\n")

    while True:
        cliente_socket, addr = servidor_socket.accept()
        print(f"\n### Nova conexão de {addr[0]}:{addr[1]} ###")
            
        thread = Thread(target=lidar_cliente, args=(cliente_socket, addr))
        thread.start()
        print(f"\n### Thread iniciada para {addr[0]}:{addr[1]} ###")
                
    servidor_socket.close()

def enviar_resposta(sock, dados):

    print("\n##########################\n<ENTROU EM ENVIAR_RESPOSTA (SERVER)>\n############################")
    tamanho = len(dados)
    cabecalho_tamanho = f"{tamanho: <{TAM_CABECALHO}}".encode('utf-8')
    sock.sendall(cabecalho_tamanho + dados)
    print(f"Resposta enviada com tamanho: {tamanho} bytes. Conteúdo: {dados.decode('utf-8').strip()}")


def lidar_cliente(cliente_socket, addr):
    print("\n##########################\n<ENTROU EM LIDAR_CLIENTE>\n############################")

    print(f"\nNova conexão de {addr}")

    try:
        while True:
            cabecalho_info = receber_cabecalho(cliente_socket)
            if not cabecalho_info:
                print(f"Cliente {addr[0]} desconectou")
                break

            tipo = cabecalho_info['tipo']
            tamanho = cabecalho_info['tamanho']
            checksum_esperado = cabecalho_info['checksum']
            nome_arquivo = cabecalho_info['nome']
            print(f"\n### Tipo: {tipo}, Tamanho: {tamanho}, Checksum esperado: {checksum_esperado}, Nome do arquivo: {nome_arquivo} ###\n")

            ok_response = b"OK"
            enviar_resposta(cliente_socket, ok_response) 

            # Receber os dados do arquivo
            dados_arquivo = receber_dados(cliente_socket, tamanho)
            if not dados_arquivo:
                print(f"Não recebeu dados completos de {addr[0]}")
                break

            # Verificar o checksum
            checksum_recebido = calcular_checksum_dados(dados_arquivo)
            print(f"\n### Checksum recebido: {checksum_recebido} ###\n")
            
            if checksum_recebido != checksum_esperado:
                cliente_socket.sendall(b"❌ [Erro]  Checksum invalido")
                continue

            # Salvar o arquivo
            caminho_completo = os.path.join(DIRETORIO_DESTINO, nome_arquivo)
            os.makedirs(os.path.dirname(caminho_completo), exist_ok=True)
            
            with open(caminho_completo, 'wb') as f:
                f.write(dados_arquivo)
            
            cliente_socket.sendall(b"Arquivo recebido com sucesso")
            print(f"\n### Arquivo {nome_arquivo} salvo em {caminho_completo} ###\n")
            break

    except ConnectionResetError:
        print(f"Conexão com {addr[0]} foi resetada")
    except Exception as e:
        print(f"❌ [Erro] com {addr[0]}: {e}")
    finally:
        cliente_socket.close()
        print(f"Conexão com {addr[0]} encerrada")



if __name__ == "__main__":
    iniciar_servidor()