import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
import time
import sys
import os

# Load environment variables from .env file
load_dotenv()

# Function to save product details to the MariaDB database
def save_to_db(data):
    try:
        # Connect to the MariaDB database
        conn = mysql.connector.connect(
            host= os.getenv("DB_HOST"),
            user= os.getenv("DB_USER"),
            password= os.getenv("DB_PASSWORD"),
            database= os.getenv("DB_NAME")
        )

        if conn.is_connected():
            cursor = conn.cursor()

            # Check if the PRICE1 table exists
            if not check_price_table_exists(cursor):
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS PRICE1 (
                    ID INT AUTO_INCREMENT PRIMARY KEY,
                    Product VARCHAR(255) COLLATE utf8mb4_unicode_ci,
                    Date VARCHAR(255) COLLATE utf8mb4_unicode_ci,
                    Seller VARCHAR(255) COLLATE utf8mb4_unicode_ci,
                    Price VARCHAR(255) COLLATE utf8mb4_unicode_ci,
                    Source VARCHAR(255) COLLATE utf8mb4_unicode_ci,
                    ProductId VARCHAR(5) COLLATE utf8mb4_unicode_ci
                ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
            ''')

            # Always insert the data without checking for duplicates
            cursor.execute('''
                INSERT INTO PRICE1 (Product, Date, Seller, Price, Source, ProductId)
                VALUES (%s, %s, %s, %s, %s, %s)
            ''', (data["Product"], data["Date"], data["Seller"], data["Price"], data["Source"], data["ProductId"]))
            conn.commit()
            print("Data saved to database:", data)

            cursor.close()
            conn.close()

    except Error as e:
        print(f"Error saving to database: {e}")

# Function to check if the PRICE table exists in the MariaDB database
def check_price_table_exists(cursor):
    try:
        cursor.execute('''
            SHOW TABLES LIKE 'PRICE1'
        ''')
        return cursor.fetchone() is not None
    except Error as e:
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
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/114.0.5735.199 Safari/537.36"
            ),
            "Accept-Language": "de-DE,de;q=0.9,en-US,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Connection": "keep-alive",
        }
        response = requests.get(url, timeout=10, headers=headers)
        response.raise_for_status()  # Raise an HTTPError for bad responses
        return response.text
    except requests.RequestException as e:
        print(f"Error fetching URL {url}: {e}")
        return None

# Function to parse eBay product pages
def parse_ebay_page(html):
    soup = BeautifulSoup(html, 'html.parser')
    product_info = {"Product": "N/A", "Seller": "N/A", "Price": "N/A", "Source": "eBay"}

    try:
        # Extracting product title
        product_title = soup.find("h1", {"class": "x-item-title__mainTitle"})
        if product_title:
            product_info["Product"] = product_title.text.replace("Details about", "").strip()

        # Extracting price
        price = soup.find("div", {"class": "x-price-primary"})
        if price:
            price_text = price.text
            euro_removed_price = price_text.replace("EUR", "").strip() # remove Euro
            euro_removed_price2 = euro_removed_price.replace("€", "").strip() # remove €
            cleaned_price = euro_removed_price2.replace(",", ".").strip()  # remove commas
            final_price = float(cleaned_price) + 5.49  # add delivery charges for eBay
            product_info["Price"] = f"{final_price:.2f}"  # format to two decimal places

        # Extracting seller information
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

        #previous code - thousand value did not work
        # price_text = f"{price_whole.text.strip()}.{price_fraction.text.strip()}"
        # cleaned_price = price_text.replace(",", "").strip()  # Remove commas
        # result = float(cleaned_price)
        # final_price = result + 5.00  # Add delivery charges
        # product_info["Price"] = f"{final_price:.2f}"  # Format to two decimal places

        if price_whole and price_fraction:
            price_text = f"{price_whole.text.strip()}.{price_fraction.text.strip()}"

            # remove the thousand separator and clean the price
            cleaned_price = price_text.replace(".", "")
            cleaned_price2 = cleaned_price.replace(",", ".").strip()

            # convert to float
            result = float(cleaned_price2)
            final_price = result + 5.00  # add delivery charges for Amazon
            product_info["Price"] = f"{final_price:.2f}"  # format to two decimal places
        else:
            product_info["Price"] = "Price not found"

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
        try:
            products = read_products("products.xlsx")

            for _, row in products.iterrows():
                product_name = row.get("Product name")
                amazon_url = row.get("Amazon URL")
                ebay_url = row.get("Ebay URL")
                product_id = row.get("ProductId")  # Get ProductId from Excel


                if ebay_url and isinstance(ebay_url, str):
                    print(f"Fetching data for {product_name} (eBay) | URL: {ebay_url}")
                    html = fetch_html(ebay_url)
                    if html:
                        product_data = parse_ebay_page(html)
                        product_data["Date"] = datetime.now().strftime("%Y-%m-%d")
                        product_data["ProductId"] = product_id  # Add ProductId to data
                        save_to_db(product_data)

                if amazon_url and isinstance(amazon_url, str):
                    print(f"Fetching data for {product_name} (Amazon) | URL: {amazon_url}")
                    html = fetch_html(amazon_url)
                    if html:
                        product_data = parse_amazon_page(html)
                        product_data["Date"] = datetime.now().strftime("%Y-%m-%d")
                        product_data["ProductId"] = product_id  # Add ProductId to data
                        save_to_db(product_data)

            print("Done!")

        except Exception as e:
            print(f"An error occurred during the loop: {e}")

if __name__ == "__main__":
    main()
