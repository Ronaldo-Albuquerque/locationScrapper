from playwright.sync_api import sync_playwright
from dataclasses import dataclass, asdict, field
import pandas as pd
import argparse
import os
import sys
import time

@dataclass
class Business:
    """Armazena os dados de um negócio obtidos via API do Google Maps"""

    name: str = None
    address: str = None
    website: str = None
    phone_number: str = None
    reviews_count: int = None
    reviews_average: float = None
    latitude: float = None
    longitude: float = None
    
    # Outros campos disponíveis na API do Google Maps... (não vamos utilizar)
    # Title: str = None
    # Rating: str = None
    # Reviews: str = None
    # Category: str = None
    # Address: str = None
    # Opening_Hours: str = None
    # Website: str = None
    # Phone_Number: str = None
    # Photos: str = None


@dataclass
class BusinessList:
    """Armazena uma lista de objetos Business e salva em arquivos Excel e CSV"""
    business_list: list[Business] = field(default_factory=list)
    save_at = 'output'

    def dataframe(self):
        """Transforma business_list em um DataFrame do pandas
        Retorna: pandas DataFrame
        """
        return pd.json_normalize(
            (asdict(business) for business in self.business_list), sep="_"
        )

    def save_to_excel(self, filename):
        """Salva o DataFrame pandas em um arquivo Excel (.xlsx)
        Args:
            filename (str): nome do arquivo
        """
        if not os.path.exists(self.save_at):
            os.makedirs(self.save_at)
        self.dataframe().to_excel(f"output/{filename}.xlsx", index=False)

    def save_to_csv(self, filename):
        """Salva o DataFrame pandas em um arquivo CSV
        Args:
            filename (str): nome do arquivo
        """
        if not os.path.exists(self.save_at):
            os.makedirs(self.save_at)
        self.dataframe().to_csv(f"output/{filename}.csv", index=False)

def extract_coordinates_from_url(url: str) -> tuple[float, float]:
    """Função auxiliar para extrair coordenadas da URL"""
    
    coordinates = url.split('/@')[-1].split('/')[0]
    # retorna latitude, longitude
    return float(coordinates.split(',')[0]), float(coordinates.split(',')[1])

def main():
    ########
    # Dados de entrada
    # Vamos utilizar os filtros salvos anteriormente (filter.txt)
    ########
    
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--search", type=str)
    parser.add_argument("-t", "--total", type=int)
    args = parser.parse_args()
    
    if args.search:
        search_list = [args.search]
        
    if args.total:
        total = args.total
    else:
        # se nenhum total for passado, usamos um valor grande aleatório
        total = 1_000_000

    if not args.search:
        search_list = []
        # lê os termos de busca a partir do arquivo input.txt
        input_file_name = 'filter.txt'
        input_file_path = os.path.join(os.getcwd(), input_file_name)
        if os.path.exists(input_file_path):
            with open(input_file_path, 'r') as file:
                search_list = file.readlines()
                
        if len(search_list) == 0:
            print('Erro: você deve passar o argumento -s ou adicionar buscas ao arquivo filter.txt')
            sys.exit()
        
    ###########
    # Fazendo scraping dos dados do Maps com os termos carregados do filter.txt
    ###########
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        page.goto("https://www.google.com/maps", timeout=30000)
        # espera extra na fase de desenvolvimento (pode ser removida depois)
        # page.wait_for_timeout(5000)
        
        for search_for_index, search_for in enumerate(search_list):
            print(f"-----\n{search_for_index} - {search_for}".strip())

            page.locator('//input[@id="searchboxinput"]').fill(search_for)
            page.wait_for_timeout(3000)

            page.keyboard.press("Enter")
            page.wait_for_timeout(5000)

            # rolagem da lista lateral
            page.wait_for_selector('//a[contains(@href, "https://www.google.com/maps/place")]') # aguarda carregamento dos resultados
            page.hover('//a[contains(@href, "https://www.google.com/maps/place")]', timeout=60000)

            # variável usada para detectar se o bot
            # já coletou todos os registros disponíveis
            previously_counted = 0
            while True:
                time.sleep(5)  # tempo extra (opcional)
                page.mouse.wheel(0, 10000)
                page.wait_for_timeout(6000)

                if (
                    page.locator(
                        '//a[contains(@href, "https://www.google.com/maps/place")]'
                    ).count()
                    >= total
                ):
                    listings = page.locator(
                        '//a[contains(@href, "https://www.google.com/maps/place")]'
                    ).all()[:total]
                    listings = [listing.locator("xpath=..") for listing in listings]
                    print(f"Total coletado: {len(listings)}")
                    break
                else:
                    # lógica para evitar loop infinito
                    if (
                        page.locator(
                            '//a[contains(@href, "https://www.google.com/maps/place")]'
                        ).count()
                        == previously_counted
                    ):
                        listings = page.locator(
                            '//a[contains(@href, "https://www.google.com/maps/place")]'
                        ).all()
                        print(f"Chegamos ao fim dos resultados disponíveis\nTotal coletado: {len(listings)}")
                        break
                    else:
                        previously_counted = page.locator(
                            '//a[contains(@href, "https://www.google.com/maps/place")]'
                        ).count()
                        print(
                            f"Coletados até agora: ",
                            page.locator(
                                '//a[contains(@href, "https://www.google.com/maps/place")]'
                            ).count(),
                        )

            business_list = BusinessList()

            # scraping dos dados individuais
            for listing in listings:
                try:
                    listing.click()
                    page.wait_for_timeout(5000)

                    name_attibute = 'aria-label'
                    address_xpath = '//button[@data-item-id="address"]//div[contains(@class, "fontBodyMedium")]'
                    website_xpath = '//a[@data-item-id="authority"]//div[contains(@class, "fontBodyMedium")]'
                    phone_number_xpath = '//button[contains(@data-item-id, "phone:tel:")]//div[contains(@class, "fontBodyMedium")]'
                    review_count_xpath = '//button[@jsaction="pane.reviewChart.moreReviews"]//span'
                    reviews_average_xpath = '//div[@jsaction="pane.reviewChart.moreReviews"]//div[@role="img"]'
                    
                    business = Business()
                    if len(listing.get_attribute(name_attibute)) >= 1:
                        business.name = listing.get_attribute(name_attibute)
                    else:
                        business.name = ""
                    if page.locator(address_xpath).count() > 0:
                        business.address = page.locator(address_xpath).all()[0].inner_text()
                    else:
                        business.address = ""
                    if page.locator(website_xpath).count() > 0:
                        business.website = page.locator(website_xpath).all()[0].inner_text()
                    else:
                        business.website = ""
                    if page.locator(phone_number_xpath).count() > 0:
                        business.phone_number = page.locator(phone_number_xpath).all()[0].inner_text()
                    else:
                        business.phone_number = ""
                    if page.locator(review_count_xpath).count() > 0:
                        business.reviews_count = int(
                            page.locator(review_count_xpath).inner_text()
                            .split()[0]
                            .replace(',','')
                            .strip()
                        )
                    else:
                        business.reviews_count = ""
                        
                    if page.locator(reviews_average_xpath).count() > 0:
                        business.reviews_average = float(
                            page.locator(reviews_average_xpath).get_attribute(name_attibute)
                            .split()[0]
                            .replace(',','.')
                            .strip())
                    else:
                        business.reviews_average = ""
                    
                    business.latitude, business.longitude = extract_coordinates_from_url(page.url)

                    business_list.business_list.append(business)
                except Exception as e:
                    print(f'Erro: {e}')
            
            #########
            # saída de dados
            #########
            business_list.save_to_excel(f"search_{search_for}".replace(' ', '_'))
            business_list.save_to_csv(f"search_{search_for}".replace(' ', '_'))

        browser.close()

if __name__ == "__main__":
    main()
