import socket
import os
from Funcoes_aux.con_config import obter_dados_conexao 
from Funcoes_aux.checksum import calcular_checksum_dados
from Funcoes_aux.cabecalho import criar_cabecalho_arquivo, enviar_cabecalho, receber_cabecalho #


IP, PORT, TAM_BUFFER, TAM_CABECALHO = obter_dados_conexao()

def criar_socket():
    print("\n##########################\n<ENTROU EM CRIAR_SOCKET>\n############################")
    return socket.socket(socket.AF_INET, socket.SOCK_STREAM)


def enviar_dados(client_socket, dados):
    """
    Envia um bloco de dados para o socket, prefixado com seu tamanho.
    Esta função é usada para enviar o *conteúdo real do arquivo*.
    """
    print("\n##########################\n<ENTROU EM ENVIAR_DADOS>\n############################")

    tamanho = len(dados)
    # Formata o tamanho para preencher o TAM_CABECALHO e o codifica em bytes
    cabecalho = f"{tamanho: {TAM_CABECALHO}}".encode('utf-8')  
    client_socket.sendall(cabecalho + dados) # Envia o cabeçalho de tamanho seguido dos dados

def receber_dados(client_socket, tamanho_esperado):    
    """
    Recebe um bloco de dados do socket até que o tamanho esperado seja atingido.
    """
    print("\n##########################\n<ENTROU EM RECEBER_DADOS>\n############################")
    dados = b''
    bytes_recebidos = 0
    
    while bytes_recebidos < tamanho_esperado:
        # Recebe uma parte dos dados, limitando pelo buffer ou pelo que falta receber
        parte = client_socket.recv(min(TAM_BUFFER, tamanho_esperado - bytes_recebidos))
        if not parte:
            print("\n### Dados incompletos. ###\n")
            break
        dados += parte
        bytes_recebidos += len(parte)
    
    if bytes_recebidos == tamanho_esperado:
        return dados
    return None

def receber_resposta(client_socket):
    print("\n##########################\n<ENTROU EM RECEBER_RESPOSTA>\n############################")

    # Recebe a parte do cabeçalho que indicaamanho da resposta
    cabecalho_tamanho_resposta = receber_dados(client_socket, TAM_CABECALHO)
    if not cabecalho_tamanho_resposta:
        print("\n### Conexão fechada pelo servidor ou cabeçalho de resposta vazio. ###\n")
        return None
    
    try:
        # Decodifica e converte o cabeçalho para obter o tamanho da resposta
        tamanho_resposta = int(cabecalho_tamanho_resposta.decode('utf-8').strip())
    except ValueError:
        print(f"\n### Erro: Cabeçalho de tamanho de resposta inválido: '{cabecalho_tamanho_resposta.decode('utf-8').strip()}' ###\n")
        return None

    print(f"\n### Tamanho da resposta esperado: {tamanho_resposta} bytes ###\n")
    
    # Recebe o corpo da resposta com o tamanho esperado
    resposta = receber_dados(client_socket, tamanho_resposta)
    
    return resposta

if __name__ == "__main__":
    client_socket = criar_socket()

    ip_servidor = input("Digite o IP do servidor: ")

    try:
        client_socket.connect((ip_servidor, PORT))
        print(f"Conectado ao servidor {ip_servidor}:{PORT}")

        caminho_arquivo = input("Digite o caminho completo do arquivo para enviar: ")
            
        if not os.path.exists(caminho_arquivo):
            print(f"\n### ERRO: O arquivo '{caminho_arquivo}' não foi encontrado. ###\n")
            exit()

        nome_arquivo = os.path.basename(caminho_arquivo)
            
        # Lê o conteúdo do arquivo em modo binário
        with open(caminho_arquivo, 'rb') as f:
            dados_arquivo = f.read()

        # Calcula o checksum do arquivo
        checksum_arquivo = calcular_checksum_dados(dados_arquivo)

        # Cria o cabeçalho do arquivo formatado (tipo|tamanho|checksum|nome)
        cabecalho_arquivo = criar_cabecalho_arquivo("FILE", nome_arquivo, dados_arquivo) # "FILE" como tipo

        print(f"\n### Enviando cabeçalho do arquivo: {cabecalho_arquivo.decode('utf-8').strip()} ###\n")
        enviar_cabecalho(client_socket, cabecalho_arquivo)

        resposta_servidor = receber_resposta(client_socket)
        if resposta_servidor.decode('utf-8').strip() == "OK":
            print("\n### Servidor pronto para receber o arquivo. Enviando dados... ###\n")
            client_socket.sendall(dados_arquivo) 

            resposta_final = receber_resposta(client_socket)
            if resposta_final:
                    print(f"\n### Resposta do servidor: {resposta_final.decode('utf-8').strip()} ###\n")
            else:
                print("\n### Nenhuma resposta final do servidor recebida. ###\n")
        else:
            print(f"\n### Servidor não enviou 'OK'. Resposta: {resposta_servidor.decode('utf-8').strip() if resposta_servidor else 'Nenhuma'} ###\n")

    except Exception as e:
        print(f"### ❌ [Erro]  ao conectar ou comunicar com o servidor: {e} ###\n")

    finally:
        print("\n--- Encerrando Cliente ---")
        client_socket.close()
