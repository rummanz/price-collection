import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import os
import re
from datetime import datetime


# Function to create and save visualizations for each product
def create_product_pdf(df):
    # Get all unique products in the dataset
    products = df['Product'].unique()
    print(f"Found {len(products)} products: {products}")  # Debug: Print product list

    # Iterate over each product and create a PDF for it
    for product_name in products:
        try:
            # Filter the data for the current product (use .copy() to avoid SettingWithCopyWarning)
            product_data = df[df['Product'] == product_name].copy()

            # Filter only G7 data and non-G7 data
            g7_data = product_data[product_data['Seller'] == 'G7']
            other_sellers = product_data[product_data['Seller'] != 'G7']

            # Group by Date to calculate min and average prices for other sellers
            other_sellers_stats = other_sellers.groupby('Date').agg(
                Min_Price=('Price', 'min'),
                Avg_Price=('Price', 'mean')
            ).reset_index()

            # Add G7 price to stats for comparison
            g7_stats = g7_data[['Date', 'Price']].rename(columns={'Price': 'G7_Price'})

            # Merge stats for plotting
            comparison_data = pd.merge(other_sellers_stats, g7_stats, on='Date', how='inner')

            # Calculate rank for all sellers on each date
            product_data['Price_Rank'] = product_data.groupby('Date')['Price'].rank(ascending=True)

            # Create a sanitized product name for the filename
            safe_product_name = re.sub(r'[^\w\s-]', '', product_name).strip().replace(' ', '_')
            pdf_filename = f"{datetime.now().strftime('%Y%m%d')}_{safe_product_name}_price_analysis.pdf"

            # Save each PDF to an "output" directory
            output_dir = os.path.join(os.getcwd(), 'output')
            os.makedirs(output_dir, exist_ok=True)  # Create output directory if it doesn't exist
            file_path = os.path.join(output_dir, pdf_filename)

            # Create and save the PDF
            with PdfPages(file_path) as pdf:
                ### First Graph: Comparison of other sellers' min price vs G7 price ###
                plt.figure(figsize=(10, 6))
                plt.plot(comparison_data['Date'], comparison_data['Min_Price'], label='Other Sellers Min Price',
                         linestyle='--', color='red', marker='o')
                plt.plot(comparison_data['Date'], comparison_data['G7_Price'], label='G7 Price', linestyle='-',
                         color='blue', marker='o')
                plt.title(f"Comparison of Min Price: Other Sellers vs G7 ({product_name})", fontsize=16)
                plt.xlabel('Date', fontsize=14)
                plt.ylabel('Price', fontsize=14)
                plt.legend(title='Price Type', fontsize=10)
                plt.xticks(rotation=45)
                plt.grid(visible=True)
                pdf.savefig()  # Save the current figure to the PDF
                plt.close()

                ### Second Graph: Comparison of other sellers' average price vs G7 price ###
                plt.figure(figsize=(10, 6))
                plt.plot(comparison_data['Date'], comparison_data['Avg_Price'], label='Other Sellers Avg Price',
                         linestyle='-.', color='green', marker='o')
                plt.plot(comparison_data['Date'], comparison_data['G7_Price'], label='G7 Price', linestyle='-',
                         color='blue', marker='o')
                plt.title(f"Comparison of Avg Price: Other Sellers vs G7 ({product_name})", fontsize=16)
                plt.xlabel('Date', fontsize=14)
                plt.ylabel('Price', fontsize=14)
                plt.legend(title='Price Type', fontsize=10)
                plt.xticks(rotation=45)
                plt.grid(visible=True)
                pdf.savefig()  # Save the current figure to the PDF
                plt.close()

                ### Third Graph: G7 Price Rank Change ###
                plt.figure(figsize=(10, 6))
                g7_rank_data = product_data[product_data['Seller'] == 'G7']
                plt.plot(g7_rank_data['Date'], g7_rank_data['Price_Rank'], label='G7 Price Rank', linestyle='-',
                         color='purple', marker='o')
                plt.gca().invert_yaxis()  # Invert y-axis to show rank #1 at the top
                plt.title(f"G7 Price Rank Change Over Time ({product_name})", fontsize=16)
                plt.xlabel('Date', fontsize=14)
                plt.ylabel('Rank', fontsize=14)
                plt.legend(title='Rank', fontsize=10)
                plt.xticks(rotation=45)
                plt.grid(visible=True)
                pdf.savefig()  # Save the current figure to the PDF
                plt.close()

            print(f"Successfully created PDF for {product_name}: {file_path}")
        except Exception as e:
            print(f"Error processing product {product_name}: {e}")


# Function to generate sample data for the defined product list
def generate_sample_data():
    dates = pd.date_range('2025-01-01', periods=5)  # Adjust as needed (5 days of data)
    products = [
        'Apple Watch Ultra 2', 'Apple Watch Ultra', 'Garmin Epix™ Pro Gen 2',
        'Garmin Venu 3S', 'Garmin Venu 3', 'Garmin fēnix® 7X Pro',
        'Garmin fēnix® 7 Pro', 'Garmin Forerunner 965',
        'Garmin Forerunner 255', 'Withings ScanWatch 2'
    ]  # Product list
    sellers = ['Seller A', 'Seller B', 'Seller C', 'G7']
    data = []
    for product in products:
        for date in dates:
            for seller in sellers:
                if seller == 'G7':
                    price = 450 + hash(f"{product}_{seller}_{date}") % 150
                else:
                    price = 500 + hash(f"{product}_{seller}_{date}") % 200
                data.append({'Product': product, 'Date': date, 'Seller': seller, 'Price': price})
    return pd.DataFrame(data)


# Main function for execution
def main():
    df = generate_sample_data()  # Load the sample data
    print(f"Loaded dataset with {len(df)} rows.")  # Debug statement
    print(df['Product'].value_counts())  # Debug statement to check product distribution
    create_product_pdf(df)  # Create PDFs for all products


# Run the script
if __name__ == "__main__":
    main()
