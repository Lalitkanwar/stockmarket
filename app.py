import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import ta
from sklearn.linear_model import LogisticRegression
from datetime import datetime
import requests
import urllib.parse

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="Nexus | Pro Finance",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- SESSION STATE INITIALIZATION ---
if 'portfolio' not in st.session_state:
    st.session_state.portfolio = {}
if 'watchlist' not in st.session_state:
    st.session_state.watchlist = []

# --- CUSTOM CSS ---
st.markdown("""
<style>
    /* Dark Theme Fintech Colors & Mobile Responsiveness */
    .stApp { background-color: #0B0E14; color: #F0F2F6; }
    [data-testid="stSidebar"] { background-color: #131722; border-right: 1px solid #2A2E39; }
    
    /* Metrics & Cards */
    div[data-testid="metric-container"], .custom-card {
        background-color: #1E222D;
        border: 1px solid #2A2E39;
        padding: 20px;
        border-radius: 8px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.2);
    }
    
    /* News Article Styling */
    .news-card {
        background-color: #1E222D;
        border-left: 4px solid #2962FF;
        padding: 15px;
        margin-bottom: 15px;
        border-radius: 4px;
        transition: transform 0.2s;
    }
    .news-card:hover { transform: translateX(5px); }
    .news-title { font-size: 18px; font-weight: bold; color: #E0E3EB; text-decoration: none; }
    .news-title:hover { color: #2962FF; }
    .news-publisher { font-size: 12px; color: #8A93A6; margin-bottom: 5px; }
    
    /* Headers */
    h1, h2, h3, h4 { color: #D1D4DC !important; font-family: 'Inter', sans-serif; }
    
    /* Form Inputs */
    .stTextInput>div>div>input, .stSelectbox>div>div>div, .stNumberInput>div>div>input {
        background-color: #131722;
        color: #D1D4DC;
        border: 1px solid #2A2E39;
    }
    
    /* AI Insights Card */
    .ai-card {
        background: linear-gradient(145deg, #1E222D, #262B38);
        border: 1px solid #2A2E39;
        padding: 20px;
        border-radius: 8px;
        height: 100%;
    }
    
    /* Typography colors for signals */
    .bullish { color: #089981; font-weight: bold; }
    .bearish { color: #F23645; font-weight: bold; }
    .neutral { color: #B2B5BE; font-weight: bold; }
    
    /* Footer */
    .footer {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background-color: #131722;
        color: #8A93A6;
        text-align: center;
        padding: 10px;
        font-size: 12px;
        border-top: 1px solid #2A2E39;
        z-index: 999;
    }
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR NAVIGATION ---
st.sidebar.title("🏦 Nexus Finance")
st.sidebar.markdown("---")

page = st.sidebar.radio("Navigation", [
    "📈 Live Market", 
    "💼 My Portfolio", 
    "📰 Market News", 
    "ℹ️ About"
])

st.sidebar.markdown("---")
# Watchlist Sidebar Section
st.sidebar.markdown("### ⭐ Watchlist")
if not st.session_state.watchlist:
    st.sidebar.info("Your watchlist is empty.")
else:
    for w_ticker in st.session_state.watchlist:
        col1, col2 = st.sidebar.columns([3, 1])
        col1.markdown(f"<div style='display:flex;align-items:center;gap:10px;margin-bottom:10px;'>{get_company_logo_html(w_ticker, 32)} <b>{w_ticker}</b></div>", unsafe_allow_html=True)
        if col2.button("❌", key=f"del_watch_{w_ticker}", help="Remove from Watchlist"):
            st.session_state.watchlist.remove(w_ticker)
            st.rerun()

# --- HELPER FUNCTIONS WITH ERROR HANDLING ---
def get_company_logo_html(ticker, size=40):
    if "logo_cache" not in st.session_state:
        st.session_state["logo_cache"] = {}
        
    if ticker not in st.session_state["logo_cache"]:
        logo_url = None
        
        # Step 1: Clearbit
        try:
            stock = yf.Ticker(ticker)
            website = stock.info.get("website", "")
            if website:
                if "://" not in website: website = "http://" + website
                domain = urllib.parse.urlparse(website).netloc.replace("www.", "")
                if domain:
                    test_url = f"https://logo.clearbit.com/{domain}"
                    if requests.head(test_url, timeout=2).status_code == 200:
                        logo_url = test_url
        except: pass
        
        # Step 2: FMP
        if not logo_url:
            try:
                test_url = f"https://financialmodelingprep.com/image-stock/{ticker}.png"
                if requests.head(test_url, timeout=2).status_code == 200:
                    logo_url = test_url
            except: pass
            
        # Step 3: EODHD
        if not logo_url:
            try:
                test_url = f"https://eodhd.com/img/logos/US/{ticker}.png"
                if requests.head(test_url, timeout=2).status_code == 200:
                    logo_url = test_url
            except: pass
            
        st.session_state["logo_cache"][ticker] = logo_url

    logo_url = st.session_state["logo_cache"][ticker]
    style = f"width: {size}px; height: {size}px; border-radius: 50%; border: 2px solid #00d4ff; box-shadow: 0 0 10px rgba(0,212,255,0.3); object-fit: cover; display: inline-block; vertical-align: middle; flex-shrink: 0;"
    
    if logo_url:
        return f'<img src="{logo_url}" style="{style}" alt="{ticker}">'
    else:
        initials = ticker[:2].upper()
        return f'<div style="{style} background-color: #1E222D; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold; font-size: {max(10, size//2.5)}px;">{initials}</div>'

@st.cache_data(ttl=300, show_spinner=False)
def get_stock_data(ticker, period, interval):
    """Fetches historical stock data with robust error handling."""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        if not info or ('regularMarketPrice' not in info and 'currentPrice' not in info and 'previousClose' not in info):
            return None, None, None
            
        hist = stock.history(period=period, interval=interval)
        hist_ml = stock.history(period="2y", interval="1d") # Data for ML
        
        if hist.empty or hist_ml.empty:
            return info, pd.DataFrame(), pd.DataFrame()
            
        return info, hist, hist_ml
    except Exception as e:
        return None, None, None

@st.cache_data(ttl=60, show_spinner=False)
def get_live_price(ticker):
    """Fetches the latest closing price."""
    try:
        stock = yf.Ticker(ticker)
        todays_data = stock.history(period='1d')
        if not todays_data.empty:
            return todays_data['Close'].iloc[-1]
        return 0.0
    except:
        return 0.0

@st.cache_data(ttl=900, show_spinner=False)
def get_news(ticker):
    """Fetches latest news articles."""
    try:
        stock = yf.Ticker(ticker)
        return stock.news
    except:
        return []

# --- PAGE ROUTING ---

try:
    if page == "📈 Live Market":
        st.title("Live Market Analysis")
        
        col1, col2 = st.columns([2, 1])
        with col1:
            ticker_symbol = st.text_input("Search Ticker (e.g., AAPL, NVDA, TSLA)", value="AAPL").upper()
        with col2:
            timeframe = st.selectbox("Timeframe", ["1 Day", "1 Week", "1 Month", "6 Months", "1 Year"], index=2)
            
        tf_mapping = {
            "1 Day": {"period": "1d", "interval": "5m"},
            "1 Week": {"period": "5d", "interval": "15m"},
            "1 Month": {"period": "1mo", "interval": "1d"},
            "6 Months": {"period": "6mo", "interval": "1d"},
            "1 Year": {"period": "1y", "interval": "1d"},
        }
        
        if ticker_symbol:
            # Watchlist Add Button
            if ticker_symbol not in st.session_state.watchlist:
                if st.button(f"⭐ Add {ticker_symbol} to Watchlist"):
                    st.session_state.watchlist.append(ticker_symbol)
                    st.rerun()
            else:
                st.button(f"⭐ {ticker_symbol} is in Watchlist", disabled=True)
                
            with st.spinner(f"Analyzing {ticker_symbol} market data..."):
                period = tf_mapping[timeframe]["period"]
                interval = tf_mapping[timeframe]["interval"]
                info, hist, hist_ml = get_stock_data(ticker_symbol, period, interval)
                
            if info is None:
                st.error(f"❌ Could not find data for '{ticker_symbol}'. Please verify the ticker symbol is correct.")
            elif hist is not None and not hist.empty:
                # Display Header Metrics
                company_name = info.get("longName", ticker_symbol)
                st.markdown(f"<div style='display:flex; align-items:center; gap:20px; margin-bottom:20px;'>{get_company_logo_html(ticker_symbol, 120)}<div><h2 style='margin:0;'>{company_name}</h2><h4 style='margin:0; color:#8A93A6;'>{ticker_symbol}</h4></div></div>", unsafe_allow_html=True)
                
                current_price = info.get("currentPrice") or info.get("regularMarketPrice", hist['Close'].iloc[-1])
                previous_close = info.get("previousClose", hist['Open'].iloc[0])
                price_change = current_price - previous_close
                pct_change = (price_change / previous_close) * 100 if previous_close else 0.0
                
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Live Price", f"${current_price:,.2f}", f"{price_change:,.2f} ({pct_change:.2f}%)")
                c2.metric("Day High", f"${info.get('dayHigh', hist['High'].max()):,.2f}")
                c3.metric("Day Low", f"${info.get('dayLow', hist['Low'].min()):,.2f}")
                vol = info.get("volume", hist['Volume'].iloc[-1])
                c4.metric("Volume", f"{vol:,.0f}")
                
                # --- AI Insights Section ---
                st.markdown("---")
                st.markdown("### 🤖 AI-Powered Insights")
                
                if hist_ml is not None and not hist_ml.empty and len(hist_ml) > 50:
                    hist_ml['RSI'] = ta.momentum.RSIIndicator(hist_ml['Close'], window=14).rsi()
                    hist_ml['MACD'] = ta.trend.MACD(hist_ml['Close']).macd()
                    hist_ml['Target'] = (hist_ml['Close'].shift(-1) > hist_ml['Close']).astype(int)
                    
                    ml_df = hist_ml.dropna()
                    if len(ml_df) > 10:
                        model = LogisticRegression()
                        model.fit(ml_df[['RSI', 'MACD']], ml_df['Target'])
                        
                        latest_rsi = ml_df['RSI'].iloc[-1]
                        latest_macd = ml_df['MACD'].iloc[-1]
                        prob_bullish = model.predict_proba([[latest_rsi, latest_macd]])[0][1]
                        
                        if prob_bullish > 0.55:
                            prediction, pred_class, suggestion, sug_class = "🐂 BULLISH", "bullish", "BUY", "bullish"
                        elif prob_bullish < 0.45:
                            prediction, pred_class, suggestion, sug_class = "🐻 BEARISH", "bearish", "SELL", "bearish"
                        else:
                            prediction, pred_class, suggestion, sug_class = "⚖️ NEUTRAL", "neutral", "HOLD", "neutral"
                            
                        ac1, ac2, ac3 = st.columns(3)
                        with ac1:
                            st.markdown(f"<div class='ai-card'><h4 style='margin-top:0;'>Trend Prediction</h4><div class='{pred_class}' style='font-size:18px;'>{prediction}</div><div style='font-size:14px; margin-bottom:10px;'>Confidence: {prob_bullish*100:.1f}%</div><hr style='border-color:#364156; margin: 10px 0;'><div>Action: <span class='{sug_class}' style='font-size:20px;'>{suggestion}</span></div></div>", unsafe_allow_html=True)
                        with ac2:
                            sentiment = "Oversold" if latest_rsi < 30 else ("Overbought" if latest_rsi > 70 else "Neutral")
                            sent_class = "bullish" if latest_rsi < 30 else ("bearish" if latest_rsi > 70 else "neutral")
                            st.markdown(f"<div class='ai-card'><h4 style='margin-top:0;'>Momentum</h4><div class='{sent_class}' style='font-size:18px;'>{sentiment} Bias</div><div style='margin-top:10px;'>MACD Signal: {'Positive' if latest_macd>0 else 'Negative'}</div></div>", unsafe_allow_html=True)
                        with ac3:
                            st.markdown(f"<div class='ai-card'><h4 style='margin-top:0;'>Key Levels</h4><div>RSI (14): <span style='color: {'#F23645' if latest_rsi > 70 else ('#089981' if latest_rsi < 30 else '#F0F2F6')}'>{latest_rsi:.1f}</span></div><div>MACD: <span style='color: {'#089981' if latest_macd > 0 else '#F23645'}'>{latest_macd:.2f}</span></div></div>", unsafe_allow_html=True)
                
                # --- Interactive Chart ---
                st.markdown("---")
                st.subheader("Technical Chart")
                fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.7, 0.3])
                
                fig.add_trace(go.Candlestick(x=hist.index, open=hist['Open'], high=hist['High'], low=hist['Low'], close=hist['Close'], name='Price', increasing_line_color='#089981', decreasing_line_color='#F23645'), row=1, col=1)
                
                hist['20_DMA'] = hist['Close'].rolling(window=20).mean()
                fig.add_trace(go.Scatter(x=hist.index, y=hist['20_DMA'], line=dict(color='#2962FF', width=1.5), name='20 DMA'), row=1, col=1)
                
                colors = ['#089981' if row['Close'] >= row['Open'] else '#F23645' for _, row in hist.iterrows()]
                fig.add_trace(go.Bar(x=hist.index, y=hist['Volume'], marker_color=colors, name='Volume'), row=2, col=1)
                
                fig.update_layout(template='plotly_dark', paper_bgcolor='#131722', plot_bgcolor='#131722', xaxis_rangeslider_visible=False, height=600, margin=dict(l=0, r=0, t=10, b=0))
                if interval in ["1d", "1wk", "1mo"]:
                    fig.update_xaxes(rangebreaks=[dict(bounds=["sat", "mon"])])
                fig.update_xaxes(showticklabels=False, row=1, col=1)
                st.plotly_chart(fig, use_container_width=True)

    elif page == "💼 My Portfolio":
        st.title("Portfolio Management & P/L")
        
        # --- Buy/Sell Simulator Form ---
        with st.expander("➕ Execute Trade (Simulator)", expanded=True):
            tc1, tc2, tc3, tc4 = st.columns(4)
            trade_ticker = tc1.text_input("Ticker Symbol").upper()
            trade_action = tc2.selectbox("Action", ["Buy", "Sell"])
            trade_shares = tc3.number_input("Shares", min_value=0.01, value=1.0, step=1.0)
            trade_price = tc4.number_input("Execution Price ($)", min_value=0.01, value=100.0, step=1.0)
            
            if st.button("Execute Trade"):
                if trade_ticker:
                    port = st.session_state.portfolio
                    if trade_action == "Buy":
                        if trade_ticker in port:
                            old_shares = port[trade_ticker]['shares']
                            old_cost = port[trade_ticker]['avg_cost']
                            new_shares = old_shares + trade_shares
                            new_cost = ((old_shares * old_cost) + (trade_shares * trade_price)) / new_shares
                            port[trade_ticker] = {'shares': new_shares, 'avg_cost': new_cost}
                        else:
                            port[trade_ticker] = {'shares': trade_shares, 'avg_cost': trade_price}
                        st.success(f"Successfully bought {trade_shares} shares of {trade_ticker}!")
                    elif trade_action == "Sell":
                        if trade_ticker in port and port[trade_ticker]['shares'] >= trade_shares:
                            port[trade_ticker]['shares'] -= trade_shares
                            if port[trade_ticker]['shares'] <= 0:
                                del port[trade_ticker]
                            st.success(f"Successfully sold {trade_shares} shares of {trade_ticker}!")
                        else:
                            st.error("Not enough shares to sell.")
                    st.rerun()
                    
        st.markdown("---")
        
        # --- Portfolio Display & Math ---
        port = st.session_state.portfolio
        if not port:
            st.info("Your portfolio is empty. Execute a simulated trade above to get started.")
        else:
            st.subheader("Holdings & Performance")
            
            total_cost = 0.0
            total_value = 0.0
            portfolio_data = []
            
            with st.spinner("Fetching live prices for your holdings..."):
                for ticker, data in port.items():
                    shares = data['shares']
                    avg_cost = data['avg_cost']
                    cost_basis = shares * avg_cost
                    
                    live_price = get_live_price(ticker)
                    if live_price == 0.0:
                        live_price = avg_cost # Fallback if API fails
                        
                    current_value = shares * live_price
                    
                    pl_usd = current_value - cost_basis
                    pl_pct = (pl_usd / cost_basis) * 100 if cost_basis > 0 else 0
                    
                    total_cost += cost_basis
                    total_value += current_value
                    
                    portfolio_data.append({
                        "Asset": f"<div style='display:flex;align-items:center;gap:10px;'>{get_company_logo_html(ticker, 32)} <b>{ticker}</b></div>",
                        "Ticker": ticker,
                        "Shares": round(shares, 4),
                        "Avg Cost": avg_cost,
                        "Current Price": live_price,
                        "Total Value": current_value,
                        "P/L ($)": pl_usd,
                        "P/L (%)": pl_pct
                    })
                
            df_port = pd.DataFrame(portfolio_data)
            
            # Display Summary Totals
            total_pl_usd = total_value - total_cost
            total_pl_pct = (total_pl_usd / total_cost) * 100 if total_cost > 0 else 0
            
            c1, c2, c3 = st.columns(3)
            c1.metric("Total Invested", f"${total_cost:,.2f}")
            c2.metric("Current Portfolio Value", f"${total_value:,.2f}", f"{total_pl_usd:,.2f} ({total_pl_pct:.2f}%)")
            
            # Display Table
            html_table = df_port.drop(columns=['Ticker']).style.format({
                "Avg Cost": "${:.2f}",
                "Current Price": "${:.2f}",
                "Total Value": "${:.2f}",
                "P/L ($)": "${:.2f}",
                "P/L (%)": "{:.2f}%"
            }).map(lambda x: 'color: #089981' if x > 0 else ('color: #F23645' if x < 0 else ''), subset=['P/L ($)', 'P/L (%)']).hide(axis="index").to_html(escape=False)
            st.markdown(f"<div style='width:100%; overflow-x:auto; margin-bottom:20px;'><style>table {{width:100%; border-collapse:collapse; color:#F0F2F6;}} th, td {{padding:12px; text-align:left; border-bottom:1px solid #2A2E39;}} th {{background-color:#1E222D;}}</style>{html_table}</div>", unsafe_allow_html=True)
            
            # Display Plotly Pie Chart
            st.markdown("### Asset Allocation")
            fig_pie = px.pie(df_port, values='Total Value', names='Ticker', hole=0.4,
                             color_discrete_sequence=px.colors.qualitative.Pastel)
            fig_pie.update_traces(textposition='inside', textinfo='percent+label')
            fig_pie.update_layout(template='plotly_dark', paper_bgcolor='#131722', plot_bgcolor='#131722', height=450, margin=dict(t=30, b=30))
            st.plotly_chart(fig_pie, use_container_width=True)

    elif page == "📰 Market News":
        st.title("Latest Financial News")
        
        news_ticker = st.text_input("Enter Ticker to fetch news (e.g., TSLA, MSFT)", value="AAPL").upper()
        
        if news_ticker:
            with st.spinner(f"Fetching latest news for {news_ticker}..."):
                news_items = get_news(news_ticker)
                
            if not news_items:
                st.warning(f"No recent news found for {news_ticker} via yfinance API. The symbol may be incorrect or news is unavailable.")
            else:
                for item in news_items[:10]:
                    title = item.get('title', 'No Title')
                    publisher = item.get('publisher', 'Unknown Publisher')
                    link = item.get('link', '#')
                    
                    pub_time = item.get('providerPublishTime')
                    date_str = ""
                    if pub_time:
                        date_str = datetime.fromtimestamp(pub_time).strftime('%Y-%m-%d %H:%M')
                    
                    st.markdown(f"""
                    <div class="news-card">
                        <div class="news-publisher">{publisher} &bull; {date_str}</div>
                        <a href="{link}" target="_blank" class="news-title">{title}</a>
                    </div>
                    """, unsafe_allow_html=True)

    elif page == "ℹ️ About":
        st.title("About Nexus Finance")
        st.markdown("""
        Welcome to **Nexus Finance** - A production-ready, AI-powered stock market application.
        
        ### Key Features:
        - **Real-Time Data Engine:** Uses `yfinance` to fetch live prices and market data with built-in request caching for high performance.
        - **Machine Learning Integration:** Uses Scikit-Learn Logistic Regression to predict bullish/bearish trends.
        - **Portfolio Manager:** Session-state driven system to track investments and calculate real-time Profit & Loss.
        - **Responsive UI:** Custom CSS ensuring mobile responsiveness and a premium dark mode aesthetic.
        
        *Built with Python, Streamlit, Plotly, and scikit-learn.*
        """)

except Exception as e:
    st.error(f"An unexpected error occurred: {str(e)}")
    st.info("Please refresh the page or try a different stock ticker.")

# --- FOOTER ---
st.markdown('<div class="footer">© 2026 Nexus Finance. All rights reserved. Data provided by yfinance. Not financial advice.</div>', unsafe_allow_html=True)
