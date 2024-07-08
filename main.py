import websocket
import json
import talib
import numpy as np
import matplotlib.pyplot as plt
from pushbullet import Pushbullet

# Pushbullet setup
PUSHBULLET_API_KEY = 'o.oU5nolhxWcIScdpVnsZgUdNZs8jlLHjA'
pb = Pushbullet(PUSHBULLET_API_KEY)

# Other setup
API_KEY = 'GFTmIPZ3PQwOVm1'
volatilities = ['R_10', 'R_25', 'R_50', 'R_75', 'R_100']
close_prices = {vol: [] for vol in volatilities}

def send_alert(message):
    pb.push_note("Market Alert", message)

def on_message(ws, message):
    data = json.loads(message)
    tick = data.get('history', {}).get('prices', [])
    symbol = data.get('echo_req', {}).get('ticks_history')
    if tick and symbol:
        close_prices[symbol].extend(map(float, tick))
        if len(close_prices[symbol]) >= 20:
            calculate_indicators(symbol)
            analyze_odd_even_market(symbol)

def on_error(ws, error):
    print(f"Error: {error}")

def on_close(ws):
    print("### closed ###")

def on_open(ws):
    for volatility in volatilities:
        sub_msg = json.dumps({
            "ticks_history": volatility,
            "adjust_start_time": 1,
            "count": 20,
            "end": "latest",
            "start": 1,
            "style": "ticks",
            "subscribe": 1
        })
        ws.send(sub_msg)

def calculate_indicators(symbol):
    prices = np.array(close_prices[symbol])
    connors_rsi = talib.RSI(prices, timeperiod=3)
    high_prices = np.array(prices[-20:])
    low_prices = np.array(prices[-20:])
    donchian_upper = talib.MAX(high_prices, timeperiod=20)
    donchian_lower = talib.MIN(low_prices, timeperiod=20)
    chaikin_volatility = talib.ATR(high_prices, low_prices, prices[-20:], timeperiod=10)

    # Conditions for a fall market
    if connors_rsi[-1] < 50 and prices[-1] < donchian_lower[-1] and chaikin_volatility[-1] > 0:
        send_alert(f"{symbol} - Fall Market Detected")
        print(f"{symbol} - Fall Market Detected")
        print(f"Connors RSI: {connors_rsi[-1]}, Donchian Lower: {donchian_lower[-1]}, Chaikin Volatility: {chaikin_volatility[-1]}")

    # Conditions for a rise market
    if connors_rsi[-1] > 50 and prices[-1] > donchian_upper[-1] and chaikin_volatility[-1] > 0:
        send_alert(f"{symbol} - Rise Market Detected")
        print(f"{symbol} - Rise Market Detected")
        print(f"Connors RSI: {connors_rsi[-1]}, Donchian Upper: {donchian_upper[-1]}, Chaikin Volatility: {chaikin_volatility[-1]}")

    print(f"{symbol} - Connors RSI: {connors_rsi[-1]}, Donchian Upper: {donchian_upper[-1]}, Donchian Lower: {donchian_lower[-1]}, Chaikin Volatility: {chaikin_volatility[-1]}")

def analyze_odd_even_market(symbol):
    prices = close_prices[symbol]
    odd_count = sum(1 for price in prices if int(price) % 2 != 0)
    even_count = sum(1 for price in prices if int(price) % 2 == 0)
    total_count = len(prices)
    
    odd_percentage = (odd_count / total_count) * 100
    even_percentage = (even_count / total_count) * 100

    print(f"{symbol} - Odd Market Percentage: {odd_percentage}%, Even Market Percentage: {even_percentage}%")

    # Plotting the results
    labels = ['Odd Market', 'Even Market']
    percentages = [odd_percentage, even_percentage]
    colors = ['g' if odd_percentage >= 80 else 'r', 
              'g' if even_percentage >= 80 else 'r']

    plt.bar(labels, percentages, color=colors)
    plt.xlabel('Market Type')
    plt.ylabel('Percentage')
    plt.title(f'{symbol} Odd/Even Market Analysis')
    plt.ylim(0, 100)
    plt.show()

if __name__ == "__main__":
    websocket.enableTrace(True)
    ws = websocket.WebSocketApp("wss://ws.binaryws.com/websockets/v3?app_id=1089",
                                on_message=on_message,
                                on_error=on_error,
                                on_close=on_close)
    ws.on_open = on_open
    ws.run_forever()
