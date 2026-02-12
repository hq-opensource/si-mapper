import logging
import os

from dotenv import load_dotenv


def configure_logging() -> logging.Logger:
    load_dotenv()
    log_level_str = os.getenv("DEBUG_LEVEL", "INFO").upper()
    log_level = getattr(logging, log_level_str, logging.INFO)

    # Configure a specific logger for the application
    logger = logging.getLogger("si-mapper") # Use a named logger for your application
    logger.setLevel(log_level)

    # Prevent the logger from propagating messages to the root logger
    # This allows independent control over this logger's output
    logger.propagate = False

    # Create a console handler and set its format
    console_handler = logging.StreamHandler()
    formatter = logging.Formatter('%(message)s')
    # formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(filename)s - %(funcName)s - %(message)s')
    console_handler.setFormatter(formatter)
    console_handler.setLevel(log_level) # Set handler level

    # Add the handler to the logger
    if not logger.handlers: # Avoid adding multiple handlers if configure_logging is called multiple times
        logger.addHandler(console_handler)

        # Create a file handler for app_run.log
        file_handler = logging.FileHandler('app_run.log', mode='a') # 'a' for append mode
        file_handler.setFormatter(formatter)
        file_handler.setLevel(log_level) # Set handler level
        logger.addHandler(file_handler)

    # Optionally, set the root logger level to WARNING or ERROR to suppress third-party logs
    # This will affect all loggers that propagate to the root logger
    logging.getLogger().setLevel(logging.WARNING)
    
    return logger