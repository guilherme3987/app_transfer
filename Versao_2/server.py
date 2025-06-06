import socket #
import os #
import json #

from threading import Thread #

from Funcoes_aux.con_config import obter_dados_conexao #
from Funcoes_aux.checksum import calcular_checksum_dados #

from Funcoes_aux.cabecalho import criar_cabecalho_arquivo, receber_cabecalho, enviar_cabecalho, receber_dados, receber_dados_com_cabecalho #

IP, PORT, TAM_BUFFER, TAM_CABECALHO = obter_dados_conexao() #

DIRETORIO_DESTINO = "arquivos_recebidos" #

def iniciar_servidor():
    print("\n##########################\n<ENTROU EM INICIAR_SERVIDOR>\n############################")

    if not os.path.exists(DIRETORIO_DESTINO): #
        os.makedirs(DIRETORIO_DESTINO) #
    
    servidor_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #
    servidor_socket.bind((IP, PORT)) #
    servidor_socket.listen() # 
    
    print(f"\n### Servidor iniciado em {IP}:{PORT} ###\n")

    while True: #
        cliente_socket, addr = servidor_socket.accept() #
        print(f"\n### Nova conexão de {addr[0]}:{addr[1]} ###") #
            
        thread = Thread(target=lidar_cliente, args=(cliente_socket, addr)) #
        thread.start() #
        print(f"\n### Thread iniciada para {addr[0]}:{addr[1]} ###") #
                
    servidor_socket.close() #

def enviar_resposta(sock, dados):
    print("\n##########################\n<ENTROU EM ENVIAR_RESPOSTA (SERVER)>\n############################") #
    tamanho = len(dados) #
    cabecalho_tamanho = f"{tamanho: <{TAM_CABECALHO}}".encode('utf-8') #
    sock.sendall(cabecalho_tamanho + dados) #
    print(f"Resposta enviada com tamanho: {tamanho} bytes. Conteúdo: {dados.decode('utf-8').strip()}") #


def lidar_cliente(cliente_socket, addr):
    print("\n##########################\n<ENTROU EM LIDAR_CLIENTE>\n############################")

    print(f"\nNova conexão de {addr}")

    try: #
        while True: #
            cabecalho_info = receber_cabecalho(cliente_socket) #
            if not cabecalho_info: #
                print(f"Cliente {addr[0]} desconectou") #
                break #

            tipo = cabecalho_info['tipo'] #
            tamanho = cabecalho_info['tamanho'] #
            checksum_esperado = cabecalho_info['checksum'] #
            nome_recebido = cabecalho_info['nome'] # pode ser nome do arquivo ou caminho do diretório
            
            print(f"\n### Tipo: {tipo}, Tamanho: {tamanho}, Checksum esperado: {checksum_esperado}, Nome/Caminho: {nome_recebido} ###\n")

            if tipo == "DIR": #
                caminho_completo_diretorio = os.path.join(DIRETORIO_DESTINO, nome_recebido) #
                try: #
                    os.makedirs(caminho_completo_diretorio, exist_ok=True) #
                    enviar_resposta(cliente_socket, b"OK") #
                    print(f"\n### Diretório '{caminho_completo_diretorio}' criado com sucesso. ###\n") #
                except OSError as e: #
                    enviar_resposta(cliente_socket, f" [Erro] ao criar diretório: {e}".encode('utf-8')) #
                    print(f"\n### ERRO: ao criar diretório '{caminho_completo_diretorio}': {e} ###\n") #
                    break # Encerra a conexão se não conseguir criar o diretório
            
            elif tipo == "FILE": #
                # Responde OK para que o cliente envie os dados do arquivo
                enviar_resposta(cliente_socket, b"OK") #

                # Receber os dados do arquivo
                dados_arquivo = receber_dados(cliente_socket, tamanho) #
                if not dados_arquivo: #
                    print(f"Não recebeu dados completos de {addr[0]} para o arquivo {nome_recebido}") #
                    enviar_resposta(cliente_socket, b" [Erro] Dados incompletos") #
                    continue # Tenta receber o próximo cabeçalho
                
                # Verificar o checksum
                checksum_recebido = calcular_checksum_dados(dados_arquivo) #
                print(f"\n### Checksum recebido: {checksum_recebido} ###\n") #
                
                if checksum_recebido != checksum_esperado: #
                    enviar_resposta(cliente_socket, b" [Erro] Checksum invalido") #
                    print(f"\n### ERRO: Checksum inválido para o arquivo {nome_recebido} ###\n") #
                    continue # Tenta receber o próximo cabeçalho

                # Salvar o arquivo no caminho completo (incluindo subdiretórios se houver)
                caminho_completo_arquivo = os.path.join(DIRETORIO_DESTINO, nome_recebido) #
                
                # Garante que o diretório pai do arquivo exista
                os.makedirs(os.path.dirname(caminho_completo_arquivo), exist_ok=True) #
                
                with open(caminho_completo_arquivo, 'wb') as f: #
                    f.write(dados_arquivo) #
                
                enviar_resposta(cliente_socket, b"Arquivo recebido com sucesso") #
                print(f"\n### Arquivo {nome_recebido} salvo em {caminho_completo_arquivo} ###\n") #
            else: #
                enviar_resposta(cliente_socket, b" [Erro] Tipo de operacao desconhecido") #
                print(f"\n### ERRO: Tipo de operação desconhecido: {tipo} ###\n") #
                break # Encerra a conexão para tipo desconhecido

    except ConnectionResetError: #
        print(f"Conexão com {addr[0]} foi resetada") #
    except Exception as e: #
        print(f" [Erro] com {addr[0]}: {e}") #
    finally: #
        cliente_socket.close() #
        print(f"Conexão com {addr[0]} encerrada") #


if __name__ == "__main__":
    iniciar_servidor() #