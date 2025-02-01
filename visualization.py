import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import pandas as pd
import mysql.connector
import unicodedata
import re
from sqlalchemy import create_engine
from dotenv import load_dotenv
import time
import sys
import os

def main():
    load_dotenv()

    engine = create_engine(os.getenv('DATABASE_URL'))

    # Create SQLAlchemy engine
    #engine = create_engine('mysql+mysqlconnector://root:admin123@localhost/udval_products')
    #engine = create_engine(os.getenv('DATABASE_URL'))

    # Query the database and load data into a DataFrame
    query = 'SELECT Product, Date, Price, Source FROM PRICE1 ORDER BY Product, Date'
    df = pd.read_sql(query, con=engine)

    # Define fixed prices dictionary
    fixed_prices = {
        'Apple Watch Ultra': 689.99,
        'Apple Watch Ultra 2': 839.99,
        'Garmin Epix Pro Gen 2': 699.99,
        'Garmin fenix 7 Pro': 619.99,
        'Garmin fenix 7X Pro': 699.99,
        'Garmin Forerunner 255': 239.99,
        'Garmin Forerunner 965': 559.99,
        'Garmin Venu 3': 409.99,
        'Garmin Venu 3S': 389.99,
        'Withings ScanWatch 2': 129.99,
    }

    # Clean the data
    df['Price'] = pd.to_numeric(df['Price'], errors='coerce')
    df_cleaned = df.dropna(subset=['Price'])
    df_cleaned.reset_index(drop=True, inplace=True)


    # Normalize text function
    def normalize_text(text):
        text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('utf-8')
        text = re.sub(r'[^\w\s\-,/_]', '', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()


    # Apply normalization to the 'Product' column
    df_cleaned.loc[:, 'Product'] = df_cleaned['Product'].apply(normalize_text)

# Define product categories and their corresponding grouping keywords
    categories = {
        'Apple Watch Ultra 2': ['Apple Watch Ultra 2'],
        'Apple Watch Ultra': ['Apple Watch Ultra'],
        'Garmin Epix Pro Gen 2': ['Epix'],
        'Garmin Venu 3S': ['Garmin Venu 3S'],
        'Garmin Venu 3': ['Garmin Venu 3'],
        'Garmin fenix 7X Pro': ['Garmin fenix 7X Pro'],
        'Garmin fenix 7 Pro': ['Garmin fenix 7 Pro'],
        'Garmin Forerunner 965': ['Forerunner 965'],
        'Garmin Forerunner 255': ['Forerunner 255'],
        'Withings ScanWatch 2': ['Withings'],
    }

# Function to categorize products based on their names
    def categorize_product(product_name):
        for category, keywords in categories.items():
            if any(keyword.lower() in product_name.lower() for keyword in keywords):
                return category
        return None


# Add a new column for category
    df_cleaned = df_cleaned.copy()  # Make a copy to avoid the warning
    df_cleaned['Category'] = df_cleaned['Product'].apply(categorize_product)


# Remove rows with None category
    df_cleaned = df_cleaned[df_cleaned['Category'].notna()]

    # Convert 'Date' to datetime
    df_cleaned['Date'] = pd.to_datetime(df_cleaned['Date'])

    # Define the function to generate PDFs for each category
def generate_category_pdf(df_cleaned, fixed_prices, categories):
        # Loop through each category and generate the PDF
    for category in categories:
        # Filter data for this category
        category_data = df_cleaned[df_cleaned['Category'] == category]

        # Data for other Sources (average price)
        other_price_data = category_data[category_data['Source'] != 'Our company']

        # Get the fixed price for this category
        fixed_price = fixed_prices.get(category)

        # Generate a PDF for each category
        pdf_filename = f'Price_Report_{category.replace(" ", "_")}.pdf'

        with PdfPages(pdf_filename) as pdf:
            # Plotting Average Price
            plt.figure(figsize=(10, 6))
            if not other_price_data.empty:
                avg_price_other = other_price_data.groupby('Date')['Price'].mean().reset_index()
                plt.plot(avg_price_other['Date'], avg_price_other['Price'], label='Other Sources (Average)', color='red', marker='o')

            if fixed_price is not None:
                plt.axhline(y=fixed_price, color='blue', linestyle='--', label='Our Company (Fixed Price)')
            plt.title(f"Average Price Over Time for {category}")
            plt.xlabel('Date')
            plt.ylabel('Price')
            plt.grid(True)
            plt.xticks(rotation=45)
            plt.tight_layout()
            plt.legend()
            pdf.savefig()  # Save the current figure to the PDF
            plt.close()

            # Plotting Minimum Price
            plt.figure(figsize=(10, 6))
            if not other_price_data.empty:
                min_price_other = other_price_data.groupby('Date')['Price'].min().reset_index()
                plt.plot(min_price_other['Date'], min_price_other['Price'], label='Other Sources (Minimum)', color='red', marker='o')

            if fixed_price is not None:
                plt.axhline(y=fixed_price, color='blue', linestyle='--', label='Our Company (Fixed Price)')
            plt.title(f"Minimum Price Over Time for {category}")
            plt.xlabel('Date')
            plt.ylabel('Price')
            plt.grid(True)
            plt.xticks(rotation=45)
            plt.tight_layout()
            plt.legend()
            pdf.savefig()  # Save the current figure to the PDF
            plt.close()

            # Plotting Price Ranking
            all_price_data = category_data[category_data['Source'] != 'Our company']

            plt.figure(figsize=(10, 6))
            if not all_price_data.empty:
                price_groups = category_data.groupby('Date')
                ranking_data = []
                for date, group in price_groups:
                    all_prices = group['Price']
                    rank = (all_prices <= fixed_price).sum()
                    ranking_data.append({'Date': date, 'Rank': rank})

                ranking_data = pd.DataFrame(ranking_data)
                plt.plot(ranking_data['Date'], ranking_data['Rank'], label='Our Price Ranking', color='green', marker='o')

            plt.title(f"Price Ranking Over Time for {category}")
            plt.xlabel('Date')
            plt.ylabel('Rank (Position Among Sources)')
            plt.grid(True)
            plt.xticks(rotation=45)
            plt.tight_layout()
            plt.legend()
            pdf.savefig()  # Save the current figure to the PDF
            plt.close()

    # Generate PDFs for each category
    generate_category_pdf(df_cleaned, fixed_prices, categories)

    # Close the database connection
    engine.dispose()

if __name__ == "__main__":
    main()
