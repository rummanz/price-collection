import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import sqlite3

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
    header_var = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0',
        'referer': 'https://www.idealo.de/',
        'Origin': 'https://www.idealo.de',
        'content-type': 'application/json; charset=utf-8',
    }
    try:
        response = requests.get(url, timeout=10, headers=header_var)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"Error fetching URL {url}: {e}")
        return None

# Function to parse product details from the HTML page
def parse_product_page(html):
    soup = BeautifulSoup(html, 'html.parser')
    product_list = []

    try:
        # Find all rows in the product offers list
        offer_rows = soup.find_all("li", {"class": "productOffers-listItem"}, limit=6)
        for row in offer_rows:
            product_info = {}

            # Extract product name
            product_name_tag = row.find("span", {"class": "productOffers-listItemTitleInner"})
            product_name = product_name_tag.text.strip() if product_name_tag else "N/A"

            # Extract price
            price_details_tag = row.find("div", {"class": "productOffers-listItemOfferShippingDetails"})
            if price_details_tag:
                price = price_details_tag.text.strip().replace("inkl. Versand", "").strip()
                price = price.replace("\u00a0", " ")  # Handle non-breaking space
                price = price.replace(".", "").replace(",", ".")  # Convert to standard float format
                price = price.replace("\u20ac", "").strip()  # Remove euro sign
                #Print ("Success", Price)
                try:
                    price = float(price)  # Convert to float
                except ValueError:
                    price = None
            else:
                price = None

            # Extract seller name
            seller_tag = row.find("a", {"class": "productOffers-listItemOfferShopV2LogoLink"})
            seller_name = seller_tag["data-shop-name"] if seller_tag and "data-shop-name" in seller_tag.attrs else "N/A"

            product_info = {
                "Product Name": product_name,
                "Seller": seller_name,
                "Price": price
            }

            # Append the product info to the list
            product_list.append(product_info)
    except Exception as e:
        print(f"Error parsing product page: {e}")

    return product_list

# Function to save product details to the SQLite database
def save_to_db(data, product_name, g7_price):
    try:
        if not isinstance(data, list):
            print("Error: Product data is not a list:", data)
            return

        conn = sqlite3.connect("products.db")
        cursor = conn.cursor()

        # Ensure the PRICE table exists
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS PRICE (
                Product TEXT,
                Date TEXT,
                Seller TEXT,
                Price REAL,
                Source TEXT
            )
        ''')

        # Insert scraped data
        for product in data:
            try:
                price = float(product.get("Price", 0))  # Fetch price and convert to float
            except (ValueError, TypeError):
                price = None

            cursor.execute('''
                INSERT INTO PRICE (Product, Date, Seller, Price, Source) 
                VALUES (?, ?, ?, ?, ?)
            ''', (
                product.get("Product Name", "N/A"),
                datetime.now().strftime("%Y-%m-%d"),
                product.get("Seller", "N/A"),
                price,
                "Idealo"
            ))

        # Insert G7 Price row
        cursor.execute('''
            INSERT INTO PRICE (Product, Date, Seller, Price, Source) 
            VALUES (?, ?, ?, ?, ?)
        ''', (
            product_name,  # Product name from Excel
            datetime.now().strftime("%Y-%m-%d"),  # Current date
            "Our company",  # Seller
            g7_price,  # G7 Price from Excel
            "Our company"  # Source
        ))

        conn.commit()
        conn.close()
        print("Data saved to database.")
    except Exception as e:
        print(f"Error saving to database: {e}")

# Main function to coordinate the scraping process
def main():
    # Step 1: Read product URLs from Excel
    products = read_products("products.xlsx")

    # Step 2: Process each product entry
    for _, row in products.iterrows():
        product_name = row.get("Product name")  # From Excel file
        idealo_url = row.get("Idealo URL")  # Assuming Idealo URLs are in the second column
        # g7_price = row.get("G7 Price")  # G7 Price column for earlier iteration

        if idealo_url and isinstance(idealo_url, str):  # Ensure URL exists and is a string
            print(f"Fetching data for {product_name} | URL: {idealo_url}")
            html = fetch_html(idealo_url)
            if html:
                product_details = parse_product_page(html)
                if product_details:
                    save_to_db(product_details, product_name, g7_price)

if __name__ == "__main__":
    main()
