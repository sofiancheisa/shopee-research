import streamlit as st
import requests
import pandas as pd
import json
import time
from datetime import datetime
from urllib.parse import quote
from random import choice

def get_user_agent():
    # List of common user agents for randomization
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Mobile/15E148 Safari/604.1",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Safari/605.1.15",
        "Mozilla/5.0 (iPad; CPU OS 14_7_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Mobile/15E148 Safari/604.1"
    ]
    return choice(user_agents)

def get_shopee_data(keyword, retries=3, delay=2):
    encoded_keyword = quote(keyword)
    base_url = "https://shopee.com.my"
    api_url = f"{base_url}/api/v4/search/search_items"
    
    params = {
        "by": "relevancy",
        "keyword": keyword,
        "limit": 60,
        "newest": 0,
        "order": "desc",
        "page_type": "search",
        "scenario": "PAGE_GLOBAL_SEARCH",
        "version": 2
    }
    
    headers = {
        "User-Agent": get_user_agent(),
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Referer": f"{base_url}/search?keyword={encoded_keyword}",
        "X-Requested-With": "XMLHttpRequest",
        "sec-ch-ua": '"Not_A Brand";v="8", "Chromium";v="120"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "Connection": "keep-alive",
        "Cookie": "SPC_F=test; REC_T_ID=test;",
    }

    for attempt in range(retries):
        try:
            # First get the search page to set cookies
            session = requests.Session()
            session.get(f"{base_url}/search?keyword={encoded_keyword}", 
                       headers=headers, 
                       timeout=10)
            
            # Add small delay to mimic human behavior
            time.sleep(delay)
            
            # Make API request
            response = session.get(
                api_url,
                params=params,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'items' in data and data['items']:
                    return data
                
            st.warning(f"Attempt {attempt + 1}: No data found. Retrying...")
            time.sleep(delay * (attempt + 1))  # Exponential backoff
            
        except Exception as e:
            if attempt == retries - 1:  # Last attempt
                st.error(f"Error fetching data after {retries} attempts: {str(e)}")
                return None
            time.sleep(delay * (attempt + 1))  # Exponential backoff
    
    return None

st.title('🛍️ Shopee Product Research v3')

with st.form("search_form"):
    keyword = st.text_input('Enter Product Keyword:', 'korean bag')
    submitted = st.form_submit_button("Search Products")

if submitted:
    with st.spinner('Searching products...'):
        data = get_shopee_data(keyword)
        
        if data and 'items' in data and data['items']:
            products = []
            
            for item in data['items']:
                basic = item.get('item_basic', {})
                if basic:
                    try:
                        name = basic.get('name', 'N/A')
                        if not name or name == 'N/A':
                            continue
                            
                        product = {
                            'Name': name[:100],
                            'Price (RM)': round(float(basic.get('price', 0)) / 100000, 2),
                            'Sales': basic.get('historical_sold', 0),
                            'Rating': round(float(basic.get('item_rating', {}).get('rating_star', 0)), 1),
                            'Stock': basic.get('stock', 0),
                            'Location': basic.get('shop_location', 'N/A'),
                            'Monthly Sales': round(float(basic.get('historical_sold', 0)) / 3, 1),
                            'Shop': basic.get('shop_name', 'N/A'),
                            'Link': f"https://shopee.com.my/{quote(name.replace(' ', '-'))}-i.{basic.get('shopid')}.{basic.get('itemid')}"
                        }
                        product['Est. Revenue (RM)'] = round(product['Price (RM)'] * product['Monthly Sales'], 2)
                        products.append(product)
                    except Exception as e:
                        st.warning(f"Skipped product due to error: {str(e)}")
                        continue
            
            if products:
                df = pd.DataFrame(products)
                
                # Display metrics
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Products", len(df))
                with col2:
                    st.metric("Avg Price", f"RM {df['Price (RM)'].mean():.2f}")
                with col3:
                    st.metric("Total Sales", df['Sales'].sum())
                
                # Sort by sales
                df_sorted = df.sort_values('Sales', ascending=False)
                
                st.write("### Top Products Found:")
                st.dataframe(df_sorted)
                
                # Download button
                csv = df_sorted.to_csv(index=False).encode('utf-8')
                st.download_button(
                    "📥 Download Full Results",
                    csv,
                    f"shopee_{keyword}_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                    "text/csv",
                    key='download-csv'
                )
                
                # Display top products details
                st.write("### Top 5 Products Details:")
                for i, row in df_sorted.head().iterrows():
                    with st.expander(f"#{i+1} - {row['Name'][:80]}..."):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write(f"💰 Price: RM{row['Price (RM)']}")
                            st.write(f"📊 Sales: {row['Sales']}")
                            st.write(f"⭐ Rating: {row['Rating']}")
                        with col2:
                            st.write(f"📍 Location: {row['Location']}")
                            st.write(f"🏪 Shop: {row['Shop']}")
                            st.write(f"💵 Monthly Revenue: RM{row['Est. Revenue (RM)']}")
                        st.markdown(f"[View Product]({row['Link']})")
                
            else:
                st.warning("No valid products found. Try a different keyword.")
        else:
            st.error("No results found. Please try a different keyword or try again later.")

st.markdown("""
---
### Tips for Better Results:
- Try using general keywords (e.g., 'korean bag' instead of specific model names)
- Include trending terms like 'viral', 'tiktok', 'korean'
- Search in English or Malay for better results
- If no results appear, wait a few seconds and try again
""")
