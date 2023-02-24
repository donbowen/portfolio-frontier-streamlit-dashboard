# todo set up github actions to recompute these monthly 

def get_data(assets):
    '''
    Assets is a list of tickers, allowing this to be used with custom lists.
    '''
  
    import csv
    from datetime import datetime

    from dateutil.relativedelta import relativedelta
    import pandas_datareader as pdr
    import yfinance as yf

    from pypfopt import expected_returns, risk_models

    # get etf prices

    if not assets:
        with open('assets.csv', newline='') as f:
            reader = csv.reader(f)
            assets = list(reader)
      
    #assets = ['SPY', 'IVV', 'VOO', 'SPLG', 'SPXL', 'SPXS', 'SPDN', 'SPUU', 'NSPI', 'SPXU', 'UPRO', 
    #             'SDS', 'SH', 'SSO','JMOM', 'VUG', 'VONV', 'IUSV', 'FREL', 'XSW', 'VHT', 'MGK', 'JVAL', 
    #             'VOT', 'VIOG', 'NURE', 'GLD', 'XLU', 'TQQQ', 'VCR', 'FNCL', 'IFRA',
    #            'PBD', 'RYT', 'FTEC', 'SCHI', 'SUSC', 'VTC', 'VCIT','VEA','IEFA','EFA',
    #             'SCHF','EFV','SCZ','SPDW','FNDF','EWC','DBEF','GSIE']

    start  = datetime.now() - relativedelta(years=10)
    end    = datetime.now() 

    asset_prices = yf.download(assets, start=start, end=end, progress=False)
    asset_prices = asset_prices.filter(like='Adj Close') # reduce to just columns with this in the name
    asset_prices.columns = asset_prices.columns.get_level_values(1)

    # get risk free rate

    risk_free_rate = pdr.DataReader("IRLTLT01USM156N", "fred", start,end)
    risk_free_rate = risk_free_rate.iloc[-1]/100
    risk_free_rate = risk_free_rate.item()

    # compute e_returns, cov_mat

    e_returns = expected_returns.capm_return(asset_prices)#, span = 200)
    cov_mat   = risk_models.exp_cov(asset_prices)#,span=100)

    return e_returns, cov_mat, risk_free_rate
  
if __name__ == "__main__":

  e_returns, cov_mat, risk_free_rate = get_data()
  
  e_returns.to_csv('inputs/e_returns.csv')
  cov_mat.to_csv('inputs/cov_mat.csv')

  with open('inputs/risk_free_rate.txt', 'w') as f:
      f.write('%f' % risk_free_rate)
