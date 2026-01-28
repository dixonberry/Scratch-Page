import streamlit as st
import yfinance as yf
import pandas as pd
import requests
import time

# --- Page Config ---
st.set_page_config(page_title="Market Insights", page_icon="📈", layout="wide")

# --- CSS Styles ---
st.markdown("""
    <style>
    .stApp {background-color: #f8f9fa;}
    .star-card {
        background-color: white;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        text-align: center;
        border: 1px solid #e0e0e0;
        height: 100%;
    }
    .pass {color: #27ae60; font-weight: bold;} 
    .fail {color: #7f8c8d; font-weight: bold;} 
    .big-star {font-size: 30px; margin: 0;}
    a {text-decoration: none; color: #2980b9; font-weight: normal; font-size: 16px;}
    a:hover {text-decoration: underline; color: #3498db;}
    footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- SEC Cache (Keep this, it works) ---
@st.cache_data(ttl=3600) 
def get_sec_tickers():
    headers = {'User-Agent': 'student-project-analysis@example.com'}
    try:
        url = "https://www.sec.gov/files/company_tickers.json"
        response = requests.get(url, headers=headers)
        data = response.json()
        df = pd.DataFrame.from_dict(data, orient='index')
        return df
    except:
        return pd.DataFrame()

# --- Robust Data Fetching (The Fix) ---
@st.cache_data(ttl=300)
def get_stock_history(ticker, period):
    """Fetch just the price history (Lightweight)"""
    try:
        # yf.download is often more robust for pure price data
        df = yf.download(ticker, period=period, progress=False)
        # Reset index to make sure Date is a column if needed, or handle standard yf format
        return df
    except Exception:
        return pd.DataFrame()

@st.cache_data(ttl=600) # Cache 'Info' longer (10 mins) to save API hits
def get_stock_info(ticker):
    """Fetch the fundamentals (Heavy - prone to blocking)"""
    try:
        stock = yf.Ticker(ticker)
        return stock.info
    except Exception:
        return None

# --- Main App ---
st.title("Market Insights") 
st.markdown("---")

with st.sidebar:
    st.header("Find a Security")
    df_tickers = get_sec_tickers()
    query = st.text_input("Ticker or Name:", value="VOO")
    time_range = st.radio("Range", ["1Y", "3Y", "5Y", "Max"], index=1, horizontal=True)
    period_map = {"1Y": "1y", "3Y": "3y", "5Y": "5y", "Max": "max"}
    
    # Reboot Button (Helps if stuck)
    if st.button("Clear Cache / Retry"):
        st.cache_data.clear()
        st.rerun()

if query:
    # 1. Ticker Resolution
    ticker_candidate = query.upper()
    if not df_tickers.empty and len(query) > 3:
        match = df_tickers[df_tickers['title'].str.contains(query, case=False, na=False)]
        if not match.empty:
            ticker_candidate = match.iloc[0]['ticker']
    
    ticker = ticker_candidate

    # 2. Fetch Data (Split Strategy)
    history = get_stock_history(ticker, period_map[time_range])
    info = get_stock_info(ticker) # This might return None if blocked

    # CHECK: If history failed, we really can't do anything.
    if history.empty:
        st.error(f"⚠️ Could not load data for **{ticker}**. Yahoo Finance may be temporarily blocking requests. Please wait 1 minute and hit 'Clear Cache'.")
        st.stop()
    
    # --- Prepare Header Data ---
    # Handle yf.download weirdness (sometimes returns MultiIndex)
    if isinstance(history.columns, pd.MultiIndex):
        history.columns = history.columns.get_level_values(0)
    
    current_price = history['Close'].iloc[-1]
    
    if len(history) >= 2:
        prev_close = history['Close'].iloc[-2]
        change = current_price - prev_close
        pct_change = (change / prev_close) * 100
    else:
        change, pct_change = 0, 0
    
    # Use info if available, otherwise fallback to Ticker
    name = info.get('shortName', ticker) if info else ticker
    
    st.subheader(f"{name} ({ticker})")
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Price", f"${current_price:,.2f}", f"{change:.2f} ({pct_change:.2f}%)")
    
    # --- FAIL-SAFE BLOCK ---
    if info is None:
        # LITE MODE: Info failed, but we have price. Show limited view.
        st.warning(f"⚠️ **Limited Mode:** Detailed fundamental data (Stars) is currently unavailable due to high server traffic. Displaying Price Chart only.")
        
    else:
        # FULL MODE: We have info, show the stars!
        if 'quoteType' in info:
            is_etf = info['quoteType'] == 'ETF'
        else:
            is_etf = False # Default

        if is_etf:
            assets = info.get('totalAssets', 0)
            c2.metric("Total Assets", f"${assets/1e9:,.2f} B" if assets else "N/A")
            c3.metric("Type", "ETF / Fund")
        else:
            mkt_cap = info.get('marketCap', 0)
            c2.metric("Market Cap", f"${mkt_cap/1e9:,.2f} B" if mkt_cap else "N/A")
            c3.metric("Sector", info.get('sector', 'Unknown'))

        st.markdown(f"### {'Fund Analysis' if is_etf else 'Fundamental Strength'}")
        
        results = {}

        # ... (Your Logic Code Here - Simplified for robustness) ...
        # I am inserting your exact previous logic here, safe inside the 'else' block
        if is_etf:
            # ETF LOGIC
            exp_ratio = info.get('annualReportExpenseRatio')
            yield_pct = info.get('yield', info.get('trailingAnnualDividendYield', 0))
            beta = info.get('beta3Year', 0)
            ytd = info.get('ytdReturn')
            assets = info.get('totalAssets', 0)

            results['Fees'] = {'pass': exp_ratio is not None and exp_ratio < 0.005, 'msg': f"Low Cost ({exp_ratio:.2%})" if exp_ratio else "N/A"}
            results['Risk'] = {'pass': beta and beta < 1.1, 'msg': f"Stable ({beta:.2f})" if beta else "N/A"}
            results['Yield'] = {'pass': yield_pct and yield_pct > 0.01, 'msg': f"Pays Divs ({yield_pct:.2%})" if yield_pct else "Low"}
            results['Return'] = {'pass': ytd and ytd > 0, 'msg': f"Positive ({ytd:.2%})" if ytd else "Negative"}
            results['Size'] = {'pass': assets > 1e9, 'msg': "Large Fund" if assets > 1e9 else "Small"}
        else:
            # STOCK LOGIC
            pe = info.get('forwardPE')
            margin = info.get('profitMargins')
            debt = info.get('debtToEquity')
            rev = info.get('revenueGrowth')
            curr = info.get('currentRatio')

            results['Value'] = {'pass': pe and 0 < pe < 30, 'msg': f"Fair ({pe:.1f})" if pe else "Expensive"}
            results['Profit'] = {'pass': margin and margin > 0.10, 'msg': f"High ({margin:.1%})" if margin else "Low"}
            results['Safety'] = {'pass': debt and debt < 150, 'msg': "Safe Debt" if debt and debt < 150 else "High Debt"}
            results['Growth'] = {'pass': rev and rev > 0.05, 'msg': "Growing" if rev else "Slow"}
            results['Liquidity'] = {'pass': curr and curr > 1.0, 'msg': "Solvent" if curr else "Tight"}

        # Render Stars
        cols = st.columns(len(results))
        for i, (key, val) in enumerate(results.items()):
            with cols[i]:
                icon = "⭐" if val['pass'] else "☆" 
                color = "pass" if val['pass'] else "fail"
                color_code = '#f1c40f' if val['pass'] else '#bdc3c7'
                st.markdown(f"""
                <div class="star-card">
                    <p class="big-star" style="color: {color_code};">{icon}</p>
                    <p style="font-weight:bold;">{key.upper()}</p>
                    <p class="{color}" style="font-size:13px;">{val['msg']}</p>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("---")
        with st.expander("What do these terms mean?"):
             if is_etf:
                st.markdown("""
                * **FEES (Expense Ratio):** The management fee you pay to hold the fund. Lower is better (we look for < 0.5%).
                * **RISK (Beta):** Measures volatility. A Beta of 1.0 moves with the market. Lower than 1.0 is more stable; higher is riskier.
                * **YIELD (Dividend):** The annual percentage paid out to you in cash dividends.
                * **RETURN (YTD):** Year-to-Date return. Is the fund actually making money this year?
                * **SIZE (Assets):** Total money invested in the fund. Larger funds (> $1B) are generally safer and more liquid.
                """)
             else:
                st.markdown("""
                * **VALUE (P/E Ratio):** Price-to-Earnings. It measures how much you pay for $1 of earnings. We look for < 30.
                * **PROFIT (Margins):** The percentage of revenue the company keeps as profit. We look for > 10%.
                * **SAFETY (Debt):** Debt-to-Equity ratio. Measures financial leverage. We want this low (< 1.5) to avoid bankruptcy risk.
                * **GROWTH (Revenue):** Measures if the company's sales are increasing year-over-year. We look for > 5% growth.
                * **LIQUIDITY (Current Ratio):** Can the company pay its short-term bills? A ratio > 1.0 means they have enough cash.
                """)

    # --- Section 4: Chart ---
    yahoo_link = f"https://finance.yahoo.com/quote/{ticker}"
    st.markdown(f"""
        ### History ({time_range}) 
        <a href="{yahoo_link}" target="_blank" style="font-size: 14px; margin-left: 10px;">(View Source Data on Yahoo Finance 🔗)</a>
        """, unsafe_allow_html=True)
        
    st.line_chart(history['Close'])
