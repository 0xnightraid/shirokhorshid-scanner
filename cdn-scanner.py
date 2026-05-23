#!/usr/bin/env python3
"""
shirOkhorshid CDN IP Scanner v1
Support: CIDR, Range, Single IPs
Features: Ctrl+C save, CDN detection, Fast & Stable
"""

import asyncio
import aiohttp
import ipaddress
from typing import List, Optional
from datetime import datetime
import time
import sys
import signal
from dataclasses import dataclass
from enum import Enum
import argparse

# ========================== COLOR CODES ==========================
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    CYAN = '\033[96m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    END = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'

# ========================== CDN TYPES ==========================
class CDNType(Enum):
    CLOUDFLARE = "Cloudflare"
    CLOUDFRONT = "CloudFront"
    AKAMAI = "Akamai"
    FASTLY = "Fastly"
    NOT_CDN = "Regular"

# ========================== DATA CLASS ==========================
@dataclass
class ScanResult:
    ip: str
    response_time: Optional[int]
    cdn_type: CDNType
    server_header: Optional[str]

# ========================== IP PARSER ==========================
class IPParser:
    @staticmethod
    def parse_cidr(cidr: str) -> List[str]:
        try:
            network = ipaddress.IPv4Network(cidr, strict=False)
            return [str(ip) for ip in network.hosts()]
        except:
            return []
    
    @staticmethod
    def parse_range(range_str: str) -> List[str]:
        try:
            if '-' not in range_str:
                return [range_str]
            
            parts = range_str.split('-')
            start_ip = parts[0].strip()
            end_ip = parts[1].strip()
            
            if start_ip.count('.') == 3 and end_ip.count('.') == 0:
                base = '.'.join(start_ip.split('.')[:3])
                start_last = int(start_ip.split('.')[-1])
                end_last = int(end_ip)
                return [f"{base}.{i}" for i in range(start_last, end_last + 1)]
            
            elif start_ip.count('.') == 3 and end_ip.count('.') == 3:
                start_int = int(ipaddress.IPv4Address(start_ip))
                end_int = int(ipaddress.IPv4Address(end_ip))
                return [str(ipaddress.IPv4Address(i)) for i in range(start_int, end_int + 1)]
            
            return []
        except:
            return []
    
    @staticmethod
    def load_from_file(filename: str) -> List[str]:
        ips = []
        try:
            with open(filename, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    
                    if '/' in line:
                        ips.extend(IPParser.parse_cidr(line))
                    elif '-' in line:
                        ips.extend(IPParser.parse_range(line))
                    elif line.count('.') == 3:
                        ips.append(line)
            
            ips = list(dict.fromkeys(ips))
            return ips
        except FileNotFoundError:
            print(f"{Colors.RED}✗ File not found: {filename}{Colors.END}")
            return []

# ========================== SCANNER ==========================
class IPScanner:
    def __init__(self, timeout: float = 2.0, threads: int = 500):
        self.timeout = timeout
        self.threads = threads
        self.results: List[ScanResult] = []
        self.scanned = 0
        self.total = 0
        self.start_time = None
        self.is_running = True
        self.output_file = None
        
    def signal_handler(self, signum, frame):
        print(f"\n\n{Colors.YELLOW}⚠ Saving current results...{Colors.END}")
        self.is_running = False
    
    async def check_ip(self, ip: str, semaphore: asyncio.Semaphore, session: aiohttp.ClientSession) -> Optional[ScanResult]:
        """Check single IP - try HTTPS first, then HTTP"""
        async with semaphore:
            if not self.is_running:
                return None
            
            # Try HTTPS first
            result = await self.try_request(ip, session, 'https')
            if result:
                return result
            
            # Fallback to HTTP
            result = await self.try_request(ip, session, 'http')
            return result
    
    async def try_request(self, ip: str, session: aiohttp.ClientSession, protocol: str) -> Optional[ScanResult]:
        """Try single request with given protocol"""
        try:
            start = time.time()
            
            async with session.get(
                f'{protocol}://{ip}',
                timeout=self.timeout,
                ssl=False,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Accept': '*/*',
                    'Connection': 'close'
                }
            ) as resp:
                response_time = int((time.time() - start) * 1000)
                server_header = resp.headers.get('Server', '')
                
                # Detect CDN
                cdn_type = CDNType.NOT_CDN
                server_lower = server_header.lower()
                
                if 'cloudflare' in server_lower or 'cf-ray' in resp.headers:
                    cdn_type = CDNType.CLOUDFLARE
                elif 'cloudfront' in server_lower or 'x-amz-cf-id' in resp.headers:
                    cdn_type = CDNType.CLOUDFRONT
                elif 'akamai' in server_lower or 'x-akamai' in str(resp.headers).lower():
                    cdn_type = CDNType.AKAMAI
                elif 'fastly' in server_lower:
                    cdn_type = CDNType.FASTLY
                
                return ScanResult(
                    ip=ip,
                    response_time=response_time,
                    cdn_type=cdn_type,
                    server_header=server_header[:50] if server_header else None
                )
        except:
            return None
    
    async def scan(self, ip_list: List[str], output_file: str):
        """Main scan function"""
        self.total = len(ip_list)
        self.start_time = time.time()
        self.results = []
        self.scanned = 0
        self.is_running = True
        self.output_file = output_file
        
        signal.signal(signal.SIGINT, self.signal_handler)
       
        print(f"  Total IPs: {self.total:,}")
        print(f"  Timeout: {self.timeout}s")
        print(f"  Threads: {self.threads}")
        print(f"  Output: {output_file}")
        print(f"{Colors.DIM}  Press Ctrl+C to save results{Colors.END}")
        print(f"{Colors.CYAN}{'='*60}{Colors.END}\n")
        
        semaphore = asyncio.Semaphore(self.threads)
        connector = aiohttp.TCPConnector(
            ssl=False, 
            limit=0,
            force_close=True,
            enable_cleanup_closed=True
        )
        
        timeout_config = aiohttp.ClientTimeout(total=self.timeout)
        
        async with aiohttp.ClientSession(connector=connector, timeout=timeout_config) as session:
            batch_size = 1000
            
            for i in range(0, self.total, batch_size):
                if not self.is_running:
                    break
                
                batch = ip_list[i:i+batch_size]
                tasks = [self.check_ip(ip, semaphore, session) for ip in batch]
                
                for coro in asyncio.as_completed(tasks):
                    if not self.is_running:
                        break
                    result = await coro
                    if result:
                        self.results.append(result)
                        self.print_live_result(result)
                    self.scanned += 1
                    
                    if self.scanned % 100 == 0 or self.scanned == self.total:
                        self.print_progress()
        
        self.save_results()
        return self.results
    
    def print_live_result(self, result: ScanResult):
        if result.cdn_type != CDNType.NOT_CDN:
            print(f"\r{Colors.GREEN}✓{Colors.END} {result.ip:18} | "
                  f"{Colors.CYAN}{result.cdn_type.value:12}{Colors.END} | "
                  f"{result.response_time:4}ms    ")
        else:
            print(f"\r{Colors.BLUE}●{Colors.END} {result.ip:18} | "
                  f"{Colors.DIM}Regular{Colors.END}      | "
                  f"{result.response_time:4}ms    ")
    
    def print_progress(self):
        percent = (self.scanned / self.total) * 100
        elapsed = time.time() - self.start_time
        speed = self.scanned / elapsed if elapsed > 0 else 0
        eta = (self.total - self.scanned) / speed if speed > 0 else 0
        
        bar_length = 30
        filled = int(bar_length * self.scanned / self.total)
        bar = f"{Colors.GREEN}{'█' * filled}{Colors.DIM}{'░' * (bar_length - filled)}{Colors.END}"
        
        sys.stdout.write(f"\r[{bar}] {percent:.1f}% | "
                       f"{Colors.GREEN}Found:{len(self.results)}{Colors.END} | "
                       f"{self.scanned:,}/{self.total:,} | "
                       f"{Colors.YELLOW}{speed:.0f} ips/s{Colors.END} | "
                       f"ETA: {eta/60:.1f}m    ")
        sys.stdout.flush()
    
    def save_results(self):
        elapsed = time.time() - self.start_time if self.start_time else 0
        actual_speed = self.scanned / elapsed if elapsed > 0 else 0
        
        cdn_ips = [r.ip for r in self.results if r.cdn_type != CDNType.NOT_CDN]
        regular_ips = [r.ip for r in self.results if r.cdn_type == CDNType.NOT_CDN]
        
        with open(self.output_file, 'w') as f:
            for r in self.results:
                f.write(f"{r.ip}\n")
        
        print(f"\n\n{Colors.CYAN}{'='*60}{Colors.END}")
        print(f"{Colors.BOLD}{Colors.GREEN}📊 SCAN RESULTS{Colors.END}")
        print(f"{Colors.CYAN}{'='*60}{Colors.END}")
        print(f"  Scanned: {self.scanned:,}/{self.total:,}")
        print(f"  {Colors.GREEN}Alive: {len(self.results):,}{Colors.END}")
        print(f"  {Colors.CYAN}CDN: {len(cdn_ips):,}{Colors.END}")
        print(f"  {Colors.DIM}Regular: {len(regular_ips):,}{Colors.END}")
        print(f"  Time: {elapsed:.1f}s")
        print(f"  Speed: {actual_speed:.0f} ips/s")
        print(f"\n  {Colors.GREEN}✓ Saved to: {self.output_file}{Colors.END}")
        print(f"{Colors.CYAN}{'='*60}{Colors.END}")

# ========================== MAIN ==========================
async def main():
    print(f"""
{Colors.CYAN}{'='*60}{Colors.END}
{Colors.BOLD}{Colors.GREEN}  shirOkhorshid CDN IP SCANNER v1{Colors.END}
{Colors.CYAN}{'='*60}{Colors.END}
    """)
    
    parser = argparse.ArgumentParser(description='shirOkhorshid CDN IP Scanner v1')
    parser.add_argument('-i', '--input', default='ip_list.txt', help='Input file')
    parser.add_argument('-o', '--output', default='alive_ips.txt', help='Output file')
    parser.add_argument('-t', '--timeout', type=float, default=2.0, help='HTTP timeout')
    parser.add_argument('-c', '--concurrent', type=int, default=500, help='Concurrent threads')
    
    args = parser.parse_args()
    
    print(f"{Colors.YELLOW}📁 Loading IPs from {args.input}...{Colors.END}")
    ip_list = IPParser.load_from_file(args.input)
    
    if not ip_list:
        print(f"{Colors.RED}❌ No valid IPs found!{Colors.END}")
        return
    
    print(f"{Colors.GREEN}✓ Loaded {len(ip_list):,} IPs{Colors.END}")
    
    scanner = IPScanner(timeout=args.timeout, threads=args.concurrent)
    await scanner.scan(ip_list, args.output)

if __name__ == "__main__":
    asyncio.run(main())
