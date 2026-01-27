import streamlit as st
import yfinance as yf
import pandas as pd

# --- Page Config ---
st.set_page_config(page_title="The Investor", page_icon="📈")

# --- Feature 1: The Smart Search Logic ---
def get_ticker_from_name(name):
    """
    A simple lookup for common companies to demonstrate 'Smart Search'.
    In a production app, this would connect to a search API.
    """
    # A mini-database of common stocks for the demo
    common_mapping = {
        "WALMART": "WMT",
        "APPLE": "AAPL",
        "MICROSOFT": "MSFT",
        "TESLA": "TSLA",
        "AMAZON": "AMZN",
        "GOOGLE": "GOOGL",
        "PATTERN": "PTRN", # Added based on your request
        "PATTERN GROUP": "PTRN",
        "NVIDIA": "NVDA",
        "FORD": "F"
    }
    
    clean_name = name.strip().upper()
    
    # Check if the user actually typed a valid ticker directly (3-4 chars)
    if len(clean_name) <= 5 and clean_name.isalpha():
        return clean_name
        
    # Check the dictionary
    return common_mapping.get(clean_name, None)

# --- App Layout ---
st.title("📈 The Investor")
st.markdown("Simple, data-driven investing for beginners.")

# Input Section
user_input = st.text_input("Enter Company Name or Ticker", placeholder="e.g. Walmart, Pattern, or AAPL")

if user_input:
    # Attempt to resolve name to ticker
    ticker_symbol = get_ticker_from_name(user_input)
    
    # If Smart Search fails, ask user for manual input
    if not ticker_symbol:
        st.warning(f"Could not auto-detect a ticker for '{user_input}'. Please enter the exact Ticker Symbol (e.g., PTRN).")
        ticker_symbol = st.text_input("Enter Ticker Symbol Manually").upper()

    # Proceed only if we have a valid ticker
    if ticker_symbol:
        try:
            # Fetch Data
            stock = yf.Ticker(ticker_symbol)
            
            # --- Feature 2: The Dashboard ---
            with st.spinner(f"Fetching data for {ticker_symbol}..."):
                # Fetch 3 years history
                history = stock.history(period="3y")
                info = stock.info
                
                if history.empty:
                    st.error(f"No data found for {ticker_symbol}. It may be delisted or misspelled.")
                    st.stop()
                
                # Display Header
                company_name = info.get('longName', ticker_symbol)
                current_price = history['Close'].iloc[-1]
                st.header(f"{company_name} ({ticker_symbol})")
                st.metric("Current Price", f"${current_price:.2f}")

                # Plot Chart
                st.subheader("📉 Price History (Last 3 Years)")
                st.line_chart(history['Close'])
                st.caption("⚠️ Data provided for educational purposes. Prices may be delayed by 15 minutes.")

                st.markdown("---")

                # --- Feature 3: The 'Analyst' Algorithm ---
                st.subheader("🤖 AI Analyst: Should I Invest?")
                
                # 1. Gather Metrics (using .get() to handle missing data safely)
                forward_pe = info.get('forwardPE', None)
                roe = info.get('returnOnEquity', 0)
                
                # Calculate 50-Day Moving Average manually from history
                ma_50 = history['Close'].tail(50).mean()
                
                # 2. Calculate Score
                score = 0
                reasons = []

                # Rule 1: Value (P/E < 25)
                if forward_pe and forward_pe < 25:
                    score += 1
                    reasons.append(f"✅ **Good Value:** Forward P/E is {forward_pe:.1f} (under 25).")
                elif forward_pe:
                    reasons.append(f"❌ **Expensive:** Forward P/E is {forward_pe:.1f} (over 25).")
                else:
                    reasons.append("⚠️ **Data Missing:** Could not verify P/E Ratio.")

                # Rule 2: Momentum (Price > 50-Day MA)
                if current_price > ma_50:
                    score += 1
                    reasons.append(f"✅ **Positive Momentum:** Price (${current_price:.2f}) is above the 50-day average (${ma_50:.2f}).")
                else:
                    reasons.append(f"❌ **Negative Momentum:** Price is below the 50-day average.")

                # Rule 3: Efficiency (ROE > 10%)
                if roe and roe > 0.10:
                    score += 1
                    reasons.append(f"✅ **High Efficiency:** ROE is {roe:.1%} (healthy is >10%).")
                else:
                    reasons.append(f"❌ **Low Efficiency:** ROE is {roe:.1%} (below 10%).")

                # 3. Display Result Card
                result_color = "red"
                result_msg = "🔴 Watch / Wait (High Risk)"
                
                if score == 3:
                    result_color = "green"
                    result_msg = "🟢 Strong Buy (Good Value & Momentum)"
                elif score == 2:
                    result_color = "orange" # Streamlit uses orange for yellow-ish warnings
                    result_msg = "🟡 Moderate Buy"

                # Render the Card
                st.success(result_msg) if score == 3 else (st.warning(result_msg) if score == 2 else st.error(result_msg))
                
                with st.expander("See Analyst Logic (Why?)"):
                    for reason in reasons:
                        st.markdown(reason)

        except Exception as e:
            st.error(f"An error occurred: {e}")
