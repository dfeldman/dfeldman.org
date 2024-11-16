import json
import sys
import requests
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
import time

BASE_URL="https://kccncna2024.sched.com/"
def setup_session():
    """
    Create a requests session with retry logic and timeouts
    """
    session = requests.Session()
    
    # Configure retry strategy
    retries = Retry(
        total=3,  # number of retries
        backoff_factor=1,  # wait 1, 2, 4 seconds between retries
        status_forcelist=[500, 502, 503, 504]  # retry on these HTTP status codes
    )
    
    # Apply retry strategy to both http and https
    session.mount('http://', HTTPAdapter(max_retries=retries))
    session.mount('https://', HTTPAdapter(max_retries=retries))
    
    return session

def download_urls(input_file):
    """
    Download URLs from input file and return as list of dictionaries
    """
    results = []
    session = setup_session()
    
    try:
        with open(input_file, 'r') as f:
            urls = [line.strip() for line in f if line.strip()]
            
        total_urls = len(urls)
        
        for i, url in enumerate(urls, 1):
            try:
                print(f"Downloading {i}/{total_urls}: {url}", file=sys.stderr)
                
                # Get the content with timeout
                response = session.get(BASE_URL+url, timeout=30)
                response.raise_for_status()
                
                results.append({
                    "url": url,
                    "content": response.text
                })
                
                # Small delay to be nice to the server
                time.sleep(1)
                
            except requests.exceptions.RequestException as e:
                print(f"WARNING: Failed to download {url}: {str(e)}", file=sys.stderr)
                results.append({
                    "url": url,
                    "content": None,
                    "error": str(e)
                })
                
    except Exception as e:
        print(f"Error processing input file: {str(e)}", file=sys.stderr)
        sys.exit(1)
        
    return results

def main():
    if len(sys.argv) != 2:
        print("Usage: python script.py <input_file>", file=sys.stderr)
        sys.exit(1)
    
    input_file = sys.argv[1]
    results = download_urls(input_file)
    
    # Output JSON to stdout
    json.dump(results, sys.stdout, indent=2)

if __name__ == "__main__":
    main()

