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

