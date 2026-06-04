import logging
import sys

def setup_logger(name: str = "ai_platform"):
    """Configures and returns a reusable logger instance."""
    logger = logging.getLogger(name)
    
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Stream handler for console output
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)
        
        # Optional: Add file handler if needed
        # file_handler = logging.FileHandler("app.log")
        # file_handler.setFormatter(formatter)
        # logger.addHandler(file_handler)

    return logger

# Reusable logger instance
logger = setup_logger()
