import pandas as pd
import numpy as np

def get_trades(obj):

    if hasattr(obj, "trades_df"):
        df = obj.trades_df()
        if df is None:
            df = pd.DataFrame()
        else:
            df = df.copy()
    else:
        
        log_attr = None
        if hasattr(obj, "trading_log") and not callable(getattr(obj, "trading_log")):
            log_attr = getattr(obj, "trading_log")
        elif hasattr(obj, "trade") and not callable(getattr(obj, "trade")):  # your Benchmark uses `self.trade`
            log_attr = getattr(obj, "trade")
        else:
            log_attr = []

        df = pd.DataFrame(list(log_attr)).copy() if log_attr else pd.DataFrame(
            columns=["date","ticker","side","qty","price","notional","cash_before","cash_after","reason"]
        )

    if not df.empty and "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"])
    return df


def get_port(obj):
    
    if hasattr(obj, "portfolio_df"):
        df = obj.portfolio_df()
        if df is None:
            df = pd.DataFrame()
        else:
            df = df.copy()
            if "date" in df.columns:
                df = df.set_index("date")

    elif hasattr(obj, "portfolio_rows") and not callable(getattr(obj, "portfolio_rows")):
        df = pd.DataFrame(getattr(obj, "portfolio_rows")).copy()
        if not df.empty and "date" in df.columns:
            df = df.set_index("date")
    else:
        df = pd.DataFrame()

    if not df.empty:
        df.index = pd.to_datetime(df.index)
        for c in ["cash","holdings","equity"]:
            if c not in df.columns:
                df[c] = np.nan
    return df
