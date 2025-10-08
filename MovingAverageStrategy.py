
import pandas as pd
import math

class MA:
    """
    Moving Average Strategy (event-based):
      Buy 1 share when MA_short crosses above MA_long on day t, execute on t+1.
      Long-only, cash-limited. Logs every BUY/SKIP and tracks daily equity.
    """

    def __init__(self, initial_capital, s_window, l_window, tickers, price_col="Close"):
        self.cash = float(initial_capital)
        self.shortWin = int(s_window)      # e.g., 20
        self.longWin  = int(l_window)      # e.g., 50
        self.tickers  = list(tickers)
        self.price_col = price_col         # "Adj Close" if you saved that; else "Close"

        self.trading_log = []              # list of dict rows
        self.positions   = {t: 0 for t in self.tickers}
        self.portfolio_daily = []          

    # ---------- data & indicators ----------

    def load_prices(self, ticker: str) -> pd.Series:
        """Read one ticker's price series (column = price_col or fallback)."""
        df = pd.read_parquet(f"data/adjclose/{ticker}.parquet")
        col = self.price_col if self.price_col in df.columns else (
            "Adj Close" if "Adj Close" in df.columns else "Close"
        )
        s = df[col].sort_index()
        s = s.iloc[1:]

        return s

    def _ma_short(self, s: pd.Series) -> pd.Series:
        return s.rolling(self.shortWin, min_periods=self.shortWin).mean()

    def _ma_long(self, s: pd.Series) -> pd.Series:
        return s.rolling(self.longWin, min_periods=self.longWin).mean()

    def _make_signals(self, price: pd.DataFrame) -> pd.DataFrame:
        """
        Vectorized signal:
          cross_up(t) = (MA_s > MA_l) & not (MA_s > MA_l at t-1)
          Then shift(1) later for t+1 execution.
        """
        ma_s = price.rolling(self.shortWin, min_periods=self.shortWin).mean()
        ma_l = price.rolling(self.longWin,  min_periods=self.longWin).mean()

        raw = (ma_s > ma_l)
        cross_up = raw & ~(raw.shift(1).fillna(False))

        # Ensure both MAs are valid today and yesterday (no warm-up look-ahead)
        valid = (ma_s.notna() & ma_l.notna() &
                 ma_s.shift(1).notna() & ma_l.shift(1).notna())

        signal_t = cross_up & valid               # boolean DataFrame on day t
        return signal_t

    # ---------- trading run with logging ----------

    def run(self):
        # 1) Load all prices into a wide DF: index=date, columns=tickers
        wide = {}
        for tkr in self.tickers:
            try:
                wide[tkr] = self.load_prices(tkr)
            except Exception:
                # if missing file, leave empty series; you can also log a SKIP here
                wide[tkr] = pd.Series(dtype="float64")

        price = pd.DataFrame(wide).sort_index()
        if price.empty:
            return self

        # 2) Signals on t → orders at t+1 (1 share per signal)
        signal_t = self._make_signals(price)
        orders = signal_t.shift(1).fillna(False).astype(int)   # 1 = buy 1 share today

        # 3) Daily execution loop (cash-limited, cheapest-first)
        for d in price.index:
            row_px = price.loc[d]              # Series: index=tickers, values=px
            row_od = orders.loc[d]             # Series: index=tickers, values=0/1

            # Collect candidates (valid price and order==1)
            candidates = [(tkr, float(row_px[tkr]))
                          for tkr in price.columns
                          if (row_od.get(tkr, 0) == 1 and pd.notna(row_px.get(tkr)) and row_px[tkr] > 0)]

            # Log SKIPs for order==1 but price is NaN/<=0
            for tkr in price.columns:
                if row_od.get(tkr, 0) == 1 and (not pd.notna(row_px.get(tkr)) or row_px.get(tkr) <= 0):
                    self._log_skip(d, tkr, reason="no_price")

            if candidates:
                # Enough cash for all → buy all; else cheapest-first
                total_cost = sum(px for _, px in candidates)
                if total_cost <= self.cash:
                    filled = candidates
                    skipped = []
                else:
                    candidates.sort(key=lambda x: (x[1], x[0]))  # price then ticker (deterministic)
                    filled, skipped, cash_left = [], [], self.cash
                    for tkr, px in candidates:
                        if px <= cash_left:
                            filled.append((tkr, px))
                            cash_left -= px
                        else:
                            skipped.append((tkr, px))

                # Execute filled and log
                for tkr, px in filled:
                    cash_before = self.cash
                    self.cash -= px
                    self.positions[tkr] += 1
                    self.trading_log.append({
                        "date": d, "ticker": tkr, "side": "BUY",
                        "qty": 1, "price": px, "notional": px,
                        "cash_before": cash_before, "cash_after": self.cash
                    })

                # Log SKIPs due to insufficient cash
                for tkr, px in skipped:
                    self._log_skip(d, tkr, reason="insufficient_cash", price=px)

            # 4) Daily portfolio snapshot (optional, handy for plots)
            holdings_val = 0.0
            px_d = price.loc[d]
            for tkr, qty in self.positions.items():
                v = px_d.get(tkr)
                if pd.notna(v):
                    holdings_val += qty * float(v)
            equity = self.cash + holdings_val
            self.portfolio_daily.append({"date": d, "cash": self.cash,
                                         "holdings": holdings_val, "equity": equity})

        return self

    # ---------- helpers ----------

    def _log_skip(self, date, ticker, reason, price=None):
        self.trading_log.append({
            "date": date, "ticker": ticker, "side": "SKIP",
            "qty": 0, "price": (float(price) if price is not None else None),
            "notional": 0.0,
            "cash_before": self.cash, "cash_after": self.cash,
            "reason": reason
        })

    def trades_df(self) -> pd.DataFrame:
        return pd.DataFrame(self.trading_log).sort_values(["date", "ticker"])

    def portfolio_df(self) -> pd.DataFrame:
        df = pd.DataFrame(self.portfolio_daily)
        return df.set_index("date").sort_index() if not df.empty else df
