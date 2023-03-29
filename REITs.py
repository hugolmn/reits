import streamlit as st
import requests
import pandas as pd
import numpy as np
import altair as alt
import gspread
from google.oauth2 import service_account

@st.cache_data(ttl=60*60*24)
def load_vnq_data():
    response = requests.get('https://investor.vanguard.com/investment-products/etfs/profile/api/VNQ/portfolio-holding/stock')
    df = pd.DataFrame(response.json()['fund']['entity'])
    price = float(requests.get('https://investor.vanguard.com/investment-products/etfs/profile/api/VNQ/price').json()['currentPrice']['dailyPrice']['market']['price'])
    return df, price

@st.cache_data(ttl=60*60*24)
def load_reit_data():
    scope = ['https://www.googleapis.com/auth/drive.readonly']
    credentials = service_account.Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
    
    gc = gspread.authorize(credentials)
    sh = gc.open_by_key('1seihTYT_rqahm0X3DAT2C1lzMcORvvFghFk35fOavLY')
    area = pd.DataFrame(sh.worksheet('Data').get_all_records())
    shares = pd.DataFrame(sh.worksheet('Stock').get_all_records())
    return area, shares

@st.cache_data(ttl=60*60*24)
def load_data():
    df, price = load_vnq_data()
    area, shares = load_reit_data()
    df = pd.merge(
        left=df,
        right=area.merge(shares, on='Ticker'),
        left_on='ticker',
        right_on='Ticker'
    )
    return df, price


st.title('REITs')
n_shares = st.slider('VNQ Shares', min_value=1, max_value=1000, value=100)

df, price = load_data()

df['Owned'] = n_shares * price * df.percentWeight.astype(float) / 100 / df.MarketCap * df.Value
aggregated_df = df.groupby(['Type', 'Unit']).Owned.sum()

# st.dataframe(df)

for index, row in aggregated_df.to_frame().iterrows():
    st.metric(label=index[0], value=f"{row.Owned:.5f} {index[1]}")

