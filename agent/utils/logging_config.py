import logging
import os

from dotenv import load_dotenv


import warnings

class NoFunctionCallWarningFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        return "there are non-text parts in the response" not in record.getMessage()

class PollingFilter(logging.Filter):
    """Filters out frequent polling requests from uvicorn access logs."""
    def filter(self, record: logging.LogRecord) -> bool:
        msg = record.getMessage()
        return not any(x in msg for x in ["/session_state", "/session_info", "/health", "GET / HTTP"])

class IterationReportFilter(logging.Filter):
    """Filters out the bulky ADK iteration reports from the console."""
    def filter(self, record: logging.LogRecord) -> bool:
        msg = record.getMessage()
        # Suppress the header, the box, and the stats lines
        return not any(x in msg for x in [
            "📊 ITERATION REPORT", 
            "────────────────────────────────────────────────────────────────────",
            "⏱  Time",
            "🔢 Tokens"
        ])

def configure_logging() -> logging.Logger:
    load_dotenv()
    
    # Suppress experimental feature warnings and FutureWarnings
    warnings.filterwarnings("ignore", message=".*EXPERIMENTAL.*")
    warnings.filterwarnings("ignore", category=UserWarning, module="ag_ui_adk")
    warnings.filterwarnings("ignore", category=UserWarning, module="google.adk")
    warnings.filterwarnings("ignore", category=FutureWarning, module="google.api_core")
    warnings.filterwarnings("ignore", category=FutureWarning, module="google.cloud")
    
    # Suppress google_genai.types warnings via logging filter
    logging.getLogger("google_genai.types").addFilter(NoFunctionCallWarningFilter())

    # Suppress polling logs in uvicorn
    logging.getLogger("uvicorn.access").addFilter(PollingFilter())

    # Suppress bulky ADK iteration reports (on both the specific and root loggers to be safe)
    logging.getLogger("google.adk").addFilter(IterationReportFilter())
    logging.getLogger().addFilter(IterationReportFilter())

    log_level_str = (os.getenv("DEBUG_LEVEL") or os.getenv("LOG_LEVEL") or "INFO").upper()
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

    # Optionally, set the root logger level to WARNING or ERROR to suppress third-party logs
    # This will affect all loggers that propagate to the root logger
    logging.getLogger().setLevel(logging.WARNING)
    
    return logger