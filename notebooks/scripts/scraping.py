import pandas as pd
import numpy as np
import json
import bs4

import selenium
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.alert import Alert

from .drive import get_files, update_file, get_file, create_file


import time
import os

from tqdm import tqdm
import requests
from selenium.webdriver.chrome.options import Options


def requirements(dic_file, progress, drive):
    if not os.path.exists('../data/morningstar'):
        os.makedirs('../data/morningstar')
    
    if not os.path.exists(progress):
        with open(progress, 'w') as f:
            f.write("")
    
    if type(dic_file) == list:
        dic_cat = pd.DataFrame(columns = ['CODE ISIN'], data = dic_file)
    elif type(dic_file) == type(pd.DataFrame()):
        dic_cat = dic_file
    else:
        dic_cat = pd.read_csv(dic_file)
        
        #Dic cat from the last isin in progress to the end
        with open(progress, 'r') as f:
            #Last line in progress
            last_isin = f.readlines()[-1].split(':')[0].strip()
            

        progress = dic_cat[dic_cat['CODE ISIN'] == last_isin].index[0]
        dic_cat = dic_cat.iloc[progress:]        
    
    if "Morningstar" not in dic_cat.columns:
            dic_cat['Morningstar'] = 'Not Found'
        
    return dic_cat

def login(mail):
    
    chrome_options = Options()
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--ignore-certificate-errors')
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(options=chrome_options)
    url = "https://doc.morningstar.com/Fund.aspx?u=ALL#"
    driver.get(url)
    
    Alert(driver).accept()
    
    login = driver.find_element(By.XPATH, '/html/body/div[10]/div[3]/div[1]/div[2]/div/div/form/input')
    login.click()
    
    mail_input = driver.find_element(By.XPATH, '/html/body/div/ctrsi-signin-component/div/div/div[2]/main/section/div/div[2]/div/div/form/label[1]/input')
    mail_input.send_keys(mail)
    
    password = driver.find_element(By.XPATH, '/html/body/div/ctrsi-signin-component/div/div/div[2]/main/section/div/div[2]/div/div/form/label[2]/div[2]/input')
    password.send_keys(mail)
    
    sign = driver.find_element(By.XPATH, '/html/body/div/ctrsi-signin-component/div/div/div[2]/main/section/div/div[2]/div/div/form/div/button[2]/span')
    sign.click()
    
    nav = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '/html/body/div[10]/ul/li[3]/div/table/tbody/tr/td[1]')))
    nav.click()
    
    driver.get('https://doc.morningstar.com/Fund.aspx?u=ALL')
    return driver

def download_classic(driver, link, isin, drive, file):
    headers = {
        "User-Agent":
            "Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36"
        }
    s = requests.session()
    s.headers.update(headers)

    for cookie in driver.get_cookies():
        c = {cookie['name']: cookie['value']}
        s.cookies.update(c)
    
    response = s.get(link)
    if response.status_code == 200:
        with open(f"./data/other/{isin}.pdf", 'wb') as f:
            f.write(response.content)
        if file != None:
            update_file(drive, file, f"./data/other/{isin}.pdf")
        else :
            create_file(drive, isin, f"./data/other/{isin}.pdf")
    return None
        
        
def download_from_progress(progress):
    driver = login("piron85023@lucvu.com")
    
    downloaded = os.listdir('../data/morningstar')
    
    with open(progress, 'r') as f:
        lines = f.readlines()
        for line in tqdm(lines, desc="Downloading..."):
            isin, link = line.split(':', 1)
            isin = isin.strip()
            link = link.strip()
            if (f"{isin}.pdf" not in downloaded) and (link != "Not Found"):
                # response = driver.request("GET", link)
                headers = {
                    "User-Agent":
                        "Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36"
                    }
                s = requests.session()
                s.headers.update(headers)

                for cookie in driver.get_cookies():
                    c = {cookie['name']: cookie['value']}
                    s.cookies.update(c)
                
                response = s.get(link)
                if response.status_code == 200:
                    with open(f"../data/other/{isin}.pdf", 'wb') as f:
                        f.write(response.content)
    return driver

def scrap(mail, dic_file, progress, drive):
    
    
    dic_cat = requirements(dic_file, progress, drive)
    
    # return
    
    driver = login(mail)
        
    for row in tqdm(dic_cat.iterrows(), total=dic_cat.shape[0], desc="Scraping..."):
        
        # print(f"Scraping {row[1]['CODE ISIN']}")
        
        isin = row[1]["CODE ISIN"]
        input = driver.find_element(By.XPATH, '//*[@id="SearchInput"]')
        input.clear()    
        input.send_keys(isin + Keys.RETURN)
        
        file = get_file(drive, isin)
        
    
        
        tr_elements = driver.find_elements(By.XPATH, '/html/body/div[10]/div[3]/div[3]/table/tbody[2]/tr')
                
        if len(tr_elements) > 0:
            for tr in tr_elements:
                if (("KID" in tr.text) or ("PRIIP" in tr.text)) and ("Français" in tr.text):
                    # print(tr.find_element(By.XPATH, 'td[5]/a[2]').get_attribute("href"))
                    link = tr.find_element(By.XPATH, 'td[5]/a[2]').get_attribute("href")
                    # response = requests.get(link)
                    # if response.status_code == 200:
                    #     with open(f"../data/other/{isin}.pdf", 'wb') as f:
                    #         f.write(response.content)
                    dic_cat.loc[row[0], "Morningstar"] = link
                    #Year
                    dic_cat.loc[row[0], "Disponibilité"] = True
                    download_classic(driver, link, isin, drive, file)
                    os.remove(f"./data/other/{isin}.pdf")    
                    file = get_file(drive, isin)
                    try :
                        dic_cat.loc[row[0], "URL"] = f"https://drive.google.com/file/d/{file.get('files')[0].get('id')}/view?usp=sharing"
                    except :
                        print("Error")
                    break
                # else:
                    # dic_cat.loc[row[0], "Morningstar"] = "Not Found"
        dic_cat.loc[row[0], "Date"] = pd.to_datetime('today').year
        
        with open(progress, 'a') as f :
            f.write(f"{row[1]['CODE ISIN']} : {dic_cat.loc[row[0], 'Morningstar']}\n")
            
    if len(dic_cat[dic_cat["Morningstar"] == "Not Found"]) > 0:
        dic_cat = scrap_geco(dic_cat, progress, drive)
    
    return driver, dic_cat 

def scrap_geco(dic_cat, progress, drive):    
        
    for row in tqdm(dic_cat.iterrows(), total=dic_cat.shape[0], desc='Scraping AMF GeCo'):
        if dic_cat.loc[row[0], "Morningstar"] == "Not Found":
            code_isin = row[1]['CODE ISIN']
            url = f'https://geco.amf-france.org/Bio/res_doc.aspx?NomProd=&NomSOc=&varvalidform=on&action=new&TypeDoc=Notice&TYPEPROD=0&NumAgr=&CodePart={code_isin}&DateDebAgr=&DateFinAgr=&DateDeb=&DateFin=&valid_form=Lancer+la+recherche'
            response = requests.get(url)
            
            file = get_file(drive, code_isin)
            
            if ".pdf" in response.url :
                dic_cat.loc[row[0], "Morningstar"] = str(response.url)
                dic_cat.loc[row[0], "Disponibilité"] = True
                with open('progress.txt', 'a') as f: 
                    f.write(f'{code_isin} : {response.url}\n')
                
                response = requests.get(response.url)
                with open(f"./data/other/{code_isin}.pdf", 'wb') as f:
                    f.write(response.content)
                    
                if file != None:
                    update_file(drive, file, f"./data/other/{code_isin}.pdf")
                else :
                    create_file(drive, code_isin, f"./data/other/{code_isin}.pdf")
                os.remove(f"./data/other/{code_isin}.pdf")    
                
                try :
                    dic_cat.loc[row[0], "URL"] = f"https://drive.google.com/file/d/{file.get('files')[0].get('id')}/view?usp=sharing"
                except :
                    print("Error")
                    
            else :
                data = response.text
                
                df = pd.DataFrame()
                
                soup = bs4.BeautifulSoup(data, 'html.parser')
                tr_elements = soup.find_all('tr')
                
                pdfs = []
                for elt in tr_elements:
                    if "ligne" in str(elt.get('class')):
                        # print(elt.find('a').get('href'))
                        pdfs.append(elt.find('a').get('href'))

                if len(pdfs) > 0:
                    dic_cat.loc[row[0], "Morningstar"] = "https://geco.amf-france.org/Bio/" + pdfs[0]
                    dic_cat.loc[row[0], "Disponibilité"] = True
                    # with open(progress, 'a') as f: 
                    #     f.write(f'{code_isin} : {pdfs[0]}\n')
                    response = requests.get(dic_cat.loc[row[0], "Morningstar"])
                    if response.status_code == 200:
                        with open(f"./data/other/{code_isin}.pdf", 'wb') as f:
                            f.write(response.content)
                        if file != None:
                            update_file(drive, file, f"./data/other/{code_isin}.pdf")
                        else :
                            create_file(drive, code_isin, f"./data/other/{code_isin}.pdf")
                        os.remove(f"./data/other/{code_isin}.pdf")    
                        
                    try :
                        dic_cat.loc[row[0], "URL"] = f"https://drive.google.com/file/d/{file.get('files')[0].get('id')}/view?usp=sharing"
                    except :
                        print("Error")
                    
                else :
                    dic_cat.loc[dic_cat['CODE ISIN'] == code_isin, 'Morningstar'] = "Not Found"
                    dic_cat.loc[row[0], "Disponibilité"] = False
                    with open(progress, 'a') as f: 
                        f.write(f'{code_isin} : No pdf\n')

    return dic_cat
    

def check_availability(isin):
    downloaded = os.listdir('./data/morningstar')
    not_available = []
    if f"{isin}.pdf" in downloaded:
        return True
    return False 
