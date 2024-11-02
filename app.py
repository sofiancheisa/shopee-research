import streamlit as st
import requests
import pandas as pd
import json
import time
from datetime import datetime
from urllib.parse import quote

def get_shopee_data(keyword):
    encoded_keyword = quote(keyword)
    url = f"https://shopee.com.my/api/v4/search/search_items?by=relevancy&keyword={encoded_keyword}&limit=60&newest=0&order=desc&page_type=search&scenario=PAGE_GLOBAL_SEARCH&version=2"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2",
        "Accept": "application/json",
        "Accept-Language": "en-US,en;q=0.5",
        "Referer": "https://shopee.com.my/search?keyword=" + encoded_keyword,
        "X-Requested-With": "XMLHttpRequest",
        "af-ac-enc-dat": "null",
        "Cookie": "SPC_F=test; REC_T_ID=test;",
    }

    try:
        response = requests.get(
            url,
            headers=headers,
            timeout=10
        )
        return response.json()
    except Exception as e:
        st.error(f"Error fetching data: {str(e)}")
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
                        product = {
                            'Name': basic.get('name', 'N/A')[:100],
                            'Price (RM)': round(float(basic.get('price', 0)) / 100000, 2),
                            'Sales': basic.get('historical_sold', 0),
                            'Rating': round(float(basic.get('item_rating', {}).get('rating_star', 0)), 1),
                            'Stock': basic.get('stock', 0),
                            'Location': basic.get('shop_location', 'N/A'),
                            'Monthly Sales': round(float(basic.get('historical_sold', 0)) / 3, 1),
                            'Shop': basic.get('shop_name', 'N/A'),
                            'Link': f"https://shopee.com.my/{quote(basic.get('name', '').replace(' ', '-'))}-i.{basic.get('shopid')}.{basic.get('itemid')}"
                        }
                        product['Est. Revenue (RM)'] = round(product['Price (RM)'] * product['Monthly Sales'], 2)
                        products.append(product)
                    except:
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
""")
