from backtester.vector_tester import VectorTester
import pandas as pd
import numpy as np
import warnings
warnings.simplefilter('ignore')

def test_run_back_test()->None:
    # CSVの読み込み
    raw = pd.read_csv("./backtester/data/bybit/2022_1_BTC.csv").dropna()
    # 終値のみ切り抜いて新たなデータフレームに格納
    data = raw[['close','timestamp']]
    # 移動平均線の格納
    data['SMA1'] = data['close'].rolling(10).mean()
    data['SMA2'] = data['close'].rolling(50).mean()
    # シグナルを作る
    data['b_sig'] = np.where(data['SMA1'] > data['SMA2'],1,0)
    data['s_sig'] = np.where(data['SMA2'] > data['SMA1'],1,0)
    data = data.dropna()

    tester = VectorTester("BTC")
    result = tester.run_backtest(df=data)
    tester.make_pl(result)
    assert type(tester.make_pl(result)) == pd.DataFrame

