import copy
import time
from typing import List

import numpy as np
import pandas as pd


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

    just_loss_cut : bool | None
        true => ロスカットが価格通りに執行
        false => ろうそく足のclose価格で執行される

    Methods
    ----------

    """

    def __init__(
        self,
        symbol: str,
        order_lot: int = 1,
        pyramitting: int = 1,
        take_profit: bool = False,
        loss_cut_rate: float = 0,
        just_loss_cut: bool = False,
    ):
        self.symbol = symbol
        self.results = None
        self.order_lot = order_lot
        self.pyramitting = pyramitting
        self.take_profit = take_profit
        self.loss_cut_rate = loss_cut_rate
        self.just_loss_cut = just_loss_cut

    def run_backtest(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        バックテストの実行
        売買条件、利確損切り条件が既に入力されたデータに対して行う

        Parameters
        ----------
        df : DataFrame
            バックテスト元データ

        Returns
        ----------
        order_df : DataFrame
            売買履歴のデータフレーム
        """
        print("----------start backtest----------")
        start = time.time()

        # 各データをリストにしておく
        buy_signals: List[int] = df["b_sig"].values
        sell_signals: List[int] = df["s_sig"].values

        if self.take_profit:
            buy_tp_signals = df["b_tp_sig"].values
            sell_tp_signals = df["s_tp_sig"].values

        if "timestamp" in df.columns:
            timestamp = df["timestamp"].values
        elif "time" in df.columns:
            timestamp = df["time"].values

        close = df["close"].values

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
                    order = [i, timestamp[i], -current_position, "SELL", price]
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
                    order = [i, timestamp[i], -current_position, "BUY", price]
                    current_position = 0
                    orders.append(order)
                    print("short is cut")
                    # print(f"losscut loopnum:{i}　現在のポジションは{current_position}です。")

        order_df = pd.DataFrame(orders, columns=["id", "time", "lot", "side", "price"])
        print(" ----   finish backtest   ----")
        elapsed_time = time.time() - start
        print(f" ----   elapsed time: {elapsed_time}   ---- ")
        return order_df

    def make_pl(self, df: pd.DataFrame, comfee: int = 0, initial: int = 100) -> pd.DataFrame:
        """
        オーダー情報を元に損益計算を行う

        Attributes
        ----------
        df : DataFrame
            size : float or int
            time : unixtime or datetime
            price : float or int
        initial : int
            初期資金
        comfee : int
            手数料

        Returns
        ----------
        df : DataFrame
            分析結果のデータフレーム
        """

        print(" ----- Make PL Graph -----")
        start = time.time()

        # それぞれをnumpyに変換
        size = df["lot"].values
        # timestamp = df.time.values
        price = df["price"].values
        pct_price = df["price"].pct_change().values

        # buy sellの書き換え
        # size = df["lot"].values

        # 計算用PL
        PLs = np.zeros(len(df))

        cumsum_position_size = np.cumsum(size)
        for i in range(1, len(df)):
            # 手数料がある場合
            if comfee:
                # ポジションサイズ*価格変動値 - 手数料
                PLs[i] = pct_price[i] * cumsum_position_size[i - 1] - comfee * price[i] * cumsum_position_size[i]
            else:
                PLs[i] = pct_price[i] * cumsum_position_size[i - 1]

        # 一回ごとの損益
        df["PL"] = PLs
        tmp_PLs = copy.copy(PLs)
        tmp_PLs[0] += initial

        # 累積損益
        PL_graph = np.cumsum(tmp_PLs)
        df["PL_graph"] = PL_graph

        # 勝率
        tmp = PLs > 0
        none_cnt = PLs == 0
        none_cnt = none_cnt.sum()
        tmp = tmp.sum()
        win_rate = tmp / (len(PLs) - none_cnt)

        # 実現損益
        realized_pl = PL_graph[-1] - initial

        # 平均損益
        avg_pl = realized_pl / len(PLs)

        # 総利益
        profit_total = df["PL"][df["PL"] > 0].sum()

        # 総損失
        loss_total = df["PL"][df["PL"] < 0].sum()

        # PF
        PF = profit_total / abs(loss_total)

        # DD_max
        PL_max = 0.00
        DD_max = 0.00
        DD_per = 0.00
        for i in df["PL_graph"]:
            if PL_max < i:
                PL_max = i
            DD = PL_max - i
            if DD_max < DD:
                DD_max = DD
                DD_per = (DD_max / PL_max) * 100
        df["_cumsum"] = cumsum_position_size
        print(
            f"""
            取引回数: {len(PLs)} \n実現損益: {realized_pl} \n勝率: {win_rate} \n
            平均損益: {avg_pl} \n総利益: {profit_total} \n
            総損失: {loss_total}\nPF: {PF}\n最大DD: {DD_max}({DD_per}%)
            """
        )
        elapsed_time = time.time() - start
        print(f" ----   elapsed time: {elapsed_time}   ---- ")
        return df
