import os
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

    # Check for Rise Contract Conditions
    if (
        is_bullish_reversal_candle(prices[-2:]) and            # Condition 1
        prices[-1] > prices[-2] and                            # Condition 2
        connors_rsi[-1] > 50 and                               # Condition 3
        prices[-1] < donchian_lower[-1] and                    # Condition 4
        chaikin_volatility[-1] > 0 and                         # Condition 5
        kst_indicator(prices) > 0                              # Condition 6
    ):
        send_alert(f"{symbol} - Rise Contract Conditions Met")

    # Check for Fall Contract Conditions
    if (
        is_bearish_reversal_candle(prices[-2:]) and            # Condition 1
        prices[-1] < prices[-2] and                            # Condition 2
        connors_rsi[-1] < 49 and                               # Condition 3
        prices[-1] > donchian_upper[-1] and                    # Condition 4
        chaikin_volatility[-1] < 0 and                         # Condition 5
        kst_indicator(prices) < 0                              # Condition 6
    ):
        send_alert(f"{symbol} - Fall Contract Conditions Met")

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

def is_bullish_reversal_candle(prices):
    if (
        bullish_engulfing(prices) or
        hammer_pattern(prices) or
        morning_star(prices) or
        three_inside_up(prices) or
        is_bullish_doji(prices)
    ):
        return True
    return False

def is_bearish_reversal_candle(prices):
    if (
        bearish_engulfing(prices) or
        hanging_man_pattern(prices) or
        evening_star(prices) or
        three_inside_down(prices) or
        is_bearish_doji(prices)
    ):
        return True
    return False

def bullish_engulfing(prices):
    if prices[1] < prices[0] and prices[1] > prices[2]:
        return True
    return False

def bearish_engulfing(prices):
    if prices[1] > prices[0] and prices[1] < prices[2]:
        return True
    return False

def hammer_pattern(prices):
    body_size = abs(prices[2] - prices[1])
    lower_shadow = min(prices[0], prices[3]) - min(prices[1], prices[2])
    if body_size < lower_shadow and prices[1] < prices[0]:
        return True
    return False

def hanging_man_pattern(prices):
    body_size = abs(prices[2] - prices[1])
    lower_shadow = min(prices[0], prices[3]) - min(prices[1], prices[2])
    if body_size < lower_shadow and prices[1] > prices[0]:
        return True
    return False

def morning_star(prices):
    if (
        prices[2] < prices[1] < prices[0] and
        prices[2] < prices[4] < prices[3] and
        prices[4] > prices[0]
    ):
        return True
    return False

def evening_star(prices):
    if (
        prices[2] > prices[1] > prices[0] and
        prices[2] > prices[4] > prices[3] and
        prices[4] < prices[0]
    ):
        return True
    return False

def three_inside_up(prices):
    if (
        prices[2] > prices[3] and
        prices[1] > prices[2] and
        prices[0] > prices[1]
    ):
        return True
    return False

def three_inside_down(prices):
    if (
        prices[2] < prices[3] and
        prices[1] < prices[2] and
        prices[0] < prices[1]
    ):
        return True
    return False

def is_bullish_doji(prices):
    if abs(prices[3] - prices[0]) < 0.1 * (prices[2] - prices[1]):
        return True
    return False

def is_bearish_doji(prices):
    if abs(prices[3] - prices[0]) < 0.1 * (prices[1] - prices[2]):
        return True
    return False

def kst_indicator(prices):
    kst = talib.KAMA(prices, timeperiod=10)
    return kst[-1] - kst[-2]

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    websocket.enableTrace(True)
    ws = websocket.WebSocketApp("wss://ws.binaryws.com/websockets/v3?app_id=1089",
                                on_message=on_message,
                                on_error=on_error,
                                on_close=on_close)
    ws.on_open = on_open
    ws.run_forever()
