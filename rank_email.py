import mysql.connector
from mysql.connector import Error
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv

load_dotenv()

# Database connection parameters from .env
config = {
    'user': os.getenv("DB_USER"),
    'password': os.getenv("DB_PASSWORD"),
    'host': os.getenv("DB_HOST"),
    'database': os.getenv("DB_NAME"),
    'raise_on_warnings': True
}

def load_email_template():
    """Load the email body template from settings.txt."""
    try:
        with open('settings.txt', 'r') as file:
            for line in file:
                if line.strip().startswith("email_body="):
                    return line.split("email_body=", 1)[1].strip()
        return None
    except FileNotFoundError:
        print("Error: settings.txt file not found.")
        return None

def send_email(subject, body, recipients):
    """Send an email using Gmail SMTP."""
    sender_email = os.getenv("SENDER_EMAIL")
    sender_password = os.getenv("SENDER_PASSWORD")
    smtp_server = os.getenv("SMTP_SERVER")
    smtp_port = int(os.getenv("SMTP_PORT"))

    if not all([sender_email, sender_password, smtp_server, smtp_port]):
        print("Incomplete email settings in .env file.")
        return

    try:
        # Create the email
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = ', '.join(recipients)
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        # Connect to Gmail SMTP and send
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, recipients, msg.as_string())
        print("Email sent successfully!")
    except Exception as e:
        print(f"Error sending email: {e}")


def get_db_connection():
    """Establish a connection to the MySQL database."""
    try:
        conn = mysql.connector.connect(**config)
        if conn.is_connected():
            return conn
    except Error as e:
        print(f"Error: {e}")
        return None

def fetch_latest_prices(conn):
    """Fetch the latest prices for each product from the database."""
    cursor = conn.cursor(dictionary=True)
    query = '''
        SELECT ProductId, Product, Seller, Price, Date
        FROM PRICE1
        WHERE Date = (SELECT MAX(Date) FROM PRICE1)
    '''
    cursor.execute(query)
    prices = cursor.fetchall()
    #print("Fetched prices:", prices)  # Debug print
    return prices

def calculate_rank(prices):
    """Calculate the rank of 'Our company' for each product."""
    rank_changes = {}
    products = set([price['ProductId'] for price in prices])

    for product in products:
        # Filter out invalid prices
        product_prices = [
            price for price in prices 
            if price['ProductId'] == product and price['Price'] not in ["Price not found", "N/A"]
        ]
        
        if not product_prices:
            continue  # Skip if no valid prices are available
        
        # Sort valid prices
        product_prices.sort(key=lambda x: float(x['Price']))

        # Assign ranks
        for i, price in enumerate(product_prices, start=1):
            price['Rank'] = i

        # Find 'Our company's rank
        our_company_price = next((price for price in product_prices if price['Seller'] == 'Our company'), None)
        if our_company_price:
            rank_changes[product] = our_company_price['Rank']

    return rank_changes


def get_previous_ranks(conn):
    """Retrieve previous ranks from the database."""
    cursor = conn.cursor(dictionary=True)
    query = '''
        SELECT ProductId, PreviousRank
        FROM PREVIOUS_RANKS
    '''
    cursor.execute(query)
    previous_ranks = {row['ProductId']: row['PreviousRank'] for row in cursor.fetchall()}
    return previous_ranks

def update_previous_ranks(conn, current_ranks):
    """Update the previous ranks in the database."""
    cursor = conn.cursor()
    for product, rank in current_ranks.items():
        query = '''
            INSERT INTO PREVIOUS_RANKS (ProductId, PreviousRank)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE PreviousRank = %s
        '''
        cursor.execute(query, (product, rank, rank))
    conn.commit()

def compare_ranks(current_ranks, previous_ranks):
    """Compare current ranks with previous ranks to identify changes."""
    rank_changes = {}
    print("Current Ranks:", current_ranks)  # Debug print
    print("Previous Ranks:", previous_ranks)  # Debug print
    for product, current_rank in current_ranks.items():
        previous_rank = previous_ranks.get(product, None)
        if previous_rank is not None and current_rank != previous_rank:
            rank_changes[product] = {'previous_rank': previous_rank, 'current_rank': current_rank}
    return rank_changes

def main():
    conn = get_db_connection()
    if conn is None:
        return

    # Fetch the latest prices
    latest_prices = fetch_latest_prices(conn)

    # Calculate the current ranks
    current_ranks = calculate_rank(latest_prices)

    # Fetch the previous ranks
    previous_ranks = get_previous_ranks(conn)

    # Compare ranks to identify changes
    rank_changes = compare_ranks(current_ranks, previous_ranks)

    if rank_changes:
    # Load email template from settings.txt
        email_template = load_email_template()
        if not email_template:
            print("Email template not found in settings.txt.")
            return
            # Build the email body
        body = "RANK CHANGE! "
        for product_id, change in rank_changes.items():
            product_name = next(
                price['Product'] for price in latest_prices 
                if price['ProductId'] == product_id
            )
            body += email_template.format(
                product_id=product_id,
                product_name=product_name,
                previous_rank=change['previous_rank'],
                current_rank=change['current_rank']
            ) + "\n\n"

        # Send email
        subject = "Rank Change Alert"
        recipients = os.getenv("RECIPIENT_EMAILS").split(',')
        send_email(subject, body.strip(), recipients)

    # Output the rank changes
    for product, change in rank_changes.items():
        print(f"Product ID: {product}, Previous Rank: {change['previous_rank']}, Current Rank: {change['current_rank']}")

    # Update the previous ranks
    update_previous_ranks(conn, current_ranks)

    conn.close()

if __name__ == "__main__":
    main()
