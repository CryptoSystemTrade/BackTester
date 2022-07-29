import warnings

import numpy as np
import pandas as pd
from vector_tester import VectorTester

warnings.simplefilter("ignore")
# CSVの読み込み
columns = [
    "open_time",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "close_time",
    "quote_asset_volume",
    "number_of_trades",
    "taker_buy_base_asset_volume",
    "taker_buy_quote_asset_volume",
    "ignore",
]
spot_columns = [
    "open_time",
    "open_s",
    "high_s",
    "low_s",
    "close_s",
    "volume_s",
    "close_time",
    "quote_asset_volume_s",
    "number_of_trades_s",
    "taker_buy_base_asset_volume_s",
    "taker_buy_quote_asset_volume_s",
    "ignore_s",
]
futures_raw = pd.read_csv("/root/Yuto/BackTester/backtester/data/futures/futures.csv", names=columns).dropna()
spot_raw = pd.read_csv("/root/Yuto/BackTester/backtester/data/spot/spot.csv", names=spot_columns).dropna()


# 先物価格と現物価格のDFをマージ
df = pd.merge(futures_raw, spot_raw)
df = df[["open_time", "close", "close_s"]]

# 差分の取得(絶対値とパーセント)
df["diff"] = df["close"] - df["close_s"]
df["diff_per"] = (df["diff"] / df["close"]) * 100

# BUSDでの取引手数料 = 0.023% (先物取引)
# 現物取引手数料 = 0.1%
# 売買条件
df["b_sig"] = np.where(df["diff_per"] < -0.1, 1, 0)
df["b_tp_sig"] = np.where(df["diff_per"] < 0.05, 1, 0)
df["s_sig"] = np.where(df["diff_per"] > 0.1, 1, 0)
df["s_tp_sig"] = np.where(df["diff_per"] > -0.05, 1, 0)

vector_test = VectorTester("BTCUSD", take_profit=True)
df.rename(columns={"open_time": "timestamp"}, inplace=True)
result = vector_test.run_backtest(df=df)
vector_test.make_pl(result,comfee=0.04)
