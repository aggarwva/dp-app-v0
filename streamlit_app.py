import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime

# Load sample data
@st.cache_data
def load_data():
    df = pd.read_csv("DryPowder_Portfolio_Latest.csv")
    df = df[df['Symbol'] != 'SPAXX**']  # exclude cash
    df['Purchase Date'] = pd.to_datetime(df['Purchase Date'])

    # Fetch SPY historical prices
    spy = yf.Ticker("SPY")
    today = datetime.today().strftime('%Y-%m-%d')
    spy_hist = spy.history(start='2024-01-01', end=today)

    # Calculate SPY return since each purchase
    def get_spy_return(purchase_date):
        try:
            spy_start = spy_hist.loc[spy_hist.index >= purchase_date].iloc[0]['Close']
            spy_end = spy_hist['Close'].iloc[-1]
            return (spy_end - spy_start) / spy_start
        except:
            return None

    df['SPY Return'] = df['Purchase Date'].apply(get_spy_return)
    df['Cost Basis'] = pd.to_numeric(df['Cost Basis Total'], errors='coerce')
    df['Current Price'] = pd.to_numeric(df['Current Value'], errors='coerce')
    df['Stock Return'] = (df['Current Price'] - df['Cost Basis']) / df['Cost Basis']
    df['Alpha vs SPY'] = df['Stock Return'] - df['SPY Return']

    return df

# UI
st.title("DryPowder Portfolio Tracker")
df = load_data()

# Dropdown for Expected Hold Duration
duration_options = ['< 1 year', '1–3 years', '3–5 years', '5+ years']
for i in df.index:
    df.at[i, 'Expected Hold Duration'] = st.selectbox(
        f"{df.at[i, 'Symbol']} - Hold Duration", duration_options, 
        index=duration_options.index(df.at[i, 'Expected Hold Duration']) if df.at[i, 'Expected Hold Duration'] in duration_options else 0,
        key=f"duration_{i}"
    )
    df.at[i, 'Target Price'] = st.number_input(f"{df.at[i, 'Symbol']} - Target Price", value=df.at[i, 'Target Price'] or 0.0, key=f"target_{i}")
    df.at[i, 'Stop Loss Price'] = st.number_input(f"{df.at[i, 'Symbol']} - Stop Loss", value=df.at[i, 'Stop Loss Price'] or 0.0, key=f"stop_{i}")

# Display Alpha vs SPY
def highlight_alpha(val):
    if pd.isna(val):
        return ''
    color = 'green' if val > 0 else 'red'
    return f'color: {color}'

styled_df = df[['Symbol', 'Current Price', 'Cost Basis', 'Stock Return', 'SPY Return', 'Alpha vs SPY']].style.applymap(highlight_alpha, subset=['Alpha vs SPY'])
st.subheader("Performance vs. S&P 500")
st.dataframe(styled_df, use_container_width=True)

# Save
if st.button("Save Changes"):
    df.to_csv("Updated_Portfolio.csv", index=False)
    st.success("Saved!")
