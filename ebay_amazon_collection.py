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
    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/114.0.5735.199 Safari/537.36"
            ),
            "Accept-Language": "de-DE,de;q=0.9,en-US,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,/;q=0.8",
            "Connection": "keep-alive",
        }
        response = requests.get(url, timeout=10, headers=headers)
        response.raise_for_status()  # Raise an HTTPError for bad responses
        return response.text
    except requests.RequestException as e:
        print(f"Error fetching URL {url}: {e}")
        return None


# Function to parse product details from the HTML page
def parse_product_page(html, source_name):
    soup = BeautifulSoup(html, 'html.parser')
    product_list = []

    try:
        # (Example logic: Adjust parsing logic per source, currently generalized)
        # Find all rows in the product offers list — adjust this based on website structure
        offer_rows = soup.find_all("li", class_="offer-row-class", limit=6)  # Replace with the actual class
        for row in offer_rows:
            product_name = row.find("span", class_="product-title-class").text.strip() if row.find("span",
                                                                                                   class_="product-title-class") else "N/A"
            seller = row.find("div", class_="seller-name-class").text.strip() if row.find("div",
                                                                                          class_="seller-name-class") else "Unknown"
            price = row.find("div", class_="price-class").text.strip() if row.find("div",
                                                                                   class_="price-class") else None
            if price:
                try:
                    price = float(price.replace("$", "").replace(",", "").strip())
                except ValueError:
                    price = None

            product_list.append({
                "Product Name": product_name,
                "Seller": seller,
                "Price": price,
                "Source": source_name
            })

    except Exception as e:
        print(f"Error parsing product page from {source_name}: {e}")

    return product_list


# Function to save product data into a SQLite database
def save_to_db(data, product_name, g7_price):
    try:
        # Connect to SQLite database
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

        # Save scraped data for eBay/Amazon sellers
        for product in data:
            cursor.execute('''
                INSERT INTO PRICE (Product, Date, Seller, Price, Source) 
                VALUES (?, ?, ?, ?, ?)
            ''', (
                product.get("Product Name", "N/A"),
                datetime.now().strftime("%Y-%m-%d"),
                product.get("Seller", "Unknown"),
                product.get("Price"),
                product.get("Source", "Unknown")
            ))

        # Handle "Our Company" price: Ensure only one "Our Company" entry per product
        cursor.execute('''
            SELECT COUNT(*) FROM PRICE 
            WHERE Product = ? AND Seller = "Our Company"
        ''', (product_name,))
        our_company_entry_exists = cursor.fetchone()[0] > 0

        if our_company_entry_exists:
            # Update "Our Company" price for this product
            cursor.execute('''
                UPDATE PRICE 
                SET Date = ?, Price = ? 
                WHERE Product = ? AND Seller = "Our Company"
            ''', (
                datetime.now().strftime("%Y-%m-%d"),
                g7_price,
                product_name
            ))
        else:
            # Insert new "Our Company" price
            cursor.execute('''
                INSERT INTO PRICE (Product, Date, Seller, Price, Source) 
                VALUES (?, ?, ?, ?, ?)
            ''', (
                product_name,  # Product name from Excel
                datetime.now().strftime("%Y-%m-%d"),  # Current date
                "Our Company",  # Custom seller
                g7_price,  # G7 price
                "Internal Data"  # Source
            ))

        # Commit changes to the database
        conn.commit()
        conn.close()
        print(f"Data for product '{product_name}' saved to SQLite database successfully.")
    except Exception as e:
        print(f"Error saving to database: {e}")


def remove_duplicates():
    try:
        # Connect to SQLite database
        conn = sqlite3.connect("products.db")
        cursor = conn.cursor()

        # Remove duplicates by creating a new table with unique records
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS PRICE_CLEAN AS
            SELECT DISTINCT * FROM PRICE;
        ''')

        # Drop the original table
        cursor.execute('DROP TABLE PRICE;')

        # Rename the clean table to PRICE
        cursor.execute('ALTER TABLE PRICE_CLEAN RENAME TO PRICE;')

        # Commit changes and close connection
        conn.commit()
        conn.close()
        print("Duplicate entries removed successfully.")
    except Exception as e:
        print(f"Error removing duplicates: {e}")

# Main function to coordinate the scraping process
def main():
    # Step 1: Read product URLs from Excel
    products = read_products("products.xlsx")

    # Step 2: Process each product entry
    for _, row in products.iterrows():
        product_name = row.get("Product name")
        ebay_url = row.get("Ebay URL")
        amazon_url = row.get("Amazon URL")
        g7_price = row.get("G7 Price")

        # Process eBay URL
        if ebay_url and isinstance(ebay_url, str):
            print(f"Fetching eBay data for: {product_name} | URL: {ebay_url}")
            ebay_html = fetch_html(ebay_url)
            if ebay_html:
                ebay_product_details = parse_product_page(ebay_html, "eBay")
                save_to_db(ebay_product_details, product_name, g7_price)

        # Process Amazon URL
        if amazon_url and isinstance(amazon_url, str):
            print(f"Fetching Amazon data for: {product_name} | URL: {amazon_url}")
            amazon_html = fetch_html(amazon_url)
            if amazon_html:
                amazon_product_details = parse_product_page(amazon_html, "Amazon")
                save_to_db(amazon_product_details, product_name, g7_price)

    # Remove duplicates after all data is saved
    remove_duplicates()

if __name__ == "__main__":
    main()