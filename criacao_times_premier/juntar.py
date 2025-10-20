import pandas as pd

import pandas as pd
import glob
import os

# --- Configuração ---
# Caminho para a pasta onde estão os seus arquivos CSV.
# Se o script Python estiver na mesma pasta que os CSVs, você pode usar '.'
caminho_da_pasta = './dados_usados' 

# Padrão de nome dos arquivos que você quer juntar.
# O '*' é um curinga que significa "qualquer coisa".
padrao_do_arquivo = 'dados_premier-league_*.csv'

# Nome do arquivo final que será criado.
arquivo_de_saida = 'dados_premier-league_consolidados.csv'
# --------------------


# Monta o caminho completo para a busca dos arquivos
caminho_de_busca = os.path.join(caminho_da_pasta, padrao_do_arquivo)

# Usa a biblioteca 'glob' para encontrar todos os arquivos que correspondem ao padrão
lista_de_arquivos = glob.glob(caminho_de_busca)

# Verifica se algum arquivo foi encontrado
if not lista_de_arquivos:
    print(f"Nenhum arquivo encontrado com o padrão '{padrao_do_arquivo}' na pasta '{caminho_da_pasta}'.")
    print("Verifique se o script está na pasta correta.")
else:
    print(f"Encontrados {len(lista_de_arquivos)} arquivos para juntar.")
    
    # Cria uma lista vazia para armazenar os dataframes de cada arquivo
    lista_de_dataframes = []

    # Loop para ler cada arquivo encontrado e adicioná-lo à lista
    for arquivo in lista_de_arquivos:
        try:
            df_temp = pd.read_csv(arquivo)
            lista_de_dataframes.append(df_temp)
            print(f"  - Lendo arquivo: {arquivo}")
        except Exception as e:
            print(f"  - Erro ao ler o arquivo {arquivo}: {e}")

    # Concatena (junta) todos os dataframes da lista em um único dataframe
    # ignore_index=True reinicia o índice do arquivo final (0, 1, 2, ...)
    df_final = pd.concat(lista_de_dataframes, ignore_index=True)

    # Salva o dataframe final em um novo arquivo CSV
    # index=False evita que o pandas crie uma coluna extra para o índice no CSV
    df_final.to_csv(os.path.join(caminho_da_pasta, arquivo_de_saida), index=False)

    print("\n----------------------------------------------------")
    print("✅ Arquivos juntados com sucesso!")
    print(f"O arquivo consolidado foi salvo como: '{arquivo_de_saida}'")
    print(f"Total de linhas no arquivo final: {len(df_final)}")
    print("----------------------------------------------------")