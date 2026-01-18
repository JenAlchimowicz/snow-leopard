class Config:
    EXCHANGE_CODE_US = "US"
    EXCHANGE_CODE_INDIA = "NSE"
    US_EXCAHNGES_IMPORTANT = ["NYSE", "NASDAQ"]  # 9k tickers
    INDIA_EXCHANGES_IMPOPORTANT = ["NSE"]  # 2.6k tickers

    LOCAL_DATA_PATH = "./data/data"
    RESOURCES_PATH = "./resources"

    S3_BUCKET_NAME = "trading-notifications-snow-leopard-1"
    S3_DATA_PATH = "data"

class ColumnConfig:
    CODE = "code"
    EXCHANGE_SHORT_NAME = "exchange_short_name"
    DATE = "date"
    OPEN = "open"
    HIGH = "high"
    LOW = "low"
    CLOSE = "close"
    ADJUSTED_CLOSE = "adjusted_close"
    VOLUME = "volume"
    ID = "id"

    @classmethod
    def validate_columns(cls, columns: list[str]) -> None:
        required_columns = {
            cls.CODE,
            cls.EXCHANGE_SHORT_NAME,
            cls.DATE,
            cls.OPEN,
            cls.HIGH,
            cls.LOW,
            cls.CLOSE,
            cls.ADJUSTED_CLOSE,
            cls.VOLUME,
        }
        assert required_columns.issubset(set(columns)), f"Missing required columns: {required_columns - set(columns)}"
