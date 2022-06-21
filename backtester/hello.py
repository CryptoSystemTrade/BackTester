from os import times
from webbrowser import get
import requests

import constant

targetDate = "1516028400"
targetPeriod = "86400"
api = "https://api.cryptowat.ch/markets/bitflyer/btcjpy/ohlc?periods=" + targetPeriod + "&after=" + targetDate

response = requests.get(api)
jsonData = response.json()

#print(response.json())

highestValut_list = [data[2] for data in jsonData["result"][targetPeriod]]
lowestValue_list = [data[3] for data in jsonData["result"][targetPeriod]]
endValut_list = [data[4] for data in jsonData["result"][targetPeriod]]

print("最高値 : " + str('{:,}'.format(max(highestValut_list))))
print("最安値 : " + str('{:,}'.format(min(lowestValue_list))))
print("終値 : " + str('{:,}'.format(endValut_list[-1])))

