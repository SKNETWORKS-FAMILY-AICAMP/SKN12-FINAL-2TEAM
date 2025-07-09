import pandas as pd
import yfinance as yf
import pandas_ta as ta
from sklearn.preprocessing import MinMaxScaler

def fetch_market_data(ticker: str, start: str, end: str) -> pd.DataFrame:
    """
    Fetch OHLCV market data for a given ticker.
    Args:
        ticker (str): Stock ticker symbol.
        start (str): Start date (YYYY-MM-DD).
        end (str): End date (YYYY-MM-DD).
    Returns:
        pd.DataFrame: OHLCV dataframe (date-indexed)
    """
    df = yf.download(ticker, start=start, end=end, progress=False)
    # MultiIndex(Price, Ticker) → 단일 인덱스(Price)
    if isinstance(df.columns, pd.MultiIndex):
        df = df.copy()
        df.columns = df.columns.get_level_values(0)
    df.columns = [str(c).lower() for c in df.columns]
    df.index.name = 'date'
    return df

def fetch_fundamentals(ticker: str) -> dict:
    """
    Fetch fundamental data for a given ticker.
    Args:
        ticker (str): Stock ticker symbol.
    Returns:
        dict: { 'EPS': float, 'ROE': float, 'PER': float, 'DebtEquity': float, 'DividendYield': float }
    """
    info = yf.Ticker(ticker).info
    fundamentals = {
        'EPS': info.get('trailingEps'),
        'ROE': info.get('returnOnEquity'),
        'PER': info.get('trailingPE'),
        'DebtEquity': info.get('debtToEquity'),
        'DividendYield': info.get('dividendYield'),
    }
    return fundamentals

def generate_technical_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Generate technical indicators using pandas-ta.
    Args:
        df (pd.DataFrame): OHLCV dataframe.
    Returns:
        pd.DataFrame: Dataframe with technical indicators columns added.
    """
    df = df.copy()
    df.columns = [str(c).lower() for c in df.columns]
    if df.empty or 'close' not in df.columns:
        print("[경고] 입력 데이터에 'close' 컬럼이 없거나 데이터가 비어 있습니다.")
        return df
    df = df.dropna(subset=['close'])
    df['rsi'] = ta.rsi(df['close'], length=14)
    macd = ta.macd(df['close'])
    if macd is not None:
        df['macd'] = macd.get('MACD_12_26_9')
        df['macd_signal'] = macd.get('MACDs_12_26_9')
        df['macd_hist'] = macd.get('MACDh_12_26_9')
    else:
        df['macd'] = df['macd_signal'] = df['macd_hist'] = None
    df['ema20'] = ta.ema(df['close'], length=20)
    bbands = ta.bbands(df['close'], length=20)
    if bbands is not None:
        df['bb_upper'] = bbands.get('BBU_20_2.0')
        df['bb_middle'] = bbands.get('BBM_20_2.0')
        df['bb_lower'] = bbands.get('BBL_20_2.0')
    else:
        df['bb_upper'] = df['bb_middle'] = df['bb_lower'] = None
    df['obv'] = ta.obv(df['close'], df['volume'])
    return df

def merge_and_normalize(
    ohlcv_df: pd.DataFrame,
    fundamentals: dict,
) -> pd.DataFrame:
    """
    Merge OHLCV, technicals, and fundamentals, then normalize.
    Args:
        ohlcv_df (pd.DataFrame): OHLCV + technicals dataframe.
        fundamentals (dict): Fundamental data.
    Returns:
        pd.DataFrame: Final normalized dataframe.
    """
    df = ohlcv_df.copy()
    # 결측치 forward fill
    df = df.fillna(method='ffill').fillna(method='bfill')
    # fundamentals를 각 row에 추가
    for key, value in fundamentals.items():
        df[key] = value
    # 정규화 (MinMaxScaler)
    scaler = MinMaxScaler()
    scaled = scaler.fit_transform(df)
    df_scaled = pd.DataFrame(scaled, columns=df.columns, index=df.index)
    return df_scaled 