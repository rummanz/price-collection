import sys
import time
from datetime import datetime
import logging
from ebay_amazon_collection import main as ebay_amazon_main
from idealo_collection import main as idealo_main
from rank_email import main as rank_email_main
from visualization import generate_category_pdf, categories, fixed_prices
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('price_monitor.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


def run_data_collection():
    """Run the data collection processes for eBay, Amazon, and Idealo"""
    try:
        logger.info("Starting eBay and Amazon data collection...")
        ebay_amazon_main()
        logger.info("eBay and Amazon data collection completed")

        logger.info("Starting Idealo data collection...")
        idealo_main()
        logger.info("Idealo data collection completed")

    except Exception as e:
        logger.error(f"Error in data collection: {e}")
        raise


def generate_visualizations():
    """Generate visualization PDFs for all product categories"""
    try:
        logger.info("Starting visualization generation...")
        generate_category_pdf(None, fixed_prices, categories)
        logger.info("Visualization generation completed")
    except Exception as e:
        logger.error(f"Error in visualization generation: {e}")
        raise


def run_rank_analysis():
    """Run the rank analysis and email notification process"""
    try:
        logger.info("Starting rank analysis and email notification...")
        rank_email_main()
        logger.info("Rank analysis and email notification completed")
    except Exception as e:
        logger.error(f"Error in rank analysis: {e}")
        raise


def main():
    """Main function to coordinate all processes"""
    load_dotenv()

    try:
        # Record start time
        start_time = time.time()
        logger.info("Starting price monitoring application...")

        # Step 1: Data Collection
        run_data_collection()

        # Step 2: Generate Visualizations
        generate_visualizations()

        # Step 3: Rank Analysis and Email Notification
        run_rank_analysis()

        # Calculate and log execution time
        execution_time = time.time() - start_time
        logger.info(f"Application completed successfully. Total execution time: {execution_time:.2f} seconds")

    except Exception as e:
        logger.error(f"Application failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()