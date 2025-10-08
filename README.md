#  FINM325 — Multi-Signal Strategy & Backtesting

**Author:** Lin Fang  
**Course:** FINM325 — Signal Engineering, Execution Modeling & Backtesting  
**Date:** Fall 2025  

This project builds a **modular trading simulator** for the S&P 500 universe.  
It includes data acquisition, multiple technical indicator strategies, execution modeling, and performance comparison with a benchmark static strategy.

---

##  Project Overview

The simulator downloads historical S&P 500 data (2005–2025), applies multiple trading signals, executes trades under liquidity constraints, and tracks portfolio evolution over time.

### Implemented Strategies

| Strategy | Core Logic | Category |
|-----------|-------------|-----------|
| **BenchmarkStrategy** | Buy X shares on day 1, hold to end | Baseline |
| **MovingAverageStrategy** | Buy when 20-day MA > 50-day MA | Price average |
| **VolatilityBreakoutStrategy** | Buy when daily return > 20-day std | Volatility |
| **MACDStrategy** | Buy when MACD line crosses above signal line | Momentum |
| **RSIStrategy** | Buy when RSI < 30 (oversold) | Oscillator |

All strategies start with **$1,000,000**, no leverage, no shorting, and execute based on the **previous day’s signal**.

---

## Repository Structure

Assign2_Multi-Signal/
│
├── PriceLoader.py # Download & clean S&P 500 price data (2005–2025)
│ # Handles batching, API limits, and saves parquet files
│
├── BenchmarkStrategy.py # Baseline static buy-and-hold strategy
│ # Tracks cash, holdings, and equity over time
│
├── MovingAverageStrategy.py # 20/50-day MA crossover signal generation
│
├── VolatilityBreakoutStrategy.py # Signal based on breakout above rolling 20-day std
│
├── MACDStrategy.py # MACD and signal line crossover implementation
│
├── RSIStrategy.py # RSI < threshold (default 30) buy signal
│
├── analysis.py # Utility functions for trade logs and performance summaries
│
├── StrategyComparison.ipynb # Jupyter notebook for visualization & performance comparison
│ # Includes signal overlays, holdings, equity, and cumulative PnL
│
├── data/ # Local data storage (ignored in .gitignore)
│ ├── adjclose/ # Adjusted close prices per ticker (.parquet)
│ └── universe/ # S&P 500 ticker list snapshot
│
├── logs/ # Optional logs of runs and download errors
│
├── results/ # Optional output charts and performance summaries
│
└── README.md # This file


---

##  Workflow Summary

1. **Data Acquisition**  
   Run `PriceLoader.py` to fetch and store adjusted close data for all current S&P 500 tickers.  
   Automatically skips missing or sparse tickers and respects Yahoo Finance API limits.

2. **Strategy Simulation**  
   Each `.py` strategy file can be run independently or through the main notebook.  
   Each produces:
   - `trading_log` — list of all executed trades  
   - `portfolio` — time series of cash, holdings, and equity  

3. **Result Analysis**  
   `StrategyComparison.ipynb` loads all results and visualizes:
   - Price + signal overlays  
   - Holdings and cash evolution  
   - Cumulative PnL comparison across strategies  

---

##  Example Outputs

- **Holdings / Cash / Equity** time-series per strategy  
- **Buy signal overlays** on price charts  
- **PnL comparison** (Benchmark vs MA vs Volatility vs MACD vs RSI)

---

##  Notes

- Time range: **2005-01-01 → 2025-01-01**  
- Data source: [Yahoo Finance via yfinance](https://pypi.org/project/yfinance/)  
- File format: `.parquet` (for efficiency)  
- Missing tickers are dropped automatically  
- Benchmark uses static allocation; others are signal-based  

---

##  Contributor

**Lin Fang**  
University of Chicago  
Department of Financial Mathematics & Statistics  
[GitHub: @linnnFang](https://github.com/linnnFang)
