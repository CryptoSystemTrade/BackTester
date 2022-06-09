import time
from typing import List
import numpy as np
import pandas as pd
from scipy.optimize import brute


class VectorTester:
    """
    Class for the vectorized backtesting of trading strategies.

    Attributes
    ----------
    symbol : str
        通貨名

    df : DataFrame
        バックテスト用データフレーム
        必要カラム
            s_sig : bool
            b_sig : bool
            time or timestamp
            if ake_profit = true
                =>  s_tp_sig
                    b_tp_sig

    order_lot : int
        1回あたりのポジションサイズ

    pyramitting : int
        最大保有ポジション単位　何回ピラミッティングするか

    take_profit : bool
        利確シグナルを含むデータフレームかどうか

    loss_cut_rate : float
        ロスカットレート

    just_loss_cut : bool
        true => ロスカットが価格通りに執行
        false => ろうそく足のclose価格で執行される

    Methods
    ----------

    """

    def __init__(
        self,
        symbol: str,
        df: pd.DataFrame,
        order_lot: int = 1,
        pyramitting: int = 1,
        take_profit: bool = False,
        loss_cut_rate=None,
        just_loss_cut=False,
    ):
        self.symbol = symbol
        self.results = None
        self.df = df
        self.order_lot = order_lot
        self.pyramitting = pyramitting
        self.take_profit = take_profit
        self.loss_cut_rate = loss_cut_rate
        self.just_loss_cut = just_loss_cut

    def run_backtest(self, df: pd.DataFrame) -> pd.DataFrame:
        print("----------start backtest----------")
        start = time.time()

        # 各データをリストにしておく
        buy_signals: List[int] = df.b_sig.values
        sell_signals: List[int] = df.s_sig.values

        if self.take_profit:
            buy_tp_signals = df.b_tp_sig.values
            sell_tp_signals = df.b_tp_sig.values

        if "timestamp" in df.columns:
            timestamp = df.timestamp.values
        elif "time" in df.columns:
            timestamp = df.time.values

        close = df.close.values

        # オーダー情報のリスト
        orders = []
        # 現在のポジション
        current_position = 0

        # rawをループ
        for i in range(len(df)):
            # is buy signal and 発注量制限
            BUY = buy_signals[i] == 1 and current_position < self.order_lot * self.pyramitting
            SELL = sell_signals[i] == 1 and current_position > self.order_lot * self.pyramitting * -1

            if self.take_profit:
                BUY_TAKE_PROFIT = buy_tp_signals[i] == 1 and current_position < 0
                SELL_TAKE_PROFIT = sell_tp_signals[i] == 1 and current_position > 0

            # new or add order
            if BUY:
                price = close[i]
                # 1回分のorder
                order = [i, timestamp[i], self.order_lot, "BUY", price]
                current_position += self.order_lot

                orders.append(order)
                # print(f"buy loopnum:{i}　現在のポジションは{current_position}です。")
            elif SELL:
                price = close[i]
                # 1回分のorder
                order = [i, timestamp[i], -self.order_lot, "SELL", price]
                current_position -= self.order_lot

                orders.append(order)
                # print(f"buy loopnum:{i}　現在のポジションは{current_position}です。")

            # take profit order
            if self.take_profit:
                # sellポジションを利確
                if BUY_TAKE_PROFIT and current_position < 0:
                    price = close[i]
                    order = [i, timestamp[i], -current_position, "BUY", price]

                    current_position = 0
                    orders.append(order)
                    # print(f"sell loopnum:{i}　現在のポジションは{current_position}です。")

                elif SELL_TAKE_PROFIT and current_position > 0:
                    price = close[i]
                    order = [i, timestamp[i], current_position, "SELL", price]

                    current_position = 0
                    orders.append(order)
                    # print(f"buy loopnum:{i}　現在のポジションは{current_position}です。")

            # loss cut
            if self.loss_cut_rate and len(orders):
                # 以前の価格よりloss_cut_rate分逆行したら損切り
                # orders[-1][-1] 最後のprice
                Long_loss_cut: bool = current_position > 0 and orders[-1][-1] - close[i] > self.loss_cut_rate
                Short_loss_cut: bool = current_position < 0 and orders[-1][-1] - close[i] < -self.loss_cut_rate
            if Long_loss_cut:
                # positionの履歴に追加
                if self.just_loss_cut:
                    price = orders[-1][-1] - self.loss_cut_rate
                else:
                    price = close[i]
                # positionの履歴に追加
                order = [i, timestamp[i], -current_position, "Sell", price]
                current_position = 0
                orders.append(order)
                # print(f"losscut loopnum:{i}　現在のポジションは{current_position}です。")
            elif Short_loss_cut:
                # positionの履歴に追加
                if self.just_loss_cut:
                    price = orders[-1][-1] + self.loss_cut_rate
                else:
                    price = close[i]
                # positionの履歴に追加
                order = [i, timestamp[i], -current_position, "Buy", price]
                current_position = 0
                orders.append(order)
                print("short is cut")
                # print(f"losscut loopnum:{i}　現在のポジションは{current_position}です。")

            order_df = pd.DataFrame(orders, columns=["id", "time", "sizes", "side", "price"])
            print(" ----   finish backtest   ----")
            elapsed_time = time.time() - start
            print(f" ----   elapsed time: {elapsed_time}   ---- ")
            return order_df

