import socket #
import os #
from Funcoes_aux.con_config import obter_dados_conexao #
from Funcoes_aux.checksum import calcular_checksum_dados #
from Funcoes_aux.cabecalho import criar_cabecalho_arquivo, enviar_cabecalho, receber_cabecalho, receber_dados #


IP, PORT, TAM_BUFFER, TAM_CABECALHO = obter_dados_conexao() #

def criar_socket():
    print("\n##########################\n<ENTROU EM CRIAR_SOCKET>\n############################") #
    return socket.socket(socket.AF_INET, socket.SOCK_STREAM) #

def receber_resposta(client_socket):
    print("\n##########################\n<ENTROU EM RECEBER_RESPOSTA>\n############################") #

    # Recebe a parte do cabeçalho que indica o tamanho da resposta
    cabecalho_tamanho_resposta = receber_dados(client_socket, TAM_CABECALHO) #
    if not cabecalho_tamanho_resposta: #
        print("\n### Conexão fechada pelo servidor ou cabeçalho de resposta vazio. ###\n") #
        return None #
    
    try: #
        # Decodifica e converte o cabeçalho para obter o tamanho da resposta
        tamanho_resposta = int(cabecalho_tamanho_resposta.decode('utf-8').strip()) #
    except ValueError: #
        print(f"\n### Erro: Cabeçalho de tamanho de resposta inválido: '{cabecalho_tamanho_resposta.decode('utf-8').strip()}' ###\n") #
        return None #

    print(f"\n### Tamanho da resposta esperado: {tamanho_resposta} bytes ###\n") #
    
    # Recebe o corpo da resposta com o tamanho esperado
    resposta = receber_dados(client_socket, tamanho_resposta) #
    
    return resposta #

def enviar_arquivo(client_socket, caminho_arquivo):
    print(f"\n### Preparando para enviar arquivo: {caminho_arquivo} ###\n") #
    nome_arquivo = os.path.basename(caminho_arquivo) #
    
    # Lê o conteúdo do arquivo em modo binário
    with open(caminho_arquivo, 'rb') as f: #
        dados_arquivo = f.read() #

    # Calcula o checksum do arquivo
    checksum_arquivo = calcular_checksum_dados(dados_arquivo) #

    # Cria o cabeçalho do arquivo formatado (tipo|tamanho|checksum|nome)
    cabecalho_arquivo = criar_cabecalho_arquivo("FILE", nome_arquivo, dados_arquivo) #

    print(f"\n### Enviando cabeçalho do arquivo: {cabecalho_arquivo.decode('utf-8').strip()} ###\n") #
    enviar_cabecalho(client_socket, cabecalho_arquivo) #

    resposta_servidor = receber_resposta(client_socket) #
    if resposta_servidor and resposta_servidor.decode('utf-8').strip() == "OK": #
        print("\n### Servidor pronto para receber o arquivo. Enviando dados... ###\n") #
        client_socket.sendall(dados_arquivo) #

        resposta_final = receber_resposta(client_socket) #
        if resposta_final: #
                print(f"\n### Resposta do servidor: {resposta_final.decode('utf-8').strip()} ###\n") #
        else: #
            print("\n### Nenhuma resposta final do servidor recebida. ###\n") #
    else: #
        print(f"\n### Servidor não enviou 'OK'. Resposta: {resposta_servidor.decode('utf-8').strip() if resposta_servidor else 'Nenhuma'} ###\n") #

def enviar_diretorio(client_socket, caminho_diretorio_base):
    print(f"\n### Preparando para enviar diretório: {caminho_diretorio_base} ###\n") #
    
    # Envia o cabeçalho para o diretório raiz
    nome_diretorio_base = os.path.basename(caminho_diretorio_base) #
    cabecalho_diretorio = criar_cabecalho_arquivo("DIR", nome_diretorio_base) #
    enviar_cabecalho(client_socket, cabecalho_diretorio) #
    
    resposta_servidor = receber_resposta(client_socket) #
    if not (resposta_servidor and resposta_servidor.decode('utf-8').strip() == "OK"): #
        print(f"\n### Servidor não confirmou a criação do diretório base. Abortando. ###\n") #
        return #

    for root, dirs, files in os.walk(caminho_diretorio_base): #
        # Enviar subdiretórios
        for dir_name in dirs: #
            caminho_completo_diretorio = os.path.join(root, dir_name) #
            # Obter o caminho relativo ao diretório base que está sendo enviado
            caminho_relativo_diretorio = os.path.relpath(caminho_completo_diretorio, caminho_diretorio_base) #
            
            print(f"\n### Enviando cabeçalho para criar diretório: {caminho_relativo_diretorio} ###\n") #
            cabecalho_subdiretorio = criar_cabecalho_arquivo("DIR", caminho_relativo_diretorio) #
            enviar_cabecalho(client_socket, cabecalho_subdiretorio) #
            
            resposta_servidor = receber_resposta(client_socket) #
            if not (resposta_servidor and resposta_servidor.decode('utf-8').strip() == "OK"): #
                print(f"\n### Servidor não confirmou a criação do subdiretório {caminho_relativo_diretorio}. Abortando. ###\n") #
                return #

        # Enviar arquivos
        for file_name in files: #
            caminho_completo_arquivo = os.path.join(root, file_name) #
            # Obter o caminho relativo ao diretório base que está sendo enviado
            caminho_relativo_arquivo = os.path.relpath(caminho_completo_arquivo, caminho_diretorio_base) #
            
            print(f"\n### Enviando arquivo: {caminho_relativo_arquivo} ###\n") #
            
            with open(caminho_completo_arquivo, 'rb') as f: #
                dados_arquivo = f.read() #
            
            checksum_arquivo = calcular_checksum_dados(dados_arquivo) #
            cabecalho_arquivo = criar_cabecalho_arquivo("FILE", caminho_relativo_arquivo, dados_arquivo) #
            
            enviar_cabecalho(client_socket, cabecalho_arquivo) #
            
            resposta_servidor = receber_resposta(client_socket) #
            if resposta_servidor and resposta_servidor.decode('utf-8').strip() == "OK": #
                print("\n### Servidor pronto para receber o arquivo. Enviando dados... ###\n") #
                client_socket.sendall(dados_arquivo) #

                resposta_final = receber_resposta(client_socket) #
                if resposta_final: #
                        print(f"\n### Resposta do servidor: {resposta_final.decode('utf-8').strip()} ###\n") #
                else: #
                    print("\n### Nenhuma resposta final do servidor recebida. ###\n") #
            else: #
                print(f"\n### Servidor não enviou 'OK' para o arquivo {caminho_relativo_arquivo}. Resposta: {resposta_servidor.decode('utf-8').strip() if resposta_servidor else 'Nenhuma'} ###\n") #
                return # Aborta se houver problema com um arquivo


if __name__ == "__main__":
    client_socket = criar_socket() #

    ip_servidor = input("Digite o IP do servidor: ") #

    try: #
        client_socket.connect((ip_servidor, PORT)) #
        print(f"Conectado ao servidor {ip_servidor}:{PORT}") #

        while True: #
            opcao = input("Deseja enviar (1) arquivo ou (2) diretório? (ou 'sair' para encerrar): ").strip().lower() #

            if opcao == 'sair': #
                break #
            elif opcao == '1': #
                caminho = input("Digite o caminho completo do arquivo para enviar: ") #
                if not os.path.exists(caminho): #
                    print(f"\n### ERRO: O arquivo '{caminho}' não foi encontrado. ###\n") #
                    continue #
                if not os.path.isfile(caminho): #
                    print(f"\n### ERRO: O caminho '{caminho}' não é um arquivo. ###\n") #
                    continue #
                enviar_arquivo(client_socket, caminho) #
                break # Envia um arquivo e encerra
            elif opcao == '2': #
                caminho = input("Digite o caminho completo do diretório para enviar: ") #
                if not os.path.exists(caminho): #
                    print(f"\n### ERRO: O diretório '{caminho}' não foi encontrado. ###\n") #
                    continue #
                if not os.path.isdir(caminho): #
                    print(f"\n### ERRO: O caminho '{caminho}' não é um diretório. ###\n") #
                    continue #
                enviar_diretorio(client_socket, caminho) #
                break # Envia um diretório e encerra
            else: #
                print("Opção inválida. Digite '1' para arquivo, '2' para diretório ou 'sair'.") #

    except Exception as e: #
        print(f"### ❌ [Erro]  ao conectar ou comunicar com o servidor: {e} ###\n") #

    finally: #
        print("\n--- Encerrando Cliente ---") #
        client_socket.close() #