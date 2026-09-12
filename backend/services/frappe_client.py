import time
import json
import requests
import pandas as pd
from config.settings import settings
from utils.logger import logger

class FrappeClient:
    def __init__(self):
        """Initialize Frappe client with credentials and base URL."""
        self.base_url = settings.ERP_BASE_URL.rstrip('/')
        self.headers = {
            "Authorization": f"token {settings.ERP_API_KEY}:{settings.ERP_API_SECRET}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

    def fetch_data(self, doctype: str, fields: list = None, filters: list = None, max_records: int = 100000):
        """
        Fetches historical data with pagination, filters, and a hard row limit.
        
        Args:
            doctype (str): The Frappe DocType to fetch.
            fields (list, optional): List of fields to retrieve.
            filters (list, optional): List of filters for the query.
            max_records (int, optional): Maximum number of records to fetch. Defaults to 100,000.
            
        Returns:
            pd.DataFrame: DataFrame containing the fetched data.
        """
        all_records = []
        limit_start = 0
        limit_page_length = 500
        
        fields_json = json.dumps(fields) if fields else '["*"]'
        filters_json = json.dumps(filters) if filters else None
        
        logger.info(f"Ingesting {doctype}: Limit={max_records}, Filters={filters_json}")
        
        while len(all_records) < max_records:
            # Adjust last batch size to not exceed max_records
            current_page_length = min(limit_page_length, max_records - len(all_records))
            
            params = {
                "fields": fields_json,
                "limit_start": limit_start,
                "limit_page_length": current_page_length,
                "order_by": "creation desc"
            }
            if filters_json:
                params["filters"] = filters_json
            
            url = f"{self.base_url}/api/resource/{doctype}"
            
            success = False
            for attempt in range(1, 4):
                try:
                    response = requests.get(url, headers=self.headers, params=params, timeout=60)
                    
                    if response.status_code == 429:
                        logger.warning("Rate limited. Retrying in 5s...")
                        time.sleep(5)
                        continue
                        
                    response.raise_for_status()
                    data = response.json().get("data", [])
                    
                    if not data:
                        logger.info(f"Reached end of data for {doctype}.")
                        success = True
                        break
                    
                    all_records.extend(data)
                    limit_start += current_page_length
                    success = True
                    
                    if len(all_records) % 5000 == 0:
                        logger.info(f"Progress ({doctype}): {len(all_records)} rows fetched.")
                    
                    time.sleep(0.3) # Fast but respectful
                    break
                    
                except requests.exceptions.RequestException as e:
                    logger.warning(f"Attempt {attempt} failed: {e}")
                    time.sleep(2 ** attempt)
            
            if not success or not data or len(all_records) >= max_records:
                break
        
        if len(all_records) >= max_records:
            logger.info(f"Row limit of {max_records} reached for {doctype}.")
            
        df = pd.DataFrame(all_records)
        if not df.empty and 'name' in df.columns:
            df.drop_duplicates(subset=['name'], inplace=True)
            
        logger.info(f"Completed {doctype}: Total {len(df)} unique rows.")
        return df
