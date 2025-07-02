"""
Configuration and argument parsing for PyRush
"""

import argparse
from .models import TestConfig

def parse_duration(duration_str: str) -> float:
    """
    Parse duration string into seconds
    
    Args:
        duration_str: Duration string (e.g., '10s', '3m', '1h')
        
    Returns:
        Duration in seconds
        
    Raises:
        ValueError: If duration format is invalid
    """
    if not duration_str:
        return None
    
    unit = duration_str[-1].lower()
    value = float(duration_str[:-1])
    
    if unit == 's':
        return value
    elif unit == 'm':
        return value * 60
    elif unit == 'h':
        return value * 3600
    else:
        raise ValueError(f"Invalid duration format: {duration_str}")

def create_argument_parser() -> argparse.ArgumentParser:
    """
    Create and configure argument parser for PyRush CLI
    
    Returns:
        Configured ArgumentParser instance
    """
    parser = argparse.ArgumentParser(
        description="PyRush - Stress Testing Application untuk Web/API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Contoh:
  python -m pyrush.cli http://example.com -n 1000 -c 50
  python -m pyrush.cli http://api.example.com -m POST -d '{"key":"value"}' -n 500 -c 25
  python -m pyrush.cli http://example.com -z 30s -c 100 -q 10
  python -m pyrush.cli http://example.com -H "Authorization: Bearer token" -o csv
        """
    )
    
    # Basic arguments
    parser.add_argument('urls', nargs='+', help='Target URL(s) to test (bisa lebih dari satu)')
    parser.add_argument('-n', '--num-requests', type=int, default=200,
                       help='Number of requests to run (default: 200)')
    parser.add_argument('-c', '--concurrency', type=int, default=50,
                       help='Number of workers to run concurrently (default: 50)')
    parser.add_argument('-q', '--rate-limit', type=float,
                       help='Rate limit in queries per second (QPS) per worker')
    parser.add_argument('-z', '--duration', type=parse_duration,
                       help='Duration of test (e.g., 10s, 3m, 1h). If specified, -n is ignored')
    parser.add_argument('-o', '--output', choices=['csv', 'json'],
                       help='Output type. "csv" atau "json" untuk ekspor hasil, default: ringkasan di terminal')
    
    # HTTP method and headers
    parser.add_argument('-m', '--method', default='GET',
                       choices=['GET', 'POST', 'PUT', 'DELETE', 'HEAD', 'OPTIONS'],
                       help='HTTP method (default: GET)')
    parser.add_argument('-H', '--header', action='append', default=[],
                       help='Custom HTTP header (can be repeated)')
    parser.add_argument('-A', '--accept', help='HTTP Accept header')
    parser.add_argument('-T', '--content-type', default='text/html',
                       help='Content-type (default: text/html)')
    parser.add_argument('-host', help='HTTP Host header')
    
    # Request body and authentication
    parser.add_argument('-d', '--data', help='HTTP request body')
    parser.add_argument('-D', '--data-file', help='HTTP request body from file')
    parser.add_argument('-a', '--auth', help='Basic authentication (username:password)')
    parser.add_argument('-x', '--proxy', help='HTTP Proxy address (host:port)')
    
    # Connection settings
    parser.add_argument('-t', '--timeout', type=float, default=20,
                       help='Timeout for each request in seconds (default: 20)')
    parser.add_argument('-h2', '--http2', action='store_true',
                       help='Enable HTTP/2')
    parser.add_argument('--disable-compression', action='store_true',
                       help='Disable compression')
    parser.add_argument('--disable-keepalive', action='store_true',
                       help='Disable keep-alive')
    parser.add_argument('--disable-redirects', action='store_true',
                       help='Disable following HTTP redirects')
    parser.add_argument('--cpus', type=int, default=8,
                       help='Number of CPU cores to use (default: 8)')
    
    # Assertion options
    parser.add_argument('--assert-status', type=int, help='Assert status code harus sama dengan nilai ini')
    parser.add_argument('--assert-body-contains', type=str, help='Assert response body harus mengandung string ini')
    parser.add_argument('--assert-max-rt', type=float, help='Assert response time harus kurang dari nilai ini (detik)')
    
    # Interactive mode
    parser.add_argument('-i', '--interactive', action='store_true', help='Jalankan mode interaktif (wizard CLI)')
    
    # Form data options
    parser.add_argument('--form', action='append', default=[], help='Field form-data, format FIELD=VALUE (bisa diulang)')
    parser.add_argument('--form-file', action='append', default=[], help='Field file upload, format FIELD=PATH (bisa diulang)')
    
    # Step load options
    parser.add_argument('--step-load', action='store_true', help='Aktifkan step load (ramp-up concurrency)')
    parser.add_argument('--step-initial', type=int, default=1, help='Concurrency awal step load')
    parser.add_argument('--step-max', type=int, help='Concurrency maksimum step load')
    parser.add_argument('--step-interval', type=int, default=10, help='Interval waktu antar step (detik)')
    parser.add_argument('--step-increment', type=int, default=1, help='Penambahan concurrency tiap step')
    
    return parser

def parse_headers_from_args(args) -> dict:
    """
    Parse headers from command line arguments
    
    Args:
        args: Parsed arguments from ArgumentParser
        
    Returns:
        Dictionary of headers
    """
    headers = {}
    
    # Parse custom headers
    for header in args.header:
        if ':' in header:
            key, value = header.split(':', 1)
            headers[key.strip()] = value.strip()
    
    # Add Accept header if specified
    if args.accept:
        headers['Accept'] = args.accept
    
    return headers

def parse_auth_from_args(args) -> tuple:
    """
    Parse authentication from command line arguments
    
    Args:
        args: Parsed arguments from ArgumentParser
        
    Returns:
        Tuple of (username, password) or None if not specified
        
    Raises:
        ValueError: If auth format is invalid
    """
    if not args.auth:
        return None
    
    if ':' in args.auth:
        username, password = args.auth.split(':', 1)
        return (username, password)
    else:
        raise ValueError("Authentication format should be 'username:password'")

def create_test_config_from_args(args) -> TestConfig:
    """
    Create TestConfig from parsed arguments
    
    Args:
        args: Parsed arguments from ArgumentParser
        
    Returns:
        TestConfig instance
        
    Raises:
        ValueError: If configuration is invalid
    """
    headers = parse_headers_from_args(args)
    auth = parse_auth_from_args(args)
    
    # Validate configuration
    if args.num_requests < args.concurrency:
        raise ValueError(f"Number of requests ({args.num_requests}) cannot be smaller than concurrency ({args.concurrency})")
    
    if args.data and args.data_file:
        raise ValueError("Cannot specify both -d and -D options")
    
    return TestConfig(
        url=args.urls[0],
        method=args.method,
        num_requests=args.num_requests,
        concurrency=args.concurrency,
        rate_limit=args.rate_limit,
        duration=args.duration,
        timeout=args.timeout,
        headers=headers,
        data=args.data,
        data_file=args.data_file,
        content_type=args.content_type,
        auth=auth,
        proxy=args.proxy,
        http2=args.http2,
        host=args.host,
        disable_compression=args.disable_compression,
        disable_keepalive=args.disable_keepalive,
        disable_redirects=args.disable_redirects,
        cpus=args.cpus
    ) 