import streamlit as st
from streamlit_gsheets import GSheetsConnection
import os
import pandas as pd
import gspread 
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from googleapiclient.http import MediaFileUpload
import io
from googleapiclient.errors import HttpError
import json


def check_drive_availability(available_files, isin):
    if f'{isin}.pdf' in available_files:
        return True
    
def get_files(drive):
    files = []
    page_token = None
    while True:
        response = (
            drive.files()
            .list(
                q='"1cTvPKQ0MDJPRR9eve2i4llw7OqkreapI" in parents',
                spaces="drive",
                fields="nextPageToken, files(name, parents, id)",
                pageToken=page_token,
            ).execute()
        )
        # Process change
        # print(f'Found file: {file.get("name")}, {file.get("id")}')
        files.extend(response.get("files", []))
        page_token = response.get("nextPageToken", None)
        if page_token is None:
            break
    return files


def get_file(drive, isin):
    try :
        file = drive.files().list(q=f'name="{isin}.pdf"').execute()
        if len(file.get('files')) == 0:
            file = None
    except:
        file = None
    return file

def update_file(drive, file, new_file):
    media_content = MediaFileUpload(new_file, mimetype='application/pdf')
    print(file)
    updated_file = drive.files().update(fileId=file.get('files')[0].get('id'), media_body=media_content).execute()
    permissions = drive.permissions().create(
        fileId=updated_file.get('id'),
        body={
            "role": "reader",
            "type": "anyone",
        }
    ).execute()
    print(f'File updated : {updated_file.get("name")}')
    return updated_file

def create_file(drive, isin, new_file):
    media_content = MediaFileUpload(new_file, mimetype='application/pdf')
    file_metadata = {
        'name': f'{isin}.pdf',
        'parents': ['1cTvPKQ0MDJPRR9eve2i4llw7OqkreapI']
    }
    file = drive.files().create(body=file_metadata, media_body=media_content).execute()
    permissions = drive.permissions().create(
        fileId=file.get('id'),
        body={
            "role": "reader",
            "type": "anyone",
        }
    ).execute()
    print(f'File created : {file.get("name")}')
    return file


# def first_scrap():
#     scope = ['https://www.googleapis.com/auth/drive']
#     credentials = service_account.Credentials.from_service_account_info(
#                                 info=dict(st.secrets['connections']['gsheets']), 
#                                 scopes=scope)
#     drive = build('drive', 'v3', credentials=credentials)

#     files = get_files(drive)
    
#     available_files = [file.get("name") for file in files]
#     # print(available_files, len(available_files))
    
    
#     conn = st.connection("gsheets", type=GSheetsConnection)
#     df = conn.read(
#             worksheet="Liste des fonds",
#             ttl="2m"
#             # usecols=[0, 2, 3, 4],
#             # skiprows = skip_rows
#         )
        
#     sheet_df = df
    
#     isins = df[df.columns[0]].dropna().tolist()
    
#     for isin in isins:
#         if check_drive_availability(available_files, isin):
#             sheet_df.loc[sheet_df[sheet_df.columns[0]] == isin, sheet_df.columns[3]] = True
#             sheet_df.loc[sheet_df[sheet_df.columns[0]] == isin, sheet_df.columns[2]] = pd.to_datetime('today').year
#             #Find the id of the file where name is isin.pdf in files
#             for file in files:
#                 if file.get("name") == f'{isin}.pdf':
#                     sheet_df.loc[sheet_df[sheet_df.columns[0]] == isin, sheet_df.columns[4]] = f'https://drive.google.com/file/d/{file.get("id")}/view?usp=sharing'
#                     # response_permission = drive.permissions().create(
#                     #     fileId=file.get("id"),
#                     #     body={
#                     #         "role": "reader",
#                     #         "type": "anyone",
#                     #     }
#                     # ).execute()
#                     break
                
#     df = conn.update(
#         worksheet="Liste des fonds",
#         data=sheet_df
#     )    
    
#     print(df.dropna(subset=[df.columns[0]]))
#     return
    