# cliente_app.py
import socket
import os
import json
import time

# Importa as funções dos seus arquivos específicos
from configuracoes import obter_dados_conexao
from caminho_dados import obter_diretorios
from func_json import receber_dados_json, enviar_json, obter_caminho_relativo, TAMANHO_BUFFER


# Obtenha configurações usando as funções
HOST_NAO_USADO, PORTA_SERVIDOR = obter_dados_conexao() # HOST não é usado no cliente, mas PORTA_SERVIDOR é
DIRETORIO_CLIENTES_ARMAZENAMENTO, ARQUIVO_DADOS_CLIENTES = obter_diretorios() # Não usado diretamente aqui, mas mantém consistência


def enviar_arquivo_diretorio(sock, caminho_origem, caminho_base_remoto):
    """
    Envia um arquivo ou um diretório (e seu conteúdo) de forma iterativa usando os.walk().
    """
    print("#### <ENTROU EM enviar_arquivo_diretorio (usando os.walk)> ####\n")

    if os.path.isfile(caminho_origem): # Se é um arquivo, envia diretamente
        # Calcula o caminho relativo do arquivo em relação ao caminho_base_remoto fornecido
        caminho_relativo_no_servidor = obter_caminho_relativo(caminho_origem, caminho_base_remoto)
        tamanho_arquivo = os.path.getsize(caminho_origem)
        comando = f"UPLOAD:false:{caminho_relativo_no_servidor}:{tamanho_arquivo}"
        sock.sendall(comando.encode('utf-8'))
        resposta_servidor = sock.recv(TAMANHO_BUFFER).decode('utf-8')

        if resposta_servidor == "PRONTO_PARA_RECEBER_ARQUIVO":
            try:
                with open(caminho_origem, 'rb') as f:
                    bytes_enviados = 0
                    while bytes_enviados < tamanho_arquivo:
                        bytes_para_enviar = min(tamanho_arquivo - bytes_enviados, TAMANHO_BUFFER)
                        dados = f.read(bytes_para_enviar)
                        if not dados:
                            print(f"ERRO: Arquivo '{caminho_origem}' lido incompletamente. Conexão perdida?\n")
                            break
                        sock.sendall(dados)
                        bytes_enviados += len(dados)
                print(f"INFO: Arquivo '{caminho_origem}' enviado. {bytes_enviados} de {tamanho_arquivo} bytes.\n")
                resposta_final = sock.recv(TAMANHO_BUFFER).decode('utf-8')
                if resposta_final == "ARQUIVO_RECEBIDO_OK":
                    print(f"INFO: Confirmação de recebimento do arquivo '{caminho_origem}'.\n")
                else:
                    print(f"ERRO: Erro ao receber confirmação para o arquivo '{caminho_origem}': {resposta_final}\n")
            except FileNotFoundError:
                print(f"ERRO: Arquivo local '{caminho_origem}' não encontrado durante o envio.\n")
                sock.sendall("ERRO:ARQUIVO_LOCAL_NAO_ENCONTRADO".encode('utf-8'))
            except Exception as e:
                print(f"ERRO: Erro durante o envio do arquivo '{caminho_origem}': {e}\n")
                sock.sendall("ERRO:FALHA_ENVIO_CLIENTE".encode('utf-8'))
        else:
            print(f"ERRO: Servidor não pronto para receber arquivo '{caminho_origem}': {resposta_servidor}\n")

    elif os.path.isdir(caminho_origem): # Se é um diretório, usa os.walk
        print(f"INFO: Iniciando upload de diretório: {caminho_origem}\n")
        
        for raiz_atual, subdiretorios, arquivos in os.walk(caminho_origem):
            caminho_relativo_dir_atual = obter_caminho_relativo(raiz_atual, caminho_base_remoto)
            
            if raiz_atual != caminho_origem:
                comando_dir = f"UPLOAD:true:{caminho_relativo_dir_atual}:MARCADOR_DIR"
                sock.sendall(comando_dir.encode('utf-8'))
                resposta_servidor_dir = sock.recv(TAMANHO_BUFFER).decode('utf-8')
                if resposta_servidor_dir == "DIR_CRIADO":
                    print(f"INFO: Subdiretório '{caminho_relativo_dir_atual}' criado no servidor.\n")
                else:
                    print(f"ERRO: Servidor não conseguiu criar subdiretório '{caminho_relativo_dir_atual}': {resposta_servidor_dir}\n")

            for nome_arquivo in arquivos:
                caminho_completo_arquivo = os.path.join(raiz_atual, nome_arquivo)
                caminho_relativo_arquivo = obter_caminho_relativo(caminho_completo_arquivo, caminho_base_remoto)
                
                tamanho_arquivo = os.path.getsize(caminho_completo_arquivo)
                comando_arquivo = f"UPLOAD:false:{caminho_relativo_arquivo}:{tamanho_arquivo}"
                sock.sendall(comando_arquivo.encode('utf-8'))
                resposta_servidor_arquivo = sock.recv(TAMANHO_BUFFER).decode('utf-8')

                if resposta_servidor_arquivo == "PRONTO_PARA_RECEBER_ARQUIVO":
                    try:
                        with open(caminho_completo_arquivo, 'rb') as f:
                            bytes_enviados = 0
                            while bytes_enviados < tamanho_arquivo:
                                bytes_para_enviar = min(tamanho_arquivo - bytes_enviados, TAMANHO_BUFFER)
                                dados = f.read(bytes_para_enviar)
                                if not dados:
                                    print(f"ERRO: Arquivo '{caminho_completo_arquivo}' lido incompletamente. Conexão perdida?\n")
                                    break
                                sock.sendall(dados)
                                bytes_enviados += len(dados)
                        print(f"INFO: Arquivo '{caminho_completo_arquivo}' enviado. {bytes_enviados} de {tamanho_arquivo} bytes.\n")
                        resposta_final = sock.recv(TAMANHO_BUFFER).decode('utf-8')
                        if resposta_final == "ARQUIVO_RECEBIDO_OK":
                            print(f"INFO: Confirmação de recebimento do arquivo '{caminho_completo_arquivo}'.\n")
                        else:
                            print(f"ERRO: Erro ao receber confirmação para o arquivo '{caminho_completo_arquivo}': {resposta_final}\n")
                    except FileNotFoundError:
                        print(f"ERRO: Arquivo local '{caminho_completo_arquivo}' não encontrado durante o envio.\n")
                        sock.sendall("ERRO:ARQUIVO_LOCAL_NAO_ENCONTRADO".encode('utf-8'))
                    except Exception as e:
                        print(f"ERRO: Erro durante o envio do arquivo '{caminho_completo_arquivo}': {e}\n")
                        sock.sendall("ERRO:FALHA_ENVIO_CLIENTE".encode('utf-8'))
                else:
                    print(f"ERRO: Servidor não pronto para receber arquivo '{caminho_completo_arquivo}': {resposta_servidor_arquivo}\n")
    else:
        print(f"AVISO: Caminho inválido ou não suportado para envio: {caminho_origem}\n")


def main():
    print("#### <ENTROU EM main (cliente)> ####\n")
    ip_servidor = input("Digite o IP do servidor: ")
    porta_servidor = PORTA_SERVIDOR # Obtém a porta do arquivo de configuração

    id_cliente_sessao = None
    caminho_base_minha_pasta = None 

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s: # Cria um socket TCP/IP
        try:
            s.connect((ip_servidor, porta_servidor)) # Conecta ao servidor
            print(f"INFO: Conectado ao servidor em {ip_servidor}:{porta_servidor}\n")

            escolha = input("Deseja criar uma nova pasta (N) ou usar uma existente (E)? ").upper()
            if escolha == 'N':
                s.sendall("CRIAR_NOVA_PASTA".encode('utf-8'))
                resposta = s.recv(TAMANHO_BUFFER).decode('utf-8')
                if resposta.startswith("PASTA_CRIADA:"):
                    id_cliente_sessao = resposta.split(":")[1]
                    print(f"INFO: Sua ID de pasta é: {id_cliente_sessao}\n")
                    caminho_base_minha_pasta = os.getcwd()
                else:
                    print(f"ERRO: Erro ao criar pasta: {resposta}\n")
                    return
            elif escolha == 'E':
                id_existente = input("Digite sua ID de pasta existente (ex: 192_168_1_10_1): ")
                s.sendall(f"USAR_PASTA_EXISTENTE:{id_existente}".encode('utf-8'))
                resposta = s.recv(TAMANHO_BUFFER).decode('utf-8')
                if resposta.startswith("PASTA_REUTILIZADA:"):
                    id_cliente_sessao = resposta.split(":")[1]
                    print(f"INFO: Usando sua ID de pasta existente: {id_cliente_sessao}\n")
                    caminho_base_minha_pasta = os.getcwd()
                else:
                    print(f"ERRO: Erro ao usar pasta existente: {resposta}\n")
                    return
            else:
                print("ERRO: Escolha inválida. Encerrando.\n")
                return

            while True:
                print("\nOpções:")
                print("1. Enviar arquivo ou diretório")
                print("2. Definir privacidade da pasta")
                print("3. Visualizar pastas públicas")
                print("4. Visualizar conteúdo de uma pasta (pública ou sua)")
                print("5. Sair")

                opcao = input("Escolha uma opção: ")

                if opcao == '1':
                    print("\n--- Antes de Enviar ---")
                    escolha_privacidade = input("Defina a privacidade da sua pasta (publica/privada) antes do envio: ").lower()
                    if escolha_privacidade in ['publica', 'privada']:
                        s.sendall(f"DEFINIR_PRIVACIDADE:{escolha_privacidade}".encode('utf-8'))
                        resposta = s.recv(TAMANHO_BUFFER).decode('utf-8')
                        print(f"INFO: Resposta do servidor: {resposta}\n")
                        if "ERRO" in resposta:
                            print("ERRO: Falha ao definir privacidade. Abortando envio.\n")
                            continue
                    else:
                        print("AVISO: Configuração de privacidade inválida. Abortando envio. Escolha 'publica' ou 'privada'.\n")
                        continue

                    caminho_para_enviar = input("Digite o caminho local do arquivo ou diretório a enviar: ")
                    if os.path.exists(caminho_para_enviar):
                        base_para_caminho_relativo = os.path.dirname(caminho_para_enviar) 
                        enviar_arquivo_diretorio(s, caminho_para_enviar, base_para_caminho_relativo)
                    else:
                        print("AVISO: Caminho não encontrado.\n")

                elif opcao == '2':
                    config_privacidade = input("Defina privacidade (publica/privada): ").lower()
                    if config_privacidade in ['publica', 'privada']:
                        s.sendall(f"DEFINIR_PRIVACIDADE:{config_privacidade}".encode('utf-8'))
                        resposta = s.recv(TAMANHO_BUFFER).decode('utf-8')
                        print(f"INFO: Resposta do servidor: {resposta}\n")
                    else:
                        print("AVISO: Configuração de privacidade inválida. Use 'publica' ou 'privada'.\n")

                elif opcao == '3':
                    s.sendall("LISTAR_PASTAS_PUBLICAS".encode('utf-8'))
                    pastas_publicas = receber_dados_json(s)
                    if pastas_publicas is not None and isinstance(pastas_publicas, list):
                        if pastas_publicas:
                            print("Pastas Públicas Disponíveis:")
                            for id_pasta in pastas_publicas:
                                print(f"- {id_pasta}")
                        else:
                            print("Nenhuma pasta pública disponível.\n")
                    else:
                        print(f"ERRO: Erro ou formato inesperado ao listar pastas públicas.\n")

                elif opcao == '4':
                    id_alvo = input(f"Digite a ID da pasta para visualizar (sua ID é '{id_cliente_sessao}'): ")
                    caminho_para_listar = input("Digite o caminho relativo dentro da pasta (deixe vazio para a raiz): ")
                    comando_listar = f"LISTAR_ARQUIVOS:{id_alvo}:{caminho_para_listar}"
                    s.sendall(comando_listar.encode('utf-8'))
                    info_arquivos = receber_dados_json(s)
                    if info_arquivos is not None:
                        if isinstance(info_arquivos, list):
                            print(f"\nConteúdo de '{id_alvo}/{caminho_para_listar}':")
                            if not info_arquivos:
                                print("(Vazio)\n")
                            for item in info_arquivos:
                                tipo_str = "DIR" if item.get('eh_diretorio') else "ARQUIVO"
                                tamanho_str = f"({item['tamanho']} bytes)" if not item.get('eh_diretorio') else ""
                                print(f"- {item['nome']} [{tipo_str}] {tamanho_str}")
                        elif isinstance(info_arquivos, dict) and info_arquivos.get("erro"):
                            print(f"ERRO: Erro ao listar arquivos: {info_arquivos.get('erro', 'Erro desconhecido')}\n")
                        else:
                            print(f"ERRO: Resposta inesperada ao listar arquivos: {info_arquivos}\n")
                    else:
                        print(f"ERRO: Nenhuma resposta ou erro ao listar arquivos.\n")


                elif opcao == '5': # SAIR
                    s.sendall("SAIR".encode('utf-8'))
                    print("INFO: Saindo...\n")
                    break
                else:
                    print("Opção inválida. Tente novamente.\n")

        except ConnectionRefusedError:
            print(f"ERRO: Conexão recusada. Certifique-se de que o servidor está rodando em {ip_servidor}:{porta_servidor}\n")
        except Exception as e:
            print(f"ERRO: Ocorreu um erro: {e}\n")
        finally:
            s.close()

if __name__ == "__main__":
    main()