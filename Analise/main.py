import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns 
df = pd.read_csv('C:/Users/guilh/OneDrive/Área de Trabalho/Python/LPIII/app_transfer/app_transfer/Analise/log_transferencias.csv')

print("====================================== Estatísticas por Categoria ======================================")

# Extrair categoria do arquivo (primeira parte do caminho)
def extrair_categoria(nome_arquivo):
    extensoes = {
        '.txt': 'txt',
        '.mp4': 'video',
        '.avi': 'video',
        '.pdf': 'pdf',
        '.jpg': 'imagem',
        '.png': 'imagem',
        '.jpeg': 'imagem',
        '.webp': 'imagem'
    }
    for ext, categoria in extensoes.items():
        if nome_arquivo.endswith(ext):
            return categoria
    return 'Outros'

df['categoria'] = df['nome_arquivo'].apply(extrair_categoria)

# Converter tamanho para MB para melhor legibilidade
df['tamanho_mb'] = df['tamanho_bytes'] / (1024 * 1024)

df['taxa_transferencia_mb_por_segundo'] = df['taxa_transferencia_bytes_por_segundo'] / 1e6

# Análise estatística básica
print("Estatísticas Gerais:")
print(f"Total de arquivos transferidos: {len(df)}")
print(f"Tamanho médio dos arquivos: {df['tamanho_mb'].mean():.2f} MB")
print(f"Taxa de transferência média: {df['taxa_transferencia_bytes_por_segundo'].mean()/1e6:.2f} MB/s")
print(f"Duração média de transferência: {df['duracao_segundos'].mean():.2f} segundos\n")

# Análise por categoria
categoria_stats = df.groupby('categoria').agg({
    'tamanho_mb': ['count', 'mean', 'median', 'min', 'max', 'sum'],
    'duracao_segundos': ['mean', 'median', 'max'],
    'taxa_transferencia_bytes_por_segundo': ['mean', 'median']
})

# Renomear colunas para melhor legibilidade
categoria_stats.columns = [
    'num_arquivos', 'tamanho_medio_mb', 'tamanho_mediano_mb', 
    'tamanho_min_mb', 'tamanho_max_mb', 'tamanho_total_mb',
    'tempo_medio_seg', 'tempo_mediano_seg', 'tempo_max_seg',
    'taxa_media_bytes_por_seg', 'taxa_mediana_bytes_por_seg'
]

print("Estatísticas por Categoria:")
print(categoria_stats)


print("\n====================================== Gráficos ======================================")

# 1. Gráfico de histograma para visualizar a distribuição do tamanho das transferências
plt.figure(figsize=(10, 6))
sns.histplot(df['tamanho_mb'], bins=30, kde=True, color='blue')
plt.title('Distribuição do Tamanho das Transferências')
plt.xlabel('Tamanho (MB)')
plt.ylabel('Frequência')
plt.grid(axis='y', alpha=0.75)
plt.tight_layout()
plt.show()

# 2. Gráfico de histograma para visualizar a distribuição da taxa de transferência
plt.figure(figsize=(10, 6))
sns.histplot(df['taxa_transferencia_mb_por_segundo'], bins=30, kde=True, color='red')
plt.title('Distribuição da Taxa de Transferência')
plt.xlabel('Taxa de Transferência (MB/segundo)')
plt.ylabel('Frequência')
plt.grid(axis='y', alpha=0.75)
plt.tight_layout()
plt.show()

# 3. Gráfico de dispersão para analisar a relação entre o tamanho e a duração das transferências
plt.figure(figsize=(10, 6))
sns.scatterplot(x='tamanho_mb', y='duracao_segundos', data=df, alpha=0.6, hue='categoria', palette='viridis')
plt.title('Tamanho vs Duração das Transferências por Categoria')
plt.xlabel('Tamanho (MB)')
plt.ylabel('Duração (segundos)')
plt.grid(True)
plt.tight_layout()
plt.show()

# 4. Gráfico de Barras: Taxa Média de Transferência por Categoria
plt.figure(figsize=(12, 7))
sns.barplot(x=categoria_stats.index, y='taxa_media_bytes_por_seg', data=categoria_stats, palette='coolwarm')
plt.title('Taxa Média de Transferência por Categoria de Arquivo')
plt.xlabel('Categoria de Arquivo')
plt.ylabel('Taxa Média de Transferência (MB/segundo)')
plt.xticks(rotation=45, ha='right')  # Rotaciona os rótulos para melhor visualização
plt.grid(axis='y', alpha=0.75)
plt.tight_layout()
plt.show()

# 5. Gráfico de Barras: Tempo Médio de Transferência por Categoria
plt.figure(figsize=(12, 7))
sns.barplot(x=categoria_stats.index, y='tempo_medio_seg', data=categoria_stats, palette='mako')
plt.title('Tempo Médio de Transferência por Categoria de Arquivo')
plt.xlabel('Categoria de Arquivo')
plt.ylabel('Tempo Médio (segundos)')
plt.xticks(rotation=45, ha='right')
plt.grid(axis='y', alpha=0.75)
plt.tight_layout()
plt.show()

# 6. Gráfico de Dispersão: Tempo de Transferência por Arquivo
plt.figure(figsize=(12, 7))
sns.scatterplot(x=df.index, y='duracao_segundos', data=df, hue='categoria', palette='tab10', alpha=0.7)
plt.title('Tempo de Transferência por Arquivo')
plt.xlabel('Índice do Arquivo')
plt.ylabel('Tempo de Transferência (segundos)')
plt.grid(True)
plt.tight_layout()
plt.show()

# 7. Gráfico de Barras: Tempo de Transferência por Arquivo
plt.figure(figsize=(12, 7))
sns.barplot(x=df.index, y='duracao_segundos', hue='categoria', data=df, palette='tab20', dodge=False)
plt.title('Tempo de Transferência por Arquivo')
plt.xlabel('Índice do Arquivo')
plt.ylabel('Tempo de Transferência (segundos)')
plt.xticks(rotation=90)
plt.grid(axis='y', alpha=0.75)
plt.tight_layout()
plt.show()

