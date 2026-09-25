from bs4 import BeautifulSoup
import requests
import os

CACHE_FOLDER = "cache"
HMTL_FILE = os.path.join(CACHE_FOLDER,"page_1.html")
URL = "https://books.toscrape.com/"

os.makedirs(CACHE_FOLDER, exist_ok=True)
if not os.path.exists(HMTL_FILE):
    print("FETCH")
    
    header= {"user_agent":"FlyRankInternship-A9/1.0 FlyRankInternship-A9/1.0/https://github.com/Quentalheitor/flyrank-crud-api"}
    request = requests.get(url=URL,headers=header,timeout=30)
    request.raise_for_status()

    with open(HMTL_FILE, "w", encoding="utf-8") as f:
        f.write(request.text)
else:
    print("CACHE HIT")

    with open(HMTL_FILE, mode="r", encoding="utf-8") as f:
        page_content = f.read()


