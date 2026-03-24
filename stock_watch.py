import pandas as pd
import yfinance as yf
import altair as alt
import streamlit as st

st.title('Stock watcher app')

st.sidebar.write("""
#GAFA price
This is GAFA price watcher. Show the term from the following options.
""")

st.sidebar.write("""
## Date options
""")

days = st.sidebar.slider('日数', 1, 50, 20)

st.write(f"""
    ### The latest {days} days' GAFA price
""")


@st.cache_data
def get_data(days, tickers):
    df = pd.DataFrame()
    for company in tickers.keys():
        # company ='Facebook'
        tkr = yf.Ticker(tickers[company])
        hist = tkr.history(period=f'{days}d')
        hist.index = hist.index.strftime('%d %B %Y')
        hist = hist[['Close']]
        hist.columns = [company]
        hist = hist.T
        hist.index.name = 'Name'
        df = pd.concat([df, hist])
    return df


st.sidebar.write("""
## Select stock range
""")

ymin, ymax = st.sidebar.slider(
    'Please select the range.',
    0.0, 3500.0, (0.0, 3500.0)
)

tickers = {
    'apple': 'AAPL',
    'facebook': 'META',
    'google': 'GOOGL',
    'microsoft': 'MSFT',
    'netflix': 'NFLX',
    'amazon': 'AMZN'
}
df = get_data(days, tickers)
companies = st.multiselect(
    'Please select companies',
    list(df.index),
    ['google', 'amazon', 'facebook', 'apple']
)

if not companies:
    st.error('Please select one company at least.')
else:
    data = df.loc[companies]
    st.write("### stock price(USD)", data.sort_index())
    data = data.T.reset_index()
    data= pd.melt(data, id_vars=['Date']).rename(
    columns={'value': 'Stock prices(USD)'}
    )