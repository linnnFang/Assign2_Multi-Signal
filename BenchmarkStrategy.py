import pandas as pd
from collections import defaultdict

class static_stratgy:
    """
    Benchmark:
      - Buy X shares of each ticker on the first available day (using previous day's volume as ADV cap).
      - No further trades.
      - Track holdings, cash, equity over time.
    """
    def __init__(self, initial_capital, tickers, pr=0.05):
        self.init_cash = float(initial_capital)
        self.cash = float(initial_capital)
        self.tickers = tickers
        self.window = 1
        self.pr_rate = float(pr)
        self.trade = []
        self.base = self.init_cash / max(1, len(tickers))
        self.portfolio = defaultdict()     
        self.equity = 0.0                  
        # time series (filled in access_portfolio)
        self.total_holdings = None        
        self.cash_series = None           
        self.equity_series = None        
        self.portfolio_rows = []           

    def base_shares(self, ticker_price: float):
        return self.base / float(ticker_price)

    @staticmethod
    def adv(volume):
        # just return the previous-day volume you pass in
        return volume

    def pr_shares(self, volume):
        return self.pr_rate * self.adv(volume)

    def get_shares(self, volume: int, ticker_price: float):
        # cap by base dollars and participation rate
        ptcpt_cap = self.pr_shares(volume)
        shares = min(self.base_shares(ticker_price), ptcpt_cap)
        return shares if shares > 0 else 0

    def strategy_static(self, prices, volume, ticker):
        """
        Buy on the first day in `prices` using previous day's volume cap.
        Then hold forever. Return the *position value series* (shares * price).
        """
        # previous day's volume (assumed aligned so volume.iloc[0] is prev day)
        shares = self.get_shares(volume.iloc[0], prices.iloc[0])

        if shares > 0:
            self.cash -= shares * prices.iloc[0]     # spend once on day 0
            self.trading_log(ticker, shares, prices.iloc[0], "BUY")
        else:
            self.trading_log(ticker, shares, prices.iloc[0], "SKIP")

        # position value over time = fixed shares * daily price series
        position_value = shares * prices
        return position_value

    def run(self):
        for ticker in self.tickers:
            df = pd.read_parquet(f"data/adjclose/{ticker}.parquet")
            prices = df["Close"].iloc[1:]    # buy at first “real” trading day
            vol    = df["Volume"]            # previous day volume is at .iloc[0]

            pos_val = self.strategy_static(prices, vol, ticker)
            self.portfolio[ticker] = pos_val
            self.equity += pos_val.iloc[-1]  # accumulate final holdings value

        self.equity += self.cash            # add remaining cash to final equity
        return self

    def trading_log(self, tkr, shares, price, action):
        self.trade.append({
            "ticker": tkr,
            "qty": shares,
            "price": price,
            "cash_snapshot": self.cash,
            "action": action
        })

    def access_portfolio(self):
        """
        Build daily series:
          - total_holdings: sum of position values across tickers (Series)
          - cash_series: cash per day (constant after day 0 here)
          - equity_series: cash_series + total_holdings
        Also populates self.portfolio_rows for easy export.
        """
        # wide matrix of position values (one column per ticker)
        wide = pd.concat(self.portfolio, axis=1).sort_index()

        # total holdings value over time
        total_holdings = wide.sum(axis=1, min_count=1).fillna(0.0)

        # cash is constant after the buys (single-shot benchmark)
        cash_series = pd.Series(self.cash, index=total_holdings.index)

        # equity = cash + holdings
        equity_series = cash_series + total_holdings

        # save for later use
        self.total_holdings = total_holdings
        self.cash_series = cash_series
        self.equity_series = equity_series

        # build row snapshots (date, cash, holdings, equity)
        self.portfolio_rows = [
            {"date": d,
             "cash": float(cash_series.loc[d]),
             "holdings": float(total_holdings.loc[d]),
             "equity": float(equity_series.loc[d])}
            for d in equity_series.index
        ]
        return total_holdings, cash_series, equity_series

    def final_shot(self):
        # make sure series exist
        if self.equity_series is None:
            self.access_portfolio()

        last_date = self.equity_series.index[-1]
        out = {
            "date": last_date,
            "cash": float(self.cash_series.loc[last_date]),
            "holdings": float(self.total_holdings.loc[last_date]),
            "equity": float(self.equity_series.loc[last_date])
        }
        return pd.DataFrame([out])  # single-row DataFrame
