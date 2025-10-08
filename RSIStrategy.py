import pandas as pd

class RSIStrategy:
    """
    Buy 1 share when RSI crosses below threshold (default 30) on day t; trade at t+1.
    """
    def __init__(self, initial_cash, tickers, period=14, threshold=30,
                 data_dir="data/adjclose", price_col="Adj Close", event_based=True):
        self.cash = float(initial_cash)
        self.tickers = list(tickers)
        self.period = int(period); self.threshold = float(threshold)
        self.event_based = bool(event_based)
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

        delta = price.diff()
        gain  = delta.clip(lower=0)
        loss  = -delta.clip(upper=0)
        alpha = 1 / self.period
        avg_gain = gain.ewm(alpha=alpha, adjust=False).mean()
        avg_loss = loss.ewm(alpha=alpha, adjust=False).mean()
        rs  = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        if self.event_based:
            below_now  = rsi < self.threshold
            below_prev = rsi.shift(1) < self.threshold
            sig_t = (below_now & ~below_prev) & rsi.notna() & rsi.shift(1).notna()
        else:
            sig_t = (rsi < self.threshold) & rsi.notna()

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
