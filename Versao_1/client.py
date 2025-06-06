import socket
from con_config import obter_dados_conexao

IP, PORT, TAM_BUFFER, TAM_CABECALHO = obter_dados_conexao()


### Funções de Envio e Recebimento de Dados ###
def enviar_dados(sock, dados):
    '''
    Envia os dados com um cabeçalho fixo que informa o tamanho dos dados.
    '''
    try:
        print("<ENTROU EM enviar_dados>")
        cabecalho = f"{len(dados):<{TAM_CABECALHO}}".encode('utf-8')  # Cabeçalho com tamanho fixo
        sock.sendall(cabecalho)
        sock.sendall(dados)
        print(f"<DADOS ENVIADOS: {dados}>")
        return True

    except Exception as e:
        print(f"Erro ao codificar o cabeçalho: {e}")
        return False
    

def receber_mensagem(sock):
    print("<ENTROU EM receber_mensagem>")

    try:
        # Recebe o cabeçalho de tamanho fixo
        cabecalho = sock.recv(TAM_CABECALHO).strip()
        if not cabecalho:
            print("Conexão fechada pelo servidor.")
            return None

        # Converte o cabeçalho para um número inteiro
        tamanho_dados = int(cabecalho.decode('utf-8'))
        print(f"Tamanho dos dados recebidos: {tamanho_dados}")

        return tamanho_dados

    except Exception as e:
        print(f"Erro ao receber dados: {e}")
        return None

def receber_dados(sock, tamanho_dados):
    print("<ENTROU EM receber_dados>")

    recebidos = []
    bytes_restantes = tamanho_dados

    while bytes_restantes > 0:
        try:
            dados = sock.recv(min(bytes_restantes, TAM_BUFFER))
            if not dados:
                print("Conexão fechada pelo servidor.")
                return None
            
            recebidos.append(dados)
            bytes_restantes -= len(dados)

        except Exception as e:
            print(f"Erro ao receber dados: {e}")
            return None
    return b''.join(recebidos)


def iniciar_cliente():
    ip_servidor = input("Digite o IP do servidor: ")
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        try:
            sock.connect((ip_servidor, PORT))
            print(f"Conectado ao servidor {ip_servidor}:{PORT}")
            
            # Exemplo de envio de dados
            mensagem = b"Hello, Server!"
            enviar_dados(sock, mensagem)
            
            # Exemplo de recebimento de resposta
            tamanho_resposta = receber_mensagem(sock)
            if tamanho_resposta:
                resposta = receber_dados(sock, tamanho_resposta)
                print(f"Resposta do servidor: {resposta.decode('utf-8')}")
        
        except Exception as e:
            print(f"Erro ao conectar ao servidor: {e}")

if __name__ == "__main__":
    iniciar_cliente()