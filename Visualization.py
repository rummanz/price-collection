import matplotlib.pyplot as plt
from matplotlib import rcParams
from matplotlib import font_manager

# Set the font to DejaVu Sans, which includes a wide range of glyphs
rcParams['font.family'] = 'DejaVu Sans'

# Ensure DejaVu Sans is used for all text elements
font_manager.findSystemFonts(fontpaths=None, fontext='ttf')
plt.rcParams['font.family'] = 'DejaVu Sans'

import sqlite3
import pandas as pd
from datetime import datetime
import seaborn as sns
import os


def connect_to_db(db_path):
    """
    Establishes connection to database
    """
    try:
        connection = sqlite3.connect(db_path)
        print("Successfully connected to the database")
        return connection
    except sqlite3.Error as err:
        print(f"Error: {err}")
        return None


def get_price_data(connection):
    """
    Retrieves price data from the PRICE table
    """
    query = """
        SELECT *
        FROM PRICE
        ORDER BY Product, Date
    """
    try:
        df = pd.read_sql(query, connection)
        if df.empty:
            print("No data found in the PRICE table")
        return df
    except Exception as e:
        print(f"Error retrieving data: {e}")
        return pd.DataFrame()


def create_visualization(df, product_name):
    """
    Creates three plots for a given product:
    1. Minimum price vs our price
    2. Average price vs our price
    3. Our price rank
    """
    if df.empty:
        print(f"No data available for product: {product_name}")
        return None

    # Set up the plotting style using seaborn
    sns.set_theme(style="whitegrid")

    # Create figure and subplots
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(10, 12))
    fig.suptitle(f'Price Analysis for {product_name}', fontsize=14)

    # Convert Date to datetime if it's not already
    df.loc[:, 'Date'] = pd.to_datetime(df['Date'], errors='coerce')

    # Ensure 'Price' is a numeric column (convert if necessary)
    df.loc[:, 'Price'] = pd.to_numeric(df['Price'], errors='coerce')

    # Drop rows with missing values
    df = df.dropna(subset=['Date', 'Price'])

    # Check for missing values
    if df.empty:
        print(f"All data for product: {product_name} is missing or invalid")
        return None

    # Get data for "Our company"
    our_data = df[df['Seller'] == 'Our company']
    other_data = df[df['Seller'] != 'Our company']

    # Group by date for statistics
    daily_stats = other_data.groupby('Date').agg({
        'Price': ['min', 'mean']
    }).reset_index()
    daily_stats.columns = ['Date', 'Min_Price', 'Avg_Price']

    # Calculate daily ranks
    def get_rank(group):
        our_company_price = group[group['Seller'] == 'Our company']['Price']
        if not our_company_price.empty:
            return our_company_price.iloc[0].rank(method='min')
        else:
            return float('nan')  # If no data for 'Our company', return NaN

    ranks = df.groupby('Date').apply(get_rank, include_groups=False).reset_index()
    ranks.columns = ['Date', 'Rank']

    # Plot 1: Minimum Price vs Our Price
    sns.lineplot(data=daily_stats, x='Date', y='Min_Price', ax=ax1, label='Minimum Market Price', color='blue')
    sns.lineplot(data=our_data, x='Date', y='Price', ax=ax1, label='Our Price', color='red', linestyle='--')
    ax1.set_ylabel('Price (€)', fontsize=10)
    ax1.set_title('Minimum Market Price vs Our Price', fontsize=12)

    # Plot 2: Average Price vs Our Price
    sns.lineplot(data=daily_stats, x='Date', y='Avg_Price', ax=ax2, label='Average Market Price', color='green')
    sns.lineplot(data=our_data, x='Date', y='Price', ax=ax2, label='Our Price', color='red', linestyle='--')
    ax2.set_ylabel('Price (€)', fontsize=10)
    ax2.set_title('Average Market Price vs Our Price', fontsize=12)

    # Plot 3: Price Rank
    sns.lineplot(data=ranks, x='Date', y='Rank', ax=ax3, color='blue')
    ax3.set_ylabel('Rank', fontsize=10)
    ax3.set_xlabel('Date', fontsize=10)
    ax3.set_title('Our Price Rank (1 = Lowest Price)', fontsize=12)
    ax3.invert_yaxis()  # Lower rank (better) should be at the top

    # Adjust layout to prevent overlap
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])

    # Save the figure
    filename = f"{datetime.now().strftime('%Y%m%d')}_prices.pdf"
    if os.path.exists(filename):
        os.remove(filename)  # Remove the file if it already exists
    plt.savefig(filename, bbox_inches='tight', dpi=300)
    plt.close()

    return filename


def main():
    # Use the full path to your database
    db_path = 'C:/Users/udwal/price-collection/products.db'

    # Connect to database
    connection = connect_to_db(db_path)
    if not connection:
        return

    try:
        # Get data
        df = get_price_data(connection)
        if df.empty:
            print("No data found in the database")
            return

        # Create visualizations for each product
        for product in df['Product'].unique():
            product_df = df[df['Product'] == product]
            filename = create_visualization(product_df, product)
            if filename:
                print(f"Created visualization for {product}: {filename}")

    except Exception as e:
        print(f"Error occurred: {str(e)}")
    finally:
        connection.close()


if __name__ == "__main__":
    main()