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
dados = pd.read_csv("loan_webscrapper/times_refatorado.csv")

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
        
        time.sleep(1) # Pausa para o anúncio se estabilizar

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
            // Linha corrigida
            var adContainers = document.querySelectorAll("{seletor_containers}");
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









#tentativa de opção (creio que não tenha feito funcionado)
options = webdriver.ChromeOptions()
options.add_experimental_option("excludeSwitches", ["disable-popup-blocking"])


#exemplo do link dos empréstimos de um time no transfermarkt
url = "https://www.transfermarkt.com.br/afc-sunderland/leihspielerhistorie/verein/289"
data = []

#itera no csv dos times que jogaram a premier league
for index, linha in dados.iterrows():
    nome_time = linha['nome_time']
    id_time = linha['id_time']
    temporadat = linha['temporada']
    
    url = f"https://www.transfermarkt.com.br/{nome_time}/leihspielerhistorie/verein/{id_time}"
    
    #código para pegar os empréstimos
    driver = webdriver.Chrome(options=options)
    # Abre a página principal
    driver.get(url)
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
    # actions.send_keys(Keys.PAGE_DOWN).perform()
    # sleep(1)
    # actions.send_keys(Keys.ARROW_UP).perform()
    # actions.send_keys(Keys.ARROW_UP).perform()
    # sleep(5)



    
   
    
    #busca anúncios de pop-up 
    verificar_e_fechar_anuncio_em_iframe(driver)
    hide_iframes(driver)
    hide_ad_containers(driver)
    
    #acha o botão seletor de ano
    year_button = WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'a[href="javascript:void(0)"]')))
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", year_button) # Rolagem precisa
    WebDriverWait(driver, 15).until(EC.element_to_be_clickable(year_button)).click()
    
    sleep(5)
    
    #seleciona o ano baseado na temporada que o time x jogou a premier
    xpath_year_option = f"//ul[@class='chzn-results']/li[text()='{temporadat}']"
    WebDriverWait(driver, 15).until(EC.element_to_be_clickable((By.XPATH, xpath_year_option))).click()

    # Seleciona o botão de tipo de empréstimo 
    loan_button_dropdown = WebDriverWait(driver, 15).until(EC.element_to_be_clickable((By.XPATH, "//a[span/text()='Jogadores emprestados']")))
    loan_button_dropdown.click()

    # Seleciona "Jogadores emprestados a outros clubes" (out on loan)
    xpath_loan_option = "//ul[@class='chzn-results']/li[text()='Jogadores emprestados a outros clubes']"
    WebDriverWait(driver, 15).until(EC.element_to_be_clickable((By.XPATH, xpath_loan_option))).click()

    # Clica no botão "Exibir"
    show_button = WebDriverWait(driver, 15).until(EC.element_to_be_clickable((By.XPATH, "//input[@class='right small button' and @value='Exibir']")))
    show_button.click()
    
    #creio que não seja utilizado pois está no carregamento
    actions.send_keys(Keys.PAGE_DOWN).perform()
    sleep(5)
    
    #busca anúncios de pop-up após carregamento de página nova
    verificar_e_fechar_anuncio_em_iframe(driver)
    hide_iframes(driver)
    hide_ad_containers(driver)
    
    # Encontra e clica no botão que mostra a tabela completa com mais dados de empréstimo
    tabela_completa_div = WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.XPATH, "//div[span/text()='Tabela completa']")))
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", tabela_completa_div) # Rolagem precisa
    WebDriverWait(driver, 15).until(EC.element_to_be_clickable(tabela_completa_div)).click()
    sleep(5)
    
    #busca anúncios de pop-up após carregamento de página nova. geralmente os anúncios costumam aparecer aqui.
    verificar_e_fechar_anuncio_em_iframe(driver) #tenta esconder o anúncio
    hide_iframes(driver) #tenta esconder o anúncio
    hide_ad_containers(driver) #tenta remover a div invisível do anúncio
    wait_and_remove_ad_containers(driver, timeout=5) #tenta remover a div invisível do anúncio

    #pega os dados da página com beautiful soup 
    page_source = driver.page_source
    sleep(1)
    soup = BeautifulSoup(page_source, "html.parser")
    table_div = soup.find("div", class_="responsive-table")
    table_div.get_text()
        
    #acha tbody (tabela)
    tbody = table_div.find("tbody", class_=False)
    
    if tbody:
        #encontra tr (linhas da tabela)
        tds_rechts = tbody.find_all('tr', recursive=False)
        sleep(5)
        for tr in tds_rechts:
            try:
                time = nome_time
                temporada = temporadat
                print("PRINTANDO TR")
                print(tr.prettify())
                tdtr = tr.find_all('td', recursive=False)

                # Célula 0: Nome e Posição
                celula_jogador = tdtr[0]
                nomeJogador = celula_jogador.find('td', class_='hauptlink').get_text(strip=True)
                # A posição está na segunda 'tr' da tabela interna
                posicao = celula_jogador.find_all('tr')[1].find('td').get_text(strip=True)

                # Célula 1: Idade
                idade = tdtr[1].get_text(strip=True)

                # Célula 2: Nacionalidade(s)
                celula_nacionalidade = tdtr[2]
                imagens_bandeiras = celula_nacionalidade.find_all('img', class_='flaggenrahmen')
                nacionalidades = [img['title'] for img in imagens_bandeiras if 'title' in img.attrs]
                nacionalidade = ', '.join(nacionalidades)
                # Célula 3: Time
                celula_time = tdtr[3]
                timeEmprestado = celula_time.find('td', class_='hauptlink').a.get('href')
                print(timeEmprestado)

                # Célula 4: Início do Empréstimo
                inicioEmp = tdtr[4].get_text(strip=True)

                # Célula 5: Fim do Empréstimo
                fimEmp = tdtr[5].get_text(strip=True)

                # Célula 6: Plantel
                plantel = tdtr[6].get_text(strip=True)
                
                # Célula 7: Jogos
                jogos = tdtr[7].get_text(strip=True)
                
                # Célula 8: Gols
                gols = tdtr[8].get_text(strip=True)
                
                # Célula 9: Valores de Mercado
                celula_valor = tdtr[9]
                # O valor final é o texto principal da célula
                valorEmpFim = celula_valor.contents[0].strip()
                
                # O valor inicial está no atributo 'title' de uma tag <span>
                span_valor_inicio = celula_valor.find('span', title=True)
                if span_valor_inicio:
                    # Extrai o valor do texto "Vdm início empréstimo: € 50.00 mi."
                    titulo = span_valor_inicio['title']
                    valor_inicio = titulo.split(':')[-1].strip()
                    valorEmpInicio = valor_inicio
                else:
                    valorEmpInicio = 'N/A'
                data.append([time, temporada, nomeJogador, posicao, idade, nacionalidade, timeEmprestado, inicioEmp, fimEmp, plantel, jogos, gols, valorEmpInicio, valorEmpFim])
            #se não encontrar a tabela, tenta fechar pop-ups como última opção
            except:
                hide_ad_containers(driver)
                wait_and_remove_ad_containers(driver, timeout=5)
    else:
        Na = "NA"
        data.append([nome_time, temporadat, Na, Na, Na, Na, Na, Na, Na, Na, Na, Na, Na, Na])
        continue
    sleep(5)
    driver.quit()
    
    
    
#após código rodar, cria a tabela
sleep(5)
csv_filename = f'dados_emprestimo_premierv2.csv'


with open(csv_filename, mode='w', newline='', encoding='utf-8') as file:
    writer = csv.writer(file)
    writer.writerow(['time', 'temporada', 'nomeJogador', 'posicao', 'idade', 'nacionalidade', 'timeEmprestado', 'inicioEmp', 'fimEmp', 'plantel', 'jogos', 'gols', 'valorEmpInicio', 'valorEmpFim'])
    writer.writerows(data)
driver.quit()

