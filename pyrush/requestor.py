"""
HTTP request handling for PyRush stress testing
"""

import asyncio
import aiohttp
import time
import ssl
import certifi
from .models import RequestResult

async def make_request(tester, session: aiohttp.ClientSession, url: str, method: str) -> RequestResult:
    """
    Make a single HTTP request and return the result
    
    Args:
        tester: StressTester instance containing configuration and state
        session: aiohttp ClientSession for making requests
        url: URL to request
        method: HTTP method to use
        
    Returns:
        RequestResult containing the response details
    """
    start_time = time.time()
    timestamp = start_time
    dns_time = None
    connect_time = None
    
    try:
        # Prepare request kwargs
        kwargs = {
            'timeout': aiohttp.ClientTimeout(total=tester.config.timeout),
            'headers': tester.config.headers.copy(),
            'allow_redirects': not tester.config.disable_redirects,
            'compress': not tester.config.disable_compression
        }
        
        # Handle multipart/form-data
        use_form = hasattr(tester, 'form') and (tester.form or tester.form_file)
        if use_form:
            from aiohttp import FormData
            form = FormData()
            
            # Add form fields
            for f in getattr(tester, 'form', []):
                if '=' in f:
                    k, v = f.split('=', 1)
                    form.add_field(k, v)
            
            # Add file uploads
            for f in getattr(tester, 'form_file', []):
                if '=' in f:
                    k, path = f.split('=', 1)
                    try:
                        form.add_field(k, open(path, 'rb'))
                    except Exception as e:
                        return RequestResult(
                            url=url, 
                            method=method, 
                            status_code=0, 
                            response_time=0, 
                            timestamp=timestamp, 
                            error=f"File error: {e}"
                        )
            
            kwargs['data'] = form
            
            # Set content-type if not already set
            if 'Content-Type' not in kwargs['headers']:
                kwargs['headers']['Content-Type'] = 'multipart/form-data'
        
        # Handle regular request body
        elif tester.config.data:
            kwargs['data'] = tester.config.data
        elif tester.config.data_file:
            with open(tester.config.data_file, 'r') as f:
                kwargs['data'] = f.read()
        
        # Add authentication
        if tester.config.auth:
            kwargs['auth'] = aiohttp.BasicAuth(tester.config.auth[0], tester.config.auth[1])
        
        # Add proxy
        if tester.config.proxy:
            kwargs['proxy'] = tester.config.proxy
        
        # Add custom host header
        if tester.config.host:
            kwargs['headers']['Host'] = tester.config.host
        
        # Make the request
        async with session.request(method, url, **kwargs) as response:
            response_data = await response.read()
            response_time = time.time() - start_time
            error = None
            
            # Check custom assertions
            if hasattr(tester, 'assert_status') and tester.assert_status is not None:
                if response.status != tester.assert_status:
                    error = f"Assert status {tester.assert_status} failed (got {response.status})"
            
            if hasattr(tester, 'assert_body_contains') and tester.assert_body_contains:
                try:
                    body_str = response_data.decode(errors='ignore')
                    if tester.assert_body_contains not in body_str:
                        error = f"Assert body contains '{tester.assert_body_contains}' failed"
                except Exception:
                    error = f"Assert body contains '{tester.assert_body_contains}' failed (decode error)"
            
            if hasattr(tester, 'assert_max_rt') and tester.assert_max_rt is not None:
                if response_time > tester.assert_max_rt:
                    error = f"Assert max response time {tester.assert_max_rt}s failed (got {response_time:.3f}s)"
            
            # Update statistics
            with tester.lock:
                if dns_time is not None:
                    tester.dns_times.append(dns_time)
                if connect_time is not None:
                    tester.connect_times.append(connect_time)
                tester.response_sizes.append(len(response_data))
            
            return RequestResult(
                url=url,
                method=method,
                status_code=response.status,
                response_time=response_time,
                timestamp=timestamp,
                error=error,
                response_size=len(response_data)
            )
    
    except Exception as e:
        response_time = time.time() - start_time
        return RequestResult(
            url=url,
            method=method,
            status_code=0,
            response_time=response_time,
            timestamp=timestamp,
            error=str(e)
        )

async def worker(tester, session: aiohttp.ClientSession, urls: list, method: str, 
                request_queue: asyncio.Queue, rate_limit):
    """
    Worker function that processes requests from the queue
    
    Args:
        tester: StressTester instance
        session: aiohttp ClientSession
        urls: List of URLs to cycle through
        method: HTTP method to use
        request_queue: Queue containing request IDs
        rate_limit: Rate limit per worker (requests per second)
    """
    url_count = len(urls)
    
    while True:
        try:
            # Get request ID from queue
            request_id = await asyncio.wait_for(request_queue.get(), timeout=1.0)
            
            # None indicates worker should stop
            if request_id is None:
                break
            
            # Apply rate limiting
            if rate_limit:
                await asyncio.sleep(1.0 / rate_limit)
            
            # Select URL (round-robin)
            url = urls[request_id % url_count]
            
            # Make the request
            result = await make_request(tester, session, url, method)
            
            # Store result and update progress
            with tester.lock:
                tester.results.append(result)
                tester.update_progress()
                
        except asyncio.TimeoutError:
            break
        except Exception as e:
            print(f"[WORKER ERROR] {e}")
            break
        finally:
            try:
                request_queue.task_done()
            except Exception:
                pass 