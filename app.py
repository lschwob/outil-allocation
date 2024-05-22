import streamlit as st
from streamlit_gsheets import GSheetsConnection
import os
import pandas as pd
from notebooks.scripts.scraping import requirements, login, download_classic, download_from_progress, scrap, check_availability


def main():
    
    # print('First run')
    pwd = os.getcwd()
    # print(pwd)
    st.title('Outil d\'allocation ALTI')
    conn = st.connection("gsheets", type=GSheetsConnection)
    return conn

def scrap_app(mail, dic_file, progress):
    driver, dic_cat = scrap(mail, dic_file, progress)
    st.session_state.scrap = True
    st.session_state.driver = driver
    st.session_state.dic_cat = dic_cat
    return driver, dic_cat

def show_isin():
    st.session_state.show_isin = True
    return None

if __name__ == "__main__":
    conn = main()
    
    st.write('Liste des ISINs des allocations proposées :')
    not_available = []
    
    st.sidebar.header('Paramètres de l\'outil')
    col = st.sidebar.number_input('Numéro de la colonne à rechercher', value=5)
    skip_rows = st.sidebar.number_input('Première ligne à lire', value=7) - 1
    
   
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
            worksheet="Arbitrage",
            ttl="0",
            usecols=[col],
            skiprows = skip_rows
        )

        df = df.dropna()

        isins = list(df.iloc[:, 0])
        
        data_df = pd.DataFrame(
            {
                "ISINs" : [isins[i:i+5] for i in range(0, len(isins), 5)],
            }
        )
        
        
        st.data_editor(
            data_df,
            column_config={
                "ISINs": st.column_config.ListColumn(
                    "Liste des ISINs",
                    width="large",
                ),
            },
            hide_index=True,
        )
        
        # print(os.getcwd())
        
        
        for isin in isins:
            if not check_availability(isin):
                not_available.append(isin)
    
    
    # print(st.session_state.scrap, '_________________________________________________________')

    if len(not_available) > 0:
        st.write('Fiches non disponibles dans la base de données :')
        st.write(not_available)
        
        with st.form(key='my_form'):
            st.form_submit_button('Scraper les fiches manquantes', on_click=scrap_app, args=('piron85023@lucvu.com', not_available, 'new_progress.txt'))
            st.info('Cette action peut prendre du temps...', icon="ℹ️")
            st.warning('Si vous n\'observez pas de changement dans les fiches manquantes après exécution du scraping cela signifie que les fiches ne sont pas disponibles sur Morningstar (ni sur GeCo de l\'AMF).', icon="⚠️")

            if st.session_state.scrap:
                for isin in not_available:
                    if check_availability(isin):
                        not_available.remove(isin)
                
                st.write('Fiches manquantes après scraping :')
                st.write(not_available)