import time
import random
import asyncio
from functools import wraps
import traceback

def resilient_api(max_retries=3, base_delay=1.0):
    """
    Intelligent backoff decorator for API resilience.
    Handles HTTP 429 (Rate Limit) and 5xx (Server Error).
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            retries = 0
            while retries < max_retries:
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    err_str = str(e).lower()
                    
                    # Logic for Rate Limits (HTTP 429)
                    if "429" in err_str or "rate limit" in err_str:
                        # Exponential backoff: 1s, 2s, 4s... + jitter
                        wait = (base_delay * (2 ** retries)) + random.uniform(0.1, 0.5)
                        print(f"🚦 Rate Limit Hit in {func.__name__}. Backing off for {wait:.2f}s (Attempt {retries+1}/{max_retries})...")
                        await asyncio.sleep(wait)
                        retries += 1
                        continue
                        
                    # Logic for Server Glitches (HTTP 5xx)
                    if "500" in err_str or "502" in err_str or "503" in err_str or "504" in err_str:
                        wait = (base_delay * 1.5) + random.uniform(0.1, 0.3)
                        print(f"🔄 Server Error in {func.__name__}. Retrying in {wait:.2f}s...")
                        await asyncio.sleep(wait)
                        retries += 1
                        continue
                        
                    # If it's something else (401, 404, 422), raise it immediately
                    # 422 usually means bad data, retrying won't help
                    if "422" in err_str or "404" in err_str or "401" in err_str:
                        raise e
                    
                    # For unexpected errors, retry once then fail
                    if retries == 0:
                        await asyncio.sleep(base_delay)
                        retries += 1
                        continue
                        
                    raise e
            
            # Final attempt
            return await func(*args, **kwargs)
            
        return wrapper
    return decorator
