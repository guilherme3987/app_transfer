import socket
import os
import uuid  
import hashlib
from datetime import datetime
import threading
from con_config import obter_dados_conexao 

IP, PORT, TAM_BUFFER, TAM_CABECALHO = obter_dados_conexao()


def calcular_checksum_dados(dados): #MD5 é uma forma de checksum
    hasher = hashlib.sha256()
    hasher.update(dados)
    return hasher.hexdigest()

def receber_arquivo(sock, nome_arquivo, tamanho, checksum_esperado, diretorio_destino):
        print("<ENTROU EM RECEBER_ARQUIVO>")
        print(f"Recebendo arquivo: {nome_arquivo}, Tamanho: {tamanho}, Checksum esperado: {checksum_esperado}")

        
        caminho_completo = os.path.join(diretorio_destino, nome_arquivo)
        os.makedirs(os.path.dirname(caminho_completo), exist_ok=True)
        
        enviar_dados(sock, b"OK")  # OK em bytes para indicar que o servidor está pronto para receber o arquivo
        
        chunks = []
        bytes_recebidos = 0
        
        while bytes_recebidos < tamanho:
            chunk = sock.recv(min(TAM_BUFFER, tamanho - bytes_recebidos))
            if not chunk:
               print("Conexão encerrada prematuramente")
            
            chunks.append(chunk)
            bytes_recebidos += len(chunk)
            print(f"Recebidos {bytes_recebidos}/{tamanho} bytes ({bytes_recebidos/tamanho:.1%})", end='\r')
        
        dados_recebidos = b''.join(chunks)
        checksum_recebido = calcular_checksum_dados(dados_recebidos)
        
        if checksum_recebido != checksum_esperado:
            erro_msg = f"ERRO: Checksum não corresponde (esperado: {checksum_esperado}, recebido: {checksum_recebido})"
            enviar_dados(sock, erro_msg.encode('utf-8'))
            print(f"\n{erro_msg}")
            return False
        
        with open(caminho_completo, 'wb') as f:
            f.write(dados_recebidos)
            
        enviar_dados(sock, b"Arquivo recebido com sucesso")
        print(f"\nArquivo {nome_arquivo} salvo em {caminho_completo}")
        return True

def enviar_dados(sock, dados):
    """Função básica para enviar dados"""
    try:
        sock.sendall(dados)
    except Exception as e:
        print(f"Erro ao enviar dados: {e}")