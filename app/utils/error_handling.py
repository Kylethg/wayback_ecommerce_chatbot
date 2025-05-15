"""
Error handling utilities for the Wayback Ecommerce Chatbot.
"""

import time
import functools
import random
from typing import Callable, TypeVar, Any

# Define a generic type for the return value of the decorated function
T = TypeVar('T')

# Custom exceptions
class WaybackError(Exception):
    """Base exception for Wayback Machine API errors."""
    pass

class SnapshotNotFoundError(WaybackError):
    """Exception raised when a snapshot is not found."""
    pass

class ContentExtractionError(Exception):
    """Exception raised when content extraction fails."""
    pass

class OpenAIError(Exception):
    """Exception raised when there's an error with OpenAI API."""
    pass

def retry_with_exponential_backoff(
    max_retries: int = 3,
    initial_delay: float = 1,
    exponential_base: float = 2,
    jitter: bool = True
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Retry a function with exponential backoff.
    
    Args:
        max_retries: Maximum number of retries
        initial_delay: Initial delay in seconds
        exponential_base: Base for exponential backoff
        jitter: Whether to add random jitter to delay
        
    Returns:
        Decorator function
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            # Initialize variables
            num_retries = 0
            delay = initial_delay
            
            # Loop until max_retries is reached
            while True:
                try:
                    return func(*args, **kwargs)
                    
                except (WaybackError, OpenAIError, ConnectionError, TimeoutError) as e:
                    # Increment retry counter
                    num_retries += 1
                    
                    # Check if max retries reached
                    if num_retries > max_retries:
                        raise e
                    
                    # Calculate delay with optional jitter
                    if jitter:
                        delay = delay * exponential_base * (1 + random.random() * 0.1)
                    else:
                        delay = delay * exponential_base
                    
                    # Log retry attempt
                    print(f"Retry {num_retries}/{max_retries} after {delay:.2f}s delay due to {str(e)}")
                    
                    # Sleep before retrying
                    time.sleep(delay)
        
        return wrapper
    
    return decorator