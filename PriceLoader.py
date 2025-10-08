

from dataclasses import dataclass
import yfinance as yf
from collections import defaultdict
import pandas as pd
import os
from pathlib import Path
import time


# change format
def _yf_symbol(sym: str) -> str:
    return sym.replace('.', '-').strip()



# get SP500 tickers today
def get_sp500_tickers():
    # Read and print the stock tickers that make up S&P500

    tables =tables = pd.read_html(
    "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies",
    flavor="lxml",
    storage_options={"User-Agent": "Mozilla/5.0"}
    )

    df = tables[0]
    col_candidates = [c for c in df.columns if str(c).lower().startswith('symbol')]
    sym_col = col_candidates[0] if col_candidates else df.columns[0]
    tickers = [ _yf_symbol(s) for s in df[sym_col].astype(str).tolist() ]

    # Deduplicate while preserving order
    seen, out = set(), []
    for t in tickers:
        if t not in seen:
            seen.add(t); out.append(t)
    return out

# trading calendar
def load_trading_calendar(start, end):
    sp500_data = yf.download("^GSPC",start =start,end = end)
    return list(sp500_data.index)

#handle raw data
def cov_rate(data,days):
        '''
        recognize and drop tickers with sparse or missing data

        input: 
                1.close price of one ticker
                2.loader(priceloader)
        output: 
                1.coverage rate
        '''
        # calculating the coverage
        data = data.squeeze() 
        nonNA = len(data) - data.isna().sum()
        return float(nonNA)/float(days) if days else 0.0





'''
functions:
1. download sp500(batch)
    - recognize sparse and missing data(check with calendar)
    - drop these data
2. fetch data
'''
@dataclass
class PriceLoader:
    start:str
    end: str
    outdir: str
    sleep: float 
    fmt:str = 'parquet'
    batch_size:int = 25
    threads:bool  = True # fetch batches concurrently
    min_coverage:float = 0.9
    covered_tickers = []

    def loader(self):
        
        # get tickers of SP 500
        tickers = get_sp500_tickers()

        # download daily adjusted close prices for all S&P 500
        frames = []
        for i in range(0, len(tickers), self.batch_size):
            batch = tickers[i:i + self.batch_size]
            df = yf.download(
                batch,
                start=self.start, end=self.end,
                group_by="ticker",
                threads=self.threads,       
                progress=False
            )
            frames.append(df)
            
            # sleep only if there is a next batch
            if i + self.batch_size < len(tickers):
                time.sleep(self.sleep)   
            

        # combine per-batch frames (MultiIndex columns will align)
        return pd.concat(frames, axis=1)

  
        
    def fetch_data(self,data):
        '''
        Store data(close price) locally and one file per ticker
        input: raw dataset
        output:many files for tickers
        '''
        
        out = Path(self.outdir) 
        out.mkdir(parents=True, exist_ok=True)

        totaldays = len(load_trading_calendar(self.start, self.end))
        for t in data.columns.levels[0]:
            df_t = data.xs(t, axis=1, level=0, drop_level=True).copy() 
            df_t = pd.DataFrame(df_t.loc[:,["Close","Volume"]])  
            df_t.sort_index(inplace=True)

            #check if empty
            if df_t.empty:
                continue

            #drop sparse ticker
            coverage_rate = cov_rate(df_t["Close"],days = totaldays)
            if coverage_rate >= self.min_coverage:
                self.covered_tickers.append(t)
                df_t.to_parquet(out / f"{t}.parquet") 
                
            else:
                continue


    

    if __name__ == "__main__":
        plr = PriceLoader(start = "2005-01-01",
                 end = "2025-01-01",
                 outdir = "data/adjclose",
                 sleep = 1.2)
        data = plr.loader()
        print(data.head())