import streamlit as st
from streamlit_gsheets import GSheetsConnection
import os
import pandas as pd
from notebooks.scripts.scraping import requirements, login, download_classic, download_from_progress, scrap, check_availability
from notebooks.scripts.drive import get_files, update_file, create_file, get_file
import gspread 
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from googleapiclient.http import MediaFileUpload
import io
from googleapiclient.errors import HttpError
import json
import time
    

def main():
    # first_scrap()
    
    # print('First run')
    pwd = os.getcwd()
    scope = ['https://www.googleapis.com/auth/drive']
    credentials = service_account.Credentials.from_service_account_info(
                                info=dict(st.secrets['connections']['gsheets']), 
                                scopes=scope)
    drive = build('drive', 'v3', credentials=credentials)
    st.title('Outil d\'allocation ALTI')
    conn = st.connection("gsheets", type=GSheetsConnection)
    
    return conn, drive

def scrap_app(mail, dic_file, progress, confirm_message, drive):
    if confirm_message != 'Confirmer':
        st.error('Veuillez écrire "Confirmer" pour lancer le scraping')
        return None
    st.session_state.scrap = True
    
    # return True
    
    driver, dic_cat = scrap(mail, dic_file, progress, drive)
    st.session_state.driver = driver
    # st.code(driver.page_source)
    st.session_state.dic_cat = dic_cat
    return driver, dic_cat

def show_isin():
    st.session_state.show_isin = True
    return None

if __name__ == "__main__":
    conn_drive = main()
    conn = conn_drive[0]
    drive = conn_drive[1]
    
    st.write('Liste des ISINs des allocations proposées :')
    not_available = []
    
    st.sidebar.header('Paramètres de l\'outil')
    col = st.sidebar.number_input('Numéro de la colonne à rechercher', value=0)
    skip_rows = st.sidebar.number_input('Première ligne à lire', value=4) - 1
    year = st.sidebar.number_input('Année', value=2024, step=1)
    
   
    if 'show_isin' not in st.session_state:
        st.session_state.show_isin = False
    
    if 'driver' not in st.session_state:
        st.session_state.driver = ''
        
    if 'dic_cat' not in st.session_state:
        st.session_state.dic_cat = ''
        
    if 'scrap' not in st.session_state:
        st.session_state.scrap = False
    
    st.button('Afficher les Codes', on_click=show_isin)
        
    if st.session_state.show_isin:    
        df = conn.read(
            worksheet="ISIN_DIC_URL",
            ttl="1m"
            # usecols=[0, 2, 3, 4],
            # skiprows = skip_rows
        )
        
        sheet_df = df
        df = df.iloc[skip_rows:, [0, 2, 3, 4]]
        df.rename(columns={df.columns[0]: 'CODE ISIN', df.columns[1]: 'Date', df.columns[2]: 'Disponibilité', df.columns[3]: 'URL'}, inplace=True)
        df.dropna(subset=[df.columns[0]], inplace=True)
        df['Date'] = df['Date'].astype(str)

        df_toscrap = df[(~df['Date'].str.contains(str(year))) & ((df['Disponibilité'] == False) | (df['Disponibilité'].isnull()))]
        

        isins = list(df_toscrap.iloc[:, 0])
        
        
        data_df = pd.DataFrame(
            {
                "ISINs" : [isins[i:i+50] for i in range(0, len(isins), 50)],
            }
        )
        
        
        st.data_editor(
            data_df,
            column_config={
                "ISINs": st.column_config.ListColumn(
                    "Liste des ISINs à récupérer",
                    width="large",
                ),
            },
            hide_index=True,
        )
        
        # print(os.getcwd())
        
        
        # for row in df_toscrap.iterrows():
        #     if not check_availability(row[1]['ISINs']):
        #         not_available.append(row[1]['ISINs'])
    
    

        # if len(not_available) > 0:
        st.write(f'Nombre de fiches à récupérer : {df_toscrap.shape[0]}')
        # st.write(not_available)

        
        with st.popover("Lancer le scraping"):
            with st.form(key='my_form'):
                confirm_message = st.text_input('Ecrivez "Confirmer" pour lancer le scraping')
                st.error('En confirmant toutes les fiches ne datant pas de l\'année indiquée seront écrasées', icon="⚠️")
                print(time.time())
                heure_lancement = time.time()
                st.form_submit_button('Scraper les fiches manquantes', on_click=scrap_app, args=('piron85023@lucvu.com', df_toscrap, 'new_progress.txt', confirm_message, drive))
                st.info('Cette action peut prendre du temps...', icon="ℹ️")
                # st.warning('Si vous n\'observez pas de changement dans les fiches manquantes après exécution du scraping cela signifie que les fiches ne sont pas disponibles sur Morningstar (ni sur GeCo de l\'AMF).', icon="⚠️")

                if st.session_state.scrap:
                    
                    df_scraped = st.session_state.dic_cat
                    print(df_scraped)
                    
                    for row in df_scraped.iterrows():
                        sheet_df.loc[sheet_df[sheet_df.columns[0]] == row[1]['CODE ISIN'], sheet_df.columns[2]] = row[1]['Date']
                        sheet_df.loc[sheet_df[sheet_df.columns[0]] == row[1]['CODE ISIN'], sheet_df.columns[3]] = row[1]['Disponibilité']
                        sheet_df.loc[sheet_df[sheet_df.columns[0]] == row[1]['CODE ISIN'], sheet_df.columns[4]] = row[1]['URL']
                    
                    print(sheet_df)
                    df = conn.update(
                        worksheet="ISIN_DIC_URL",
                        data=sheet_df
                    )
                    
                    st.cache_data.clear()
                    # st.experimental_rerun()
                    
                    st.write('Fiches manquantes après scraping :')
                    st.write(not_available)
                    heure_fin = time.time()
                    print(time.time())
                    print(f'Temps d\'exécution : {heure_fin - heure_lancement}')