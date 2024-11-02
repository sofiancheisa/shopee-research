import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import time

st.title('Shopee Product Research Tool')

# Input keywords
keywords = st.text_area('Enter keywords (one per line):', 
    '''korean fashion
wireless earbuds
phone holder
makeup brush
smart watch''')

# Filter settings
col1, col2, col3 = st.columns(3)
with col1:
    min_price = st.number_input('Min Price (RM)', value=50)
with col2:
    max_price = st.number_input('Max Price (RM)', value=200)
with col3:
    min_rating = st.number_input('Min Rating', value=4.5)

if st.button('Search Products'):
    keywords_list = keywords.split('\n')
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    products = []
    
    # Search products
    for i, keyword in enumerate(keywords_list):
        status_text.text(f'Searching for: {keyword}')
        
        try:
            response = requests.get(
                "https://shopee.com.my/api/v4/search/search_items",
                params={
                    "keyword": keyword,
                    "limit": 50,
                    "page_type": "search"
                },
                headers={"User-Agent": "Mozilla/5.0"}
            )
            
            data = response.json()
            
            if 'items' in data:
                for item in data['items']:
                    # Ensure item_basic has required keys
                    if ('item_basic' in item and
                        'name' in item['item_basic'] and
                        'price' in item['item_basic'] and
                        'historical_sold' in item['item_basic'] and
                        'item_rating' in item['item_basic'] and
                        'rating_star' in item['item_basic']['item_rating'] and
                        'stock' in item['item_basic']):
                        
                        product = {
                            'name': item['item_basic']['name'],
                            'price': item['item_basic']['price'] / 100000,
                            'sales': item['item_basic']['historical_sold'],
                            'rating': item['item_basic']['item_rating']['rating_star'],
                            'stock': item['item_basic']['stock'],
                            'product_url': f"https://shopee.com.my/product/{item['item_basic']['shopid']}/{item['item_basic']['itemid']}"
                        }
                        products.append(product)
                    else:
                        st.write(f"Missing expected keys in item: {item}")
            
            progress_bar.progress((i + 1) / len(keywords_list))
            time.sleep(1)
            
        except Exception as e:
            st.error(f"Error searching {keyword}: {e}")
            continue
    
    # Convert to DataFrame if products list is not empty
    if products:
        df = pd.DataFrame(products)
        
        # Apply filters if df is not empty
        if not df.em
