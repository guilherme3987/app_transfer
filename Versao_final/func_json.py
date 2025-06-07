# func_json.py
import os
import json

TAMANHO = 1024

# Recebe tamanho, confirma e recebe dados em pedaços
def receber_dados_json(sock):
    print("#### <ENTROU EM receber_dados_json> ####\n")

    cabecalho = sock.recv(TAMANHO).decode('utf-8')

    padrao_json = "JSON_TAMANHO:"

    if not cabecalho.startswith(padrao_json):
        print("ERRO: Cabeçalho inválido recebido:", cabecalho)
        sock.sendall("ERRO_CABECALHO_JSON".encode('utf-8'))
        return None

    try:
        tamanho_json = int(cabecalho.replace(padrao_json, "").strip())
        print("INFO: Tamanho do JSON a ser recebido:", tamanho_json)

        # CORREÇÃO: Encodar a string para bytes
        sock.sendall("OK_PARA_JSON".encode('utf-8')) #

        dados_recebidos = 0
        json_buffer = b""

        while dados_recebidos < tamanho_json:
            bytes_para_receber = min(tamanho_json - dados_recebidos, TAMANHO)
            pacote = sock.recv(bytes_para_receber)

            if not pacote:
                print("ERRO: Conexão perdida ou pacote vazio durante o recebimento do JSON.")
                return None

            json_buffer += pacote
            dados_recebidos += len(pacote)

        try:
            dados_json = json.loads(json_buffer.decode('utf-8'))
            print("INFO: Dados JSON recebidos e decodificados com sucesso.")
            return dados_json
        except json.JSONDecodeError as e:
            print(f"ERRO: Erro ao decodificar JSON recebido: {e}")
            return None

    except ValueError:
        print(f"ERRO: Tamanho do JSON inválido no cabeçalho: {cabecalho}")
        return None
    except Exception as e:
        print(f"ERRO: Erro inesperado ao receber dados JSON: {e}")
        return None

def enviar_json(sock, dados):
    print("#### <ENTROU EM enviar_json> ####\n")

    json_string = json.dumps(dados).encode('utf-8')

    tamanho = len(json_string)

    sock.sendall(f"JSON_TAMANHO:{tamanho}".encode('utf-8'))

    resposta = sock.recv(TAMANHO).decode('utf-8')

    if resposta == "OK_PARA_JSON":
        sock.sendall(json_string)
        print("INFO: JSON enviado com sucesso.")
        return True
    else:
        print(f"ERRO: Cliente não estava pronto para receber JSON. Resposta: {resposta}")
        return False

def get_relative_path(full_path, base_path):
    print("#### <ENTROU EM get_relative_path> ####\n")

    return os.path.relpath(full_path, base_path)