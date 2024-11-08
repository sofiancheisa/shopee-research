headers = {
    "User-Agent": "Mozilla/5.0",
    "Accept-Language": "en-US,en;q=0.9",
    "Connection": "keep-alive",
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://shopee.com.my/"
}
headers={
    "User-Agent": "Mozilla/5.0",
    "Accept-Language": "en-US,en;q=0.9",
    "Connection": "keep-alive"
}

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
            st.write(data)  # Ini akan paparkan data dari Shopee

            
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
        if not df.empty:
            filtered_df = df[
                (df['price'].between(min_price, max_price)) &
                (df['rating'] >= min_rating) &
                (df['stock'] > 50)
            ]
            
            # Calculate potential if filtered_df is not empty
            if not filtered_df.empty:
                filtered_df['daily_sales'] = filtered_df['sales'] / 30
                filtered_df['potential_commission'] = filtered_df['price'] * 0.20
                filtered_df['daily_potential'] = filtered_df['daily_sales'] * filtered_df['potential_commission']
                
                # Sort and display
                filtered_df = filtered_df.sort_values('daily_potential', ascending=False)
                st.write('### Top Products Found:')
                st.dataframe(filtered_df)
                
                # Download button
                csv = filtered_df.to_csv(index=False)
                st.download_button(
                    label="Download Results",
                    data=csv,
                    file_name=f"shopee_research_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                    mime="text/csv"
                )
            else:
                st.write("No products found within the specified filters.")
        else:
            st.write("No products found for the entered keywords.")
    else:
        st.write("No products retrieved from Shopee API.")
