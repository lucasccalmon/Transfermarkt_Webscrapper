from selenium import webdriver
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from time import sleep
import csv
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from urllib.parse import urlparse
import re

#escrever anos desejados
years = [ "23/24", "22/23", "21/22", "20/21","19/20"]
# Adicione URLs conforme necessário
urls = [
    "https://www.transfermarkt.com.br/laliga/startseite/wettbewerb/ES1",
    "https://www.transfermarkt.com.br/bundesliga/startseite/wettbewerb/L1",
    "https://www.transfermarkt.com.br/ligue-1/startseite/wettbewerb/FR1",
    "https://www.transfermarkt.com.br/serie-a/startseite/wettbewerb/IT1"
    
]

#o programa dura em torno de 1min40s por ano



for url in urls:
    for year in years:
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
        show_button = driver.find_element(By.XPATH, "//input[@class='small button' and @value='Mostrar']")
        show_button.click()
        sleep(10)
        page_source = driver.page_source

     
        soup = BeautifulSoup(page_source, "html.parser")
        table_div = soup.find("div", class_="responsive-table")
        #table_div.get_text()
        #print(table_div.prettify())
        tds_rechts = soup.find_all('td', class_='rechts')
        sleep(5)
        data = []
        for td in tds_rechts:
            a_tag = td.find('a')
            if a_tag:
                href = a_tag.get('href')
                title = a_tag.get('title')
                valor_monetario = a_tag.get_text(strip=True)
                data.append([href, title, valor_monetario])

        sleep(5)
        #troca a barra no ano para evitar bugs na hora de criar arquivo
        safe_year = year.replace('/', '-')
        # Extrai o caminho da URL
        path = urlparse(url).path
        # Usa uma expressão regular para encontrar a parte com o nome da liga
        match = re.search(r'/([^/]+)/', path)
        csv_filename = f'dados_{match.group(1)}_{safe_year}.csv'
    
        with open(csv_filename, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            # Escreva o cabeçalho
            writer.writerow(['href', 'title', 'valor_monetario'])
            writer.writerows(data)

        sleep(5)
        driver.quit()

driver.quit()