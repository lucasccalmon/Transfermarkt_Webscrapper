import pandas as pd

tab = pd.read_csv("dados_premier-league_consolidados.csv")

links = tab['href']
print(links)

padrao_regex = r'/([^/]+)/kader/verein/(\d+)/saison_id/(\d+)'

# Aplica a extração e cria 3 novas colunas de uma só vez
tab[['nome_time', 'id_time', 'ano']] = tab['href'].str.extract(padrao_regex)

# --- ETAPA 2: A transformação da coluna 'ano' ---

# Garante que a coluna 'ano' seja numérica para podermos somar 1
ano_numerico = pd.to_numeric(tab['ano'])

# Pega os dois últimos dígitos do ano inicial (ex: 2004 -> '04')
ano_inicio_str = ano_numerico.astype(str).str[-2:]

# Pega os dois últimos dígitos do ano seguinte (ex: 2004+1=2005 -> '05')
ano_fim_str = (ano_numerico + 1).astype(str).str[-2:]

# Junta as duas partes com uma barra no meio para formar o novo formato
tab['ano'] = ano_inicio_str + '/' + ano_fim_str

# Renomeia a coluna para refletir o novo formato (opcional, mas recomendado)
tab.rename(columns={'ano': 'temporada'}, inplace=True)
# 3. Exibindo o resultado
print("DataFrame com as novas colunas extraídas:")
print(tab)

tab.to_csv("times_refatorado.csv")