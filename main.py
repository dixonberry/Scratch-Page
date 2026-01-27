import streamlit as st
import yfinance as yf
import pandas as pd
import requests

# --- Page Configuration ---
st.set_page_config(
    page_title="Market Insights",
    page_icon="📈",
    layout="wide"
)

# --- Custom CSS (Clean & Professional) ---
st.markdown("""
    <style>
    .stApp {background-color: #f8f9fa;}
    h1, h2, h3 {font-family: 'Arial', sans-serif; color: #333;}
    
    /* Star Card Styling */
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
    
    /* Hide default footer */
    footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- Helper: SEC Data Cache ---
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

# --- Sidebar: Search Logic ---
with st.sidebar:
    st.header("Find a Security") 
    
    df_tickers = get_sec_tickers()
    
    # Simple Text Input 
    query = st.text_input("Ticker or Company Name:", value="AAPL")
    
    # Time Range Selector 
    time_range = st.radio("Time Range", ["1Y", "3Y", "5Y", "Max"], index=1, horizontal=True)
    
    period_map = {"1Y": "1y", "3Y": "3y", "5Y": "5y", "Max": "max"}
    selected_period = period_map[time_range]

# --- App Logic ---
if query:
    # 1. Ticker Resolution Logic
    ticker_candidate = query.upper()
    
    if not df_tickers.empty and len(query) > 3:
        match = df_tickers[df_tickers['title'].str.contains(query, case=False, na=False)]
        if not match.empty:
            ticker_candidate = match.iloc[0]['ticker']
    
    # 2. Fetch Data
    ticker = ticker_candidate
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        history = stock.history(period=selected_period)
        
        if history.empty:
            st.error(f"Could not find data for '{ticker}'. Please check the spelling.")
            st.stop()
            
        # --- Section 1: Key Metrics ---
        current_price = history['Close'].iloc[-1]
        
        if len(history) >= 2:
            prev_close = history['Close'].iloc[-2]
            change_amt = current_price - prev_close
            change_pct = (change_amt / prev_close) * 100
        else:
            change_amt = 0
            change_pct = 0

        st.subheader(f"{info.get('shortName', ticker)} ({ticker})")
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Current Price", f"${current_price:,.2f}", f"{change_amt:.2f} ({change_pct:.2f}%)")
        col2.metric("Market Cap", f"${info.get('marketCap', 0)/1e9:,.2f} B")
        col3.metric("Volume", f"{info.get('volume', 0):,}")

        # --- Section 2: The 5-Star Analysis ---
        st.markdown("### Fundamental Strength")
        
        # Gather Data
        pe = info.get('forwardPE')
        margin = info.get('profitMargins')
        debt_equity = info.get('debtToEquity')
        if debt_equity: debt_equity = debt_equity / 100
        revenue_growth = info.get('revenueGrowth')
        current_ratio = info.get('currentRatio')

        # Score Logic
        results = {}

        # 1. Value
        if pe and 0 < pe < 30:
            results['Value'] = {'pass': True, 'msg': f"Fair Price (P/E: {pe:.1f})"}
        else:
            val = f"{pe:.1f}" if pe else "N/A"
            results['Value'] = {'pass': False, 'msg': f"Expensive (P/E: {val})"}

        # 2. Profit
        if margin and margin > 0.10:
            results['Profit'] = {'pass': True, 'msg': f"Healthy ({margin:.1%})"}
        else:
            val = f"{margin:.1%}" if margin else "N/A"
            results['Profit'] = {'pass': False, 'msg': f"Low Margin ({val})"}

        # 3. Safety
        if debt_equity and debt_equity < 1.5:
            results['Safety'] = {'pass': True, 'msg': f"Safe Debt ({debt_equity:.2f})"}
        else:
            val = f"{debt_equity:.2f}" if debt_equity else "N/A"
            results['Safety'] = {'pass': False, 'msg': f"High Debt ({val})"}

        # 4. Growth
        if revenue_growth and revenue_growth > 0.05:
            results['Growth'] = {'pass': True, 'msg': f"Growing ({revenue_growth:.1%})"}
        else:
            val = f"{revenue_growth:.1%}" if revenue_growth else "N/A"
            results['Growth'] = {'pass': False, 'msg': f"Slow Growth ({val})"}

        # 5. Liquidity
        if current_ratio and current_ratio > 1.0:
            results['Liquidity'] = {'pass': True, 'msg': f"Solvent ({current_ratio:.2f})"}
        else:
            val = f"{current_ratio:.2f}" if current_ratio else "N/A"
            results['Liquidity'] = {'pass': False, 'msg': f"Tight Cash ({val})"}

        # Display Stars
        c1, c2, c3, c4, c5 = st.columns(5)
        
        def show_card(col, title, result):
            with col:
                icon = "⭐" if result['pass'] else "⚪"
                color_class = "pass" if result['pass'] else "fail"
                st.markdown(f"""
                <div class="star-card">
                    <p class="big-star">{icon}</p>
                    <p style="font-weight:bold; margin-bottom:5px;">{title}</p>
                    <p class="{color_class}" style="font-size:13px;">{result['msg']}</p>
                </div>
                """, unsafe_allow_html=True)

        show_card(c1, "VALUE", results['Value'])
        show_card(c2, "PROFIT", results['Profit'])
        show_card(c3, "SAFETY", results['Safety'])
        show_card(c4, "GROWTH", results['Growth'])
        show_card(c5, "LIQUIDITY", results['Liquidity'])

        # --- NEW: Definitions Expander ---
        with st.expander("📘 What do these stars mean? (Click to Learn)"):
            st.markdown("""
            * **VALUE (P/E Ratio):** The "Price Tag" of the stock. We want a P/E under 30. If it's higher, you are paying a premium for every dollar the company earns.
            * **PROFIT (Margins):** How much money they actually keep. If a company sells \$100 of goods and keeps \$15, that's a 15% margin. We want > 10%.
            * **SAFETY (Debt-to-Equity):** How much debt they have compared to their own money. Lower is safer. We want this under 1.5.
            * **GROWTH (Revenue):** Is the business getting bigger? We look for sales to be higher this year than last year (> 5%).
            * **LIQUIDITY (Current Ratio):** Can they pay their immediate bills? A ratio > 1.0 means they have enough cash/assets to cover short-term debts.
            """)

        # --- Section 3: Chart ---
        st.markdown("---")
        st.subheader(f"Price History ({time_range})")
        st.line_chart(history['Close'])

    except Exception as e:
        st.error(f"Error: {e}")
