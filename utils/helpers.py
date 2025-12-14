"""
Utility helper functions for AI CV Screener.
Contains retry logic, time utilities, and other helper functions.
"""

import time
from functools import wraps
from datetime import datetime
import pytz
import logging
from constants.constants import MAX_RETRIES, INITIAL_RETRY_DELAY, MAX_RETRY_DELAY

logger = logging.getLogger(__name__)


def retry_with_exponential_backoff(
    max_retries=MAX_RETRIES,
    initial_delay=INITIAL_RETRY_DELAY,
    max_delay=MAX_RETRY_DELAY
):
    """Decorator for retrying API calls with exponential backoff."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            delay = initial_delay
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    error_msg = str(e).lower()
                    
                    # Check if it's a rate limit error
                    if 'rate limit' in error_msg or 'quota' in error_msg or '429' in error_msg:
                        if attempt < max_retries - 1:
                            logger.warning(f"Rate limit hit. Retrying in {delay}s... (Attempt {attempt + 1}/{max_retries})")
                            print(f"⏳ Rate limit hit. Retrying in {delay}s... (Attempt {attempt + 1}/{max_retries})")
                            time.sleep(delay)
                            delay = min(delay * 2, max_delay)
                        else:
                            logger.error(f"Max retries reached. Rate limit error: {str(e)}")
                            raise Exception(f"Max retries ({max_retries}) reached. Rate limit error: {str(e)}")
                    else:
                        logger.error(f"Non-rate-limit error: {str(e)}", exc_info=True)
                        raise
            
            raise last_exception
        
        return wrapper
    return decorator


def get_jakarta_time():
    """Get current time in Jakarta timezone."""
    try:
        jakarta_tz = pytz.timezone('Asia/Jakarta')
        return datetime.now(jakarta_tz)
    except Exception as e:
        logger.error(f"Error getting Jakarta time: {e}", exc_info=True)
        return datetime.now()


def format_timestamp(dt):
    """Format datetime object to readable string."""
    try:
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    except Exception as e:
        logger.error(f"Error formatting timestamp: {e}", exc_info=True)
        return str(dt)
