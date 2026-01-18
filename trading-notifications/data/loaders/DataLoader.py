from datetime import date, timedelta
from data.loaders.EodhdClient import EodhdClient
from data.loaders.storage.StorageClient import StorageClient
from config import Config, ColumnConfig
from typing import List
import polars as pl

class DataLoader:
    def __init__(self, eodhdClient: EodhdClient, storageClient: StorageClient):
        self.eodhdClient = eodhdClient
        self.storageClient = storageClient

    def _dates_between(self, date_from: date, date_to: date | None = None) -> list[str]:
        """Return all dates between date_from and date_to (inclusive) as YYYY-MM-DD strings.
        If date_to is None, use today's date."""
        date_to = date_to or date.today()
        step = timedelta(days=1)
        direction = 1 if date_to >= date_from else -1
        dates = []
        current = date_from
        while True:
            dates.append(current.isoformat())
            if current == date_to:
                break
            current += step * direction
        return dates

    def _get_relevant_tickers(self) -> pl.DataFrame:
        tickers = []
        for exchange in Config.US_EXCAHNGES_IMPORTANT + Config.INDIA_EXCHANGES_IMPOPORTANT:
            exchange_tickers = (
                self.eodhdClient.get_tickers_for_exchange(exchange)
                .filter(pl.col("Type").is_in(["Common Stock"]))
                .select(pl.col("Code").alias(ColumnConfig.CODE))
            )
            tickers.append(exchange_tickers)
        return pl.concat(tickers, how="vertical")

    def load_missing_data(self) -> None:
        dates_for_which_we_have_data: List[str] = self.storageClient.list_files()
        dates_for_which_we_need_data: List[str] = self._dates_between(date(2024, 1, 1))
        dates_for_which_we_need_to_download_data = (
            set(dates_for_which_we_need_data) - set(dates_for_which_we_have_data)
        )
        print(f"Days missing: {len(dates_for_which_we_need_to_download_data)}")
        relevant_tickers: pl.DataFrame = self._get_relevant_tickers()
        for dateString in list(dates_for_which_we_need_to_download_data):
            print(dateString)
            data: pl.DataFrame = self.eodhdClient.bulk_load_us_india_exchanges_eod_data(dateString)
            try:
                data = (
                    data
                    # Filters junk us exchanges and non common stocks (etfs, bonds etc)
                    .filter(pl.col(ColumnConfig.CODE).is_in(relevant_tickers[ColumnConfig.CODE].implode()))
                )
            except Exception as e:
                print("empty df - weekend or holiday")
            
            # most likely there is no data yet for today
            if dateString == date.today().isoformat():
                if data.height == 0:
                    continue

            if data.height > 0:
                ColumnConfig.validate_columns(data.columns)
            self.storageClient.upload_polars_df(data, dateString)

    def load_data(self, date_from: date, date_to: date | None = None) -> pl.DataFrame:
        dates = self._dates_between(date_from, date_to)

        dates_for_which_we_have_data: List[str] = []
        for dateString in dates:
            if self.storageClient.exists(dateString):
                dates_for_which_we_have_data.append(dateString)
            else:
                print(f"Data for date {dateString} is missing in storage.")
        data = self.storageClient.load_files_to_polars_df(dates_for_which_we_have_data)
        ColumnConfig.validate_columns(data.columns)
        return data
