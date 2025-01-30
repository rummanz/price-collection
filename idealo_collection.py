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

load_dotenv()

# Function to read products and URLs from Excel
def read_excel(file_path):
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
  "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
  "accept-encoding": "gzip, deflate, br, zstd",
  "accept-language": "en-US,en;q=0.9,de-DE;q=0.8,de;q=0.7",
  "cache-control": "max-age=0",
  "cookie": "_cmp_controllerid=cf9a98f1fe158df23e63f7e05f659bd5686a8b5c57f0b4a28518fb1c326c9829; trackingid=9cf422e1-2af9-4d6b-8cc0-5e5bdc98aaaa; consentStatus=true; xp_seed_p=c2855; fs_sampled=false; _gcl_au=1.1.477155101.1737071014; sp=aa8ef104-fc6c-42ba-9bdf-3101427bb49d; FPAU=1.1.477155101.1737071014; _tt_enable_cookie=1; _ttp=gu0w-t0tmpRzMjQii1GHTMteQvt.tt.1; _fbp=fb.1.1737071015637.332911955219135486; crto_is_user_optout=false; crto_mapped_user_id=oTpIyd_lj2Hrtvy-8bxKIBvwewcUrvFx; sessionid=1738258379748_6af35aa5-a0e2-a54a-9861-83696909e454; ttrjm=23853872-477a-c2c2-0742-e37aa57f4d35; JSESSIONID=962255957BDCC93A338797C25A5D6D76; bm_mi=B97BA577D6E90DA7D68CFF48E77DA2A0~YAAQF09lXw8VsqiUAQAAPvpFuBqYBfccj1kwJW2ua1AzqFP7VrbBDgjjfFMP6tZphzucmuqAfSJI2utIgLXfW7Y3I5S4sSI/BdsIRT7nho+s2/HYsYTsr602MHfTB3yqvCeATnhLYdr/PcMDI64MQK2cizvQqe7fUPws1kMpzd0CGmldInw1lxw38rD7m92ykcbPnD1YLG+yLGm1gXTUvrRqVizDmBPX5Mumq+Z0sTncmh7dr8VvEuAmdpVGToU5aLD5PCRMbaD7zpHvH9JJVZNGz0SgilLM2cEvbnoix7xtvyR/DObuwv37nQ0pILmj7G15U6hW6RcM51iMCf+VqqM/tUXP+lz4XbBuJvJ5qTjwzQLOqQ==~1; ak_bmsc=A3ECB184B10CDC7AC31395125199C8A7~000000000000000000000000000000~YAAQFE9lX2jcfaiUAQAAqf1FuBpGFIvRL1LjkDLfokCHDB6pI8GAyIFAub2Y1vQgy+LfSFEbxmiINubw0sBNSCmXtBhAinFOV2shd8WlgrjW0rowuD64fxz13YYIegpgWRBPEthKfwQHnDGXco+EGCBeZnC+Ln1ZGZTwChS9mG8KU+FMJ6GhQ7lCNtJa60Fu8YKSjS0cEST5+sIuY9CWfBbR/cD/qkBXP6v9hwV35mpMFckKqD4tUsaIh3wPUsGSpjQ59isdL1U21v4XYWjxROukVlCfqoXCjaul8gdNtLi8xwQnAICYTdz9+b74oLg8hBcIshVhVLbNcghAWRy9RSoKLaQwJSOYzoq8tYdJA4LdKV2JNzBWLoO876ljFY/PBojv9TIOgaOVb/rSak9pRRM8YAGOlvnticB8F9oghfNn5szRPJKRQ0OSPnMpOFKJBOioVllfaJkLYSbJrz4fpskcfFHKm048/xonQIWSCYKgX2M8oy9dqWPvkts7Y7mhbQGFOysN2hFR+1A=; _tq_id.TV-7245903663-1.f8ad=b658cf4ecf9b9258.1737071014.0.1738258383..; __rtbh.lid=%7B%22eventType%22%3A%22lid%22%2C%22id%22%3A%22e9lgDiwEhNvO21q4iSZ6%22%2C%22expiryDate%22%3A%222026-01-30T17%3A33%3A03.631Z%22%7D; _uetsid=7f792d60defa11efb1fd4189e9ecb4f1; _uetvid=b40ec080d46311ef9de67f8643850af7",
  "dnt": "1",
  "priority": "u=0, i",
  "sec-ch-ua": "\"Google Chrome\";v=\"131\", \"Chromium\";v=\"131\", \"Not_A Brand\";v=\"24\"",
  "sec-ch-ua-mobile": "?0",
  "sec-ch-ua-platform": "\"Linux\"",
  "sec-fetch-dest": "document",
  "sec-fetch-mode": "navigate",
  "sec-fetch-site": "none",
  "sec-fetch-user": "?1",
  "upgrade-insecure-requests": "1",
  "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
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
# Function to save product details to the MySQL database
def save_to_db(product_data, product_name, g7_price, product_id):
    try:
        # Connect to the MariaDB database
        conn = mysql.connector.connect(
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME")
        )

        if conn.is_connected():
            cursor = conn.cursor()

            # Ensure the PRICE table exists
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS PRICE1 (
                    ID INT AUTO_INCREMENT PRIMARY KEY,
                    Product VARCHAR(255),
                    Date DATE,
                    Seller VARCHAR(255),
                    Price FLOAT,
                    Source VARCHAR(255),
		    ProductId VARCHAR(50)
                )
            ''')

            # Insert scraped data into the database
            for product in product_data:
                try:
                    cursor.execute('''
                        INSERT INTO PRICE1 (Product, Date, Seller, Price, Source, ProductId)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    ''', (
                        product.get("Product Name", product_name),  # Default to Excel name if missing
                        datetime.now().strftime("%Y-%m-%d"),  # Current date
                        product.get("Seller", "N/A"),  # Seller
                        product.get("Price", 0.0),  # Price
                        "Idealo",  # Source
			product_id
                    ))
                except Error as e:
                    print(f"Error inserting row: {e}")

            # Add "Our company" row with G7 Price
            try:
                cursor.execute('''
                    INSERT INTO PRICE1 (Product, Date, Seller, Price, Source, ProductId)
                    VALUES (%s, %s, %s, %s, %s, %s)
                ''', (
                    product_name,
                    datetime.now().strftime("%Y-%m-%d"),
                    "Our company",
                    g7_price,
                    "Our company",
		    product_id
                ))
            except Error as e:
                print(f"Error inserting 'Our company' row: {e}")

            conn.commit()
            print("Data saved to database.")
            cursor.close()
            conn.close()

    except Error as e:
        print(f"Error saving to database: {e}")


# Main function to coordinate the scraping process
def main():
    # Step 1: Read product URLs from Excel
    products = read_excel("products.xlsx")

    # Step 2: Process each product entry
    for _, row in products.iterrows():
        product_name = row.get("Product name")  # From Excel file
        idealo_url = row.get("Idealo URL")  # Assuming Idealo URLs are in the second column
        g7_price = row.get("G7 Price")  # G7 Price column
        product_id = row.get("ProductId")

        if idealo_url and isinstance(idealo_url, str):  # Ensure URL exists and is a string
            print(f"Fetching data for {product_name} | URL: {idealo_url}")
            html = fetch_html(idealo_url)
            if html:
                product_details = parse_product_page(html)
                if product_details:
                    save_to_db(product_details, product_name, g7_price, product_id)

if __name__ == "__main__":
    main()

# sources - https://ioflood.com/blog/python-isinstance-function-guide-with-examples/#:~:text=The%20isinstance()%20function%20in%20Python%20is%20a%20built%2Din,Python
