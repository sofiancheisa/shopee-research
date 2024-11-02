import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import time
import json

def get_shopee_products(keyword):
    url = "https://shopee.com.my/api/v4/search/search_items"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Referer': 'https://shopee.com.my/search?keyword=' + keyword,
        'Accept': '*/*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Connection': 'keep-alive',
        'DNT': '1'
    }
    
    params = {
        'by': 'relevancy',
        'keyword': keyword,
        'limit': 60,
        'newest': 0,
        'order': 'desc',
        'page_type': 'search',
        'scenario': 'PAGE_GLOBAL_SEARCH',
        'version': 2
    }

    try:
        response = requests.get(url, headers=headers, params=params)
        data = response.json()
        return data.get('items', [])
    except:
        return []

def main():
    st.title('Shopee Product Research Tool')

    # Input keywords
    keywords = st.text_area('Enter keywords (one per line):', 
        '''tiktok viral gadget
korean style bag
portable fan
mini vacuum
wireless earbuds''')

    # Filter settings
    col1, col2, col3 = st.columns(3)
    with col1:
        min_price = st.number_input('Min Price (RM)', value=50)
    with col2:
        max_price = st.number_input('Max Price (RM)', value=200)
    with col3:
        min_rating = st.number_input('Min Rating', value=4.5)

    if st.button('Search Products'):
        keywords_list = [k.strip() for k in keywords.split('\n') if k.strip()]
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        all_products = []
        
        # Search products
        for i, keyword in enumerate(keywords_list):
            status_text.text(f'Searching for: {keyword}')
            
            items = get_shopee_products(keyword)
            
            for item in items:
                try:
                    price = float(item.get('item_basic', {}).get('price', 0)) / 100000
                    if min_price <= price <= max_price:
                        product = {
                            'keyword': keyword,
                            'name': item.get('item_basic', {}).get('name', ''),
                            'price': price,
                            'sales': item.get('item_basic', {}).get('historical_sold', 0),
                            'rating': float(item.get('item_basic', {}).get('item_rating', {}).get('rating_star', 0)),
                            'stock': item.get('item_basic', {}).get('stock', 0),
                            'shop_location': item.get('item_basic', {}).get('shop_location', ''),
                            'shopid': item.get('item_basic', {}).get('shopid', ''),
                            'itemid': item.get('item_basic', {}).get('itemid', '')
                        }
                        
                        if product['rating'] >= min_rating:
                            product['product_url'] = f"https://shopee.com.my/product/{product['shopid']}/{product['itemid']}"
                            all_products.append(product)
                except:
                    continue
            
            progress_bar.progress((i + 1) / len(keywords_list))
            time.sleep(1)
        
        if all_products:
            # Convert to DataFrame
            df = pd.DataFrame(all_products)
            
            # Calculate potential
            df['daily_sales'] = df['sales'] / 30
            df['potential_commission'] = df['price'] * 0.20
            df['daily_potential'] = df['daily_sales'] * df['potential_commission']
            
            # Sort and display
            df = df.sort_values('daily_potential', ascending=False)
            
            # Format numbers
            df['price'] = df['price'].round(2)
            df['daily_potential'] = df['daily_potential'].round(2)
            
            st.write(f'### Found {len(df)} Products:')
            st.dataframe(df)
            
            # Download button
            csv = df.to_csv(index=False)
            st.download_button(
                label="Download Results as CSV",
                data=csv,
                file_name=f"shopee_research_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv"
            )
        else:
            st.warning('No products found. Try different keywords or adjust your filters.')

if __name__ == '__main__':
    main()
