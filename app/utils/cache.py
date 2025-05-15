"""
Caching utilities for the Wayback Ecommerce Chatbot.
"""

import os
import json
import hashlib
import functools
import datetime
from typing import Callable, TypeVar, Any, Dict, Optional, Union

# Define a generic type for the return value of the decorated function
T = TypeVar('T')

# Default cache directory
CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'cache')

def ensure_cache_dir(cache_dir: str = CACHE_DIR) -> None:
    """
    Ensure the cache directory exists.
    
    Args:
        cache_dir: Path to the cache directory
    """
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)

def generate_cache_key(func_name: str, args: tuple, kwargs: Dict[str, Any]) -> str:
    """
    Generate a unique cache key based on function name and arguments.
    
    Args:
        func_name: Name of the function
        args: Positional arguments
        kwargs: Keyword arguments
        
    Returns:
        Unique cache key as string
    """
    # Convert args and kwargs to a string representation
    args_str = str(args)
    kwargs_str = str(sorted(kwargs.items()))
    
    # Combine function name and arguments
    key_data = f"{func_name}:{args_str}:{kwargs_str}"
    
    # Generate MD5 hash
    return hashlib.md5(key_data.encode()).hexdigest()

def cache_result(
    expire_after_days: int = 30,
    cache_dir: str = CACHE_DIR
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Cache the result of a function call to disk.
    
    Args:
        expire_after_days: Number of days after which cache expires
        cache_dir: Directory to store cache files
        
    Returns:
        Decorator function
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            # Check if caching is disabled via kwargs
            cache_enabled = kwargs.pop('cache_enabled', True)
            
            if not cache_enabled:
                return func(*args, **kwargs)
            
            # Ensure cache directory exists
            ensure_cache_dir(cache_dir)
            
            # Generate cache key
            cache_key = generate_cache_key(func.__name__, args, kwargs)
            cache_file = os.path.join(cache_dir, f"{cache_key}.json")
            
            # Check if cache file exists and is not expired
            if os.path.exists(cache_file):
                try:
                    with open(cache_file, 'r') as f:
                        cache_data = json.load(f)
                    
                    # Check if cache is expired
                    cached_time = datetime.datetime.fromisoformat(cache_data['timestamp'])
                    current_time = datetime.datetime.now()
                    
                    if (current_time - cached_time).days < expire_after_days:
                        print(f"Cache hit for {func.__name__}")
                        return cache_data['result']
                    else:
                        print(f"Cache expired for {func.__name__}")
                except (json.JSONDecodeError, KeyError) as e:
                    print(f"Cache error for {func.__name__}: {e}")
            
            # Cache miss or expired, call the function
            result = func(*args, **kwargs)
            
            # Save result to cache
            try:
                cache_data = {
                    'timestamp': datetime.datetime.now().isoformat(),
                    'result': result
                }
                
                with open(cache_file, 'w') as f:
                    json.dump(cache_data, f)
                
                print(f"Cached result for {func.__name__}")
            except (TypeError, OverflowError) as e:
                print(f"Could not cache result for {func.__name__}: {e}")
            
            return result
        
        return wrapper
    
    return decorator

def clear_cache(cache_dir: str = CACHE_DIR) -> None:
    """
    Clear all cache files.
    
    Args:
        cache_dir: Directory containing cache files
    """
    if os.path.exists(cache_dir):
        for filename in os.listdir(cache_dir):
            if filename.endswith('.json'):
                os.remove(os.path.join(cache_dir, filename))
        print(f"Cleared cache in {cache_dir}")
    else:
        print(f"Cache directory {cache_dir} does not exist")