import hashlib

def calcular_checksum_dados(dados): #MD5 é uma forma de checksum
    hasher = hashlib.sha256()
    hasher.update(dados)
    return hasher.hexdigest()
