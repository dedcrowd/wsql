


import os
import sys
import requests
import time
import concurrent.futures
import random
import argparse

class Color:
    BLUE = '\033[94m'
    GREEN = '\033[1;92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    RESET = '\033[0m'

class BSQLI:
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        # diğer user-agent'lar...
    ]

    def __init__(self, payload_file, cookie=None, threads=0, verbose=False):
        self.vulnerabilities_found = 0
        self.total_tests = 0
        self.verbose = verbose
        self.vulnerable_urls = []
        self.payloads = self.read_file(payload_file)
        self.cookie = cookie
        self.threads = threads

    def get_random_user_agent(self):
        return random.choice(self.USER_AGENTS)

    def perform_request(self, url, payload, cookie):
        url_with_payload = f"{url}{payload}"
        start_time = time.time()

        headers = {'User-Agent': self.get_random_user_agent()}

        try:
            response = requests.get(url_with_payload, headers=headers, cookies={'cookie': cookie} if cookie else None)
            response.raise_for_status()
            response_time = time.time() - start_time
            success = True
            error_message = None
        except requests.exceptions.RequestException as e:
            response_time = time.time() - start_time
            success = False
            error_message = str(e)

        return success, url_with_payload, response_time, response.status_code if success else None, error_message

    def read_file(self, path):
        try:
            with open(path) as file:
                return [line.strip() for line in file if line.strip()]
        except Exception as e:
            print(f"{Color.RED}Error reading file {path}: {e}{Color.RESET}")
            return []

    def scan(self, urls):
        print(f"\n{Color.PURPLE}Starting scan...{Color.RESET}")

        try:
            if self.threads == 0:
                for url in urls:
                    for payload in self.payloads:
                        self.total_tests += 1
                        success, url_with_payload, response_time, status_code, error_message = self.perform_request(url, payload, self.cookie)
                        if success and status_code and response_time >= 10:
                            self.vulnerabilities_found += 1
                            self.vulnerable_urls.append(url_with_payload)
                            print(f"{Color.BOLD}{Color.GREEN}[✓] Vulnerable URL Detected!{Color.RESET}")
                            print(f"{Color.GREEN}{'='*60}{Color.RESET}")
                            print(f"{Color.GREEN}URL: {Color.RESET}{url_with_payload}")
                            print(f"{Color.GREEN}Status Code: {Color.RESET}{status_code}")
                            print(f"{Color.GREEN}Response Time: {Color.RESET}{response_time} seconds")
                            print(f"{Color.GREEN}Exploit Payload: {Color.RESET}{url_with_payload}")
                            print(f"{Color.GREEN}{'='*60}{Color.RESET}\n")
                        
                        else:
                            if self.verbose:
                                print(f"{Color.BOLD}{Color.RED}[✗] No Vulnerability Found{Color.RESET}")
                                print(f"{Color.RED}{'-'*60}")
                                print(f"{Color.RED}URL Tested: {Color.RESET}{url_with_payload}")
                                print(f"{Color.RED}Status Code: {Color.RESET}{status_code if status_code else 'N/A'}")
                                print(f"{Color.RED}Response Time: {Color.RESET}{response_time if response_time else 'N/A'} seconds")
                                print(f"{Color.RED}Payload Attempted: {Color.RESET}{url_with_payload}")
                                print(f"{Color.RED}{'-'*60}{Color.RESET}\n")

            else:
                with concurrent.futures.ThreadPoolExecutor(max_workers=self.threads) as executor:
                    futures = [executor.submit(self.perform_request, url, payload, self.cookie) for url in urls for payload in self.payloads]
                    for future in concurrent.futures.as_completed(futures):
                        self.total_tests += 1
                        success, url_with_payload, response_time, status_code, error_message = future.result()
                        if success and status_code and response_time >= 10:
                            self.vulnerabilities_found += 1
                            self.vulnerable_urls.append(url_with_payload)
                            print(f"{Color.BOLD}{Color.GREEN}[✓] Vulnerability Detected!{Color.RESET}")
                            print(f"{Color.GREEN}{'-'*60}")
                            print(f"{Color.GREEN}URL: {Color.RESET}{url_with_payload}")
                            print(f"{Color.GREEN}Status Code: {Color.RESET}{status_code}")
                            print(f"{Color.GREEN}Response Time: {Color.RESET}{response_time} seconds")
                            print(f"{Color.GREEN}Payload: {Color.RESET}{url_with_payload}")
                            print(f"{Color.GREEN}{'-'*60}{Color.RESET}\n")
                        
                        else:
                            if self.verbose:
                                print(f"{Color.BOLD}{Color.RED}[✗] No Vulnerability Detected{Color.RESET}")
                                print(f"{Color.RED}{'-'*60}")
                                print(f"{Color.RED}URL: {Color.RESET}{url_with_payload}")
                                print(f"{Color.RED}Status Code: {Color.RESET}{status_code if status_code else 'N/A'}")
                                print(f"{Color.RED}Response Time: {Color.RESET}{response_time if response_time else 'N/A'} seconds")
                                print(f"{Color.RED}Payload Tested: {Color.RESET}{url_with_payload}")
                                print(f"{Color.RED}{'-'*60}{Color.RESET}\n")
                            

        except KeyboardInterrupt:
            print(f"{Color.YELLOW}Scan interrupted by user.{Color.RESET}")

        print(f"\n{Color.BOLD}{Color.BLUE}--- SCAN COMPLETE ---{Color.RESET}\n")
        print(f"{Color.CYAN}{'='*50}{Color.RESET}")
        print(f"{Color.YELLOW}Total Tests Performed: {Color.RESET}{Color.BOLD}{self.total_tests}{Color.RESET}")
        print(f"{Color.GREEN}Vulnerabilities Detected (BSQLi): {Color.RESET}{Color.BOLD}{self.vulnerabilities_found}{Color.RESET}")
        print(f"{Color.CYAN}{'='*50}{Color.RESET}\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='BSQLI Scanner')
    parser.add_argument('-p', '--payloads', required=True, help='Path to the payloads file')
    parser.add_argument('-c', '--cookie', help='Cookie to include in the requests', default=None)
    parser.add_argument('-t', '--threads', type=int, help='Number of concurrent threads (0-10)', default=0)
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose output')

    args = parser.parse_args()

    # URL'yi stdin'den alıyoruz (örneğin: echo example.com | python3 program.py ...)
    input_url = sys.stdin.read().strip()
    if not input_url:
        print(f"{Color.RED}No URL provided.{Color.RESET}")
        sys.exit(1)

    scanner = BSQLI(payload_file=args.payloads, cookie=args.cookie, threads=args.threads, verbose=args.verbose)
    scanner.scan([input_url])
