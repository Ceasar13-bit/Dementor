from selenium import webdriver
import requests
import csv
import os
from deepdiff import DeepDiff
import json
import time
from datetime import datetime

url_biznes_gov = "https://www.biznes.gov.pl/pl/wyszukiwarka-firm/"

def get_cookie_session(url):
    driver = webdriver.Chrome()
    driver.get(url)
    cookies = driver.get_cookies()
    cookie_str = ";".join(f"{c['name']}={c['value']}" for c in cookies)
    return cookie_str

def save_cookie_to_file(url, cookie):
    write_headers = not os.path.exists("cookies.csv")
    with open("cookies.csv","w", newline="") as csvfile:
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

def get_company_register_type(krs_str):
    url = "https://prs-openapi2-prs-prod.apps.ocp.prod.ms.gov.pl/api/wyszukiwarka/krs"
    payload = {
        "rejestr": ["P", "S"],
        "podmiot": {
            "krs": krs_str,
            "nip": None,
            "regon": None,
            "nazwa": None,
            "wojewodztwo": None,
            "powiat": None,
            "gmina": None,
            "miejscowosc": None
        },
        "status": {
            "czyOpp": None,
            "czyWpisDotyczacyPostepowaniaUpadlosciowego": None,
            "dataPrzyznaniaStatutuOppOd": None,
            "dataPrzyznaniaStatutuOppDo": None
        },
        "paginacja": {
            "liczbaElementowNaStronie": 100,
            "maksymalnaLiczbaWynikow": 100,
            "numerStrony": 1
        }
    }
    headers = {
    "Host": "prs-openapi2-prs-prod.apps.ocp.prod.ms.gov.pl",
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:140.0) Gecko/20100101 Firefox/140.0",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "x-api-key": "TopSecretApiKey",
    "Content-Type": "application/json",
    "Origin": "https://wyszukiwarka-krs.ms.gov.pl",
    "Connection": "keep-alive",
    "Referer": "https://wyszukiwarka-krs.ms.gov.pl/",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-site",
    "Priority": "u=0"
    }
    response = requests.post(url, json=payload, headers=headers)
    data = response.json()
    if data["liczbaPodmiotow"] >= 1:
        return data["listaPodmiotow"][0]["typRejestru"]
    return None

def get_company_report(krs_str, report_type = "A"):
    base_url = "https://api-krs.ms.gov.pl/api/krs"
    endpoint = "OdpisAktualny" if report_type == "A" else "OdpisPelny"
    register_type = get_company_register_type(krs_str)
    if not register_type:
        return None
    url = f"{base_url}/{endpoint}/{krs_str}?rejestr={register_type}"
    response = requests.get(url)
    if response.status_code == 204 and report_type == "A":
        return get_company_report(krs_str, "F")
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


def save_companies_reports():
    with open("krs_watchlist.txt", "r") as file:
        lines = [line.strip() for line in file]
    for line in lines:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        data = get_company_report(line, "A")
        if not data:
            continue
        with open(f"KRS_reports/{line}_{timestamp}.json", "w") as jfile:
            json.dump(data, jfile, ensure_ascii=False, indent=2)
        time.sleep(1)

def get_recent_changes(data = datetime.today().date()):
    url = f"https://api-krs.ms.gov.pl/api/Krs/Biuletyn/{data}"
    response = requests.get(url)
    return response.json()

def check_if_changed(krs_list):
    krs_set = set(krs_list)
    with open("krs_watchlist.txt", "r") as file:
        lines = set(line.strip() for line in file)
    return krs_set & lines

def check_what_changed(krs_set):
    arr = [f for f in os.listdir("KRS_reports") if any(f.startswith(krs) for krs in krs_set)]
    changes = []
    for f in arr:
        krs = f[:10]
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        updated_report = get_company_report(krs)
        with open(f"KRS_reports/{f}", "r") as file:
            old_report = json.load(file)
        diff = DeepDiff(old_report, updated_report, ignore_order=True)
        changes.append({"krs":krs, "filename": f, "diff": diff})
        os.remove(f"KRS_reports/{f}")
        with open(f"KRS_reports/{krs}_{timestamp}.json", "w") as file:
            json.dump(updated_report, file, ensure_ascii=False, indent=2)
    return changes


