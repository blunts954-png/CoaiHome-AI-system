"""
Shared utility functions for automation modules.
Provides cross-platform compatibility helpers for printing and console output.
"""
import sys
import asyncio
import threading
from typing import Callable, Any
from functools import wraps


def _safe_print(message: str):
    """Print without crashing on cp1252 Windows consoles.
    
    Handles UnicodeEncodeError that occurs on Windows consoles that use
    cp1252 encoding instead of UTF-8.
    """
    try:
        print(message)
    except UnicodeEncodeError:
        print(message.encode("ascii", "replace").decode("ascii"))


def _configure_utf8_console():
    """Avoid UnicodeEncodeError on Windows cp1252 consoles.
    
    Configures stdout/stderr to use UTF-8 encoding with fallback
    for Windows compatibility.
    """
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8", errors="replace")
            except Exception:
                pass


class AsyncRunner:
    """Helper class for running async tasks from sync context.
    
    Provides a persistent event loop to avoid the overhead of
    creating/destroying event loops for each task.
    Thread-safe implementation with proper locking.
    """
    
    def __init__(self):
        self._loop: asyncio.AbstractEventLoop | None = None
        self._thread: threading.Thread | None = None
        self._running = False
        self._lock = threading.Lock()
        self._started_event = threading.Event()
    
    def start(self):
        """Start the async runner in a background thread."""
        with self._lock:
            if self._running:
                return
            
            self._running = True
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
            self._thread = threading.Thread(target=self._run_loop, daemon=True)
            self._thread.start()
            self._started_event.set()
    
    def _run_loop(self):
        """Run the event loop in the background thread."""
        if self._loop:
            self._loop.run_forever()
    
    def stop(self):
        """Stop the async runner."""
        with self._lock:
            if not self._running:
                return
            self._running = False
        
        if self._loop:
            self._loop.call_soon_threadsafe(self._loop.stop)
            self._loop.close()
        
        if self._thread:
            self._thread.join(timeout=5)
        
        with self._lock:
            self._loop = None
            self._thread = None
    
    def run_task(self, coro):
        """Run an async task in the persistent event loop.
        
        Args:
            coro: An awaitable (coroutine)
            
        Returns:
            The result of the coroutine
        """
        if not self._loop or not self._running:
            # Fallback to asyncio.run if not started
            return asyncio.run(coro)
        
        # Wait for the loop to be ready
        if not self._started_event.wait(timeout=5):
            raise RuntimeError("AsyncRunner event loop not ready")
        
        future = asyncio.run_coroutine_threadsafe(coro, self._loop)
        return future.result(timeout=30)


# Global async runner instance for scheduler
_async_runner: AsyncRunner | None = None


def get_async_runner() -> AsyncRunner:
    """Get or create the global AsyncRunner instance."""
    global _async_runner
    if _async_runner is None:
        _async_runner = AsyncRunner()
    return _async_runner


# ============ CJ Credential Parsing Utilities ============


def is_valid_email(value: str) -> bool:
    """Validate email address format.
    
    Args:
        value: Email address string to validate
        
    Returns:
        True if email format is valid, False otherwise
    """
    if not value:
        return False
    value = value.strip()
    if "@" not in value:
        return False
    local_part, _, domain = value.partition("@")
    # Must have local part and domain with at least one dot
    if not local_part or not domain or "." not in domain:
        return False
    # Domain should have at least one character before and after the dot
    domain_parts = domain.split(".")
    if len(domain_parts[0]) < 1 or len(domain_parts[-1]) < 1:
        return False
    return True


def parse_cj_credentials(cj_token: str = None, cj_email: str = None, cj_key: str = None) -> dict:
    """Parse and validate CJ Dropshipping credentials.
    
    Handles the combined token format (email@api@key) and separate fields.
    
    Args:
        cj_token: CJ API token (can be combined "email@api@key" format)
        cj_email: CJ API email (used if token not in combined format)
        cj_key: CJ API key (used if token not in combined format)
        
    Returns:
        Dictionary with keys:
            - email: Parsed email address
            - api_key: Parsed API key
            - is_valid: Boolean indicating if credentials are valid
    """
    # Initialize result
    email = (cj_email or "").strip()
    api_key = (cj_key or "").strip()
    
    # Parse combined token format: email@api@key
    if cj_token and "@api@" in cj_token:
        parts = cj_token.split("@api@", 1)
        if len(parts) == 2:
            if not email:
                email = parts[0].strip()
            if not api_key:
                api_key = parts[1].strip()
    
    # Validate credentials
    is_valid = bool(email and api_key and is_valid_email(email))
    
    return {
        "email": email,
        "api_key": api_key,
        "is_valid": is_valid
    }
