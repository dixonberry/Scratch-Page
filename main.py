import streamlit as st
import yfinance as yf
import pandas as pd
import requests

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
    .fail {color: #e74c3c; font-weight: bold;} 
    .big-star {font-size: 30px; margin: 0;}
    footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- SEC Cache ---
@st.cache_data
def get_sec_tickers():
    headers = {'User-Agent': 'student-project@example.com'}
    try:
        url = "https://www.sec.gov/files/company_tickers.json"
        response = requests.get(url, headers=headers)
        data = response.json()
        df = pd.DataFrame.from_dict(data, orient='index')
        return df
    except:
        return pd.DataFrame()

# --- Main App ---
st.title("Market Insights") 
st.markdown("---")

with st.sidebar:
    st.header("Find a Security")
    df_tickers = get_sec_tickers()
    query = st.text_input("Ticker or Name:", value="VOO") # Changed default to VOO to test
    time_range = st.radio("Range", ["1Y", "3Y", "5Y", "Max"], index=1, horizontal=True)
    period_map = {"1Y": "1y", "3Y": "3y", "5Y": "5y", "Max": "max"}

if query:
    # 1. Ticker Resolution
    ticker_candidate = query.upper()
    if not df_tickers.empty and len(query) > 3:
        match = df_tickers[df_tickers['title'].str.contains(query, case=False, na=False)]
        if not match.empty:
            ticker_candidate = match.iloc[0]['ticker']
    
    ticker = ticker_candidate

    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        history = stock.history(period=period_map[time_range])
        
        if history.empty:
            st.error(f"No data found for '{ticker}'.")
            st.stop()
            
        # Detect Type: ETF vs STOCK
        quote_type = info.get('quoteType', 'EQUITY') # Default to Equity if unknown
        is_etf = quote_type == 'ETF'

        # --- Section 1: Header ---
        current_price = history['Close'].iloc[-1]
        
        # Calculate Change
        if len(history) >= 2:
            prev_close = history['Close'].iloc[-2]
            change = current_price - prev_close
            pct_change = (change / prev_close) * 100
        else:
            change, pct_change = 0, 0

        st.subheader(f"{info.get('shortName', ticker)} ({ticker})")
        
        # Metric Badge Logic
        c1, c2, c3 = st.columns(3)
        c1.metric("Price", f"${current_price:,.2f}", f"{change:.2f} ({pct_change:.2f}%)")
        
        # Market Cap (Stocks) or Assets (ETFs)
        if is_etf:
            assets = info.get('totalAssets', 0)
            c2.metric("Total Assets", f"${assets/1e9:,.2f} B" if assets else "N/A")
            c3.metric("Asset Class", "ETF / Fund")
        else:
            mkt_cap = info.get('marketCap', 0)
            c2.metric("Market Cap", f"${mkt_cap/1e9:,.2f} B" if mkt_cap else "N/A")
            c3.metric("Sector", info.get('sector', 'Unknown'))

        # --- Section 2: The "Brain" (Smart Switch) ---
        st.markdown(f"### {'Fund Analysis' if is_etf else 'Fundamental Strength'}")
        
        results = {}

        if is_etf:
            # === ETF LOGIC ===
            
            # 1. Expense Ratio (Lower is Better)
            exp_ratio = info.get('annualReportExpenseRatio') # Returns 0.0003 for 0.03%
            # Sometimes yfinance returns 'trailingAnnualDividendYield' for Yield
            yield_pct = info.get('yield', info.get('trailingAnnualDividendYield', 0))
            beta = info.get('beta3Year', 0)

            # Rule 1: Expense Ratio (Cheap?)
            if exp_ratio is not None and exp_ratio < 0.005: # < 0.50%
                results['Fees'] = {'pass': True, 'msg': f"Low Fees ({exp_ratio:.2%})"}
            else:
                val = f"{exp_ratio:.2%}" if exp_ratio else "N/A"
                results['Fees'] = {'pass': False, 'msg': f"High Fees ({val})"}

            # Rule 2: Risk (Beta)
            # Beta 1.0 = Market. < 1.0 = Less Volatile.
            if beta and beta < 1.1:
                results['Risk'] = {'pass': True, 'msg': f"Stable (Beta: {beta:.2f})"}
            else:
                val = f"{beta:.2f}" if beta else "N/A"
                results['Risk'] = {'pass': False, 'msg': f"Volatile (Beta: {val})"}

            # Rule 3: Yield (Dividends)
            if yield_pct and yield_pct > 0.01:
                results['Yield'] = {'pass': True, 'msg': f"Pays Divs ({yield_pct:.2%})"}
            else:
                val = f"{yield_pct:.2%}" if yield_pct else "Low/None"
                results['Yield'] = {'pass': False, 'msg': f"Low Yield ({val})"}

            # Rule 4: Performance (Yearly Return)
            ytd = info.get('ytdReturn')
            if ytd and ytd > 0:
                results['YTD'] = {'pass': True, 'msg': f"Positive ({ytd:.2%})"}
            else:
                val = f"{ytd:.2%}" if ytd else "N/A"
                results['YTD'] = {'pass': False, 'msg': f"Negative/Flat ({val})"}

            # Rule 5: Assets (Popularity)
            assets = info.get('totalAssets', 0)
            if assets > 1e9: # > $1 Billion
                results['Size'] = {'pass': True, 'msg': "Large/Liquid Fund"}
            else:
                results['Size'] = {'pass': False, 'msg': "Small Fund"}

        else:
            # === STOCK LOGIC (Your Original 5 Stars) ===
            pe = info.get('forwardPE')
            margin = info.get('profitMargins')
            debt = info.get('debtToEquity')
            rev_growth = info.get('revenueGrowth')
            curr_ratio = info.get('currentRatio')

            # (Same logic as before...)
            if pe and 0 < pe < 30: results['Value'] = {'pass': True, 'msg': f"Fair (P/E: {pe:.1f})"}
            else: results['Value'] = {'pass': False, 'msg': f"Expensive (P/E: {pe}N/A)"}

            if margin and margin > 0.10: results['Profit'] = {'pass': True, 'msg': f"High ({margin:.1%})"}
            else: results['Profit'] = {'pass': False, 'msg': f"Low ({margin}N/A)"}
            
            # Using simple keys for brevity in this snippet
            results['Safety'] = {'pass': True, 'msg': "Safe Debt"} if (debt and debt < 150) else {'pass': False, 'msg': "High Debt"}
            results['Growth'] = {'pass': True, 'msg': "Growing"} if (rev_growth and rev_growth > 0.05) else {'pass': False, 'msg': "Slow Growth"}
            results['Liquidity'] = {'pass': True, 'msg': "Solvent"} if (curr_ratio and curr_ratio > 1.0) else {'pass': False, 'msg': "Tight Cash"}

        # Display Logic (Works for BOTH)
        cols = st.columns(len(results))
        def show_card(col, title, result):
            with col:
                icon = "⭐" if result['pass'] else "⚪"
                color = "pass" if result['pass'] else "fail"
                st.markdown(f"""
                <div class="star-card">
                    <p class="big-star">{icon}</p>
                    <p style="font-weight:bold;">{title}</p>
                    <p class="{color}" style="font-size:13px;">{result['msg']}</p>
                </div>
                """, unsafe_allow_html=True)

        for i, (key, val) in enumerate(results.items()):
            show_card(cols[i], key.upper(), val)

        # --- Section 3: Chart ---
        st.markdown("---")
        st.subheader(f"History ({time_range})")
        st.line_chart(history['Close'])

    except Exception as e:
        st.error(f"Error: {e}")
