import os
import json
from datetime import datetime
import time 


from func_json import receber_dados_json, enviar_json, obter_caminho_relativo, TAMANHO_BUFFER # Usar TAMANHO_BUFFER
from func_log import registrar_log 


def lidar_envio_arquivo_diretorio(instancia_servidor, conn, id_cliente, ip_cliente, caminho_armazenamento_cliente, comando):
    print(f"#### <ENTROU EM lidar_envio_arquivo_diretorio> ####\nComando: {comando}\n") 
    
    try:
        partes = comando.split(":", 3)
        
        if len(partes) < 4:
            conn.sendall("ERRO:COMANDO_UPLOAD_MAL_FORMADO".encode('utf-8'))
            return
            
        eh_diretorio_str = partes[1]
        caminho_relativo = partes[2]
        tamanho_ou_marcador_dir = partes[3]

        eh_diretorio = eh_diretorio_str.lower() == 'true' # Verifica se é um diretório

        # Normaliza o caminho para lidar com caracteres especiais
        caminho_relativo = os.path.normpath(caminho_relativo)
        caminho_destino = os.path.join(caminho_armazenamento_cliente, caminho_relativo)
        
        if eh_diretorio: # Use a variável booleana 'eh_diretorio'
            # Criação de diretório
            tipo_arquivo = 'diretorio' # Padronizado sem acento
            try:
                os.makedirs(caminho_destino, exist_ok=True) 
                conn.sendall("DIR_CRIADO".encode('utf-8'))
                registrar_log(id_cliente, ip_cliente, caminho_relativo, 0, tipo_arquivo, 'sucesso', None, None) # Passa None para tempo/taxa
                print(f"INFO: Log registrado para criação de diretório: {caminho_destino}\n")
                print(f"Diretório criado: {caminho_destino}\n")
            except Exception as e:
                conn.sendall("ERRO:CRIACAO_DIRETORIO".encode('utf-8'))
                registrar_log(id_cliente, ip_cliente, caminho_relativo, 0, tipo_arquivo, 'falha', None, None) # Passa None para tempo/taxa
                print(f"ERRO ao criar diretório {caminho_destino}: {e}\n")
        else:
            # Upload de arquivo
            tipo_arquivo = 'arquivo' 
            tempo_inicio = time.time() # Inicia a contagem de tempo
            try:
                tamanho_arquivo = int(tamanho_ou_marcador_dir)
                os.makedirs(os.path.dirname(caminho_destino), exist_ok=True)
                conn.sendall("PRONTO_PARA_RECEBER_ARQUIVO".encode('utf-8'))
                
                bytes_recebidos = 0
                with open(caminho_destino, 'wb') as arquivo_destino: 
                    while bytes_recebidos < tamanho_arquivo:
                        bytes_para_ler = min(tamanho_arquivo - bytes_recebidos, instancia_servidor.tamanho_buffer) 
                        dados = conn.recv(bytes_para_ler)
                        if not dados:
                            print(f"ERRO: Conexão encerrada antes de completar o upload do {tipo_arquivo}.\n")
                            # Registra falha com tempo/taxa, pois a transferência foi interrompida
                            # Calcula o tempo decorrido e a taxa de transferência até o momento da falha
                            tempo_decorrido = time.time() - tempo_inicio
                            taxa_transferencia_mbps = (bytes_recebidos / (1024 * 1024)) / (tempo_decorrido + 0.001)  # Evita divisão por zero
                            
                            # Registra o log com os dados da falha
                            registrar_log(
                                id_cliente, 
                                ip_cliente, 
                                caminho_relativo, 
                                bytes_recebidos, 
                                tipo_arquivo, 
                                'falha', 
                                tempo_decorrido, 
                                taxa_transferencia_mbps
                            )
                            break
                        arquivo_destino.write(dados)
                        bytes_recebidos += len(dados)
                
                tempo_fim = time.time() # Finaliza a contagem de tempo
                duracao_segundos = round(tempo_fim - tempo_inicio, 2) # Calcula a duração
                
                taxa_transferencia_mbps = 0
                if duracao_segundos > 0 and bytes_recebidos > 0: 
                    taxa_transferencia_mbps = (bytes_recebidos / (1024 * 1024)) / duracao_segundos # Calcula taxa em MB/s

                if bytes_recebidos == tamanho_arquivo:
                    conn.sendall("ARQUIVO_RECEBIDO_OK".encode('utf-8'))
                    # Registra sucesso com tempo e taxa
                    registrar_log(id_cliente, ip_cliente, caminho_relativo, tamanho_arquivo, tipo_arquivo, 'sucesso', duracao_segundos, taxa_transferencia_mbps) 
                    print(f"Arquivo recebido: {caminho_destino} ({bytes_recebidos} bytes) em {duracao_segundos}s ({taxa_transferencia_mbps:.2f} MB/s)\n")
                else:
                    conn.sendall("ERRO:UPLOAD_INCOMPLETO".encode('utf-8'))
                    # Registra falha com bytes recebidos, tempo e taxa até o momento da falha
                    registrar_log(id_cliente, ip_cliente, caminho_relativo, bytes_recebidos, tipo_arquivo, 'falha', duracao_segundos, taxa_transferencia_mbps) 
                    print(f"Upload incompleto: {bytes_recebidos}/{tamanho_arquivo} bytes em {duracao_segundos}s ({taxa_transferencia_mbps:.2f} MB/s)\n")
            except ValueError:
                print(f"ERRO: Tamanho do arquivo inválido recebido para upload: {tamanho_ou_marcador_dir}\n")
                conn.sendall("ERRO:TAMANHO_ARQUIVO_INVALIDO".encode('utf-8'))
                registrar_log(id_cliente, ip_cliente, caminho_relativo, 0, tipo_arquivo, 'falha', None, None) # Loga com 0 e None
            except Exception as e:
                print(f"ERRO: Erro no upload do arquivo {caminho_relativo}: {e}\n")
                conn.sendall("ERRO:FALHA_RECEBER_ARQUIVO".encode('utf-8'))
                registrar_log(id_cliente, ip_cliente, caminho_relativo, 0, tipo_arquivo, 'falha', None, None) # Loga com 0 e None
    except Exception as e:
        conn.sendall("ERRO:ERRO_INTERNO".encode('utf-8'))
        print(f"ERRO interno na função de upload: {e}\n")


def lidar_definir_privacidade(instancia_servidor, conn, id_cliente, comando):
    print(f"#### <ENTROU EM lidar_definir_privacidade> ####\nComando: {comando}\n")

    lista_privacidade = ['publica', 'privada']
    
    try:
        with instancia_servidor.trava_clientes[id_cliente]:
            config_privacidade = comando.split(":")[1].lower()

            if config_privacidade not in lista_privacidade:
                print(f"ERRO: Privacidade inválida: {config_privacidade}\n")
                conn.sendall("ERRO:PRIVACIDADE_INVALIDA".encode('utf-8'))
                return
            else:
                instancia_servidor.dados_clientes[id_cliente]['publico'] = (config_privacidade == 'publica') 
                instancia_servidor.salvar_dados_clientes()
                print(f"INFO: Privacidade do cliente {id_cliente} definida como {config_privacidade}\n")
                conn.sendall(f"PRIVACIDADE_ATUALIZADA:{config_privacidade.upper()}".encode('utf-8'))

    except Exception as e:
        print(f"ERRO: Erro ao definir privacidade para {id_cliente}: {e}\n")
        conn.sendall("ERRO:FALHA_DEFINIR_PRIVACIDADE".encode('utf-8'))


def lidar_listar_pastas_publicas(instancia_servidor, conn, id_cliente_solicitante):
    print(f"#### <ENTROU EM lidar_listar_pastas_publicas> ####\n")

    lista_pastas_publicas = []
    for id_cliente_na_lista, dados_cliente_na_lista in instancia_servidor.dados_clientes.items():
        if dados_cliente_na_lista['publico']:
            lista_pastas_publicas.append(id_cliente_na_lista)
    enviar_json(conn, lista_pastas_publicas)
    print(f"INFO: Lista de pastas públicas enviada para {id_cliente_solicitante}\n")


def lidar_listar_arquivos(instancia_servidor, conn, id_cliente_atual, caminho_armazenamento_cliente, comando):
    print(f"#### <ENTROU EM lidar_listar_arquivos> ####\nComando: {comando}\n")

    id_cliente_alvo = comando.split(":")[1]
    caminho_para_listar = ""
    # Deve-se verificar se existe a terceira parte no comando após o split por ":", que é o índice 2.
    if len(comando.split(":")) > 2: # Verifica se existe uma terceira parte no comando
        caminho_para_listar = comando.split(":", 2)[2] # Pega a terceira parte (índice 2)
    
    diretorio_base = ""
    if id_cliente_alvo == id_cliente_atual:
        diretorio_base = caminho_armazenamento_cliente
    else:
        if id_cliente_alvo in instancia_servidor.dados_clientes:
            if instancia_servidor.dados_clientes[id_cliente_alvo]['publico']:
                diretorio_base = instancia_servidor.dados_clientes[id_cliente_alvo]['caminho']
            else:
                enviar_json(conn, {"erro": "PASTA_NAO_PUBLICA"}) 
                print(f"ERRO: A pasta do cliente {id_cliente_alvo} não é pública.\n")
                return
        else:
            enviar_json(conn, {"erro": "CLIENTE_NAO_ENCONTRADO"}) 
            print(f"ERRO: Cliente {id_cliente_alvo} não encontrado.\n")
            return
    
    caminho_completo_no_servidor = os.path.join(diretorio_base, caminho_para_listar) 

    if not os.path.exists(caminho_completo_no_servidor):
        enviar_json(conn, {"erro": "CAMINHO_NAO_ENCONTRADO_NO_SERVIDORES"}) 
        print(f"ERRO: Caminho '{caminho_completo_no_servidor}' não encontrado.\n")
        return

    if not os.path.isdir(caminho_completo_no_servidor):
        enviar_json(conn, {"erro": "CAMINHO_NAO_EH_DIRETORIO"}) 
        print(f"ERRO: Caminho '{caminho_completo_no_servidor}' não é um diretório.\n")
        return

    info_arquivos = []
    for item in os.listdir(caminho_completo_no_servidor):
        caminho_item = os.path.join(caminho_completo_no_servidor, item)
        eh_diretorio_item = os.path.isdir(caminho_item)
        tamanho = os.path.getsize(caminho_item) if not eh_diretorio_item else 0
        info_arquivos.append({
            "nome": item,
            "tamanho": tamanho,
            "eh_diretorio": eh_diretorio_item
        })
    enviar_json(conn, info_arquivos)
    print(f"INFO: Lista de arquivos do cliente {id_cliente_alvo} enviada para {id_cliente_atual}\n")