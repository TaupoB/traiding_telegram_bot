import yfinance as yf
from random import random

def bollinger(data):
    data = data[['Date', 'Open', 'High', 'Low', 'Close']]
    data.columns = ['Date', 'Open', 'High', 'Low', 'Close']
    data['sma_20'] = data['Close'].rolling(window=20).mean()
    up = data[data['Close'] >= data['Open']]
    down = data[data['Close'] < data['Open']]
    data['up_sma'] = data['sma_20'] + 2 * data['Close'].rolling(window=20).std()
    data['down_sma'] = data['sma_20'] - 2 * data['Close'].rolling(window=20).std()

    col1 = 'green'
    col2 = 'red'
    width = .4
    width2 = .05

    data['Signal'] = 0
    data['Buy'] = 0
    data['Sell'] = 0

    for i in range(len(data)):
        if data['Close'][i] > data['up_sma'][i]:
            data['Signal'][i] = -1
            data['Sell'][i] = data['Close'][i]
        elif data['Close'][i] < data['down_sma'][i]:
            data['Signal'][i] = 1
            data['Buy'][i] = data['Close'][i]

    data['Signal_bb'] = data['Signal']

    return data


def rsi(data):
    def calculate_rsi(data, window=14):
        delta = data['Close'].diff(1)
        delta = delta[1:]
        up = delta.copy()
        down = delta.copy()
        up[up < 0] = 0
        down[down > 0] = 0
        avg_gain = up.rolling(window).mean()
        avg_loss = abs(down.rolling(window).mean())
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    data['RSI'] = calculate_rsi(data)

    overbought_threshold = 60
    oversold_threshold = 25
    capital = 1000000

    def decide_to_trade(position, price, rsi_value):
        if position == 1 and rsi_value >= overbought_threshold:
            position = -1
            capital = 0
            capital -= price
        elif position == -1 and rsi_value <= oversold_threshold:
            position = 1
            capital = 0
            capital += price
        return position

    position = 1
    pos_df = []

    for i in range(len(data)):
        price = data['Close'][i]
        rsi_value = data['RSI'][i]
        position = decide_to_trade(position, price, rsi_value)
        pos_df.append(position)

    data['position'] = pos_df
    return data

# def backtest(prices):
#     return random()
def indicator(hist):
    hist['Date'] = hist.index
    hist.index = range(len(hist))
    bol = bollinger(hist).iloc[-1, -1]
    rsi_ind = rsi(hist).iloc[-1, -1]
    if bol == rsi:
        return bol
    elif bol == 0 and rsi_ind != 0:
        return rsi_ind
    else:
        return 0


if __name__ == "__main__":
    ticker = yf.Ticker('MSFT')
    hist = ticker.history(period="1mo")
    print(indicator(hist))
