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


import time
import os

from tqdm import tqdm
import requests


def requirements(dic_file, progress):
    if not os.path.exists('../data/morningstar'):
        os.makedirs('../data/morningstar')
    
    if not os.path.exists(progress):
        with open(progress, 'w') as f:
            f.write("")
    
    if type(dic_file) == list:
        dic_cat = pd.DataFrame(columns = ['CODE ISIN'], data = dic_file)
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
    
    driver = webdriver.Chrome()
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

def download_classic(driver, link, isin):
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
        with open(f"./data/morningstar/{isin}.pdf", 'wb') as f:
            f.write(response.content)
            
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
                    with open(f"../data/morningstar/{isin}.pdf", 'wb') as f:
                        f.write(response.content)
    return driver

def scrap(mail, dic_file, progress):
    
    
    dic_cat = requirements(dic_file, progress)
    
    driver = login(mail)
    
    for row in tqdm(dic_cat.iterrows(), total=dic_cat.shape[0], desc="Scraping..."):
        
        # print(f"Scraping {row[1]['CODE ISIN']}")
        
        isin = row[1]["CODE ISIN"]
        input = driver.find_element(By.XPATH, '//*[@id="SearchInput"]')
        input.clear()    
        input.send_keys(isin + Keys.RETURN)
    
        
        tr_elements = driver.find_elements(By.XPATH, '/html/body/div[10]/div[3]/div[3]/table/tbody[2]/tr')
                
        if len(tr_elements) > 0:
            for tr in tr_elements:
                if (("KID" in tr.text) or ("PRIIP" in tr.text)) and ("Français" in tr.text):
                    # print(tr.find_element(By.XPATH, 'td[5]/a[2]').get_attribute("href"))
                    link = tr.find_element(By.XPATH, 'td[5]/a[2]').get_attribute("href")
                    # response = requests.get(link)
                    # if response.status_code == 200:
                    #     with open(f"../data/morningstar/{isin}.pdf", 'wb') as f:
                    #         f.write(response.content)
                    dic_cat.loc[row[0], "Morningstar"] = link
                    download_classic(driver, link, isin)
                    break
                # else:
                    # dic_cat.loc[row[0], "Morningstar"] = "Not Found"
            
        with open(progress, 'a') as f :
            f.write(f"{row[1]['CODE ISIN']} : {dic_cat.loc[row[0], 'Morningstar']}\n")
            
    if len(dic_cat[dic_cat["Morningstar"] == "Not Found"]) > 0:
        dic_cat = dic_cat[dic_cat["Morningstar"] == "Not Found"]
        dic_cat = scrap_geco(dic_cat, progress)
    
    return driver, dic_cat 

def scrap_geco(dic_cat, progress):    
        
    for row in tqdm(dic_cat.iterrows(), total=dic_cat.shape[0], desc='Scraping AMF GeCo'):
        code_isin = row[1]['CODE ISIN']
        url = f'https://geco.amf-france.org/Bio/res_doc.aspx?NomProd=&NomSOc=&varvalidform=on&action=new&TypeDoc=Notice&TYPEPROD=0&NumAgr=&CodePart={code_isin}&DateDebAgr=&DateFinAgr=&DateDeb=&DateFin=&valid_form=Lancer+la+recherche'
        response = requests.get(url)
        
        if ".pdf" in response.url :
            dic_cat.loc[row[0], "Morningstar"] = str(response.url)
            with open('progress.txt', 'a') as f: 
                f.write(f'{code_isin} : {response.url}\n')
            
            response = requests.get(response.url)
            with open(f"./data/morningstar/{code_isin}.pdf", 'wb') as f:
                f.write(response.content)
                
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
                # with open(progress, 'a') as f: 
                #     f.write(f'{code_isin} : {pdfs[0]}\n')
                response = requests.get(dic_cat.loc[row[0], "Morningstar"])
                if response.status_code == 200:
                    with open(f"./data/morningstar/{code_isin}.pdf", 'wb') as f:
                        f.write(response.content)
                
            else :
                dic_cat.loc[dic_cat['CODE ISIN'] == code_isin, 'Morningstar'] = "Not Found"
                with open(progress, 'a') as f: 
                    f.write(f'{code_isin} : No pdf\n')

    return dic_cat
    

def check_availability(isin):
    downloaded = os.listdir('./data/morningstar')
    not_available = []
    if f"{isin}.pdf" in downloaded:
        return True
    return False 