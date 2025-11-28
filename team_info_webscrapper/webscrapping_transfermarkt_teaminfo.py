from selenium import webdriver
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from time import sleep
import csv
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from urllib.parse import urlparse
import re
import pandas as pd
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import os 

# --- Funções de Anúncio -> Fecham Pop-Ups Inesperados  ---

def fechar_anuncio_interno_do_card(driver):
    """
    Esta função opera *DENTRO* de um iframe de anúncio.
    Ela encontra o div#card e clica acima dele para fechá-lo.
    """
    try:
        seletor_card = "div#card"
        card_element = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, seletor_card))
        )
        print("   -> 'div#card' encontrado dentro do iframe.")
        
        sleep(1) # Pausa para o anúncio se estabilizar

        print("   -> Clicando acima do card para fechar...")
        actions = ActionChains(driver)
        actions.move_to_element_with_offset(card_element, card_element.size['width'] // 2, -5).click().perform()

        WebDriverWait(driver, 5).until(
            EC.invisibility_of_element_located((By.CSS_SELECTOR, seletor_card))
        )
        print("   -> Anúncio interno fechado com sucesso.")
        return True
    except Exception as e:
        print(f"   -> Não foi possível fechar o anúncio interno do card: {e}")
        return False

def verificar_e_fechar_anuncio_em_iframe(driver, timeout=5):
    """
    Função guardiã principal: VERIFICA se um iframe de anúncio do Google apareceu,
    muda para ele e tenta fechar o anúncio que está lá dentro.
    """
    try:
        seletor_iframe_css = "iframe[id*='google_ads_iframe']" 
        
        iframe_anuncio = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, seletor_iframe_css))
        )
        print("✅ Iframe de anúncio do Google detectado. Mudando o foco...")

        driver.switch_to.frame(iframe_anuncio)

        fechar_anuncio_interno_do_card(driver)

    except TimeoutException:
        print("ⓘ Nenhum iframe de anúncio do Google encontrado. Continuando...")
    except Exception as e:
        print(f"⚠️ Ocorreu um erro inesperado ao lidar com o iframe de anúncio: {e}")
    finally:
        print("Retornando o foco para a página principal.")
        driver.switch_to.default_content()

def hide_ad_containers(driver):
    """
    Encontra e esconde os contêineres principais dos anúncios (como a tag <ins>).
    """
    seletor_containers = "ins[id*='gpt_unit']"
    
    try:
        script = f"""
            var adContainers = document.querySelectorAll("{seletor_containers}");
            if (adContainers.length > 0) {{
                console.log(adContainers.length + ' contêiner(s) de anúncio encontrado(s). Ocultando...');
                adContainers.forEach(function(container) {{
                    container.style.display = 'none';
                }});
                return true;
            }}
            return false;
        """
        encontrou_anuncio = driver.execute_script(script)
        
        if encontrou_anuncio:
            print("Contêiner(s) de anúncio <ins> ocultado(s) com sucesso.")
        else:
            print("Nenhum contêiner de anúncio <ins> encontrado.")
            
    except Exception as e:
        print(f"Ocorreu um erro ao tentar esconder os contêineres de anúncio: {e}")

def hide_iframes(driver):
    try:
        all_iframes = driver.find_elements(By.TAG_NAME,"iframe")
        if len(all_iframes) > 0:
            print("Ad Found\n")
            driver.execute_script("""
                var elems = document.getElementsByTagName("iframe"); 
                for(var i = 0, max = elems.length; i < max; i++)
                    {
                        elems[i].style.display = 'none';
                    }
                                """)
            print('Total Ads: ' + str(len(all_iframes)))
        else:
            print('No frames found')
    except Exception as e:
        print(f"Erro ao esconder iframes: {e}")
    finally:
        driver.switch_to.default_content()


def wait_and_remove_ad_containers(driver, timeout=5):
    """
    Função guardiã aprimorada: ESPERA ATIVAMENTE pela aparição dos 
    contêineres de anúncio <ins> e os REMOVE completamente do DOM.
    """
    seletor_containers = "ins[id*='gpt_unit']"
    
    try:
        WebDriverWait(driver, timeout).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, seletor_containers))
        )
        print("✅ Contêiner de anúncio <ins> detectado. Removendo...")

        script = f"""
            var adContainers = document.querySelectorAll("{seletor_containers}");
            adContainers.forEach(function(container) {{
                container.remove();
            }});
            return adContainers.length;
        """
        num_removidos = driver.execute_script(script)
        
        if num_removidos > 0:
            print(f"{num_removidos} contêiner(s) de anúncio <ins> removido(s) com sucesso.")
        else:
            print("Contêiner de anúncio <ins> estava visível, mas não foi removido.")
            
    except TimeoutException:
        print("ⓘ Nenhum contêiner de anúncio <ins> apareceu no tempo esperado. Continuando...")
    except Exception as e:
        print(f"⚠️ Ocorreu um erro ao tentar remover os contêineres de anúncio: {e}")

# --- Fim das Funções de Anúncio ---


# Lógica de verificação de arquivos -> verifica quais combinações de time e ano já estão no arquivo
csv_filename = 'dados_times_emprestados.csv'
colunas_header = ['time_x', 'temporada', 'nomeJogador', 'posicao', 'idade', 'nacionalidade', 'altura', 'pe', 'dataEntrada', 'valorMercado']

def carregar_processados(filename):
    """Lê o CSV existente e retorna um set de (time, temporada) já processados."""
    processados = set()
    if not os.path.exists(filename):
        print("Arquivo CSV não encontrado. Criando um novo com cabeçalho.")
        try:
            with open(filename, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow(colunas_header)
        except IOError as e:
            print(f"Erro ao criar o arquivo CSV: {e}")
            return None # Retorna None se não conseguir criar o arquivo
    else:
        print("Lendo arquivo CSV existente para pular itens já processados...")
        try:
            # Usar pandas para ler é mais fácil e robusto
            df_existente = pd.read_csv(filename)
            # Converte 'temporada' para string para garantir a correspondência
            df_existente['time_x'] = df_existente['time_x'].astype(str).str.strip()
            df_existente['temporada'] = df_existente['temporada'].astype(str).str.strip()
         #   df_existente['temporada'] = df_existente['temporada'].astype(str)
            
            for index, row in df_existente.iterrows():
                processados.add((row['time_x'], row['temporada']))
            print(f"Encontrados {len(processados)} registros já processados.")
            #debug
            if len(processados) > 0:
                print(f"Exemplos de chaves na memória: {list(processados)[:3]}")
        except pd.errors.EmptyDataError:
            print("Arquivo CSV encontrado, mas está vazio. Adicionando cabeçalho.")
            with open(filename, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow(colunas_header)
        except Exception as e:
            print(f"Erro ao ler o arquivo CSV existente: {e}")
            
    return processados

processados = carregar_processados(csv_filename)
if processados is None:
    print("Não foi possível iniciar o script devido a erro no arquivo. Encerrando.")
    exit()

#recebe um csv com todos os times que jogaram a premier league de 2004/05 - 2024/25 -> Criado com o market_value_webscrapper e com junção dos arquivos gerados 
dados = pd.read_csv("team_info_webscrapper/data.csv")

#tentativa de opção para retirar pop ups
options = webdriver.ChromeOptions()
options.add_experimental_option("excludeSwitches", ["disable-popup-blocking"])



#itera no csv dos times que jogaram a premier league
for index, linha in dados.iterrows():
    nome_time = str(linha['timeEmprestado']).strip()
    try:
        id_time = int(linha['id_timeEmprestado'])
    except Exception as baba:
        print(f"!!!!!!!!!!!!! ERRO GERAL !!!!!!!!!!!!!")
        print(f"Ocorreu um erro grave ao processar {nome_time} ({temporadat}) id_time: {baba}")
        print("Os dados desta iteração NÃO serão salvos.")

        continue
    temporadat = str(linha['temporada']).strip()
    ano = linha['ano']
    print(f"Checando: ('{nome_time}', '{temporadat}')")
    # Bloco de verificação se time está no csv
    if (nome_time, temporadat) in processados:
        print(f"\n--- PULANDO: {nome_time} ({temporadat}) já está no CSV. ---")
        continue

    print(f"\n--- PROCESSANDO: {nome_time} ({temporadat}) ---")

    # Lista temporária para esta iteração
    dados_desta_iteracao = []
    driver = None # Inicializa o driver como None para o bloco finally
    
    try:
        # Entra na página do histórico de empréstimos do time
        url = f"https://www.transfermarkt.com.br/{nome_time}/kader/verein/{id_time}/plus/1/galerie/0?saison_id={ano}"
       
        driver = webdriver.Chrome(options=options)
        driver.get(url)
        
        # Clica no pop-up de Aceitação de cookies
        WebDriverWait(driver, 15).until(EC.frame_to_be_available_and_switch_to_it((By.ID, "sp_message_iframe_954038")))
        WebDriverWait(driver, 15).until(EC.element_to_be_clickable((By.XPATH, '//button[@title="Aceitar e continuar"]'))).click()
        driver.switch_to.default_content() 

        try:
            close_ad_button = WebDriverWait(driver, 15).until(EC.element_to_be_clickable((By.ID, "nadzCloseDesktop")))
            close_ad_button.click()
            print("Anúncio superior fechado.")
        except TimeoutException:
            print("Nenhum anúncio superior encontrado para fechar, continuando.")
        
        actions = ActionChains(driver)
        
        
        sleep(5)
        actions.send_keys(Keys.PAGE_DOWN).perform()
        sleep(5)
        
        #Verifica Pop Ups
        verificar_e_fechar_anuncio_em_iframe(driver)
        hide_iframes(driver)
        hide_ad_containers(driver)
        wait_and_remove_ad_containers(driver, timeout=5)
        

        page_source = driver.page_source
        sleep(1)
        soup = BeautifulSoup(page_source, "html.parser")
        table_div = soup.find("div", class_="responsive-table")
        
        # Verifica se table_div foi encontrado antes de prosseguir
        if not table_div:
            print(f"Div da tabela não encontrada para {nome_time} ({temporadat}). Pulando para o próximo.")
            # Adiciona "NA" mesmo se a tabela não for encontrada
            Na = "NA"
            dados_desta_iteracao.append([nome_time, temporadat, Na, Na, Na, Na, Na, Na, Na, Na])
        else:
            tbody = table_div.find("tbody", class_=False)
            
            # Pega dados de empréstimos do clube na temporada
            if tbody:
                tds_rechts = tbody.find_all('tr', recursive=False)
                print(f"Encontradas {len(tds_rechts)} linhas de jogadores.")
                sleep(5)
                for tr in tds_rechts:
                    try:
                        time = nome_time
                        temporada = temporadat
                        
                        tdtr = tr.find_all('td', recursive=False)

                        celula_jogador = tdtr[1]
                        nomeJogador = celula_jogador.find('td', class_='hauptlink').get_text(strip=True)
                        posicao = celula_jogador.find_all('tr')[1].find('td').get_text(strip=True)

                        idade = tdtr[2].get_text(strip=True)
                        
                        celula_nacionalidade = tdtr[3]
                        imagens_bandeiras = celula_nacionalidade.find_all('img', class_='flaggenrahmen')
                        nacionalidades = [img['title'] for img in imagens_bandeiras if 'title' in img.attrs]
                        nacionalidade = ', '.join(nacionalidades)
                        
                        altura = tdtr[5].get_text(strip=True)
                        pe = tdtr[6].get_text(strip=True)
                        dataEntrada = tdtr[7].get_text(strip=True)
                        valorMercado = tdtr[9].get_text(strip=True)


#['time_x', 'temporada', 'nomeJogador', 'posicao', 'idade', 'nacionalidade', 'altura', 'pe', 'dataEntrada', 'valorMercado']

                       
                        
                        # Adiciona à lista temporária
                        dados_desta_iteracao.append([time, temporada, nomeJogador, posicao, idade, nacionalidade, altura, pe, dataEntrada, valorMercado])
                    
                    except Exception as e_row:
                        print(f"!!!!!!!!!!!!! ERRO GERAL !!!!!!!!!!!!!")
                        print(f"Ocorreu um erro grave ao processar {nome_time} ({temporadat}): {e_row}")
                        print("Os dados desta iteração NÃO serão salvos.")
                        # Limpa a lista para garantir que nada seja salvo
                        dados_desta_iteracao.clear()
                        continue
            
            else:
                print(f"Tabela encontrada, mas 'tbody' vazio para {nome_time} ({temporadat}).")
                Na = "NA"
                # Adiciona à lista temporária
                dados_desta_iteracao.append([nome_time, temporadat, Na, Na, Na, Na, Na, Na, Na, Na])

    except Exception as e_main:
        print(f"!!!!!!!!!!!!! ERRO GERAL !!!!!!!!!!!!!")
        print(f"Ocorreu um erro grave ao processar {nome_time} ({temporadat}): {e_main}")
        print("Os dados desta iteração NÃO serão salvos.")
        # Limpa a lista para garantir que nada seja salvo
        dados_desta_iteracao.clear() 

    finally:
        #  Garante que o driver feche A CADA iteração
        if driver:
            driver.quit()
        
        #  Bloco de escrita no CSV 
        if dados_desta_iteracao:
            try:
                with open(csv_filename, mode='a', newline='', encoding='utf-8') as file:
                    writer = csv.writer(file)
                    writer.writerows(dados_desta_iteracao)
                print(f">>> DADOS SALVOS: {len(dados_desta_iteracao)} linhas salvas para {nome_time} ({temporadat})")
                processados.add((nome_time, temporadat))
            except IOError as e:
                print(f"Erro ao salvar dados no CSV para {nome_time}: {e}")
        else:
            print(f"Nenhum dado novo para salvar para {nome_time} ({temporadat}).")

#  Bloco final de escrita foi removido
print("\n--- Processamento concluído. ---")