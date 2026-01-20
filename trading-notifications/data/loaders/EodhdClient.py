from typing import Optional
import requests
from config import Config
import polars as pl

class EodhdClient:
    BASE_URL = "https://eodhd.com/api"
    
    def __init__(self, apiToken: str):
        self.API_TOKEN = apiToken

    def get_list_exchanges_url(self) -> str:
        return f"{self.BASE_URL}/exchanges-list/?api_token={self.API_TOKEN}&fmt=json"
    
    def get_list_tickers_url(self, exchange_code: str) -> str:
        return f"{self.BASE_URL}/exchange-symbol-list/{exchange_code}?api_token={self.API_TOKEN}&fmt=json"
    
    def get_bulk_eod_data_url(self, exchange_code: str, date: str) -> str:
        return f'{self.BASE_URL}/eod-bulk-last-day/{exchange_code}?api_token={self.API_TOKEN}&date={date}&fmt=json'
    
    def get_eod_data_for_ticker_url(self, ticker: str, from_date: Optional[str] = None, to_date: Optional[str] = None) -> str:
        """
        from_date, to_date format: YYYY-MM-DD (optional)
        """
        params = {"period": "d", "api_token": self.API_TOKEN, "fmt": "json"}
        if from_date:
            params["from"] = from_date
        if to_date:
            params["to"] = to_date
        return f"{self.BASE_URL}/eod/{ticker}?" + "&".join([f"{k}={v}" for k, v in params.items()])

    def _fetch_eodhd_data(self, url: str) -> pl.DataFrame:
        resp = requests.get(url, timeout=15)
        if not resp.ok:
            raise RuntimeError(f"Error fetching exchanges list: {resp.status_code} - {resp.text}")
        data = resp.json()
        df = pl.DataFrame(data)
        return df

    def get_tickers_for_exchange(self, exchange_code: str) -> pl.DataFrame:
        url = self.get_list_tickers_url(exchange_code)
        data: pl.DataFrame = self._fetch_eodhd_data(url)
        return data

    def bulk_load_us_india_exchanges_eod_data(self, date: str) -> pl.DataFrame:
        frames = []
        for exchange in [Config.EXCHANGE_CODE_US, Config.EXCHANGE_CODE_INDIA]:
            url = self.get_bulk_eod_data_url(exchange, date)
            df: pl.DataFrame = self._fetch_eodhd_data(url)
            print(f"Loaded {df.height} rows for exchange {exchange} on date {date}")
            if df.height > 5:
                frames.append(df)
        return pl.concat(frames, how="vertical") if frames else pl.DataFrame()
