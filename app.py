import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import time
import json

def search_shopee(keyword):
    url = "https://shopee.com.my/api/v4/search/search_items"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "X-Requested-With": "XMLHttpRequest",
        "Connection": "keep-alive",
    }
    
    params = {
        "keyword": keyword,
        "limit": 20,
        "newest": 0,
        "order": "desc",
        "page_type": "search",
        "version": 2
    }
    
    response = requests.get(url, headers=headers, params=params)
    return response.json()

st.title('Shopee Product Finder v2')

keyword = st.text_input('Enter search keyword:', 'wireless earbuds')

if st.button('Search'):
    st.write(f'Searching for: {keyword}')
    
    try:
        results = search_shopee(keyword)
        
        if 'items' in results and results['items']:
            products = []
            
            for item in results['items']:
                basic = item.get('item_basic', {})
                
                product = {
                    'name': basic.get('name', 'N/A'),
                    'price': basic.get('price', 0) / 100000,
                    'sales': basic.get('historical_sold', 0),
                    'rating': basic.get('item_rating', {}).get('rating_star', 0),
                    'location': basic.get('shop_location', 'N/A'),
                }
                
                products.append(product)
            
            df = pd.DataFrame(products)
            st.dataframe(df)
            
            # Download button
            csv = df.to_csv(index=False)
            st.download_button(
                "Download Data",
                csv,
                f"shopee_search_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                "text/csv"
            )
            
        else:
            st.error('No items found')
            
    except Exception as e:
        st.error(f'Error occurred: {str(e)}')
