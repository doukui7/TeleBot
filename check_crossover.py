"""Check TQQQ crossover history"""
import requests
from datetime import datetime

url = 'https://query1.finance.yahoo.com/v8/finance/chart/TQQQ'
params = {'interval': '1d', 'range': '2y'}
headers = {'User-Agent': 'Mozilla/5.0'}

response = requests.get(url, params=params, headers=headers, timeout=15)
data = response.json()
result = data['chart']['result'][0]

timestamps = result['timestamp']
closes = result['indicators']['quote'][0]['close']

# Calculate SMA 193 for all data points
def calc_sma(closes, idx, period=193):
    if idx < period - 1:
        return None
    valid = [c for c in closes[idx-period+1:idx+1] if c is not None]
    if len(valid) < period:
        return None
    return sum(valid) / len(valid)

# Find all crossover points
print('=== TQQQ 193 SMA Crossover History (2 years) ===')
print()

for i in range(194, len(closes)):
    if closes[i] is None or closes[i-1] is None:
        continue

    prev_sma = calc_sma(closes, i-1)
    curr_sma = calc_sma(closes, i)

    if prev_sma is None or curr_sma is None:
        continue

    prev_close = closes[i-1]
    curr_close = closes[i]

    # Upward crossover (BUY signal)
    if prev_close <= prev_sma and curr_close > curr_sma:
        date = datetime.fromtimestamp(timestamps[i]).strftime('%Y-%m-%d')
        print(f'BUY  {date}: ${curr_close:.2f} (SMA: ${curr_sma:.2f})')

    # Downward crossover (SELL signal)
    if prev_close > prev_sma and curr_close <= curr_sma:
        date = datetime.fromtimestamp(timestamps[i]).strftime('%Y-%m-%d')
        print(f'SELL {date}: ${curr_close:.2f} (SMA: ${curr_sma:.2f})')

print()
current_sma = calc_sma(closes, len(closes)-1)
print(f'Current Price: ${closes[-1]:.2f}')
print(f'Current SMA: ${current_sma:.2f}')
print(f'Status: {"Above SMA (Hold TQQQ)" if closes[-1] > current_sma else "Below SMA (Hold Cash)"}')
