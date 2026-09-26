from bs4 import BeautifulSoup
from urllib.parse import urljoin
import requests
import os
import time
from datetime import datetime,timezone
import json
from pydantic import BaseModel,ValidationError

class RecordSchema(BaseModel):
    id: str
    title: str
    product_url: str
    price_text: str
    price: int | float
    availability: str
    rating: str
    description: str|None
    source_pg: str
    fetched_at: str

start_time = datetime.now()
fetched = 0
cached = 0
valid = 0
invalid = 0
page_fail = 0


CACHE_FOLDER = "cache"
html_file = os.path.join(CACHE_FOLDER,"page_1.html")
url = "https://books.toscrape.com/"
links_livros = []

for x in "123":
    os.makedirs(CACHE_FOLDER, exist_ok=True)
    html_file =os.path.join(CACHE_FOLDER,f"page_{x}.html")
    if not os.path.exists(html_file):
        print("FETCH")
        
        header= {"User-Agent":"FlyRankInternship-A9/1.0 FlyRankInternship-A9/1.0/https://github.com/Quentalheitor/flyrank-crud-api"}
        time.sleep(0.5)
        try:
            request = requests.get(url=url,headers=header,timeout=30)
            request.raise_for_status()
        except requests.exceptions.RequestException as e:
            status_code = getattr(e.response, "status_code", None)
            if status_code and status_code in (403, 404):
                page_fail += 1
                continue
            elif isinstance(e, requests.exceptions.Timeout) or (status_code and status_code >= 500):
                # Wait and retry once
                time.sleep(1.0)
                try:
                    request = requests.get(url=url, headers=header, timeout=30)
                    request.raise_for_status()
                except Exception as retry_err:
                    page_fail += 1
                    print(f"Retry failed: {retry_err}")
                    continue
            else:
                page_fail += 1
                continue
        fetched += 1
    else:
        print("CACHE HIT")
        cached += 1

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
CACHE_BOOKS_OUTPUTS =  "output"
valid_list = []
error_list = []
for idx,x in enumerate(links_livros):
    url = x['book']

    os.makedirs(CACHE_BOOKS_FOLDER, exist_ok=True)
    json_book_file =os.path.join(CACHE_BOOKS_FOLDER,f"book{idx+1}.json")
    if not os.path.exists(json_book_file):
        print("FETCH")
        
        header= {"User-Agent":"FlyRankInternship-A9/1.0 FlyRankInternship-A9/1.0/https://github.com/Quentalheitor/flyrank-crud-api"}
        time.sleep(0.5)
        try:
            request = requests.get(url=url,headers=header,timeout=30)
            request.raise_for_status()
        except requests.exceptions.RequestException as e:
            status_code = getattr(e.response, "status_code", None)
            if status_code and status_code in (403, 404):
                page_fail += 1
                continue
            elif isinstance(e, requests.exceptions.Timeout) or (status_code and status_code >= 500):
                # Wait and retry once
                time.sleep(1.0)
                try:
                    request = requests.get(url=url, headers=header, timeout=30)
                    request.raise_for_status()
                except Exception as retry_err:
                    page_fail += 1
                    print(f"Retry failed: {retry_err}")
                    continue
            else:
                page_fail += 1
                continue
        fetched += 1

        current_page = BeautifulSoup(request.text,"html.parser")
        title = current_page.select_one("div.product_main h1").get_text(strip=True)
        price_gbp = float(current_page.select_one("table.table-striped tr:nth-of-type(4) td").get_text(strip=True)[2:])
        availability_text = current_page.select_one("table.table-striped tr:nth-of-type(6) td").get_text(strip=True)
        rating_text =  current_page.select_one("div.product_main p.star-rating").get("class",[])[1]
        description = current_page.select_one("article.product_page > p").get_text(strip=True)
        source_page = x['origin_page']
        fetched_at = datetime.now(timezone.utc).isoformat()
        records = {'id':x['book'],
                   'title':title,
                   'product_url':x['book'],
                   'price_text': f"{price_gbp} pounds",
                   'price':price_gbp,
                   'availability':availability_text,
                   'rating':rating_text,
                   'description':description,
                   'source_pg':source_page,
                   'fetched_at':fetched_at}
        with open(json_book_file, "w", encoding="utf-8") as f:
            json.dump(records,f,indent=4)
            page_content = records
    else:
        print("CACHE HIT")
        cached += 1

        with open(json_book_file, mode="r", encoding="utf-8") as f:
            page_content = json.load(f)

    try:
        os.makedirs(CACHE_BOOKS_OUTPUTS, exist_ok=True)
        json_book_file =os.path.join(CACHE_BOOKS_OUTPUTS,"books.json")
        error_json_book_file = os.path.join(CACHE_BOOKS_OUTPUTS,"errors.json")
        validate_book = RecordSchema.model_validate(page_content)
        valid += 1

        if not os.path.exists(json_book_file):
            for z in valid_list:
                if z['id'] == x['book']:
                    print("skipped")
                    continue
            with open(json_book_file, "w", encoding="utf-8") as f:
                valid_list.append(page_content)
                json.dump(valid_list,f,indent=4)
        else:
            with open(json_book_file,"r", encoding="utf-8") as f:
                file_content = json.load(f)
                for z in file_content:
                    if z['id'] == x['book']:
                        print("skipped")
                        continue
                valid_list.append(page_content)
            with open(json_book_file,"w", encoding="utf-8") as f:
                json.dump(valid_list,f,indent=4)
    except ValidationError as e:
        invalid += 1
        if not os.path.exists(error_json_book_file):
            with open(error_json_book_file, "w", encoding="utf-8") as f:
                error_list.append(page_content)
                json.dump(error_list,f,indent=4)
        else:
            with open(error_json_book_file,"r", encoding="utf-8") as f:
                file_content = json.load(f)
                error_list.append(e.errors())
            with open(error_json_book_file,"w", encoding="utf-8") as f:
                json.dump(error_list,f,indent=4)

    books.append(page_content)

end_run = datetime.now()
duration = end_run - start_time
os.makedirs(CACHE_BOOKS_OUTPUTS,exist_ok=True)
run_report_path = os.path.join(CACHE_BOOKS_OUTPUTS,"run-report.json")
run_report = {'start_time': str(start_time),
              'duration': str(duration),
              'pages_fetched': fetched,
              'cache_hits': cached,
              'valid_records': valid,
              'invalid_records': invalid,
              'failed_pages': page_fail}

with open(run_report_path,"w",encoding="utf-8") as f:
    json.dump(run_report,f,indent=4)
print(len(valid_list))
print(len(books))
print(run_report)