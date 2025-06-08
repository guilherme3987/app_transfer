import socket
import threading
import json
import os
from datetime import datetime


# Importa as funções de configuração e utilitários
from configuracoes import obter_dados_conexao
from func_json import receber_dados_json, enviar_json, obter_caminho_relativo, TAMANHO_BUFFER
from func_log import obter_config_log, registrar_log, inicializar_log
from caminho_dados import obter_diretorios

# Importa as funções de comandos do servidor
from comandos_servidor import lidar_envio_arquivo_diretorio, lidar_definir_privacidade, lidar_listar_pastas_publicas, lidar_listar_arquivos


# Obtenha configurações usando as funções
HOST, PORTA_SERVIDOR = obter_dados_conexao()
DIRETORIO_CLIENTES_ARMAZENAMENTO, ARQUIVO_DADOS_CLIENTES = obter_diretorios()


# Classe para gerenciar estados do servidor e clientes
class Servidor:
    def __init__(self):
        print("#### <ENTROU EM Servidor.__init__> ####\n")
        self.dados_clientes = {}
        self.trava_clientes = {} # Trava para acesso concorrente aos dados dos clientes
        self.cont_ip = {}
        self.tamanho_buffer = TAMANHO_BUFFER # Atributo da instância
        self.carregar_dados_clientes()

        if not os.path.exists(DIRETORIO_CLIENTES_ARMAZENAMENTO):
            os.makedirs(DIRETORIO_CLIENTES_ARMAZENAMENTO)
            print(f"INFO: Diretório '{DIRETORIO_CLIENTES_ARMAZENAMENTO}' criado com sucesso.\n")
        else:
            print(f"INFO: Diretório '{DIRETORIO_CLIENTES_ARMAZENAMENTO}' já existe.\n")
        
        inicializar_log()

    def carregar_dados_clientes(self):
        print("#### <ENTROU EM carregar_dados_clientes (Servidor)> ####\n")
        
        if os.path.exists(ARQUIVO_DADOS_CLIENTES):
            try:
                with open(ARQUIVO_DADOS_CLIENTES, 'r', encoding='utf-8') as f:
                    self.dados_clientes = json.load(f)
                print(f"INFO: DADOS_CLIENTES carregados: {self.dados_clientes}\n")

                self.cont_ip = {}
                for id_cliente_completo_carregado in self.dados_clientes:
                    partes = id_cliente_completo_carregado.split('_')
                    if len(partes) > 1:
                        ip_formatado_partes = partes[:-1]
                        if ip_formatado_partes and ip_formatado_partes[-1] == '':
                            ip_formatado_partes.pop()
                        ip_formatado = '_'.join(ip_formatado_partes)

                        try:
                            contador_atual = int(partes[-1])
                            if ip_formatado in self.cont_ip:
                                self.cont_ip[ip_formatado] = max(self.cont_ip[ip_formatado], contador_atual + 1)
                            else:
                                self.cont_ip[ip_formatado] = contador_atual + 1
                        except ValueError:
                            print(f"AVISO: ID de cliente '{id_cliente_completo_carregado}' com formato de contador inválido. Ignorando na contagem de IP.\n")
                            continue#IA: continue serve para pular o loop e continuar com o próximo cliente

            except json.JSONDecodeError as e:
                print(f"ERRO: Erro ao decodificar metadados dos clientes de '{ARQUIVO_DADOS_CLIENTES}': {e}. Iniciando com dados vazios.\n")
                self.dados_clientes = {}
                self.cont_ip = {}
        else:
            print("INFO: Nenhum arquivo de metadados de cliente encontrado. Iniciando vazio.\n")
            self.cont_ip = {}

        for id_cliente_carregado in self.dados_clientes:
            if id_cliente_carregado not in self.trava_clientes:
                self.trava_clientes[id_cliente_carregado] = threading.Lock()

    def salvar_dados_clientes(self):
        print("#### <ENTROU EM salvar_dados_clientes (Servidor)> ####\n")
        try:
            with open(ARQUIVO_DADOS_CLIENTES, 'w', encoding='utf-8') as f:
                json.dump(self.dados_clientes, f, indent=4, ensure_ascii=False)
            print(f"INFO: Dados dos clientes salvos.\n")
        except Exception as e:
            print(f"ERRO: Erro ao salvar dados dos clientes: {e}\n")

    def criar_diretorio_cliente(self, ip_cliente):
        print("#### <ENTROU EM criar_diretorio_cliente (Servidor)> ####\n")
        
        ip_cliente_formatado = ip_cliente.replace('.', '_')
        proximo_contador = self.cont_ip.get(ip_cliente_formatado, 1)
        print(f"INFO: Próximo contador para {ip_cliente_formatado}: {proximo_contador}\n")

        nome_pasta_cliente = f"{ip_cliente_formatado}_{proximo_contador}"
        caminho_pasta_cliente = os.path.join(DIRETORIO_CLIENTES_ARMAZENAMENTO, nome_pasta_cliente)
        
        os.makedirs(caminho_pasta_cliente)
        print(f"INFO: Pasta do cliente criada: {caminho_pasta_cliente}\n")
        
        id_cliente_novo = nome_pasta_cliente
        self.dados_clientes[id_cliente_novo] = {'publico': False, 'ip': ip_cliente, 'caminho': caminho_pasta_cliente}
        self.trava_clientes[id_cliente_novo] = threading.Lock()
        
        self.cont_ip[ip_cliente_formatado] = proximo_contador + 1
        
        self.salvar_dados_clientes()
        print(f"INFO: Dados do cliente {id_cliente_novo} salvos com sucesso.\n")
        
        return id_cliente_novo, caminho_pasta_cliente


    def lidar_com_conexao_cliente(self, conn, addr):
        print("#### <ENTROU EM lidar_com_conexao_cliente (Servidor)> ####\n")
        ip_cliente, _ = addr
        print(f"INFO: Conexão aceita de {ip_cliente}:{_}\n")

        id_cliente_atual = None
        caminho_armazenamento_cliente = None
        try:
            mensagem_inicial = conn.recv(self.tamanho_buffer).decode('utf-8')
            
            if mensagem_inicial == "CRIAR_NOVA_PASTA":
                id_cliente_atual, caminho_armazenamento_cliente = self.criar_diretorio_cliente(ip_cliente)
                conn.sendall(f"PASTA_CRIADA:{id_cliente_atual}".encode('utf-8'))
                print(f"INFO: Novo cliente {id_cliente_atual} conectado e pasta criada.\n")

            elif mensagem_inicial.startswith("USAR_PASTA_EXISTENTE:"):
                partes = mensagem_inicial.split(":") 
                if len(partes) == 2:
                    id_cliente_recebido = partes[1]
                    #Testar se o ID do cliente recebido é válido e pertence ao IP do cliente
                    if id_cliente_recebido in self.dados_clientes and self.dados_clientes[id_cliente_recebido]['ip'] == ip_cliente:
                        id_cliente_atual = id_cliente_recebido
                        caminho_armazenamento_cliente = self.dados_clientes[id_cliente_atual]['caminho']
                        conn.sendall(f"PASTA_REUTILIZADA:{id_cliente_atual}".encode('utf-8'))
                        print(f"INFO: Cliente {ip_cliente} reconectado e usando pasta existente: {id_cliente_atual}\n")
                    
                    else:
                        conn.sendall("ERRO:ID_PASTA_INVALIDA_OU_ACESSO_NEGADO".encode('utf-8'))
                        print(f"ERRO: Cliente {ip_cliente} tentou usar ID de pasta inválido ou não pertencente: {id_cliente_recebido}\n")
                        return
                else:
                    conn.sendall("ERRO:SOLICITACAO_MAL_FORMADA".encode('utf-8'))
                    print(f"ERRO: Cliente {ip_cliente} enviou solicitação malformada: {mensagem_inicial}\n")
                    return
            else:
                conn.sendall("ERRO:SOLICITACAO_INICIAL_DESCONHECIDA".encode('utf-8'))
                print(f"ERRO: Cliente {ip_cliente} enviou solicitação inicial desconhecida: {mensagem_inicial}\n")
                return

            if not id_cliente_atual or not caminho_armazenamento_cliente:
                print(f"ERRO: Falha ao determinar id_cliente_atual ou caminho_armazenamento_cliente para {ip_cliente}.\n")
                return

            while True:
                comando = conn.recv(self.tamanho_buffer).decode('utf-8')
                if not comando:
                    break

                print(f"INFO: Comando recebido de {id_cliente_atual}: {comando}\n")

                if comando.startswith("UPLOAD:"):
                    lidar_envio_arquivo_diretorio(self, conn, id_cliente_atual, ip_cliente, caminho_armazenamento_cliente, comando)
                elif comando.startswith("DEFINIR_PRIVACIDADE:"):
                    lidar_definir_privacidade(self, conn, id_cliente_atual, comando)
                elif comando == "LISTAR_PASTAS_PUBLICAS":
                    lidar_listar_pastas_publicas(self, conn, id_cliente_atual)
                elif comando.startswith("LISTAR_ARQUIVOS:"):
                    lidar_listar_arquivos(self, conn, id_cliente_atual, caminho_armazenamento_cliente, comando)
                elif comando == "SAIR":
                    break
                else:
                    conn.sendall("ERRO:COMANDO_DESCONHECIDO".encode('utf-8'))
                    print(f"AVISO: Comando desconhecido de {id_cliente_atual}: {comando}\n")

        except ConnectionResetError:
            print(f"AVISO: Conexão com {ip_cliente}:{_} resetada.\n")
        except Exception as e:
            print(f"ERRO: Ocorreu um erro ao lidar com o cliente {ip_cliente}:{_}: {e}\n")
        finally:
            conn.close()
            print(f"INFO: Conexão com {ip_cliente}:{_} encerrada.\n")

    def iniciar(self):
        print("#### <ENTROU EM iniciar (Servidor)> ####\n")
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((HOST, PORTA_SERVIDOR))
            s.listen()
            print(f"INFO: Servidor ouvindo em {HOST}:{PORTA_SERVIDOR}\n")
            while True:
                conn, addr = s.accept()
                thread_cliente = threading.Thread(target=self.lidar_com_conexao_cliente, args=(conn, addr))
                thread_cliente.start()

if __name__ == "__main__":
    servidor = Servidor()
    servidor.iniciar()
