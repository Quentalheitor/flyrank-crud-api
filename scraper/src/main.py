from bs4 import BeautifulSoup
from urllib.parse import urljoin
import requests
import os
import time
from datetime import datetime,timezone
import json

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
                links_livros.append({'book':href_real,'origin_page':url})
    next_button = current_page.select_one('ul.pager li.next a')
    if next_button and 'href' in next_button.attrs:
        print('next_button_found')
        next_page_url = next_button['href']
        next_page_url_real = urljoin(url,next_page_url)
        url = next_page_url_real

print(f"Catalogue_pages = 3, discovered = 60, Unique_urls = {len(links_livros)}")

books = []
CACHE_BOOKS_FOLDER = "cache/Books"
html_book_file = os.path.join(CACHE_BOOKS_FOLDER,"book_1.html")

for idx,x in enumerate(links_livros):
    url = x['book']

    os.makedirs(CACHE_BOOKS_FOLDER, exist_ok=True)
    html_file =os.path.join(CACHE_BOOKS_FOLDER,f"book{idx+1}.html")
    if not os.path.exists(html_file):
        print("FETCH")
        
        header= {"user_agent":"FlyRankInternship-A9/1.0 FlyRankInternship-A9/1.0/https://github.com/Quentalheitor/flyrank-crud-api"}
        time.sleep(0.5)
        request = requests.get(url=url,headers=header,timeout=30)
        request.raise_for_status()

        current_page = BeautifulSoup(request.text,"html.parser")
        title = current_page.select_one("div.product_main h1").get_text(strip=True)
        price_text = current_page.select_one("table.table-striped tr:nth-of-type(4) td").get_text(strip=True)[2:]+" pounds"
        availability_text = current_page.select_one("table.table-striped tr:nth-of-type(6) td").get_text(strip=True)
        rating_text =  current_page.select_one("div.product_main p.star-rating").get("class",[])[1]
        description = current_page.select_one("article.product_page > p").get_text(strip=True)
        source_page = x['origin_page']
        fetched_at = datetime.now(timezone.utc).isoformat()
        records = {'title':title,
                   'product_url':x['book'],
                   'price text':price_text,
                   'availability_text':availability_text,
                   'rating text':rating_text,
                   'decription':description,
                   'source_page':source_page,
                   'fetched_at':fetched_at}
        with open(html_file, "w", encoding="utf-8") as f:
            json.dump(records,f,indent=4)
            page_content = str(records)
    else:
        print("CACHE HIT")

        with open(html_file, mode="r", encoding="utf-8") as f:
            page_content = f.read()
    books.append(page_content)

print(books[0])        