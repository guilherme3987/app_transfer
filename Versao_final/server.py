import socket
import threading
import json
import os

from config import dados_con
from func_json import receber_dados_json, enviar_json, get_relative_path, TAMANHO # Importa TAMANHO aqui
from func_log import log as get_log_config, registra_log, criar_log
from caminho import diretorio

HOST, PORT = dados_con()
DIRETORIO_CLIENTES, DADOS_CLIENTES = diretorio()


#Classe para gerenciar estados dos clientes
class Servidor:
    def __init__(self):
        self.dados_clientes = {}
        self.trava_clientes = {} #Trava para acesso concorrente aos dados dos clientes
        self.carregar_dados_clientes()
        self.cont_ip={} #Contador de IPs para evitar duplicidade

        if not os.path.exists(DIRETORIO_CLIENTES):
            os.makedirs(DIRETORIO_CLIENTES)
            print(f"Diretório '{DIRETORIO_CLIENTES}' criado com sucesso.\n")
        
        criar_log()

    def carregar_dados_clientes(self):
        print("#### <ENTROU EM carregar_dados_clientes> ####\n")
        
        caminho_clientes = os.path.exists(DADOS_CLIENTES)
        
        if caminho_clientes:
        
            with open(DADOS_CLIENTES, 'r', encoding='utf-8') as f:
                self.dados_clientes = json.load(f)
            print(f"DADOS_CLIENTES carregados: {self.dados_clientes}\n")

            self.cont_ip = {}
            
            for cliente_id in self.dados_clientes:
                # cliente_id_completo é tipo '192_168_1_1_1'
                partes = cliente_id_completo.split('_')

                if len(partes) > 1:
                    # Remove o último item (contador) para formatar o IP
                    ip_formatado_partes = partes[:-1]
                    
                    
                    if ip_formatado_partes and ip_formatado_partes[-1] == '':
                        ip_formatado_partes.pop()
                    ip_formatado = '_'.join(ip_formatado_partes)

                    try:
                        contador_atual = int(partes[-1]) # O último item é o contador
                        if ip_formatado not in self.cont_ip or contador_atual >= self.cont_ip[ip_formatado]:    
                            self.cont_ip[ip_formatado] = contador_atual + 1 # Próximo contador para esse IP
                    except ValueError:
                        print(f"AVISO: ID de cliente '{cliente_id_completo}' com formato de contador inválido. Ignorando na contagem de IP.\n")
                        continue
            print(f"Contagem de IPs: {self.cont_ip}\n")
        else:
            print(f"AVISO: Arquivo '{DADOS_CLIENTES}' não encontrado. Usando dados_clientes vazio.\n")
            self.dados_clientes = {}

        #Incia a trava para cada cliente
        for cliente_id in self.dados_clientes:
            if cliente_id not in self.trava_clientes:
                self.trava_clientes[cliente_id] = threading.Lock()

    def salvar_dados_clientes(self):
        print("#### <ENTROU EM salvar_dados_clientes> ####\n")

        with open(DADOS_CLIENTES, 'w', encoding='utf-8') as f:
            json.dump(self.dados_clientes, f, indent=4, ensure_ascii=False)
        print(f"DADOS_CLIENTES salvos: {self.dados_clientes}\n")

    def criar_diretorio_cliente(self, cliente_id):
        print("#### <ENTROU EM criar_diretorio_cliente (Servidor)> ####\n")
        ip_cliente_formatado = ip_cliente.replace('.', '_') # Formata o IP para o nome da pasta
        proximo_contador = self.cont_ip.get(ip_cliente_formatado, 1) # Obtém o próximo contador para o IP

        nome_pasta_cliente = f"{ip_cliente_formatado}_{proximo_contador}" # Cria o nome da pasta
        caminho_pasta_cliente = os.path.join(DIRETORIO_CLIENTES, nome_pasta_cliente) # Cria o caminho completo da pasta

        os.makedirs(caminho_pasta_cliente) # Cria o diretório
        print(f"INFO: Pasta do cliente criada: {caminho_pasta_cliente}\n")

        cliente_id = nome_pasta_cliente # A ID do cliente é o nome da pasta
        # Armazena os dados do cliente
        self.dados_clientes[cliente_id] = {'publico': False, 'ip': ip_cliente, 'caminho': caminho_pasta_cliente}
        self.trava_clientes[cliente_id] = threading.Lock() # Cria uma trava para o cliente
        
        self.cont_ip[ip_cliente_formatado] = proximo_contador + 1 # Incrementa o contador para o próximo uso
        self.salvar_dados_clientes() # Salva os metadados atualizados
        return cliente_id, caminho_pasta_cliente

    def salvar_dados_clientes(self):
        print("#### <ENTROU EM salvar_dados_clientes (Servidor)> ####\n")
        try:
            with open(DADOS_CLIENTES_FILE, 'w', encoding='utf-8') as f: # Abre o arquivo para escrita
                json.dump(self.dados_clientes, f, indent=4, ensure_ascii=False) # Salva os dados JSON formatados
            print(f"INFO: Dados dos clientes salvos.\n")
        except Exception as e:
            print(f"ERRO: Erro ao salvar dados dos clientes: {e}\n")

    def criar_diretorio_cliente(self, ip_cliente):
        print("#### <ENTROU EM criar_diretorio_cliente (Servidor)> ####\n")
        ip_cliente_formatado = ip_cliente.replace('.', '_') # Formata o IP para o nome da pasta
        proximo_contador = self.cont_ip.get(ip_cliente_formatado, 1) # Obtém o próximo contador para o IP

        nome_pasta_cliente = f"{ip_cliente_formatado}_{proximo_contador}" # Cria o nome da pasta
        caminho_pasta_cliente = os.path.join(DIRETORIO_CLIENTES, nome_pasta_cliente) # Cria o caminho completo da pasta

        os.makedirs(caminho_pasta_cliente) # Cria o diretório
        print(f"INFO: Pasta do cliente criada: {caminho_pasta_cliente}\n")

        cliente_id = nome_pasta_cliente # A ID do cliente é o nome da pasta
        # Armazena os dados do cliente
        self.dados_clientes[cliente_id] = {'publico': False, 'ip': ip_cliente, 'caminho': caminho_pasta_cliente}
        self.trava_clientes[cliente_id] = threading.Lock() # Cria uma trava para o cliente
        
        self.cont_ip[ip_cliente_formatado] = proximo_contador + 1 # Incrementa o contador para o próximo uso
        self.salvar_dados_clientes() # Salva os metadados atualizados
        return cliente_id, caminho_pasta_cliente

    def lidar_com_conexao_cliente(self, conn, addr):
        print("#### <ENTROU EM lidar_com_conexao_cliente (Servidor)> ####\n")
        ip_cliente, _ = addr
        print(f"INFO: Conexão aceita de {ip_cliente}:{_}\n")

        cliente_id = None
        caminho_armazenamento_cliente = None
        try:
            mensagem_inicial = conn.recv(TAMANHO).decode('utf-8') # Recebe a mensagem inicial do cliente
            if mensagem_inicial == "CRIAR_NOVA_PASTA":
                cliente_id, caminho_armazenamento_cliente = self.criar_diretorio_cliente(ip_cliente) # Cria nova pasta
                conn.sendall(f"PASTA_CRIADA:{cliente_id}".encode('utf-8')) # Envia confirmação ao cliente
                print(f"INFO: Novo cliente {cliente_id} conectado e pasta criada.\n")
            elif mensagem_inicial.startswith("USAR_PASTA_EXISTENTE:"):
                _partes = mensagem_inicial.split(":")
                if len(_partes) == 2:
                    id_cliente_recebido = _partes[1]
                    # Verifica se a ID da pasta existe e pertence ao IP do cliente
                    if id_cliente_recebido in self.dados_clientes and self.dados_clientes[id_cliente_recebido]['ip'] == ip_cliente:
                        cliente_id = id_cliente_recebido
                        caminho_armazenamento_cliente = self.dados_clientes[cliente_id]['caminho']
                        conn.sendall(f"PASTA_REUTILIZADA:{cliente_id}".encode('utf-8')) # Confirma reutilização
                        print(f"INFO: Cliente {ip_cliente} reconectado e usando pasta existente: {cliente_id}\n")
                    else:
                        conn.sendall("ERRO:ID_PASTA_INVALIDA_OU_ACESSO_NEGADO".encode('utf-8')) # Erro de ID ou permissão
                        print(f"ERRO: Cliente {ip_cliente} tentou usar ID de pasta inválido ou não pertencente: {id_cliente_recebido}\n")
                        return # Encerra a conexão
                else:
                    conn.sendall("ERRO:SOLICITACAO_MAL_FORMADA".encode('utf-8')) # Erro de formato da solicitação
                    print(f"ERRO: Cliente {ip_cliente} enviou solicitação malformada: {mensagem_inicial}\n")
                    return # Encerra a conexão
            else:
                conn.sendall("ERRO:SOLICITACAO_INICIAL_DESCONHECIDA".encode('utf-8')) # Erro de solicitação desconhecida
                print(f"ERRO: Cliente {ip_cliente} enviou solicitação inicial desconhecida: {mensagem_inicial}\n")
                return # Encerra a conexão

            if not cliente_id or not caminho_armazenamento_cliente:
                print(f"ERRO: Falha ao determinar cliente_id ou caminho_armazenamento_cliente para {ip_cliente}.\n")
                return # Encerra a conexão

            while True:
                comando = conn.recv(TAMANHO).decode('utf-8') # Recebe comandos do cliente
                if not comando:
                    break # Cliente desconectou

                print(f"INFO: Comando recebido de {cliente_id}: {comando}\n")

                if comando.startswith("UPLOAD:"):
                    partes = comando.split(":", 3)
                    if len(partes) < 4:
                        conn.sendall("ERRO:COMANDO_UPLOAD_MAL_FORMADO".encode('utf-8')) # Erro de formato
                        continue

                    _, eh_diretorio_str, caminho_relativo, tamanho_ou_marcador_dir = partes
                    eh_diretorio = eh_diretorio_str.lower() == 'true'
                    caminho_destino = os.path.join(caminho_armazenamento_cliente, caminho_relativo) # Caminho de destino no servidor
                    tamanho_arquivo = 0 # Padrão para diretórios ou falhas
                    tipo_arquivo = 'diretorio' if eh_diretorio else 'arquivo'

                    if eh_diretorio:
                        os.makedirs(caminho_destino, exist_ok=True) # Cria o diretório
                        conn.sendall("DIR_CRIADO".encode('utf-8')) # Confirma criação
                        print(f"INFO: Diretório criado para {cliente_id}: {caminho_destino}\n")
                        registra_log(cliente_id, ip_cliente, caminho_relativo, 0, tipo_arquivo, 'sucesso') # Log de sucesso
                    else:
                        tamanho_arquivo = int(tamanho_ou_marcador_dir)
                        diretorio_pai = os.path.dirname(caminho_destino)
                        os.makedirs(diretorio_pai, exist_ok=True) # Garante que o diretório pai exista

                        conn.sendall("PRONTO_PARA_RECEBER_ARQUIVO".encode('utf-8')) # Pronto para receber o arquivo

                        bytes_recebidos = 0
                        try:
                            with open(caminho_destino, 'wb') as f: # Abre o arquivo para escrita binária
                                while bytes_recebidos < tamanho_arquivo:
                                    bytes_para_ler = min(tamanho_arquivo - bytes_recebidos, TAMANHO)
                                    dados_recebidos = conn.recv(bytes_para_ler) # Recebe pedaços do arquivo
                                    if not dados_recebidos:
                                        print(f"ERRO: Conexão perdida durante o recebimento de arquivo para {cliente_id}.\n")
                                        registra_log(cliente_id, ip_cliente, caminho_relativo, tamanho_arquivo, tipo_arquivo, 'falha') # Log de falha
                                        break
                                    f.write(dados_recebidos) # Escreve no arquivo
                                    bytes_recebidos += len(dados_recebidos) # Atualiza bytes recebidos
                            print(f"INFO: Arquivo recebido de {cliente_id}: {caminho_destino} ({bytes_recebidos} bytes)\n")
                            conn.sendall("ARQUIVO_RECEBIDO_OK".encode('utf-8')) # Confirma recebimento
                            registra_log(cliente_id, ip_cliente, caminho_relativo, tamanho_arquivo, tipo_arquivo, 'sucesso') # Log de sucesso
                        except Exception as erro_upload:
                            print(f"ERRO: Erro ao receber arquivo '{caminho_relativo}' de {cliente_id}: {erro_upload}\n")
                            conn.sendall("ERRO:FALHA_RECEBER_ARQUIVO".encode('utf-8')) # Erro de recebimento
                            registra_log(cliente_id, ip_cliente, caminho_relativo, tamanho_arquivo, tipo_arquivo, 'falha') # Log de falha


                elif comando.startswith("DEFINIR_PRIVACIDADE:"):
                    with self.trava_clientes[cliente_id]: # Usa trava para acesso seguro
                        config_privacidade = comando.split(":")[1].lower()
                        if config_privacidade in ['publica', 'privada']:
                            self.dados_clientes[cliente_id]['publico'] = (config_privacidade == 'publica') # Atualiza privacidade
                            self.salvar_dados_clientes() # Salva dados
                            conn.sendall(f"PRIVACIDADE_DEFINIDA_PARA_{config_privacidade.upper()}".encode('utf-8')) # Confirma
                            print(f"INFO: Privacidade de {cliente_id} definida para: {config_privacidade}\n")
                        else:
                            conn.sendall("ERRO:CONFIGURACAO_PRIVACIDADE_INVALIDA".encode('utf-8')) # Erro de privacidade
                            print(f"AVISO: Comando DEFINIR_PRIVACIDADE inválido de {cliente_id}: {config_privacidade}\n")

                elif comando == "LISTAR_PASTAS_PUBLICAS":
                    info_pastas_publicas = []
                    for id_cliente, dados_cliente in self.dados_clientes.items(): # Itera sobre os dados dos clientes
                        if dados_cliente['publico']: # Se a pasta for pública
                            info_pastas_publicas.append(f"{id_cliente}") # Adiciona ID à lista
                    enviar_json(conn, info_pastas_publicas) # Envia a lista como JSON
                    print(f"INFO: Lista de pastas públicas enviada para {cliente_id}.\n")

                elif comando.startswith("LISTAR_ARQUIVOS:"):
                    id_cliente_alvo = comando.split(":")[1]
                    caminho_para_listar = ""
                    if len(comando.split(":")) > 2:
                        caminho_para_listar = comando.split(":", 2)[2]

                    if id_cliente_alvo == cliente_id: # Listando a própria pasta
                        diretorio_base = caminho_armazenamento_cliente
                    elif id_cliente_alvo in self.dados_clientes and self.dados_clientes[id_cliente_alvo]['publico']: # Listando pasta pública de outro
                        diretorio_base = self.dados_clientes[id_cliente_alvo]['caminho']
                    else:
                        enviar_json(conn, {"ERRO": True, "MENSAGEM_ERRO": "ACESSO_NEGADO_OU_PASTA_NAO_ENCONTRADA"}) # Erro de acesso
                        print(f"AVISO: Cliente {cliente_id} tentou listar pasta privada ou inexistente: {id_cliente_alvo}\n")
                        continue

                    caminho_completo = os.path.join(diretorio_base, caminho_para_listar) # Caminho completo da pasta a listar

                    if not os.path.exists(caminho_completo):
                        enviar_json(conn, {"ERRO": True, "MENSAGEM_ERRO": "CAMINHO_NAO_ENCONTRADO"}) # Erro de caminho
                        continue

                    if not os.path.isdir(caminho_completo):
                        enviar_json(conn, {"ERRO": True, "MENSAGEM_ERRO": "NAO_EH_DIRETORIO"}) # Erro não é diretório
                        continue

                    info_arquivos = []
                    for item in os.listdir(caminho_completo): # Lista o conteúdo do diretório
                        caminho_item = os.path.join(caminho_completo, item)
                        eh_diretorio_item = os.path.isdir(caminho_item) # Verifica se é diretório
                        tamanho_item = os.path.getsize(caminho_item) if not eh_diretorio_item else 0 # Obtém o tamanho
                        info_arquivos.append({'nome': item, 'eh_diretorio': eh_diretorio_item, 'tamanho': tamanho_item}) # Adiciona info

                    enviar_json(conn, info_arquivos) # Envia a lista de arquivos como JSON
                    print(f"INFO: Conteúdo de '{caminho_para_listar}' da pasta {id_cliente_alvo} enviado para {cliente_id}.\n")

                elif comando.startswith("DOWNLOAD:"):
                    partes = comando.split(":", 2)
                    if len(partes) < 3:
                        conn.sendall("ERRO:COMANDO_DOWNLOAD_MAL_FORMADO".encode('utf-8')) # Erro de formato
                        continue
                    id_cliente_alvo = partes[1]
                    caminho_arquivo_relativo = partes[2]

                    tamanho_arquivo = 0 # Padrão para falhas
                    tipo_arquivo = 'arquivo'

                    if id_cliente_alvo == cliente_id: # Baixando da própria pasta
                        diretorio_base = caminho_armazenamento_cliente
                    elif id_cliente_alvo in self.dados_clientes and self.dados_clientes[id_cliente_alvo]['publico']: # Baixando de pasta pública
                        diretorio_base = self.dados_clientes[id_cliente_alvo]['caminho']
                    else:
                        conn.sendall("ERRO:ACESSO_NEGADO_OU_PASTA_NAO_ENCONTRADA".encode('utf-8')) # Erro de acesso
                        print(f"AVISO: Cliente {cliente_id} tentou baixar de pasta privada ou inexistente: {id_cliente_alvo}\n")
                        registra_log(cliente_id, ip_cliente, caminho_arquivo_relativo, tamanho_arquivo, tipo_arquivo, 'falha') # Log de falha
                        continue

                    caminho_arquivo = os.path.join(diretorio_base, caminho_arquivo_relativo) # Caminho completo do arquivo

                    if not os.path.exists(caminho_arquivo):
                        conn.sendall("ERRO:ARQUIVO_NAO_ENCONTRADO".encode('utf-8')) # Erro de arquivo não encontrado
                        print(f"AVISO: Arquivo não encontrado para download: {caminho_arquivo}\n")
                        registra_log(cliente_id, ip_cliente, caminho_arquivo_relativo, tamanho_arquivo, tipo_arquivo, 'falha') # Log de falha
                        continue

                    if os.path.isdir(caminho_arquivo):
                        conn.sendall("ERRO:NAO_PODE_BAIXAR_DIRETORIO".encode('utf-8')) # Não pode baixar diretório
                        print(f"AVISO: Tentativa de baixar diretório em vez de arquivo: {caminho_arquivo}\n")
                        registra_log(cliente_id, ip_cliente, caminho_arquivo_relativo, tamanho_arquivo, 'diretorio', 'falha') # Log de falha como diretório
                        continue

                    tamanho_arquivo = os.path.getsize(caminho_arquivo) # Obtém o tamanho do arquivo
                    conn.sendall(f"INFO_ARQUIVO:{tamanho_arquivo}".encode('utf-8')) # Envia informações do arquivo
                    resposta_cliente = conn.recv(TAMANHO).decode('utf-8') # Espera confirmação do cliente
                    if resposta_cliente == "PRONTO_PARA_RECEBER_ARQUIVO":
                        try:
                            with open(caminho_arquivo, 'rb') as f: # Abre o arquivo para leitura binária
                                while True:
                                    bytes_lidos = f.read(TAMANHO) # Lê pedaços do arquivo
                                    if not bytes_lidos:
                                        break
                                    conn.sendall(bytes_lidos) # Envia pedaços ao cliente
                            print(f"INFO: Arquivo enviado para {cliente_id}: {caminho_arquivo}\n")
                            registra_log(cliente_id, ip_cliente, caminho_arquivo_relativo, tamanho_arquivo, tipo_arquivo, 'sucesso') # Log de sucesso
                        except Exception as erro_download:
                            print(f"ERRO: Erro ao enviar arquivo '{caminho_arquivo_relativo}' para {cliente_id}: {erro_download}\n")
                            registra_log(cliente_id, ip_cliente, caminho_arquivo_relativo, tamanho_arquivo, tipo_arquivo, 'falha') # Log de falha
                    else:
                        print(f"ERRO: Cliente {cliente_id} não estava pronto para receber arquivo: {resposta_cliente}\n")
                        registra_log(cliente_id, ip_cliente, caminho_arquivo_relativo, tamanho_arquivo, tipo_arquivo, 'falha') # Log de falha

                elif comando == "SAIR":
                    break # Cliente solicitou encerramento
                else:
                    conn.sendall("ERRO:COMANDO_DESCONHECIDO".encode('utf-8')) # Comando desconhecido
                    print(f"AVISO: Comando desconhecido de {cliente_id}: {comando}\n")

        except ConnectionResetError:
            print(f"AVISO: Conexão com {ip_cliente}:{_} resetada.\n")
        except Exception as e:
            print(f"ERRO: Ocorreu um erro ao lidar com o cliente {ip_cliente}:{_}: {e}\n")
        finally:
            conn.close() # Fecha a conexão
            print(f"INFO: Conexão com {ip_cliente}:{_} encerrada.\n")

    def iniciar(self):
        """Inicia o servidor e aceita conexões de clientes."""
        print("#### <ENTROU EM iniciar (Servidor)> ####\n")
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s: # Cria um socket TCP/IP
            s.bind((HOST, PORT)) # Liga o socket ao endereço e porta
            s.listen() # Começa a ouvir por conexões
            print(f"INFO: Servidor ouvindo em {HOST}:{PORT}\n")
            while True:
                conn, addr = s.accept() # Aceita uma nova conexão
                # Cria um novo thread para lidar com o cliente
                thread_cliente = threading.Thread(target=self.lidar_com_conexao_cliente, args=(conn, addr))
                thread_cliente.start() # Inicia o thread

if __name__ == "__main__":
    servidor = Servidor() # Cria uma instância do servidor
    servidor.iniciar() # Inicia o servidor
