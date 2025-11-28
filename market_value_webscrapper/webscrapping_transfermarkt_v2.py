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

#recebe um csv com todos os times que jogaram a premier league de 2004/05 - 2024/25. 
#link do time no transfermarkt,nome_time,id_time,temporada (e outras colunas)


#o código demora pouco mais de um minuto por time        


#conjunto de funções para tratar os anúncios de pop-up que  aparecem durante o uso do código
#geradas com GEMINI
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
        # 1. VERIFICAÇÃO: Usa o seletor de ID parcial para encontrar o iframe.
        seletor_iframe_css = "iframe[id*='google_ads_iframe']" # <-- O SELETOR CORRETO!
        
        iframe_anuncio = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, seletor_iframe_css))
        )
        print("✅ Iframe de anúncio do Google detectado. Mudando o foco...")

        # 2. MUDANÇA DE CONTEXTO: Entra no iframe.
        driver.switch_to.frame(iframe_anuncio)

        # 3. AÇÃO: Executa a lógica de fechar o anúncio DENTRO do iframe.
        # (Aqui você chamaria a função que clica acima do 'div#card')
        fechar_anuncio_interno_do_card(driver)

    except TimeoutException:
        print("ⓘ Nenhum iframe de anúncio do Google encontrado. Continuando...")
    except Exception as e:
        print(f"⚠️ Ocorreu um erro inesperado ao lidar com o iframe de anúncio: {e}")
    finally:
        # 4. RETORNO: ESSENCIAL! Sempre volte para a página principal.
        print("Retornando o foco para a página principal.")
        driver.switch_to.default_content()



def hide_ad_containers(driver):
    """
    Encontra e esconde os contêineres principais dos anúncios (como a tag <ins>).
    """
    # Seletor CSS para encontrar qualquer tag <ins> cujo id contenha 'gpt_unit'
    seletor_containers = "ins[id*='gpt_unit']"
    
    try:
        # Usa JavaScript para encontrar todos e escondê-los de uma vez
        script = f"""
            var adContainers = document.querySelectorAll('{seletor_containers}');
            if (adContainers.length > 0) {{
                console.log(adContainers.length + ' contêiner(s) de anúncio encontrado(s). Ocultando...');
                adContainers.forEach(function(container) {{
                    container.style.display = 'none';
                }});
                return true; // Retorna true se encontrou e escondeu
            }}
            return false; // Retorna false se não encontrou
        """
        encontrou_anuncio = driver.execute_script(script)
        
        if encontrou_anuncio:
            print("Contêiner(s) de anúncio <ins> ocultado(s) com sucesso.")
        else:
            print("Nenhum contêiner de anúncio <ins> encontrado.")
            
    except Exception as e:
        print(f"Ocorreu um erro ao tentar esconder os contêineres de anúncio: {e}")
        


def hide_iframes(driver):
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

        # AÇÃO AGRESSIVA: Executa um script para REMOVER todos os contêineres encontrados.
        # AQUI ESTÁ A CORREÇÃO: Usamos aspas duplas ("") em querySelectorAll
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



#escrever anos desejados
years = ["2004","2005","2006", "2007", "2008", "2009", "2010", "2011", "2012", "2013", "2014", "2015", "2016", "2017", "2018", "2019", "2020", "2021", "2022", "2023", "2024"]

# Adicione URLs conforme necessário
urls = [
    "https://www.transfermarkt.com.br/premier-league/startseite/wettbewerb/GB1",
    "https://www.transfermarkt.com.br/championship/startseite/wettbewerb/GB2",
    "https://www.transfermarkt.com.br/championship/startseite/wettbewerb/GB3",
    "https://www.transfermarkt.com.br/championship/startseite/wettbewerb/GB4",
    "https://www.transfermarkt.com.br/laliga/startseite/wettbewerb/ES1",
    "https://www.transfermarkt.com.br/bundesliga/startseite/wettbewerb/L1",
    "https://www.transfermarkt.com.br/bundesliga/startseite/wettbewerb/L2",
    "https://www.transfermarkt.com.br/ligue-1/startseite/wettbewerb/FR1",
    "https://www.transfermarkt.com.br/serie-a/startseite/wettbewerb/IT1",
    "https://www.transfermarkt.com.br/eredivisie/startseite/wettbewerb/NL1",
    "https://www.transfermarkt.com.br/liga-nos/startseite/wettbewerb/PO1",
    "https://www.transfermarkt.com.br/jupiler-pro-league/startseite/wettbewerb/BE1",
    "https://www.transfermarkt.com.br/super-lig/startseite/wettbewerb/TR1",
    "https://www.transfermarkt.com.br/scottish-premiership/startseite/wettbewerb/SC1",
]

#o programa dura em torno de 1min40s por ano


options = webdriver.ChromeOptions()
options.add_experimental_option("excludeSwitches", ["disable-popup-blocking"])
for url in urls:
    for year in years:
        sleep(2)
        driver = webdriver.Chrome(options=options)
        # Abre a página principal
        urln = f'{url}/plus/?saison_id={year}'
        driver.get(urln)
        
        # Espera pelo pop-up de cookies e o aceita
        WebDriverWait(driver, 15).until(EC.frame_to_be_available_and_switch_to_it((By.ID, "sp_message_iframe_954038")))
        WebDriverWait(driver, 15).until(EC.element_to_be_clickable((By.XPATH, '//button[@title="Aceitar e continuar"]'))).click()
        driver.switch_to.default_content() # Volta ao conteúdo principal


        #tenta fechar o alerta do site que pede para permitir notificações
        try:
            close_ad_button = WebDriverWait(driver, 15).until(EC.element_to_be_clickable((By.ID, "nadzCloseDesktop")))
            close_ad_button.click()
            print("Anúncio superior fechado.")
        except TimeoutException:
            print("Nenhum anúncio superior encontrado para fechar, continuando.")
        actions = ActionChains(driver)
        
        #desce para mostrar os seletores e a tabela
        actions.send_keys(Keys.PAGE_DOWN).perform()
        sleep(2)

  
        #busca anúncios de pop-up 
       # verificar_e_fechar_anuncio_em_iframe(driver)
        #hide_iframes(driver)
       # hide_ad_containers(driver)
        
        page_source = driver.page_source

     
        soup = BeautifulSoup(page_source, "html.parser")
        table_div = soup.find("div", class_="responsive-table")
        #table_div.get_text()
        #print(table_div.prettify())
        tds_rechts = soup.find_all('td', class_='rechts')
        sleep(2)
        data = []
        for td in tds_rechts:
            a_tag = td.find('a')
            if a_tag:
                href = a_tag.get('href')
                title = a_tag.get('title')
                valor_monetario = a_tag.get_text(strip=True)
                data.append([href, title, valor_monetario])

        sleep(2)

        # Extrai o caminho da URL
        path = urlparse(url).path
        # Usa uma expressão regular para encontrar a parte com o nome da liga
        match = re.search(r'/([^/]+)/startseite/wettbewerb/([^/]+)$', path)
        csv_filename = f'dados_times_ligas/dadosv2_{match.group(1)}_{match.group(2)}_{year}.csv'
    
        with open(csv_filename, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            # Escreva o cabeçalho
            writer.writerow(['href', 'title', 'valor_monetario'])
            writer.writerows(data)

        sleep(2)
        driver.quit()

driver.quit()