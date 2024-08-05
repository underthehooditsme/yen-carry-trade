import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from alpha_vantage.foreignexchange import ForeignExchange
import requests
from config import alpha_vantage_api_key, fred_api_key  

# Function to get historical data from Alpha Vantage
def get_exchange_rate(from_currency, to_currency, api_key):
    cc = ForeignExchange(key=api_key)  
    data, _ = cc.get_currency_exchange_daily(from_symbol=from_currency, to_symbol=to_currency, outputsize='full')  
    df = pd.DataFrame.from_dict(data, orient='index')  
    df.index = pd.to_datetime(df.index) 
    df = df.astype(float) 
    df.rename(columns={'4. close': 'Close'}, inplace=True)  
    return df[['Close']]

# Function to get historical interest rates data from FRED
def get_interest_rates(api_key, series_id):
    url = f'https://api.stlouisfed.org/fred/series/observations?series_id={series_id}&api_key={api_key}&file_type=json' 
    response = requests.get(url).json() 
    data = pd.DataFrame(response['observations'])  
    data['date'] = pd.to_datetime(data['date']) 
    data.set_index('date', inplace=True)  
    data['value'] = pd.to_numeric(data['value'].replace('.', np.nan), errors='coerce') 
    return data[['value']].rename(columns={'value': series_id}) 


usd_jpy = get_exchange_rate('USD', 'JPY', alpha_vantage_api_key)
eur_jpy = get_exchange_rate('EUR', 'JPY', alpha_vantage_api_key)


japan_interest_rate = get_interest_rates(fred_api_key, 'IR3TIB01JPM156N')
us_interest_rate = get_interest_rates(fred_api_key, 'IR3TIB01USM156N')
euro_interest_rate = get_interest_rates(fred_api_key, 'IR3TIB01EZM156N')



interest_rates = japan_interest_rate.merge(us_interest_rate, left_index=True, right_index=True, how='inner')
interest_rates = interest_rates.merge(euro_interest_rate, left_index=True, right_index=True, how='inner')
interest_rates.columns = ['Japan', 'US', 'Eurozone']


interest_rates['US-Japan'] = interest_rates['US'] - interest_rates['Japan']
interest_rates['Euro-Japan'] = interest_rates['Eurozone'] - interest_rates['Japan']


data = interest_rates.merge(usd_jpy['Close'], left_index=True, right_index=True, how='inner')
data = data.merge(eur_jpy['Close'], left_index=True, right_index=True, how='inner')
data.columns = ['Japan', 'US', 'Eurozone', 'US-Japan', 'Euro-Japan', 'USD/JPY', 'EUR/JPY']


data['USD/JPY Returns'] = data['USD/JPY'].pct_change()
data['EUR/JPY Returns'] = data['EUR/JPY'].pct_change()


data['Carry Trade USD'] = data['US-Japan'] / 100 + data['USD/JPY Returns']
data['Carry Trade Euro'] = data['Euro-Japan'] / 100 + data['EUR/JPY Returns']


data['Cumulative USD Carry'] = (1 + data['Carry Trade USD']).cumprod()
data['Cumulative Euro Carry'] = (1 + data['Carry Trade Euro']).cumprod()


data['Volatility USD Carry'] = data['Carry Trade USD'].rolling(window=12).std() * np.sqrt(12)
data['Volatility Euro Carry'] = data['Carry Trade Euro'].rolling(window=12).std() * np.sqrt(12)

# Max drawdown 
def max_drawdown(series):
    roll_max = series.cummax()
    drawdown = series / roll_max - 1.0
    return drawdown.cummin()

data['Max Drawdown USD Carry'] = max_drawdown(data['Cumulative USD Carry'])
data['Max Drawdown Euro Carry'] = max_drawdown(data['Cumulative Euro Carry'])


plt.figure(figsize=(14, 7))
plt.plot(data['Cumulative USD Carry'], label='USD/JPY Carry Trade')
plt.plot(data['Cumulative Euro Carry'], label='EUR/JPY Carry Trade')
plt.title('Cumulative Returns of Yen Carry Trade')
plt.xlabel('Date')
plt.ylabel('Cumulative Returns')
plt.legend()
plt.show()


plt.figure(figsize=(14, 7))
plt.plot(data['Volatility USD Carry'], label='USD/JPY Carry Trade Volatility')
plt.plot(data['Volatility Euro Carry'], label='EUR/JPY Carry Trade Volatility')
plt.title('Volatility of Yen Carry Trade')
plt.xlabel('Date')
plt.ylabel('Annualized Volatility')
plt.legend()
plt.show()


plt.figure(figsize=(14, 7))
plt.plot(data['Max Drawdown USD Carry'], label='USD/JPY Carry Trade Max Drawdown')
plt.plot(data['Max Drawdown Euro Carry'], label='EUR/JPY Carry Trade Max Drawdown')
plt.title('Max Drawdown of Yen Carry Trade')
plt.xlabel('Date')
plt.ylabel('Drawdown')
plt.legend()
plt.show()
