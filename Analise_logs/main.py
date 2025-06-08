import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

df_registro = pd.read_csv('Analise_logs/log.csv') 
print(df_registro.head())


df_registro['TIMESTAMP'] = pd.to_datetime(df_registro['TIMESTAMP']) # TIMESTAMP' para datas e horas
df_registro['DIA_DA_SEMANA'] = df_registro['TIMESTAMP'].dt.day_name() # Nnome do dia da semana de cada data

#IA: COERCE SERVE PARA converter valores inválidos em NaN
df_registro['TAMANHO_ARQUIVO_BYTES'] = pd.to_numeric(df_registro['TAMANHO_ARQUIVO_BYTES'], errors='coerce')
df_registro['TAXA_TRANSFERENCIA_MBPS'] = pd.to_numeric(df_registro['TAXA_TRANSFERENCIA_MBPS'], errors='coerce')
df_registro['TEMPO_TRANSFERENCIA_SEGUNDOS'] = pd.to_numeric(df_registro['TEMPO_TRANSFERENCIA_SEGUNDOS'], errors='coerce')

#Remover linhas com valores NaN
df_registro.dropna(subset=['TAMANHO_ARQUIVO_BYTES', 'TAXA_TRANSFERENCIA_MBPS', 'TEMPO_TRANSFERENCIA_SEGUNDOS', 'TIPO_ARQUIVO', 'DIA_DA_SEMANA'], inplace=True)

#Análise das transferências com sucesso
df_sucesso = df_registro[df_registro['STATUS'] == 'sucesso'].copy()

print(" \n########## Velocidades de Transferência (MB/s) ##########\n")
print(df_sucesso['TAXA_TRANSFERENCIA_MBPS'].describe())

print(" \n########## Tempo as Transferências ##########\n")
print(df_sucesso['TEMPO_TRANSFERENCIA_SEGUNDOS'].describe())

print("\n ########## Velocidade Média por tipo de arquivo ##########\n")
taxa_media_por_tipo = df_sucesso.groupby('TIPO_ARQUIVO')['TAXA_TRANSFERENCIA_MBPS'].mean().reset_index()#reset_index() cria um novo DataFrame com o índice padrão
print(taxa_media_por_tipo)

print("\n########## Tempo Médio de Transferência por tipo de arquivo ##########\n")
metricas_medias_por_tipo = df_sucesso.groupby('TIPO_ARQUIVO').agg(
    Tamanho_Medio_MB=('TAMANHO_ARQUIVO_MB', 'mean'), # 'Tamanho_Medio_MB' é o nome da nova coluna
    Taxa_Media_MBPS=('TAXA_TRANSFERENCIA_MBPS', 'mean'),
    Tempo_Medio_Segundos=('TEMPO_TRANSFERENCIA_SEGUNDOS', 'mean')
).reset_index()
print(metricas_medias_por_tipo)


# Gráfico de Dispersão: Tamanho do Arquivo vs. Velocidade de Transferência
plt.figure(figsize=(12, 6)) 
sns.scatterplot(x='TAMANHO_ARQUIVO_MB', y='TAXA_TRANSFERENCIA_MBPS', hue='TIPO_ARQUIVO', data=df_sucesso, alpha=0.7)
plt.title('Como o Tamanho do Arquivo (MB) Afeta a Velocidade (MB/s)') 
plt.xlabel('Tamanho do Arquivo (MB)') 
plt.ylabel('Velocidade de Transferência (MB/s)')
plt.grid(True) 
plt.tight_layout()
plt.show() 

#Histograma da Velocidade de Transferência
plt.figure(figsize=(10, 6))
sns.histplot(df_sucesso['TAXA_TRANSFERENCIA_MBPS'], kde=True, bins=30)
plt.title('Distribuição das Velocidades de Transferência (MB/s)')
plt.xlabel('Velocidade de Transferência (MB/s)')
plt.ylabel('Frequência')
plt.grid(True)
plt.tight_layout()
plt.show()
