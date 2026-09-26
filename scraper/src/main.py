from bs4 import BeautifulSoup
from urllib.parse import urljoin
import requests
import os
import time

CACHE_FOLDER = "cache"
html_file = os.path.join(CACHE_FOLDER,"page_1.html")
url = "https://books.toscrape.com/"
links_livros = []

for x in "123":
    os.makedirs(CACHE_FOLDER, exist_ok=True)
    html_file =os.path.join(CACHE_FOLDER,f"page_{x}.html")
    if not os.path.exists(html_file):
        print("FETCH")
        
        header= {"user_agent":"FlyRankInternship-A9/1.0 FlyRankInternship-A9/1.0/https://github.com/Quentalheitor/flyrank-crud-api"}
        time.sleep(0.5)
        request = requests.get(url=url,headers=header,timeout=30)
        request.raise_for_status()

        with open(html_file, "w", encoding="utf-8") as f:
            f.write(request.text)
            page_content=request.text
    else:
        print("CACHE HIT")

        with open(html_file, mode="r", encoding="utf-8") as f:
            page_content = f.read()

    current_page = BeautifulSoup(page_content,"html.parser")
    for a_tag in current_page.select("h3 a"):
        href_relative = a_tag.get("href")
        if href_relative:
            href_real = urljoin(url,href_relative)
            if href_real not in links_livros:
                links_livros.append(href_real)
    next_button = current_page.select_one('ul.pager li.next a')
    if next_button and 'href' in next_button.attrs:
        print('next_button_found')
        next_page_url = next_button['href']
        next_page_url_real = urljoin(url,next_page_url)
        url = next_page_url_real

print(f"Catalogue_pages = 3, discovered = 60, Unique_urls = {len(links_livros)}")