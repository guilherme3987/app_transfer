# client.py
import socket
import os
import json
import time

# Importa as funções dos seus arquivos específicos
from config import dados_con
from caminho import diretorio
from func_json import receber_dados_json, enviar_json, get_relative_path, TAMANHO


# Obtenha configurações usando as funções
HOST, PORT = dados_con() # HOST não é usado no cliente, mas PORT é
DIRETORIO_CLIENTES, DADOS_CLIENTES_FILE = diretorio() # Não usado diretamente aqui, mas mantém consistência


def send_file_or_directory(sock, source_path, remote_base_path):
    """Envia um arquivo ou um diretório recursivamente."""
    print("#### <ENTROU EM send_file_or_directory> ####\n")
    if os.path.isfile(source_path): # Verifica se o caminho é um arquivo
        relative_path = get_relative_path(source_path, remote_base_path) # Obtém o caminho relativo
        file_size = os.path.getsize(source_path) # Obtém o tamanho do arquivo

        # Envia comando de upload para arquivo
        command = f"UPLOAD:false:{relative_path}:{file_size}"
        sock.sendall(command.encode('utf-8')) # Envia o comando
        response = sock.recv(TAMANHO).decode('utf-8') # Recebe a resposta do servidor

        if response == "PRONTO_PARA_RECEBER_ARQUIVO": # Se o servidor estiver pronto para receber
            try:
                with open(source_path, 'rb') as f: # Abre o arquivo local para leitura binária
                    bytes_sent = 0
                    while bytes_sent < file_size: # Loop para enviar o arquivo em pedaços
                        bytes_to_send = min(file_size - bytes_sent, TAMANHO)
                        data = f.read(bytes_to_send) # Lê um pedaço do arquivo
                        if not data:
                            print(f"ERRO: Arquivo '{source_path}' lido incompletamente.\n")
                            break
                        sock.sendall(data) # Envia o pedaço ao servidor
                        bytes_sent += len(data) # Atualiza bytes enviados
                print(f"INFO: Arquivo '{source_path}' enviado. {bytes_sent} de {file_size} bytes.\n")
                final_response = sock.recv(TAMANHO).decode('utf-8') # Espera a confirmação final do servidor
                if final_response == "ARQUIVO_RECEBIDO_OK":
                    print(f"INFO: Confirmação de recebimento do arquivo '{source_path}'.\n")
                else:
                    print(f"ERRO: Erro ao receber confirmação para o arquivo '{source_path}': {final_response}\n")
            except FileNotFoundError:
                print(f"ERRO: Arquivo local '{source_path}' não encontrado durante o envio.\n")
                sock.sendall("ERRO:ARQUIVO_LOCAL_NAO_ENCONTRADO".encode('utf-8')) # Informa o servidor sobre a falha
            except Exception as e:
                print(f"ERRO: Erro durante o envio do arquivo '{source_path}': {e}\n")
                sock.sendall("ERRO:FALHA_ENVIO_CLIENTE".encode('utf-8')) # Informa o servidor sobre a falha
        else:
            print(f"ERRO: Servidor não pronto para receber arquivo '{source_path}': {response}\n")

    elif os.path.isdir(source_path): # Se o caminho for um diretório
        relative_path = get_relative_path(source_path, remote_base_path) # Obtém o caminho relativo

        # Envia comando de upload para diretório
        command = f"UPLOAD:true:{relative_path}:MARCADOR_DIR"
        sock.sendall(command.encode('utf-8')) # Envia o comando
        response = sock.recv(TAMANHO).decode('utf-8') # Recebe a resposta do servidor

        if response == "DIR_CRIADO": # Se o diretório foi criado no servidor
            print(f"INFO: Diretório '{source_path}' criado no servidor.\n")
            for item in os.listdir(source_path): # Itera sobre os itens no diretório
                item_path = os.path.join(source_path, item) # Caminho completo do item
                send_file_or_directory(sock, item_path, remote_base_path) # Chama recursivamente para subitens
        else:
            print(f"ERRO: Servidor não conseguiu criar diretório '{source_path}': {response}\n")
    else:
        print(f"AVISO: Caminho inválido ou não suportado para envio: {source_path}\n")


def download_file(sock, target_client_id, relative_file_path, save_directory):
    """Baixa um arquivo do servidor."""
    print("#### <ENTROU EM download_file> ####\n")
    command = f"DOWNLOAD:{target_client_id}:{relative_file_path}"
    sock.sendall(command.encode('utf-8')) # Envia o comando de download

    response = sock.recv(TAMANHO).decode('utf-8') # Recebe a resposta do servidor
    if response.startswith("INFO_ARQUIVO:"): # Se o servidor enviar informações do arquivo
        file_size = int(response.split(":")[1]) # Extrai o tamanho do arquivo
        print(f"INFO: Baixando '{relative_file_path}'. Tamanho: {file_size} bytes.\n")

        sock.sendall("PRONTO_PARA_RECEBER_ARQUIVO".encode('utf-8')) # Confirma que está pronto para receber

        local_file_path = os.path.join(save_directory, relative_file_path) # Caminho local para salvar
        os.makedirs(os.path.dirname(local_file_path), exist_ok=True) # Cria diretórios pais localmente

        bytes_received = 0
        try:
            with open(local_file_path, 'wb') as f: # Abre o arquivo local para escrita binária
                while bytes_received < file_size: # Loop para receber o arquivo em pedaços
                    bytes_to_read = min(file_size - bytes_received, TAMANHO)
                    data = sock.recv(bytes_to_read) # Recebe pedaços do arquivo
                    if not data:
                        print(f"ERRO: Conexão perdida durante o download de '{relative_file_path}'.\n")
                        break
                    f.write(data) # Escreve no arquivo
                    bytes_received += len(data) # Atualiza bytes recebidos
            print(f"INFO: Arquivo '{relative_file_path}' baixado para '{local_file_path}'. {bytes_received} de {file_size} bytes.\n")
        except Exception as e:
            print(f"ERRO: Erro durante o download do arquivo '{relative_file_path}': {e}\n")
    elif response.startswith("ERRO:"):
        print(f"ERRO: Erro ao tentar baixar arquivo: {response}\n")
    else:
        print(f"ERRO: Resposta inesperada do servidor ao tentar baixar arquivo: {response}\n")

def main():
    print("#### <ENTROU EM main (client)> ####\n")
    server_ip = input("Digite o IP do servidor: ")
    server_port = PORT # Obtém a porta do arquivo de configuração

    client_id = None
    my_folder_path = None # Usado como base para calcular caminhos relativos ao fazer upload

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s: # Cria um socket TCP/IP
        try:
            s.connect((server_ip, server_port)) # Conecta ao servidor
            print(f"INFO: Conectado ao servidor em {server_ip}:{server_port}\n")

            # Primeira comunicação: criar ou usar pasta existente
            choice = input("Deseja criar uma nova pasta (N) ou usar uma existente (E)? ").upper()
            if choice == 'N':
                s.sendall("CRIAR_NOVA_PASTA".encode('utf-8')) # Envia comando para criar nova pasta
                response = s.recv(TAMANHO).decode('utf-8') # Recebe a resposta
                if response.startswith("PASTA_CRIADA:"):
                    client_id = response.split(":")[1] # Extrai a ID da pasta
                    print(f"INFO: Sua ID de pasta é: {client_id}\n")
                    my_folder_path = os.getcwd() # Define o diretório de trabalho atual como base
                else:
                    print(f"ERRO: Erro ao criar pasta: {response}\n")
                    return
            elif choice == 'E':
                existing_id = input("Digite sua ID de pasta existente (ex: 192_168_1_10_1): ")
                s.sendall(f"USAR_PASTA_EXISTENTE:{existing_id}".encode('utf-8')) # Envia comando para usar pasta existente
                response = s.recv(TAMANHO).decode('utf-8') # Recebe a resposta
                if response.startswith("PASTA_REUTILIZADA:"):
                    client_id = response.split(":")[1] # Extrai a ID da pasta
                    print(f"INFO: Usando sua ID de pasta existente: {client_id}\n")
                    my_folder_path = os.getcwd() # Define o diretório de trabalho atual como base
                else:
                    print(f"ERRO: Erro ao usar pasta existente: {response}\n")
                    return
            else:
                print("ERRO: Escolha inválida. Encerrando.\n")
                return

            while True:
                print("\nOpções:")
                print("1. Enviar arquivo/diretório")
                print("2. Definir privacidade da pasta")
                print("3. Visualizar pastas públicas")
                print("4. Visualizar conteúdo de uma pasta (pública ou sua)")
                print("5. Baixar arquivo")
                print("6. Sair")

                option = input("Escolha uma opção: ")

                if option == '1':
                    # A visibilidade é definida antes do envio
                    print("\n--- Antes de Enviar ---")
                    privacy_choice = input("Defina a privacidade da sua pasta (publica/privada) antes do envio: ").lower()
                    if privacy_choice in ['publica', 'privada']:
                        s.sendall(f"DEFINIR_PRIVACIDADE:{privacy_choice}".encode('utf-8')) # Envia comando de privacidade
                        response = s.recv(TAMANHO).decode('utf-8') # Recebe resposta
                        print(f"INFO: Resposta do servidor: {response}\n")
                        if "ERRO" in response:
                            print("ERRO: Falha ao definir privacidade. Abortando envio.\n")
                            continue # Não prossegue com o envio se a definição de privacidade falhou
                    else:
                        print("AVISO: Configuração de privacidade inválida. Abortando envio. Escolha 'publica' ou 'privada'.\n")
                        continue # Não prossegue com o envio

                    path_to_send = input("Digite o caminho local do arquivo ou diretório a enviar: ")
                    if os.path.exists(path_to_send): # Verifica se o caminho existe localmente
                        # Define a base para o caminho relativo
                        base_for_relative_path = path_to_send if os.path.isdir(path_to_send) else os.path.dirname(path_to_send)
                        send_file_or_directory(s, path_to_send, base_for_relative_path) # Chama função de envio
                    else:
                        print("AVISO: Caminho não encontrado.\n")

                elif option == '2':
                    privacy_setting = input("Defina privacidade (publica/privada): ").lower()
                    if privacy_setting in ['publica', 'privada']:
                        s.sendall(f"DEFINIR_PRIVACIDADE:{privacy_setting}".encode('utf-8')) # Envia comando de privacidade
                        response = s.recv(TAMANHO).decode('utf-8') # Recebe resposta
                        print(f"INFO: Resposta do servidor: {response}\n")
                    else:
                        print("AVISO: Configuração de privacidade inválida. Use 'publica' ou 'privada'.\n")

                elif option == '3':
                    s.sendall("LISTAR_PASTAS_PUBLICAS".encode('utf-8')) # Envia comando para listar pastas públicas
                    public_folders = receber_dados_json(s) # Recebe a lista como JSON
                    if public_folders is not None and isinstance(public_folders, list):
                        if public_folders:
                            print("Pastas Públicas Disponíveis:")
                            for folder_id in public_folders:
                                print(f"- {folder_id}")
                        else:
                            print("Nenhuma pasta pública disponível.\n")
                    else:
                        print(f"ERRO: Erro ou formato inesperado ao listar pastas públicas.\n")

                elif option == '4':
                    target_id = input(f"Digite a ID da pasta para visualizar (sua ID é '{client_id}'): ")
                    path_to_list = input("Digite o caminho relativo dentro da pasta (deixe vazio para a raiz): ")
                    command = f"LISTAR_ARQUIVOS:{target_id}:{path_to_list}"
                    s.sendall(command.encode('utf-8')) # Envia comando para listar arquivos
                    files_info = receber_dados_json(s) # Recebe as informações dos arquivos como JSON
                    if files_info is not None:
                        if isinstance(files_info, list):
                            print(f"\nConteúdo de '{target_id}/{path_to_list}':")
                            if not files_info:
                                print("(Vazio)\n")
                            for item in files_info:
                                type_str = "DIR" if item['eh_diretorio'] else "ARQUIVO"
                                size_str = f"({item['tamanho']} bytes)" if not item['eh_diretorio'] else ""
                                print(f"- {item['nome']} [{type_str}] {size_str}")
                        elif isinstance(files_info, dict) and files_info.get("ERRO"):
                            print(f"ERRO: Erro ao listar arquivos: {files_info.get('MENSAGEM_ERRO', 'Erro desconhecido')}\n")
                        else:
                            print(f"ERRO: Resposta inesperada ao listar arquivos: {files_info}\n")
                    else:
                        print(f"ERRO: Nenhuma resposta ou erro ao listar arquivos.\n")


                elif option == '5':
                    target_id = input(f"Digite a ID da pasta de onde baixar (sua ID é '{client_id}'): ")
                    relative_path_to_download = input("Digite o caminho relativo do arquivo a baixar: ")
                    save_dir = input("Digite o diretório local para salvar (deixe vazio para o diretório atual): ") or "."
                    download_file(s, target_id, relative_path_to_download, save_dir) # Chama função de download

                elif option == '6':
                    s.sendall("SAIR".encode('utf-8')) # Envia comando para sair
                    print("INFO: Saindo...\n")
                    break
                else:
                    print("Opção inválida. Tente novamente.\n")

        except ConnectionRefusedError:
            print(f"ERRO: Conexão recusada. Certifique-se de que o servidor está rodando em {server_ip}:{server_port}\n")
        except Exception as e:
            print(f"ERRO: Ocorreu um erro: {e}\n")
        finally:
            s.close() # Fecha o socket do cliente

if __name__ == "__main__":
    main()