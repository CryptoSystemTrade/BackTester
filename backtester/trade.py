from ast import Param
from itertools import product
from os import times
from signal import sigpending
from webbrowser import get
import requests
import hashlib
import hmac
import datetime
import json

import constant

base_url = "https://api.bitflyer.jp"
purchase_path_url = "/v1/me/sendchildorder"
method = "POST"

api_key = "2kiUNzwpudsBse1k637fzi"
api_secret = "riGH5ESxH207GYGkROXsfhIa0h1xVByvJJ6Ug9fQbv8="



class TradeClass :
    
    #買い注文処理
    def purchase(self, product_code ,child_order_type ,side, price ,size):
        method = "POST"

        timestamp = str(datetime.datetime.today())

        param = {
            "product_code" : "FX_BTC_JPY",
            "child_order_type" : "LIMIT",
            "side" : "BUY",
            "price" :  product_code,
            "size" : size,
        }

        body = json.dumps(param)
        
        message = timestamp + method + purchase_path_url + body
        signatuer = hmac.new(bytearray(api_secret.encode('utf-8')), message.encode('utf-8'), digestmod = hashlib.sha256).hexdigest()

        headers = {
            'ACCESS-KEY' : api_key,
            'ACCESS-TIMESTAMP' : timestamp,
            'ACCESS-SIGN' : signatuer,
            'content-type' : 'application/json'
        }

        self.response = requests.post(base_url + purchase_path_url , data = body, headers  = headers)



    def sell(self):
        print("this is sell class")



    pass





