import trade


product_code = "FX_BTC_JPY"
child_order_type = "LIMIT"
side = "BUY"
price = 3800000
size = 0.01

trade1 = trade.TradeClass()
trade1.purchase(product_code ,child_order_type ,side, price ,size)

print(trade1.response.status_code)
print(trade1.response.json())