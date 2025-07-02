"""
Data models for PyRush stress testing application
"""

from dataclasses import dataclass
from typing import Dict, Optional, Tuple

@dataclass
class RequestResult:
    """
    Represents the result of a single HTTP request
    
    Attributes:
        url: The URL that was requested
        method: HTTP method used (GET, POST, etc.)
        status_code: HTTP status code returned
        response_time: Time taken for the request in seconds
        timestamp: Unix timestamp when request was made
        error: Error message if request failed, None if successful
        response_size: Size of response body in bytes
    """
    url: str
    method: str
    status_code: int
    response_time: float
    timestamp: float
    error: Optional[str] = None
    response_size: int = 0

@dataclass
class TestConfig:
    """
    Configuration for stress testing
    
    Attributes:
        url: Base URL for testing
        method: HTTP method to use
        num_requests: Total number of requests to make
        concurrency: Number of concurrent workers
        rate_limit: Rate limit per worker (requests per second)
        duration: Test duration in seconds (overrides num_requests if set)
        timeout: Request timeout in seconds
        headers: Custom HTTP headers
        data: Request body data
        data_file: File containing request body
        content_type: Content-Type header
        auth: Basic authentication (username, password)
        proxy: Proxy server (host:port)
        http2: Whether to use HTTP/2
        host: Custom Host header
        disable_compression: Disable HTTP compression
        disable_keepalive: Disable HTTP keep-alive
        disable_redirects: Disable following redirects
        cpus: Number of CPU cores to use
    """
    url: str
    method: str
    num_requests: int
    concurrency: int
    rate_limit: Optional[float]
    duration: Optional[float]
    timeout: float
    headers: Dict[str, str]
    data: Optional[str]
    data_file: Optional[str]
    content_type: str
    auth: Optional[Tuple[str, str]]
    proxy: Optional[str]
    http2: bool
    host: Optional[str]
    disable_compression: bool
    disable_keepalive: bool
    disable_redirects: bool
    cpus: int 