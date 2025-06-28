from selenium import webdriver
import requests
import csv
import os
from collections import defaultdict

url_biznes_gov = "https://www.biznes.gov.pl/pl/wyszukiwarka-firm/"

def get_cookie_session(url):
    driver = webdriver.Chrome()
    driver.get(url)
    cookies = driver.get_cookies()
    cookie_str = ";".join(f"{c['name']}={c['value']}" for c in cookies)
    return cookie_str

def save_to_file(url, cookie):
    write_headers = not os.path.exists("cookies.csv")
    with open("cookies.csv","a+", newline="") as csvfile:
        fieldnames = ["url", "cookie"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        if write_headers:
            writer.writeheader()
        writer.writerow({"url": url, "cookie": cookie})

def get_company_basic_info(krs_num, cookie):
    url = f"https://www.biznes.gov.pl/pl/wyszukiwarka-firm/api/data-warehouse/GetCompanyDetails?id={krs_num}"
    headers = {
    "Host": "www.biznes.gov.pl",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:139.0) Gecko/20100101 Firefox/139.0",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Connection": "keep-alive",
    "Referer": f"https://www.biznes.gov.pl/pl/wyszukiwarka-firm/wpis/krs/{krs_num}",
    "Cookie":cookie,
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "TE": "trailers"
    }
    response = requests.get(url, headers=headers)
    return response.json()

def get_company_report(krs_str, report_type):
    base_url = "https://api-krs.ms.gov.pl/api/krs"
    endpoint = "OdpisAktualny" if report_type == "A" else "OdpisPelny"
    url = f"{base_url}/{endpoint}/{krs_str}"
    response = response.get(url)
    return response.json()

def create_companies_watchlist():
    n = int(input("Ile spółek chcesz dodać: ").strip())
    krs_list = [input("Podaj numer KRS: ").zfill(10) for _ in range(n)]

    with open("krs_watchlist.txt", "a+") as file:
        file.seek(0)
        existing = set(line.strip() for line in file)

        for krs_str in krs_list:
            if krs_str not in existing:
                file.write(f"{krs_str}\n")
            else:
                print(f"{krs_str} znajduje się już na liście.")

def remove_from_watchlist(krs_str):
    krs_str = krs_str.zfill(10)
    with open("krs_watchlist.txt", "r") as file:
        lines = file.readlines()

    if f"{krs_str}\n" not in lines:
        print(f"{krs_str} nie znajduję się na liście.")
        return
    
    with open("krs_watchlist.txt", "w") as file:
        for line in lines:
            if line.strip() != krs_str:
                file.write(f"{line}")
            else:
                print(f"{krs_str} usunięty z listy")

