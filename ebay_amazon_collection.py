import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import sqlite3
import time

# Function to save product details to the SQLite database
def save_to_db(data):
    try:
        conn = sqlite3.connect("products.db")
        cursor = conn.cursor()

        # Check if the PRICE table exists
        if not check_price_table_exists(conn):
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS PRICE (
                    ID INTEGER PRIMARY KEY AUTOINCREMENT,
                    Product TEXT,
                    Date TEXT,
                    Seller TEXT,
                    Price TEXT,
                    Source TEXT
                )
            ''')

        # Check if the same product, seller, and date already exist
        cursor.execute('''
            SELECT * FROM PRICE
            WHERE Product = ? AND Date = ? AND Seller = ?
        ''', (data["Product"], data["Date"], data["Seller"]))

        if cursor.fetchone():
            print(f"Duplicate entry found, skipping: {data}")
        else:
            # Insert data into the PRICE table
            cursor.execute('''
                INSERT INTO PRICE (Product, Date, Seller, Price, Source)
                VALUES (?, ?, ?, ?, ?)
            ''', (data["Product"], data["Date"], data["Seller"], data["Price"], data["Source"]))
            conn.commit()
            print("Data saved to database:", data)

        conn.close()
    except Exception as e:
        print(f"Error saving to database: {e}")


# Function to check if the PRICE table exists
def check_price_table_exists(conn):
    try:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT name FROM sqlite_master WHERE type='table' AND name='PRICE'
        ''')
        return cursor.fetchone() is not None
    except Exception as e:
        print(f"Error checking for PRICE table: {e}")
        return False

# Function to read products and URLs from Excel
def read_products(file_path):
    try:
        products = pd.read_excel(file_path)
        print(f"Successfully read {len(products)} product entries from {file_path}")
        return products
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        return pd.DataFrame()


# Function to fetch HTML content of a webpage
def fetch_html(url):
    try:
        response = requests.get(url, timeout=10, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.66 Safari/537.36"
        })
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"Error fetching URL {url}: {e}")
        return None

# Function to parse eBay product pages
def parse_ebay_page(html):
    soup = BeautifulSoup(html, 'html.parser')
    product_info = {"Product": "N/A", "Seller": "N/A", "Price": "N/A", "Source": "eBay"}

    try:
        product_title = soup.find("h1", {"class": "x-item-title__mainTitle"})
        if product_title:
            product_info["Product"] = product_title.text.replace("Details about", "").strip()

        price = soup.find("div", {"class": "x-price-primary"})
        if price:
            price_text = price.text
            euro_removed_price = price_text.replace("EUR", "").strip() # Remove Euro
            euro_removed_price2 = euro_removed_price.replace("€", "").strip() # Remove €
            cleaned_price = euro_removed_price2.replace(",", ".").strip()  # Remove commas
            final_price = float(cleaned_price) + 5.49  # Add delivery charges for eBay
            product_info["Price"] = f"{final_price:.2f}"  # Format to two decimal places

        seller = soup.find("h2", {"class": "x-store-information__store-name"})
        if seller:
            product_info["Seller"] = seller.text.strip()

    except Exception as e:
        print(f"Error parsing eBay page: {e}")

    return product_info

# Function to parse Amazon product pages
def parse_amazon_page(html):
    soup = BeautifulSoup(html, 'html.parser')
    product_info = {"Product": "N/A", "Seller": "N/A", "Price": "N/A", "Source": "Amazon"}

    try:
        # Extracting product title
        product_title = soup.find("span", {"id": "productTitle"})
        if product_title:
            product_info["Product"] = product_title.text.strip()

        # Extracting price
        price_whole = soup.find("span", {"class": "a-price-whole"})
        price_fraction = soup.find("span", {"class": "a-price-fraction"})

        price_text = f"{price_whole.text.strip()}.{price_fraction.text.strip()}"
        cleaned_price = price_text.replace(",", "").strip()  # Remove commas
        result = float(cleaned_price)
        final_price = result + 5.00  # Add delivery charges
        product_info["Price"] = f"{final_price:.2f}"  # Format to two decimal places

        # Extracting seller information
        seller = soup.find("a", {"id": "sellerProfileTriggerId"})
        if seller:
            product_info["Seller"] = seller.text.strip()
        else:
            # If "Seller" is N/A, try to extract from the "bylineInfo" section
            byline = soup.find("a", {"id": "bylineInfo", "class": "a-link-normal"})
            if byline and "Besuche den" in byline.text:
                product_info["Seller"] = byline.text.replace("Besuche den", "").strip()

    except Exception as e:
        print(f"Error parsing Amazon page: {e}")

    return product_info

# Main function
def main():
    while True:
        try:
            products = read_products("products.xlsx")

            for _, row in products.iterrows():
                product_name = row.get("Product name")
                amazon_url = row.get("Amazon URL")
                ebay_url = row.get("Ebay URL")

                if ebay_url and isinstance(ebay_url, str):
                    print(f"Fetching data for {product_name} (eBay) | URL: {ebay_url}")
                    html = fetch_html(ebay_url)
                    if html:
                        product_data = parse_ebay_page(html)
                        product_data["Date"] = datetime.now().strftime("%Y-%m-%d")
                        save_to_db(product_data)

                if amazon_url and isinstance(amazon_url, str):
                    print(f"Fetching data for {product_name} (Amazon) | URL: {amazon_url}")
                    html = fetch_html(amazon_url)
                    if html:
                        product_data = parse_amazon_page(html)
                        product_data["Date"] = datetime.now().strftime("%Y-%m-%d")
                        save_to_db(product_data)

            print("Waiting 24 hours before the next run...")
            time.sleep(86400)

        except Exception as e:
            print(f"An error occurred during the loop: {e}")
            break

if __name__ == "__main__":
    main()
