import mysql.connector
from mysql.connector import Error

# Database connection parameters
config = {
    'user': 'pyuser11',
    'password': 'P7Oc19B5mTAmb2Kh',
    'host': '127.0.0.1',
    'database': 'products',
    'raise_on_warnings': True

}

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
    print("Fetched prices:", prices)  # Debug print
    return prices

def calculate_rank(prices):
    """Calculate the rank of 'Our company' for each product."""
    rank_changes = {}
    products = set([price['ProductId'] for price in prices])
    
    for product in products:
        product_prices = [price for price in prices if price['ProductId'] == product]
        product_prices.sort(key=lambda x: float(x['Price']))
        
        # Assign ranks
        for i, price in enumerate(product_prices, start=1):
            price['Rank'] = i
        
        # Find 'Our company's rank
        our_company_price = next((price for price in product_prices if price['Seller'] == 'Our company'), None)
        if our_company_price:
            rank_changes[product] = our_company_price['Rank']
            print(f"Product ID: {product}, Our company Rank: {our_company_price['Rank']}")  # Debug print
    
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

    # Output the rank changes
    for product, change in rank_changes.items():
        print(f"Product ID: {product}, Previous Rank: {change['previous_rank']}, Current Rank: {change['current_rank']}")

    # Update the previous ranks
    update_previous_ranks(conn, current_ranks)

    conn.close()

if __name__ == "__main__":
    main()
