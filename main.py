import websocket
import json
import numpy as np
import pandas as pd
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
    connors_rsi = calculate_rsi(prices, period=3)
    high_prices = prices[-20:]
    low_prices = prices[-20:]
    donchian_upper = high_prices.max()
    donchian_lower = low_prices.min()
    chaikin_volatility = calculate_atr(high_prices, low_prices, prices[-20:], period=10)

    # Conditions for a fall market
    if connors_rsi < 50 and prices[-1] < donchian_lower and chaikin_volatility > 0:
        send_alert(f"{symbol} - Fall Market Detected")
        print(f"{symbol} - Fall Market Detected")
        print(f"Connors RSI: {connors_rsi}, Donchian Lower: {donchian_lower}, Chaikin Volatility: {chaikin_volatility}")

    # Conditions for a rise market
    if connors_rsi > 50 and prices[-1] > donchian_upper and chaikin_volatility > 0:
        send_alert(f"{symbol} - Rise Market Detected")
        print(f"{symbol} - Rise Market Detected")
        print(f"Connors RSI: {connors_rsi}, Donchian Upper: {donchian_upper}, Chaikin Volatility: {chaikin_volatility}")

    print(f"{symbol} - Connors RSI: {connors_rsi}, Donchian Upper: {donchian_upper}, Donchian Lower: {donchian_lower}, Chaikin Volatility: {chaikin_volatility}")

def calculate_rsi(prices, period=14):
    delta = np.diff(prices)
    gains = delta[delta >= 0]
    losses = -delta[delta < 0]
    avg_gain = np.mean(gains[:period])
    avg_loss = np.mean(losses[:period])
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def calculate_atr(high_prices, low_prices, close_prices, period=14):
    trs = []
    for i in range(1, len(close_prices)):
        tr = max(high_prices[i] - low_prices[i],
                 abs(high_prices[i] - close_prices[i-1]),
                 abs(low_prices[i] - close_prices[i-1]))
        trs.append(tr)
    atr = np.mean(trs[-period:])
    return atr

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
