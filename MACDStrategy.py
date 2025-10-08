import pandas as pd

class MACDStrategy:
    """
    Buy 1 share when MACD crosses above signal on day t; trade at t+1.
    MACD = EMA(fast) - EMA(slow); signal = EMA(signal_span) of MACD.
    """
    def __init__(self, initial_cash, tickers, fast=12, slow=26, signal_span=9,
                 data_dir="data/adjclose", price_col="Adj Close"):
        self.cash = float(initial_cash)
        self.tickers = list(tickers)
        self.fast = int(fast); self.slow = int(slow); self.signal_span = int(signal_span)
        self.data_dir = data_dir; self.price_col = price_col
        self.positions = {t: 0 for t in self.tickers}
        self.trades = []; self.portfolio_rows = []

    def _load_one(self, tkr):
        df = pd.read_parquet(f"{self.data_dir}/{tkr}.parquet")
        col = self.price_col if self.price_col in df.columns else ("Adj Close" if "Adj Close" in df.columns else "Close")
        return df[col].sort_index()

    def run(self):
        price = pd.DataFrame({t: self._load_one(t) for t in self.tickers}).sort_index()
        if price.empty: return self

        ema_fast = price.ewm(span=self.fast, adjust=False).mean()
        ema_slow = price.ewm(span=self.slow, adjust=False).mean()
        macd = ema_fast - ema_slow
        sigl = macd.ewm(span=self.signal_span, adjust=False).mean()

        above_now  = macd > sigl
        above_prev = macd.shift(1) > sigl.shift(1)
        cross_up = above_now & ~above_prev
        valid = (macd.notna() & sigl.notna() & macd.shift(1).notna() & sigl.shift(1).notna())
        sig_t = cross_up & valid

        orders = sig_t.shift(1).fillna(False).astype(int)

        for d in price.index:
            px_d = price.loc[d]; od_d = orders.loc[d]
            cands = [(t,float(px_d[t])) for t in price.columns if od_d.get(t,0)==1 and pd.notna(px_d.get(t)) and px_d[t]>0]
            for t in price.columns:
                if od_d.get(t,0)==1 and (not pd.notna(px_d.get(t)) or px_d.get(t)<=0):
                    self._log_skip(d, t, "no_price")

            if cands:
                total = sum(p for _, p in cands)
                if total <= self.cash:
                    filled, skipped = cands, []
                else:
                    cands.sort(key=lambda x: (x[1], x[0]))
                    filled, skipped, cash_left = [], [], self.cash
                    for t, p in cands:
                        if p <= cash_left: filled.append((t,p)); cash_left -= p
                        else: skipped.append((t,p))
                for t, p in filled:
                    cb = self.cash; self.cash -= p; self.positions[t]+=1
                    self.trades.append({"date": d, "ticker": t, "side":"BUY", "qty":1,
                                        "price": p, "notional": p,
                                        "cash_before": cb, "cash_after": self.cash})
                for t, p in skipped:
                    self._log_skip(d, t, "insufficient_cash", price=p)

            hold = sum(self.positions[t]*float(px_d[t]) for t in price.columns if pd.notna(px_d.get(t)))
            self.portfolio_rows.append({"date": d, "cash": self.cash, "holdings": hold, "equity": self.cash + hold})

        return self

    def _log_skip(self, date, ticker, reason, price=None):
        self.trades.append({"date": date, "ticker": ticker, "side":"SKIP", "qty":0,
                            "price": (float(price) if price is not None else None),
                            "notional": 0.0, "cash_before": self.cash, "cash_after": self.cash,
                            "reason": reason})

    def trades_df(self):     return pd.DataFrame(self.trades).sort_values(["date","ticker"])
    def portfolio_df(self):  return pd.DataFrame(self.portfolio_rows).set_index("date").sort_index()
