import pandas as pd


def timestamp_change(df: pd.DataFrame, span: int) -> pd.DataFrame:
    """
    受け取ったdataframeの時間足を指定した分足に変換
    
    Parameters
    ----------
    df : DataFrame
        変換元となるデータフレーム
    span : int
        何分足にするか → 分数で必ず記載

    Returns
    -------
    result_df : DataFrame
        指定した時間足で丸めたもの
    """
    cols = ["open", "high", "low", "close", "symbol", "timestamp"]
    # span刻みでのstart時刻
    if df["timestamp"].values[0] % (span * 60) == 0:
        start = df["timestamp"].values[0]
    else:
        start = (df["timestamp"].values[0] // (span * 60) * (span * 60)) + (span * 60)
    last = df["timestamp"].values[-1] // (span * 60) * (span * 60)
    data = []
    while start <= last:
        # 指定範囲での切り出し
        term_df = df[(df["timestamp"] >= start) & (df["timestamp"] < start + (span * 60))]

        # span刻みでのロウソク足作成
        timestamp = start
        max_price = term_df.max()["high"]
        min_price = term_df.min()["low"]
        open_price = term_df["open"].values[0]
        close_price = term_df["close"].values[-1]
        raw = [open_price, max_price, min_price, close_price, df["symbol"], timestamp]
        data.append(raw)
        start += span * 60
    result_df = pd.DataFrame(data)
    result_df.columns = cols

    return result_df
