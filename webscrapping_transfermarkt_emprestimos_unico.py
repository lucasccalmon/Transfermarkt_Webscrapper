from selenium import webdriver
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from time import sleep
import csv
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from urllib.parse import urlparse
import re

#código para pegar os dados de empréstimo de um time, em um ano específico.
#quando utilizei para testar, não apareceu nenhum anúncio, por isso não tem nenhum método de contenção nesse código
#foi criado apenas no processo da criação do código que automatiza todos os times.


year = "18/19"
url = "https://www.transfermarkt.com.br/chelsea-fc/leihspielerhistorie/verein/631/plus/1?saison_id=2025&leihe=ist"
#código para pegar os empréstimos
sleep(5)
driver = webdriver.Edge()
# Abre a página principal
driver.get(url)
sleep(5)

driver.switch_to.frame('sp_message_iframe_954038') 


button = driver.find_element(By.XPATH, '//button[@title="Aceitar e continuar"]')
button.click()


driver.switch_to.default_content()
sleep(10)
actions = ActionChains(driver)
actions.send_keys(Keys.PAGE_DOWN).perform()
sleep(5)

year_button = driver.find_element(By.CSS_SELECTOR, 'a[href="javascript:void(0)"]')
year_button.click()
sleep(10)
year_option = driver.find_element(By.XPATH, f"//ul[@class='chzn-results']/li[text()='{year}']")
year_option.click()
sleep(10)
show_button = driver.find_element(By.XPATH, "//input[@class='right small button' and @value='Exibir']")
show_button.click()
sleep(10)
page_source = driver.page_source


soup = BeautifulSoup(page_source, "html.parser")
table_div = soup.find("div", class_="responsive-table")
table_div.get_text()
#print(table_div.prettify())
tbody = table_div.find("tbody", class_=False)
tds_rechts = tbody.find_all('tr', recursive=False)
sleep(5)
data = []
for tr in tds_rechts:
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
    timeEmprestado = celula_time.find('td', class_='hauptlink').a.get_text(strip=True)

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
    data.append([nomeJogador, posicao, idade, nacionalidade, timeEmprestado, inicioEmp, fimEmp, plantel, jogos, gols, valorEmpInicio, valorEmpFim])

sleep(5)
#troca a barra no ano para evitar bugs na hora de criar arquivo
safe_year = year.replace('/', '-')
# Extrai o caminho da URL
path = urlparse(url).path
# Usa uma expressão regular para encontrar a parte com o nome da liga
#match = re.search(r'/([^/]+)/', path)
#csv_filename = f'dados_{match.group(1)}_{safe_year}.csv'
csv_filename = f'dados_Chelsea_{safe_year}.csv'

with open(csv_filename, mode='w', newline='', encoding='utf-8') as file:
    writer = csv.writer(file)
    # Escreva o cabeçalho
    writer.writerow(['nomeJogador', 'posicao', 'idade', 'nacionalidade', 'timeEmprestado', 'inicioEmp', 'fimEmp', 'plantel', 'jogos', 'gols', 'valorEmpInicio', 'valorEmpFim'])
    writer.writerows(data)

sleep(5)
driver.quit()

