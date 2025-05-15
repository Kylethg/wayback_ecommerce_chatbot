"""
Wayback Machine API client for the Wayback Ecommerce Chatbot.
"""

import requests
import urllib.parse
import time
import datetime
import random
from typing import Tuple, Optional

# Change relative imports to absolute imports
from app.utils.cache import cache_result
from app.utils.error_handling import retry_with_exponential_backoff, WaybackError, SnapshotNotFoundError

class WaybackClient:
    """Client for interacting with the Wayback Machine API"""
    
    def __init__(self, cache_enabled=True, max_retries=3):
        self.cache_enabled = cache_enabled
        self.max_retries = max_retries
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36",
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive"
        }
    
    @cache_result(expire_after_days=90)
    @retry_with_exponential_backoff(max_retries=3)
    def find_snapshot_for_date(self, site_url: str, target_date: datetime.date, max_offset: int = 7) -> Tuple[Optional[str], Optional[str], Optional[datetime.date]]:
        """
        Find the closest snapshot to the target date using the CDX API.
        
        Args:
            site_url: The URL to find snapshots for
            target_date: The target date to find snapshots for
            max_offset: Maximum number of days to look before/after target date
            
        Returns:
            Tuple of (timestamp, original_url, found_date) or (None, None, None) if no snapshot found
        """
        quoted_url = urllib.parse.quote_plus(site_url)
        
        # Generate a list of dates to try, starting with target_date and then alternating between
        # dates before and after, increasing the offset each time
        offsets = [0]
        for i in range(1, max_offset + 1):
            offsets.append(i)
            offsets.append(-i)
        offsets.sort(key=lambda x: abs(x))  # 0, 1, -1, 2, -2, ...
        
        for offset in offsets:
            test_date = target_date + datetime.timedelta(days=offset)
            timestamp = test_date.strftime("%Y%m%d")
            
            # Use exact date in the Wayback CDX API 
            cdx_url = f"http://web.archive.org/cdx/search/cdx?url={quoted_url}&from={timestamp}&to={timestamp}&output=json&fl=timestamp,original&limit=1&filter=statuscode:200"
            
            print(f"Searching for snapshot on {test_date.isoformat()} for URL: {site_url}")
            
            try:
                response = requests.get(cdx_url, headers=self.headers)
                # Introduce a small delay to be respectful of the Wayback Machine's servers
                time.sleep(0.5)
                
                if response.status_code == 200:
                    data = response.json()
                    # CDX API returns a list with the first item being the column headers, followed by results
                    if len(data) > 1:  # If we have a result besides the header
                        timestamp, original_url = data[1]
                        return timestamp, original_url, test_date
                    else:
                        print(f"No snapshot found for {test_date.isoformat()}")
                else:
                    print(f"CDX API request failed with status code: {response.status_code}")
                    
            except Exception as e:
                print(f"Error searching for snapshot for {test_date.isoformat()}: {e}")
        
        # If we get here, we've tried all offsets and found nothing
        return None, None, None
    
    @cache_result(expire_after_days=90)
    @retry_with_exponential_backoff(max_retries=3)
    def get_snapshot_content(self, timestamp: str, original_url: str) -> Optional[str]:
        """
        Retrieve the full HTML content of a snapshot using the timestamp and original URL.
        
        Args:
            timestamp: The Wayback Machine timestamp
            original_url: The original URL of the snapshot
            
        Returns:
            HTML content as string, or None if retrieval failed
        """
        # URL encode the original URL to use in the Wayback Machine URL
        encoded_url = urllib.parse.quote(original_url, safe='')
        wayback_url = f"http://web.archive.org/web/{timestamp}/{encoded_url}"
        
        print(f"Retrieving content from: {wayback_url}")
        
        try:
            response = requests.get(wayback_url, headers=self.headers)
            # Introduce a small delay to be respectful of the Wayback Machine's servers
            time.sleep(1)
            
            if response.status_code == 200:
                content = response.text
                # Quick validation to ensure we got actual HTML content
                if content and len(content) > 500 and "<html" in content.lower():
                    return content
                else:
                    print(f"Retrieved content appears invalid or too short (length: {len(content) if content else 0})")
            else:
                print(f"Failed to retrieve snapshot content. Status code: {response.status_code}")
        except Exception as e:
            print(f"Error retrieving snapshot content: {e}")
        
        return None
    
    def get_wayback_url(self, timestamp: str, original_url: str) -> str:
        """
        Generate the Wayback Machine URL for a snapshot.
        
        Args:
            timestamp: The Wayback Machine timestamp
            original_url: The original URL of the snapshot
            
        Returns:
            Wayback Machine URL as string
        """
        encoded_url = urllib.parse.quote(original_url, safe='')
        return f"https://web.archive.org/web/{timestamp}/{encoded_url}"