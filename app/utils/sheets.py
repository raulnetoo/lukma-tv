import os
import time
import gspread
import streamlit as st
from google.oauth2.service_account import Credentials
import pandas as pd

SCOPE = ["https://www.googleapis.com/auth/spreadsheets",
         "https://www.googleapis.com/auth/drive"]

@st.cache_resource(show_spinner=False)
def _client():
    creds_info = st.secrets["gcp_service_account"]
    creds = Credentials.from_service_account_info(creds_info, scopes=SCOPE)
    return gspread.authorize(creds)

@st.cache_resource(show_spinner=False)
def _sheet():
    client = _client()
    return client.open_by_key(st.secrets["gsheets"]["spreadsheet_id"])

def read_df(ws_name: str) -> pd.DataFrame:
    ws = _sheet().worksheet(ws_name)
    rows = ws.get_all_records()
    df = pd.DataFrame(rows)
    return df

def replace_df(ws_name: str, df: pd.DataFrame):
    ws = _sheet().worksheet(ws_name)
    ws.clear()
    if df.empty:
        ws.update([[]])
        return
    ws.update([df.columns.tolist()] + df.fillna("").values.tolist())

def append_row(ws_name: str, row: dict):
    ws = _sheet().worksheet(ws_name)
    headers = ws.row_values(1)
    values = [str(row.get(h, "")) for h in headers]
    ws.append_row(values, value_input_option="USER_ENTERED")

def upsert_row(ws_name: str, key_field: str, row: dict):
    """Atualiza se existir (por key_field), senão insere."""
    df = read_df(ws_name)
    if not df.empty and key_field in df.columns:
        idx = df.index[df[key_field].astype(str) == str(row[key_field])]
        if len(idx) > 0:
            for k, v in row.items():
                if k in df.columns:
                    df.loc[idx[0], k] = v
            replace_df(ws_name, df)
            return
    # insert
    append_row(ws_name, row)
