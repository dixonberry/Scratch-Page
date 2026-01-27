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
    query = st.text_input("Ticker or Name:", value="VOO")
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
        quote_type = info.get('quoteType', 'EQUITY') 
        is_etf = quote_type == 'ETF'

        # --- Section 1: Header ---
        current_price = history['Close'].iloc[-1]
        
        if len(history) >= 2:
            prev_close = history['Close'].iloc[-2]
            change = current_price - prev_close
            pct_change = (change / prev_close) * 100
        else:
            change, pct_change = 0, 0

        st.subheader(f"{info.get('shortName', ticker)} ({ticker})")
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Price", f"${current_price:,.2f}", f"{change:.2f} ({pct_change:.2f}%)")
        
        if is_etf:
            assets = info.get('totalAssets', 0)
            c2.metric("Total Assets", f"${assets/1e9:,.2f} B" if assets else "N/A")
            c3.metric("Type", "ETF / Fund")
        else:
            mkt_cap = info.get('marketCap', 0)
            c2.metric("Market Cap", f"${mkt_cap/1e9:,.2f} B" if mkt_cap else "N/A")
            c3.metric("Sector", info.get('sector', 'Unknown'))

        # --- Section 2: Analysis Logic ---
        st.markdown(f"### {'Fund Analysis' if is_etf else 'Fundamental Strength'}")
        
        results = {}

        if is_etf:
            # === ETF LOGIC ===
            exp_ratio = info.get('annualReportExpenseRatio')
            yield_pct = info.get('yield', info.get('trailingAnnualDividendYield', 0))
            beta = info.get('beta3Year', 0)
            ytd = info.get('ytdReturn')
            assets = info.get('totalAssets', 0)

            # Rule 1: Fees
            if exp_ratio is not None and exp_ratio < 0.005:
                results['Fees'] = {'pass': True, 'msg': f"Low Cost ({exp_ratio:.2%})"}
            else:
                val = f"{exp_ratio:.2%}" if exp_ratio else "N/A"
                results['Fees'] = {'pass': False, 'msg': f"High Cost ({val})"}

            # Rule 2: Risk (Beta)
            if beta and beta < 1.1:
                results['Risk'] = {'pass': True, 'msg': f"Stable ({beta:.2f})"}
            else:
                val = f"{beta:.2f}" if beta else "N/A"
                results['Risk'] = {'pass': False, 'msg': f"Volatile ({val})"}

            # Rule 3: Yield
            if yield_pct and yield_pct > 0.01:
                results['Yield'] = {'pass': True, 'msg': f"Pays Divs ({yield_pct:.2%})"}
            else:
                val = f"{yield_pct:.2%}" if yield_pct else "Low/None"
                results['Yield'] = {'pass': False, 'msg': f"Low Yield ({val})"}

            # Rule 4: Return
            if ytd and ytd > 0:
                results['Return'] = {'pass': True, 'msg': f"Positive YTD ({ytd:.2%})"}
            else:
                val = f"{ytd:.2%}" if ytd else "N/A"
                results['Return'] = {'pass': False, 'msg': f"Negative YTD ({val})"}

            # Rule 5: Popularity
            if assets > 1e9:
                results['Size'] = {'pass': True, 'msg': "Large Fund"}
            else:
                results['Size'] = {'pass': False, 'msg': "Small Fund"}

        else:
            # === STOCK LOGIC ===
            pe = info.get('forwardPE')
            margin = info.get('profitMargins')
            debt = info.get('debtToEquity')
            rev_growth = info.get('revenueGrowth')
            curr_ratio = info.get('currentRatio')

            # Metric 1: Value
            if pe and 0 < pe < 30: results['Value'] = {'pass': True, 'msg': f"Fair Price ({pe:.1f})"}
            else: results['Value'] = {'pass': False, 'msg': f"Expensive ({pe}N/A)"}

            # Metric 2: Profit
            if margin and margin > 0.10: results['Profit'] = {'pass': True, 'msg': f"High Margin ({margin:.1%})"}
            else: results['Profit'] = {'pass': False, 'msg': f"Low Margin ({margin}N/A)"}
            
            # Metric 3: Safety
            if debt and debt < 150: results['Safety'] = {'pass': True, 'msg': "Safe Debt"} 
            else: results['Safety'] = {'pass': False, 'msg': "High Debt"}
            
            # Metric 4: Growth
            if rev_growth and rev_growth > 0.05: results['Growth'] = {'pass': True, 'msg': "Growing"} 
            else: results['Growth'] = {'pass': False, 'msg': "Slow/No Growth"}
            
            # Metric 5: Liquidity
            if curr_ratio and curr_ratio > 1.0: results['Liquidity'] = {'pass': True, 'msg': "Solvent"} 
            else: results['Liquidity'] = {'pass': False, 'msg': "Tight Cash"}

        # Display Logic
        cols = st.columns(len(results))
        for i, (key, val) in enumerate(results.items()):
            with cols[i]:
                icon = "⭐" if val['pass'] else "⚪"
                color = "pass" if val['pass'] else "fail"
                st.markdown(f"""
                <div class="star-card">
                    <p class="big-star">{icon}</p>
                    <p style="font-weight:bold;">{key.upper()}</p>
                    <p class="{color}" style="font-size:13px;">{val['msg']}</p>
                </div>
                """, unsafe_allow_html=True)

        # --- Section 3: Clean Definitions ---
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
        st.subheader(f"History ({time_range})")
        st.line_chart(history['Close'])

    except Exception as e:
        st.error(f"Error: {e}")
