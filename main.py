import streamlit as st
import yfinance as yf
import pandas as pd
import requests

# --- Page Configuration ---
st.set_page_config(
    page_title="Market Insights Pro",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Custom CSS for Professional Styling ---
# This hides the default Streamlit menu and adds a professional color palette
st.markdown("""
    <style>
    /* Main Background adjustments */
    .stApp {
        background-color: #f5f7f9;
    }
    
    /* Header Styling */
    h1, h2, h3 {
        color: #0e1117;
        font-family: 'Helvetica Neue', sans-serif;
    }
    
    /* Custom Card for Metrics */
    .metric-container {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-bottom: 20px;
        border-left: 5px solid #2b6cb0; /* Professional Blue Accent */
    }
    
    /* Hide the default Streamlit footer */
    footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- Function to Load SEC Data (Cached) ---
@st.cache_data
def get_sec_tickers():
    headers = {'User-Agent': 'student-project-analytics@example.com'}
    try:
        url = "https://www.sec.gov/files/company_tickers.json"
        response = requests.get(url, headers=headers)
        data = response.json()
        df = pd.DataFrame.from_dict(data, orient='index')
        df['label'] = df['ticker'] + " | " + df['title']
        return df
    except:
        return pd.DataFrame()

# --- Main Interface ---
st.title("Market Insights | Fundamental Analytics")
st.markdown("Institutional-grade analysis for the modern investor.")
st.markdown("---")

# Sidebar for Controls
with st.sidebar:
    st.header("Analysis Controls")
    
    # Load Data
    with st.spinner("Connecting to SEC Database..."):
        df_tickers = get_sec_tickers()
    
    if not df_tickers.empty:
        selected_company = st.selectbox(
            "Select Security",
            options=df_tickers['label'],
            index=None,
            placeholder="Type company name or ticker..."
        )
    else:
        # Fallback if SEC data fails
        user_input = st.text_input("Enter Ticker Symbol", value="AAPL")
        selected_company = user_input

# --- Main Dashboard Logic ---
if selected_company:
    # Extract ticker (handles both SEC format and manual input)
    if " | " in selected_company:
        ticker = selected_company.split(" | ")[0]
    else:
        ticker = selected_company.upper()

    try:
        stock = yf.Ticker(ticker)
        
        # Fetch History & Info
        history = stock.history(period="3y")
        info = stock.info
        
        if history.empty:
            st.error(f"Unable to retrieve data for {ticker}. The security may be delisted.")
            st.stop()

        # --- Section 1: Executive Summary ---
        current_price = history['Close'].iloc[-1]
        market_cap = info.get('marketCap', 0)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Current Price", f"${current_price:,.2f}")
        with col2:
            st.metric("Market Cap", f"${market_cap/1e9:,.2f} B")
        with col3:
            # 52 Week High logic
            high_52 = info.get('fiftyTwoWeekHigh', current_price)
            diff_from_high = ((current_price - high_52) / high_52) * 100
            st.metric("Dist. to 52W High", f"{diff_from_high:.1f}%")

        # --- Section 2: Price Action ---
        st.subheader(f"Price Performance: {ticker}")
        st.area_chart(history['Close'], color="#2b6cb0") # Professional Blue Chart

        # --- Section 3: Fundamental Health Score ---
        st.markdown("### Algorithmic Assessment")
        
        # Calculate Scores
        score = 0
        reasons = []
        
        # Metric 1: Valuation (P/E)
        pe_ratio = info.get('forwardPE', None)
        if pe_ratio and pe_ratio < 25:
            score += 1
            reasons.append(f"Undervalued: Forward P/E is {pe_ratio:.1f} (Target < 25)")
        elif pe_ratio:
            reasons.append(f"Overvalued: Forward P/E is {pe_ratio:.1f} (Target < 25)")
        else:
            reasons.append("Valuation: Data Unavailable")

        # Metric 2: Efficiency (ROE)
        roe = info.get('returnOnEquity', 0)
        if roe > 0.10:
            score += 1
            reasons.append(f"Efficient Management: ROE is {roe:.1%} (Target > 10%)")
        else:
            reasons.append(f"Inefficient Management: ROE is {roe:.1%} (Target > 10%)")

        # Metric 3: Momentum (vs 50 Day Avg)
        ma_50 = history['Close'].tail(50).mean()
        if current_price > ma_50:
            score += 1
            reasons.append(f"Positive Momentum: Price is above 50-day average")
        else:
            reasons.append(f"Negative Momentum: Price is below 50-day average")

        # Display the Score Card cleanly
        # We use a container with a border instead of st.success to avoid the 'green box' look if you want it neutral
        with st.container():
            st.write(f"**Composite Score: {score} / 3**")
            
            if score == 3:
                st.success("Rating: STRONG BUY")
            elif score == 2:
                st.warning("Rating: ACCUMULATE / HOLD")
            else:
                st.error("Rating: AVOID / SELL")
            
            # Show details in a clean bulleted list, not a raw object print
            with st.expander("View Analyst Logic"):
                for reason in reasons:
                    st.write(f"• {reason}")

    except Exception as e:
        st.error(f"System Error: {e}")

else:
    # Landing Page content (when no stock is selected)
    st.info("Select a company from the sidebar to begin analysis.")
