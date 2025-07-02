"""
Core stress testing functionality for PyRush
"""

import asyncio
import aiohttp
import ssl
import certifi
import statistics
import threading
import time
from typing import Dict, List
from tqdm import tqdm
from .models import TestConfig, RequestResult
from .requestor import worker

class StressTester:
    """
    Main stress testing orchestrator
    
    Handles the execution of stress tests, manages workers, and collects results.
    """
    
    def __init__(self, config: TestConfig, urls: list):
        """
        Initialize the stress tester
        
        Args:
            config: Test configuration
            urls: List of URLs to test
        """
        self.config = config
        self.urls = urls
        self.results: List[RequestResult] = []
        self.start_time: float = None
        self.end_time: float = None
        self.lock = threading.Lock()
        
        # Statistics tracking
        self.dns_times = []
        self.connect_times = []
        self.response_sizes = []
        
        # Progress tracking
        self.progress_bar = None
        self.progress_total = 0
        
        # Assertion settings
        self.assert_status = None
        self.assert_body_contains = None
        self.assert_max_rt = None
        
        # Step load settings
        self.step_load = False
        self.step_initial = 1
        self.step_max = config.concurrency
        self.step_interval = 10
        self.step_increment = 1
        
        # Form data settings
        self.form = []
        self.form_file = []
    
    def set_progress_bar(self, pbar, total):
        """Set the progress bar for tracking test progress"""
        self.progress_bar = pbar
        self.progress_total = total
    
    def update_progress(self):
        """Update the progress bar"""
        if self.progress_bar:
            self.progress_bar.update(1)
    
    async def run_test(self):
        """
        Run the stress test
        
        This method orchestrates the entire stress testing process:
        1. Sets up HTTP session with tracing
        2. Creates request queue
        3. Starts workers (with step load if enabled)
        4. Waits for completion
        5. Collects final statistics
        """
        self.start_time = time.time()
        
        # Setup tracing for DNS and connection times
        trace_dns = {}
        trace_connect = {}
        trace_config = aiohttp.TraceConfig()
        
        async def on_dns_resolvehost_start(session, context, params):
            trace_dns['start'] = time.time()
        
        async def on_dns_resolvehost_end(session, context, params):
            trace_dns['end'] = time.time()
        
        async def on_connection_create_start(session, context, params):
            trace_connect['start'] = time.time()
        
        async def on_connection_create_end(session, context, params):
            trace_connect['end'] = time.time()
        
        # Register trace handlers
        trace_config.on_dns_resolvehost_start.append(on_dns_resolvehost_start)
        trace_config.on_dns_resolvehost_end.append(on_dns_resolvehost_end)
        trace_config.on_connection_create_start.append(on_connection_create_start)
        trace_config.on_connection_create_end.append(on_connection_create_end)
        
        # Setup HTTP connector
        connector = aiohttp.TCPConnector(
            limit=self.config.concurrency * 2,
            limit_per_host=self.config.concurrency,
            keepalive_timeout=30 if not self.config.disable_keepalive else 0,
            enable_cleanup_closed=True,
            ssl=ssl.create_default_context(cafile=certifi.where())
        )
        
        # Setup session
        session_kwargs = {
            'connector': connector,
            'trust_env': True,
            'trace_configs': [trace_config]
        }
        
        if self.config.http2:
            session_kwargs['version'] = aiohttp.HttpVersion20
        
        async with aiohttp.ClientSession(**session_kwargs) as session:
            # Create request queue
            request_queue = asyncio.Queue()
            
            # Determine number of requests
            if self.config.duration:
                num_requests = 1000000  # Large number for duration-based tests
            else:
                num_requests = self.config.num_requests
            
            # Add request IDs to queue
            for i in range(num_requests):
                await request_queue.put(i)
            
            # Add stop signals for workers
            for _ in range(self.config.concurrency):
                await request_queue.put(None)
            
            # Setup progress bar
            pbar = None
            if not self.config.duration:
                pbar = tqdm(total=num_requests, desc="Progress", unit="req")
                self.set_progress_bar(pbar, num_requests)
            
            workers = []
            
            # Handle step load (ramp-up concurrency)
            if self.step_load:
                initial = self.step_initial
                max_c = self.step_max
                interval = self.step_interval
                increment = self.step_increment
                current_c = initial
                
                # Start initial workers
                for _ in range(initial):
                    w = asyncio.create_task(
                        worker(self, session, self.urls, self.config.method, 
                              request_queue, self.config.rate_limit)
                    )
                    workers.append(w)
                
                # Ramp-up function
                async def ramp_up():
                    nonlocal current_c
                    while current_c < max_c:
                        await asyncio.sleep(interval)
                        add = min(increment, max_c - current_c)
                        
                        for _ in range(add):
                            w = asyncio.create_task(
                                worker(self, session, self.urls, self.config.method, 
                                      request_queue, self.config.rate_limit)
                            )
                            workers.append(w)
                        
                        current_c += add
                
                ramp_task = asyncio.create_task(ramp_up())
            
            else:
                # Start all workers at once
                for _ in range(self.config.concurrency):
                    w = asyncio.create_task(
                        worker(self, session, self.urls, self.config.method, 
                              request_queue, self.config.rate_limit)
                    )
                    workers.append(w)
            
            # Wait for completion
            if self.config.duration:
                try:
                    await asyncio.wait_for(asyncio.gather(*workers), timeout=self.config.duration)
                except asyncio.TimeoutError:
                    # Cancel workers when duration is reached
                    for w in workers:
                        w.cancel()
                    await asyncio.gather(*workers, return_exceptions=True)
            else:
                await asyncio.gather(*workers)
            
            # Wait for queue to be processed
            await request_queue.join()
            
            # Close progress bar
            if pbar:
                pbar.close()
        
        # Collect final timing statistics
        if 'end' in trace_dns and 'start' in trace_dns:
            self.dns_times.append(trace_dns['end'] - trace_dns['start'])
        
        if 'end' in trace_connect and 'start' in trace_connect:
            self.connect_times.append(trace_connect['end'] - trace_connect['start'])
        
        self.end_time = time.time()
    
    def generate_statistics(self) -> Dict:
        """
        Generate comprehensive statistics from test results
        
        Returns:
            Dictionary containing all test statistics
        """
        if not self.results:
            return {}
        
        # Separate successful and failed requests
        successful_requests = [r for r in self.results if r.error is None]
        failed_requests = [r for r in self.results if r.error is not None]
        response_times = [r.response_time for r in successful_requests]
        response_sizes = self.response_sizes
        
        # Basic statistics
        stats = {
            'total_requests': len(self.results),
            'successful_requests': len(successful_requests),
            'failed_requests': len(failed_requests),
            'success_rate': len(successful_requests) / len(self.results) * 100 if self.results else 0,
            'total_duration': self.end_time - self.start_time if self.end_time and self.start_time else 0,
            'requests_per_second': len(self.results) / (self.end_time - self.start_time) if self.end_time and self.start_time else 0,
            'throughput_bytes_per_sec': sum(response_sizes) / (self.end_time - self.start_time) if response_sizes and self.end_time and self.start_time else 0,
        }
        
        # Response time statistics
        if response_times:
            stats.update({
                'min_response_time': min(response_times),
                'max_response_time': max(response_times),
                'mean_response_time': statistics.mean(response_times),
                'median_response_time': statistics.median(response_times),
                'std_response_time': statistics.stdev(response_times) if len(response_times) > 1 else 0,
                'p25_response_time': statistics.quantiles(response_times, n=4)[0] if len(response_times) > 3 else response_times[0],
                'p50_response_time': statistics.quantiles(response_times, n=2)[0] if len(response_times) > 1 else response_times[0],
                'p75_response_time': statistics.quantiles(response_times, n=4)[2] if len(response_times) > 3 else response_times[-1],
                'p90_response_time': statistics.quantiles(response_times, n=10)[8] if len(response_times) > 9 else max(response_times),
                'p95_response_time': statistics.quantiles(response_times, n=20)[18] if len(response_times) > 19 else max(response_times),
                'p99_response_time': statistics.quantiles(response_times, n=100)[98] if len(response_times) > 99 else max(response_times),
            })
        
        # Status code distribution
        status_codes = {}
        for result in successful_requests:
            status_codes[result.status_code] = status_codes.get(result.status_code, 0) + 1
        stats['status_code_distribution'] = status_codes
        
        # Error distribution
        error_types = {}
        for result in failed_requests:
            error_types[result.error] = error_types.get(result.error, 0) + 1
        stats['error_distribution'] = error_types
        
        # Response size statistics
        if response_sizes:
            stats['min_response_size'] = min(response_sizes)
            stats['max_response_size'] = max(response_sizes)
            stats['mean_response_size'] = statistics.mean(response_sizes)
            stats['median_response_size'] = statistics.median(response_sizes)
        
        # DNS and connection time statistics
        if self.dns_times:
            stats['mean_dns_time'] = statistics.mean(self.dns_times)
            stats['max_dns_time'] = max(self.dns_times)
        
        if self.connect_times:
            stats['mean_connect_time'] = statistics.mean(self.connect_times)
            stats['max_connect_time'] = max(self.connect_times)
        
        return stats 