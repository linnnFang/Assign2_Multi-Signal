import pandas as pd, numpy as np, matplotlib.pyplot as plt
import analysis
from pathlib import Path

def load_price_series(ticker, col=PRICE_COL):
    df = pd.read_parquet(DATA_DIR/f"{ticker}.parquet").sort_index()
    if col not in df.columns:
        col = "Adj Close" if "Adj Close" in df.columns else "Close"
    return df[col]

def plot_signal_overlay(ticker):
    px = load_price_series(ticker)
    plt.figure(figsize=(11,4))
    plt.plot(px.index, px.values, label=f"{ticker} price")
    markers = {"Benchmark":"x", "MA":"^", "VOL":"o", "MACD":"s", "RSI":"v"}
    for name, tr in TRADES.items():
        if tr.empty: continue
        buys = tr.query("side=='BUY' and ticker==@ticker")["date"]
        if not buys.empty:
            plt.scatter(buys, px.reindex(buys), marker=markers.get(name,"o"), s=36, label=f"{name} BUY", zorder=3)
    plt.title(f"{ticker} — price with BUY markers"); plt.legend(ncol=3); plt.tight_layout(); plt.show()
def plot_hce(name):
    df = PORTS[name][["holdings","cash","equity"]].dropna(how="all")
    fig, ax = plt.subplots(3,1, figsize=(11,8), sharex=True)
    ax[0].plot(df.index, df["holdings"]); ax[0].set_ylabel("Holdings ($)")
    ax[1].plot(df.index, df["cash"]);     ax[1].set_ylabel("Cash ($)")
    ax[2].plot(df.index, df["equity"]);   ax[2].set_ylabel("Equity ($)")
    ax[2].set_title(f"{name} — Holdings / Cash / Equity")
    plt.tight_layout(); plt.show()
