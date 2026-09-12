import sys
import os

# Add the project root to sys.path to allow absolute imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pipelines.data_ingestion import run_data_ingestion
from utils.logger import logger

if __name__ == "__main__":
    """
    Entry point for the ERP data ingestion script.
    """
    logger.info("Initializing ERP Data Ingestion Script...")
    
    try:
        run_data_ingestion()
        logger.info("Ingestion script finished successfully.")
    except Exception as e:
        logger.critical(f"Ingestion script terminated with errors: {e}")
        sys.exit(1)
