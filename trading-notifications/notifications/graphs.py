import polars as pl
import mplfinance as mpf
import pandas as pd
from config import Config

def create_candlestick_chart(df, ticker_id):
    """
    Create a candlestick chart with EMA lines for a specific ticker
    
    Parameters:
    df: polars DataFrame with the data
    ticker_id: the id value to filter for (e.g., 'NSE_ASIANPAINT')
    """
    # Filter for the specific ticker and get last 60 days
    ticker_df = df.filter(pl.col('id') == ticker_id).sort('date').tail(60)
    
    if ticker_df.height == 0:
        print(f"No data found for ticker: {ticker_id}")
        return
    
    # Convert to pandas (mplfinance requires pandas)
    pdf = ticker_df.to_pandas()
    
    # Convert date to datetime and set as index
    pdf['date'] = pd.to_datetime(pdf['date'])
    pdf.set_index('date', inplace=True)
    
    # Get ticker info for title
    ticker_code = ticker_df['code'][0]
    ticker_exchange = ticker_df['exchange_short_name'][0]
    
    # Create EMA lines
    ema_lines = [
        mpf.make_addplot(pdf['ema_200'], color='blue', width=2, label='EMA 200'),
        mpf.make_addplot(pdf['ema_20'], color='orange', width=2, label='EMA 20'),
        mpf.make_addplot(pdf['ema_5'], color='purple', width=2, label='EMA 5'),
    ]
    
    # Add flag markers if any exist
    flag_dates = ticker_df.filter(pl.col('flag_ema5_x_ema20_on_green_candle') == True)
    if flag_dates.height > 0:
        # Create a series with NaN for non-flag dates and max price for flag dates
        max_price = pdf['high'].max()
        markers = pd.Series(index=pdf.index, data=float('nan'))
        flag_indices = pd.to_datetime(flag_dates['date'].to_list())
        markers.loc[flag_indices] = max_price * 1.02
        
        ema_lines.append(
            mpf.make_addplot(markers, type='scatter', markersize=100, 
                           marker='v', color='lime', edgecolors='darkgreen',
                           label='EMA5 x EMA20 Cross')
        )
    
    # Custom style
    mc = mpf.make_marketcolors(up='green', down='red', edge='inherit', 
                               wick='inherit', volume='in')
    s = mpf.make_mpf_style(marketcolors=mc, gridstyle=':', y_on_right=False)
    
    # Create and save the plot
    fig, axes = mpf.plot(
        pdf,
        type='candle',
        style=s,
        addplot=ema_lines,
        title=f'{ticker_code} ({ticker_exchange}) - Last 60 Days',
        ylabel='Price',
        figsize=(12, 5),
        returnfig=True,
        warn_too_much_data=100
    )
    
    # Add legend
    axes[0].legend(loc='upper left')
    
    # Save
    fig.savefig(f"{Config.RESOURCES_PATH}/{ticker_id}.png", dpi=100, bbox_inches='tight')
    
    # Close to free memory
    import matplotlib.pyplot as plt
    plt.close(fig)

def create_charts(df: pl.DataFrame, tickers: list[str]):
    for ticker in tickers:
        create_candlestick_chart(df, ticker)
        print(f"Chart created successfully for {ticker}")
