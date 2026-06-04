import sys
import os

# Add the project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pipelines.data_processing import run_data_processing
from utils.logger import logger

if __name__ == "__main__":
    logger.info("Starting Data Processing and Feature Engineering...")
    try:
        run_data_processing()
        logger.info("Processing script finished successfully.")
    except Exception as e:
        logger.critical(f"Processing script failed: {e}")
        sys.exit(1)
