# Sistema de Armazenamento e Compartilhamento de Arquivos

Este projeto implementa um sistema distribuído básico para armazenamento e compartilhamento de arquivos, utilizando comunicação via sockets TCP/IP em Python. Os clientes podem criar e gerenciar suas próprias pastas no servidor, definindo privacidade (pública ou privada) e realizando upload de arquivos e diretórios. O servidor gerencia o armazenamento, a privacidade e registra todas as operações em um arquivo de log.

## Funcionalidades

* **Criação e Reutilização de Pastas de Cliente:** Os clientes podem criar uma nova pasta no servidor (associada ao seu IP) ou reutilizar uma pasta existente.
* **Definição de Privacidade da Pasta:** As pastas podem ser configuradas como 'públicas' (visíveis para todos os clientes) ou 'privadas' (visíveis apenas para o proprietário).
* **Upload de Arquivos e Diretórios:** Clientes podem enviar arquivos individuais ou diretórios completos (com subdiretórios e arquivos) para suas pastas no servidor.
* **Listagem de Pastas Públicas:** Clientes podem visualizar uma lista de todas as pastas públicas disponíveis no servidor.
* **Listagem de Conteúdo da Pasta:** Clientes podem listar o conteúdo de sua própria pasta ou de qualquer pasta pública, incluindo arquivos e subdiretórios, com seus respectivos tamanhos.
* **Registro de Logs:** Todas as operações de upload e criação de diretórios são registradas em um arquivo CSV (`log.csv`) no servidor, incluindo timestamp, ID do cliente, IP do cliente, nome do arquivo/diretório, tamanho, tipo, status (sucesso/falha), tempo de transferência e taxa de transferência.
* **Concorrência:** O servidor é multi-threaded, permitindo que múltiplos clientes se conectem e interajam simultaneamente.

## Estrutura do Projeto

O projeto é dividido em vários arquivos Python para melhor organização e modularidade:

* `server_app.py`: O script principal do servidor que gerencia as conexões dos clientes, as operações de arquivo e a lógica de negócios.
* `client_app.py`: O script principal do cliente que permite aos usuários interagir com o servidor para upload, definição de privacidade e listagem de arquivos.
* `configuracoes.py`: Define configurações de conexão, como HOST e PORTA.
* `caminho_dados.py`: Define os diretórios de armazenamento e nomes de arquivos para dados do cliente.
* `func_json.py`: Contém funções utilitárias para envio e recebimento de dados JSON via socket, e para obter o caminho relativo de arquivos.
* `func_log.py`: Contém funções para inicializar e registrar eventos no arquivo de log do servidor.
* `comandos_servidor.py`: Implementa as funções que lidam com os diferentes comandos enviados pelos clientes (upload, privacidade, listagem).

## Como Executar

### Pré-requisitos

* Python 3.x instalado.

### Configuração

Não há configurações adicionais necessárias além das definidas nos arquivos `configuracoes.py` e `caminho_dados.py`, que já vêm com valores padrão.

### Executando o Servidor

1.  Abra um terminal.
2.  Navegue até o diretório raiz do projeto.
3.  Execute o script do servidor:
    ```bash
    python server_app.py
    ```
    O servidor começará a ouvir em `0.0.0.0:5001` (ou na porta configurada).

### Executando o Cliente

1.  Abra outro terminal.
2.  Navegue até o diretório raiz do projeto.
3.  Execute o script do cliente:
    ```bash
    python client_app.py
    ```
    O cliente solicitará o IP do servidor e guiará você pelas opções disponíveis.

## Uso

### No Servidor

Ao iniciar o `server_app.py`, você verá mensagens de log no console indicando o status do servidor, como a criação do diretório de clientes (se não existir) e o carregamento de dados.

### No Cliente

1.  **Conexão:** Ao executar `client_app.py`, você será solicitado a digitar o IP do servidor. Se estiver executando localmente, use `127.0.0.1` ou o IP da sua máquina na rede local.
2.  **Criação/Reutilização de Pasta:**
    * `N` para criar uma nova pasta: O servidor gerará um ID de pasta exclusivo para você.
    * `E` para usar uma pasta existente: Você precisará fornecer o ID de uma pasta que você já possui.
3.  **Privacidade:** Defina a privacidade da sua pasta como `publica` ou `privada`.
4.  **Menu de Opções:** Após a configuração inicial, um menu será exibido:
    * **1. Enviar arquivo ou diretório:** Forneça o caminho local completo do arquivo ou diretório que deseja enviar.
    * **2. Definir privacidade da pasta:** Altera a privacidade da sua pasta.
    * **3. Visualizar pastas públicas:** Lista os IDs de todas as pastas que foram definidas como públicas por outros clientes.
    * **4. Visualizar conteúdo de uma pasta:** Permite ver os arquivos e subdiretórios dentro de uma pasta específica (sua ou pública). Você precisará do ID da pasta e, opcionalmente, um caminho relativo dentro dela.
    * **5. Sair:** Encerra a conexão do cliente com o servidor.

## Explicações de Trechos de Código

### `server_app.py`

* **`class Servidor:`**
    A classe `Servidor` encapsula toda a lógica do servidor. O construtor `__init__` carrega os dados dos clientes existentes, inicializa travas para controle de concorrência e garante que o diretório de armazenamento de clientes e o arquivo de log existam. O uso de `self.trava_clientes = {}` é fundamental para garantir que as operações em `self.dados_clientes` sejam thread-safe, evitando problemas de concorrência.
* **`self.carregar_dados_clientes()` e `self.salvar_dados_clientes()`:**
    Essas funções são responsáveis por persistir o estado dos clientes (ID da pasta, IP, caminho e privacidade) em um arquivo JSON (`dados_clientes.json`). Isso permite que o servidor lembre dos clientes e de suas configurações mesmo após ser reiniciado. A lógica para atualizar `self.cont_ip` durante o carregamento garante que novos IDs de cliente sejam gerados corretamente.
* **`self.lidar_com_conexao_cliente(self, conn, addr)`:**
    Esta função é executada em uma thread separada para cada cliente conectado. Ela lida com a fase inicial de criação ou reutilização de pasta do cliente e, em seguida, entra em um loop para processar os comandos enviados pelo cliente (UPLOAD, DEFINIR\_PRIVACIDADE, LISTAR\_PASTAS\_PUBLICAS, LISTAR\_ARQUIVOS, SAIR). O uso de `conn.recv(self.tamanho_buffer).decode('utf-8')` recebe os comandos do cliente.
* **`threading.Thread(target=self.lidar_com_conexao_cliente, args=(conn, addr))`:**
    No método `iniciar` da classe `Servidor`, cada nova conexão de cliente (`s.accept()`) é delegada a uma nova thread. Isso permite que o servidor atenda a múltiplos clientes simultaneamente, sem que uma conexão bloqueie as outras.

### `client_app.py`

* **`enviar_arquivo_diretorio(sock, caminho_origem, caminho_base_remoto)`:**
    Esta função é responsável por enviar arquivos e diretórios.
    * Se `os.path.isfile(caminho_origem)`, ele prepara um comando `UPLOAD` com o tamanho do arquivo e o caminho relativo, envia para o servidor e aguarda a confirmação (`PRONTO_PARA_RECEBER_ARQUIVO`). Em seguida, lê o arquivo em blocos (`f.read(bytes_para_enviar)`) e os envia ao servidor.
    * Se `os.path.isdir(caminho_origem)`, ele usa `os.walk(caminho_origem)` para percorrer recursivamente o diretório. Para cada subdiretório e arquivo encontrado, ele envia comandos específicos ao servidor para criar o diretório ou fazer o upload do arquivo, mantendo a estrutura de pastas.
* **`main()`:**
    A função `main` do cliente estabelece a conexão com o servidor (`s.connect((ip_servidor, porta_servidor))`), gerencia a interação inicial para criar ou reutilizar uma pasta, define a privacidade e, em seguida, entra em um loop que apresenta um menu de opções ao usuário, chamando as funções apropriadas com base na escolha.

### `func_json.py`

* **`receber_dados_json(sock)` e `enviar_json(sock, dados)`:**
    Essas funções implementam um pequeno protocolo para garantir a transmissão correta de dados JSON. Antes de enviar o JSON real, o remetente envia um cabeçalho indicando o tamanho do JSON (`JSON_TAMANHO:tamanho`). O receptor confirma que está pronto (`OK_PARA_JSON`) antes de receber os dados em blocos. Isso evita que o receptor tente decodificar um JSON incompleto. O `json.loads()` e `json.dumps()` são usados para serializar e desserializar os dados Python para/de formato JSON.
* **`TAMANHO_BUFFER = 4096`:**
    Define o tamanho dos "pedaços" de dados (em bytes) que são lidos ou enviados em cada operação de socket. Um buffer de 4096 bytes é um tamanho comum e equilibrado para muitas operações de rede.

### `func_log.py`

* **`inicializar_log()`:**
    Verifica se o arquivo de log (`log.csv`) já existe. Se não existir, ele cria o arquivo e escreve o cabeçalho das colunas (`CABECALHO_LOG`), garantindo que o arquivo esteja pronto para receber os registros.
* **`registrar_log(...)`:**
    Esta função é chamada pelo servidor para registrar cada evento de upload ou criação de diretório. Ela captura o `timestamp` atual, calcula o tamanho do arquivo em MB e a taxa de transferência em MB/s, e escreve esses dados como uma nova linha no arquivo CSV. O modo `'a'` (append) garante que novos registros sejam adicionados ao final do arquivo sem sobrescrever o conteúdo existente.

### `comandos_servidor.py`

* **`lidar_envio_arquivo_diretorio(...)`:**
    Esta função no servidor recebe os comandos de UPLOAD do cliente. Ela verifica se o comando é para um arquivo ou diretório.
    * Para um diretório, ela usa `os.makedirs(caminho_destino, exist_ok=True)` para criar a estrutura de pastas no servidor.
    * Para um arquivo, ela envia `PRONTO_PARA_RECEBER_ARQUIVO`, recebe os dados em blocos (`conn.recv(bytes_para_ler)`) e os escreve no arquivo (`arquivo_destino.write(dados)`). Inclui medições de `tempo_inicio` e `tempo_fim` para calcular a duração e a taxa de transferência, que são então passadas para `registrar_log`.
* **`lidar_listar_arquivos(...)`:**
    Processa o comando `LISTAR_ARQUIVOS`. Verifica se o cliente solicitou sua própria pasta ou uma pasta pública. Usa `os.path.join` para construir o caminho completo e `os.listdir` para obter o conteúdo do diretório. Em seguida, coleta informações como nome, tamanho e se é um diretório (`os.path.isdir`) para cada item e envia esses dados formatados em JSON de volta para o cliente.

## Como o JSON é Usado na Aplicação

O JSON (JavaScript Object Notation) é amplamente utilizado nesta aplicação como o formato padrão para troca de dados estruturados entre o cliente e o servidor. Ele permite que informações complexas, como configurações de upload ou listas de arquivos, sejam transmitidas de forma legível e facilmente interpretável por ambos os lados.

### Serialização (Python Dict/List para JSON String)

A serialização é o processo de converter um objeto Python (como um dicionário ou uma lista) em uma string JSON, que pode então ser enviada através da rede. No Python, isso é feito usando `json.dumps()`.

**Exemplo de Serialização no Cliente (`client_app.py`) para um Upload de Arquivo:**

Quando o cliente envia um comando de UPLOAD de um arquivo, ele cria um dicionário Python contendo os metadados do arquivo e o converte para JSON:

```python
# No client_app.py, dentro de enviar_arquivo_diretorio, para upload de arquivo
comando = json.dumps({ #dumps converte o dicionário em uma string JSON: SERIALIZAÇÃO
    "acao": "UPLOAD",
    "diretorio": False,
    "caminho_relativo": caminho_relativo_no_servidor,
    "tamanho_arquivo": tamanho_arquivo
})
sock.sendall(comando.encode('utf-8')) # Envia a string JSON como bytes