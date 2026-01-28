import streamlit as st
import pandas as pd
import numpy as np
import time

# --- Page Config ---
st.set_page_config(page_title="Market Insights (Demo)", page_icon="📈", layout="wide")

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
    footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- MOCK DATA GENERATOR ---
# This creates realistic-looking data without needing the internet
def get_mock_data(ticker, period):
    # Seed random so the "fake" data looks the same every time (consistency)
    np.random.seed(len(ticker)) 
    
    # Create fake price history
    days = 365 if "1Y" in period else 1000
    dates = pd.date_range(end=pd.Timestamp.today(), periods=days)
    base_price = np.random.uniform(50, 400)
    volatility = 0.02
    
    # Random walk
    changes = np.random.normal(0, volatility, days)
    prices = base_price * np.exp(np.cumsum(changes))
    
    history = pd.DataFrame({'Close': prices}, index=dates)
    
    # Create fake fundamentals
    is_etf = "VOO" in ticker or "IVV" in ticker or "SPY" in ticker
    
    info = {
        'shortName': f"{ticker} Corp" if not is_etf else f"{ticker} Vanguard Fund",
        'quoteType': 'ETF' if is_etf else 'EQUITY',
        'marketCap': np.random.uniform(10e9, 2000e9),
        'totalAssets': np.random.uniform(1e9, 500e9),
        'sector': 'Technology' if not is_etf else None,
        # Stock Metrics
        'forwardPE': np.random.uniform(15, 45),
        'profitMargins': np.random.uniform(0.05, 0.30),
        'debtToEquity': np.random.uniform(50, 200),
        'revenueGrowth': np.random.uniform(-0.05, 0.20),
        'currentRatio': np.random.uniform(0.8, 2.5),
        # ETF Metrics
        'annualReportExpenseRatio': np.random.uniform(0.0003, 0.01),
        'beta3Year': np.random.uniform(0.8, 1.4),
        'yield': np.random.uniform(0.01, 0.04),
        'ytdReturn': np.random.uniform(-0.10, 0.25)
    }
    return history, info

# --- Main App ---
st.title("Market Insights") 
st.caption("⚠️ DEMO MODE: Running with simulated data for presentation stability.")
st.markdown("---")

with st.sidebar:
    st.header("Find a Security")
    # We removed the SEC fetch to make it faster/safer
    query = st.text_input("Ticker or Name:", value="AAPL")
    time_range = st.radio("Range", ["1Y", "3Y", "5Y", "Max"], index=1, horizontal=True)

if query:
    ticker = query.upper()
    
    # Simulate "Loading" so it feels real
    with st.spinner(f"Searching market data for {ticker}..."):
        time.sleep(0.5) 
        history, info = get_mock_data(ticker, time_range)
    
    # --- The Rest is EXACTLY the same as your real app ---
    current_price = history['Close'].iloc[-1]
    prev_close = history['Close'].iloc[-2]
    change = current_price - prev_close
    pct_change = (change / prev_close) * 100
    
    st.subheader(f"{info.get('shortName', ticker)} ({ticker})")
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Price", f"${current_price:,.2f}", f"{change:.2f} ({pct_change:.2f}%)")
    
    is_etf = info['quoteType'] == 'ETF'

    if is_etf:
        assets = info.get('totalAssets', 0)
        c2.metric("Total Assets", f"${assets/1e9:,.2f} B")
        c3.metric("Type", "ETF / Fund")
    else:
        mkt_cap = info.get('marketCap', 0)
        c2.metric("Market Cap", f"${mkt_cap/1e9:,.2f} B")
        c3.metric("Sector", info.get('sector', 'Unknown'))

    st.markdown(f"### {'Fund Analysis' if is_etf else 'Fundamental Strength'}")
    
    results = {}

    if is_etf:
        # ETF LOGIC
        exp_ratio = info.get('annualReportExpenseRatio')
        yield_pct = info.get('yield')
        beta = info.get('beta3Year')
        ytd = info.get('ytdReturn')
        assets = info.get('totalAssets')

        results['Fees'] = {'pass': exp_ratio < 0.005, 'msg': f"Low Cost ({exp_ratio:.2%})"}
        results['Risk'] = {'pass': beta < 1.1, 'msg': f"Stable ({beta:.2f})"}
        results['Yield'] = {'pass': yield_pct > 0.01, 'msg': f"Pays Divs ({yield_pct:.2%})"}
        results['Return'] = {'pass': ytd > 0, 'msg': f"Positive ({ytd:.2%})"}
        results['Size'] = {'pass': assets > 1e9, 'msg': "Large Fund"}
    else:
        # STOCK LOGIC
        pe = info.get('forwardPE')
        margin = info.get('profitMargins')
        debt = info.get('debtToEquity')
        rev = info.get('revenueGrowth')
        curr = info.get('currentRatio')

        results['Value'] = {'pass': pe < 30, 'msg': f"Fair ({pe:.1f})"}
        results['Profit'] = {'pass': margin > 0.10, 'msg': f"High ({margin:.1%})"}
        results['Safety'] = {'pass': debt < 150, 'msg': "Safe Debt" if debt < 150 else "High Debt"}
        results['Growth'] = {'pass': rev > 0.05, 'msg': "Growing" if rev > 0.05 else "Slow"}
        results['Liquidity'] = {'pass': curr > 1.0, 'msg': "Solvent" if curr > 1.0 else "Tight"}

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
    # Definitions Section
    with st.expander("What do these terms mean?"):
         if is_etf:
            st.markdown("""
            * **FEES (Expense Ratio):** The management fee you pay. Lower is better (< 0.5%).
            * **RISK (Beta):** Measures volatility. A Beta of 1.0 moves with the market.
            * **YIELD (Dividend):** The annual percentage paid out in cash dividends.
            * **RETURN (YTD):** Year-to-Date return. Is the fund making money?
            * **SIZE (Assets):** Total money in the fund. Larger funds (> $1B) are safer.
            """)
         else:
            st.markdown("""
            * **VALUE (P/E Ratio):** Price-to-Earnings. How much you pay for $1 of earnings (< 30 is good).
            * **PROFIT (Margins):** Percentage of revenue kept as profit (> 10% is good).
            * **SAFETY (Debt):** Debt-to-Equity ratio. We want this low (< 1.5).
            * **GROWTH (Revenue):** Is sales increasing year-over-year (> 5%).
            * **LIQUIDITY (Current Ratio):** Can they pay short-term bills (> 1.0).
            """)

    st.markdown(f"### History ({time_range})")
    st.line_chart(history['Close'])
