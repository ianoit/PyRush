"""
Main entry point for PyRush stress testing application
"""

import asyncio
import os
from datetime import datetime
from .config import create_argument_parser, create_test_config_from_args, parse_duration
from .core import StressTester
from .reporter import export_csv, export_json, generate_pdf_report

def run_interactive_mode():
    """
    Run interactive mode (wizard CLI) to collect test parameters
    
    Returns:
        Parsed arguments object with user input
    """
    print("=== PyRush Interactive Mode ===")
    
    # Collect basic parameters
    urls = input("Target URL (bisa lebih dari satu, pisahkan spasi): ").strip().split()
    method = input("HTTP Method [GET/POST/PUT/DELETE] (default: GET): ").strip().upper() or 'GET'
    num_requests = int(input("Jumlah request (default: 200): ") or 200)
    concurrency = int(input("Concurrency (default: 50): ") or 50)
    
    # Rate limiting
    rate_limit = input("Rate limit per worker (QPS, kosong=tanpa limit): ")
    rate_limit = float(rate_limit) if rate_limit else None
    
    # Duration
    duration = input("Durasi pengujian (misal 10s, 3m, kosong=pakai jumlah request): ")
    duration = parse_duration(duration) if duration else None
    
    # Timeout
    timeout = float(input("Timeout per request (default: 20): ") or 20)
    
    # Headers
    headers = {}
    while True:
        h = input("Tambahkan header (format Key:Value, kosong untuk lanjut): ")
        if not h.strip():
            break
        if ':' in h:
            k, v = h.split(':', 1)
            headers[k.strip()] = v.strip()
    
    # Request body
    data = input("Body request (kosong jika tidak ada): ")
    data_file = input("Body request dari file (kosong jika tidak ada): ")
    content_type = input("Content-Type (default: text/html): ") or 'text/html'
    
    # Authentication and proxy
    auth = input("Basic auth (username:password, kosong jika tidak ada): ")
    proxy = input("Proxy (host:port, kosong jika tidak ada): ")
    
    # HTTP settings
    http2 = input("Aktifkan HTTP/2? (y/n, default: n): ").lower() == 'y'
    host = input("Custom Host header (kosong jika tidak ada): ")
    disable_compression = input("Disable compression? (y/n, default: n): ").lower() == 'y'
    disable_keepalive = input("Disable keep-alive? (y/n, default: n): ").lower() == 'y'
    disable_redirects = input("Disable redirects? (y/n, default: n): ").lower() == 'y'
    cpus = int(input("Jumlah CPU core (default: 8): ") or 8)
    
    # Assertions
    assert_status = input("Assert status code (kosong jika tidak ada): ")
    assert_status = int(assert_status) if assert_status else None
    assert_body_contains = input("Assert body contains (kosong jika tidak ada): ") or None
    assert_max_rt = input("Assert max response time (detik, kosong jika tidak ada): ")
    assert_max_rt = float(assert_max_rt) if assert_max_rt else None
    
    # Step load
    step_load = input("Aktifkan step load/ramp-up concurrency? (y/n, default: n): ").lower() == 'y'
    step_initial = int(input("Step load: concurrency awal (default: 1): ") or 1) if step_load else None
    step_max = int(input("Step load: concurrency maksimum (default: concurrency): ") or concurrency) if step_load else None
    step_interval = int(input("Step load: interval detik (default: 10): ") or 10) if step_load else None
    step_increment = int(input("Step load: increment worker (default: 1): ") or 1) if step_load else None
    
    # Output
    output = input("Output (csv/json, kosong=ringkasan saja): ") or None
    
    # Show configuration summary
    print("\nConfiguration Summary:")
    print(f"URLs: {urls}")
    print(f"Method: {method}")
    print(f"Requests: {num_requests}")
    print(f"Concurrency: {concurrency}")
    print(f"Rate limit: {rate_limit}")
    print(f"Duration: {duration}")
    print(f"Timeout: {timeout}")
    print(f"Headers: {headers}")
    print(f"Body: {data}")
    print(f"Body file: {data_file}")
    print(f"Content-Type: {content_type}")
    print(f"Auth: {auth}")
    print(f"Proxy: {proxy}")
    print(f"HTTP/2: {http2}")
    print(f"Host: {host}")
    print(f"Disable compression: {disable_compression}")
    print(f"Disable keepalive: {disable_keepalive}")
    print(f"Disable redirects: {disable_redirects}")
    print(f"CPU: {cpus}")
    print(f"Assert status: {assert_status}")
    print(f"Assert body contains: {assert_body_contains}")
    print(f"Assert max rt: {assert_max_rt}")
    print(f"Step load: {step_load}")
    if step_load:
        print(f"  Step initial: {step_initial}")
        print(f"  Step max: {step_max}")
        print(f"  Step interval: {step_interval}")
        print(f"  Step increment: {step_increment}")
    print(f"Output: {output}")
    
    # Confirm execution
    confirm = input("Continue with test? (y/n): ").lower()
    if confirm != 'y':
        print("Test cancelled.")
        return None
    
    # Create mock args object
    class MockArgs:
        pass
    
    args = MockArgs()
    args.urls = urls
    args.method = method
    args.num_requests = num_requests
    args.concurrency = concurrency
    args.rate_limit = rate_limit
    args.duration = duration
    args.timeout = timeout
    args.header = [f"{k}: {v}" for k, v in headers.items()]
    args.data = data if data else None
    args.data_file = data_file if data_file else None
    args.content_type = content_type
    args.auth = auth if auth else None
    args.proxy = proxy if proxy else None
    args.http2 = http2
    args.host = host if host else None
    args.disable_compression = disable_compression
    args.disable_keepalive = disable_keepalive
    args.disable_redirects = disable_redirects
    args.cpus = cpus
    args.assert_status = assert_status
    args.assert_body_contains = assert_body_contains
    args.assert_max_rt = assert_max_rt
    args.step_load = step_load
    args.step_initial = step_initial if step_load else 1
    args.step_max = step_max if step_load else concurrency
    args.step_interval = step_interval if step_load else 10
    args.step_increment = step_increment if step_load else 1
    args.output = output
    args.form = []
    args.form_file = []
    
    return args

def main():
    """
    Main entry point for PyRush CLI
    
    Handles argument parsing, test execution, and result reporting.
    """
    # Create and parse arguments
    parser = create_argument_parser()
    args = parser.parse_args()
    
    # Handle interactive mode
    if args.interactive:
        args = run_interactive_mode()
        if args is None:
            return 0
    
    try:
        # Create test configuration
        config = create_test_config_from_args(args)
        urls = args.urls
        
        # Create and configure stress tester
        tester = StressTester(config, urls)
        
        # Set assertion parameters
        tester.assert_status = args.assert_status
        tester.assert_body_contains = args.assert_body_contains
        tester.assert_max_rt = args.assert_max_rt
        
        # Set step load parameters
        tester.step_load = args.step_load
        tester.step_initial = args.step_initial
        tester.step_max = args.step_max if args.step_max else config.concurrency
        tester.step_interval = args.step_interval
        tester.step_increment = args.step_increment
        
        # Set form data parameters
        tester.form = args.form
        tester.form_file = args.form_file
        
        # Display test configuration
        print(f"Starting stress test...")
        print(f"URLs: {', '.join(urls)}")
        print(f"Method: {config.method}")
        print(f"Requests: {config.num_requests}")
        print(f"Concurrency: {config.concurrency}")
        if config.rate_limit:
            print(f"Rate limit: {config.rate_limit} QPS per worker")
        if config.duration:
            print(f"Duration: {config.duration}s")
        print()
        
        # Run the test
        asyncio.run(tester.run_test())
        
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
        return 1
    except Exception as e:
        print(f"Error during test: {e}")
        return 1
    
    try:
        # Generate and display statistics
        stats = tester.generate_statistics()
        print("[INFO] Statistics generated successfully")
        
        print("\n" + "="*60)
        print("PYRUSH STRESS TEST RESULTS")
        print("="*60)
        print(f"Total Requests: {stats['total_requests']}")
        print(f"Successful Requests: {stats['successful_requests']}")
        print(f"Failed Requests: {stats['failed_requests']}")
        print(f"Success Rate: {stats['success_rate']:.2f}%")
        print(f"Total Duration: {stats['total_duration']:.2f}s")
        print(f"Requests per Second: {stats['requests_per_second']:.2f}")
        print(f"Throughput (bytes/sec): {stats['throughput_bytes_per_sec']:.2f}")
        
        # Display response time statistics
        if 'mean_response_time' in stats:
            print(f"\nResponse Time Statistics:")
            print(f"  Mean: {stats['mean_response_time']:.3f}s")
            print(f"  Median: {stats['median_response_time']:.3f}s")
            print(f"  Min: {stats['min_response_time']:.3f}s")
            print(f"  Max: {stats['max_response_time']:.3f}s")
            print(f"  P25: {stats['p25_response_time']:.3f}s")
            print(f"  P50: {stats['p50_response_time']:.3f}s")
            print(f"  P75: {stats['p75_response_time']:.3f}s")
            print(f"  P90: {stats['p90_response_time']:.3f}s")
            print(f"  P95: {stats['p95_response_time']:.3f}s")
            print(f"  P99: {stats['p99_response_time']:.3f}s")
        
        # Display status code distribution
        if stats.get('status_code_distribution'):
            print(f"\nStatus Code Distribution:")
            for status_code, count in sorted(stats['status_code_distribution'].items()):
                print(f"  {status_code}: {count}")
        
        # Display error distribution
        if stats.get('error_distribution'):
            print(f"\nError Distribution:")
            for error_type, count in stats['error_distribution'].items():
                print(f"  {error_type}: {count}")
        
        # Create output directory
        os.makedirs('report_files', exist_ok=True)
        
        # Export results based on output type
        if args.output == 'csv':
            csv_filename = os.path.join('report_files', f"results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
            export_csv(tester, csv_filename)
            print(f"[INFO] CSV results exported to: {csv_filename}")
        
        if args.output == 'json':
            json_filename = os.path.join('report_files', f"results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
            export_json(tester, json_filename, stats)
            print(f"[INFO] JSON results exported to: {json_filename}")
        
        # Always generate PDF report
        pdf_filename = os.path.join('report_files', f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf")
        generate_pdf_report(tester, pdf_filename)
        print(f"[INFO] PDF report generated: {pdf_filename}")
        
        print("[INFO] All done!")
        
    except Exception as e:
        print(f"[ERROR] Failed to generate report: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main()) 