# %%
# Gap Up Identifier - Jupyter Notebook
import pandas as pd
pd.set_option('display.width', 160)
pd.set_option('display.max_rows', 10) 
import numpy as np
import matplotlib.pyplot as plt
import mplfinance as mpf
from _Utils import Utils
from _Class import Trade, Strategy, StrategySummary
from StrategyGapUp import StrategyGapUp
import datetime
from IPython.display import display
from typing import cast


pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)

# csv_file = 'ES(495512563)(1 hour)(3 M)_historical_data.csv'
# csv_file = 'ES(495512563)(1 hour)(1 Y)_historical_data.csv'
# csv_file = 'ES(495512563)(1 hour)(6 M)_historical_data.csv'
# csv_file = 'ES(495512563)(1 hour)(3 M)_historical_data.csv'
csv_file = 'ES(495512563)(1 day)(3 M)_historical_data.csv'
# csv_file = 'ES(495512563)(1 day)(4 M)_historical_data.csv'
# csv_file = 'test.csv'

INITIAL_CAPITAL = 10000
GAP_THRESHOLD = 0.35


# %% load_data
def load_data(csv_file):
    """Load and prepare OHLC data"""
    df = pd.read_csv(csv_file, parse_dates=True)
    df.columns = df.columns.str.lower()
    df.index = pd.DatetimeIndex(df['date'])
    df['tick_num'] = np.arange(1, len(df) + 1)
    
    required_cols = ['open', 'close', 'high', 'low']
    if not all(col in df.columns for col in required_cols):
        raise ValueError(f"CSV must contain {required_cols}. Found: {list(df.columns)}")
    
    
    df['date'] = pd.to_datetime(df['date'])
    
    # df = df.sort_values('date').reset_index(drop=True)

    
    # Calculate gaps
    df['is_market_open'] = False
    df['is_market_close'] = False

    opening_bars = df.groupby(df['date'].dt.floor('1D')).head(1)
    closing_bars = df.groupby(df['date'].dt.floor('1D')).tail(1)

    df.loc[df['date'].isin(opening_bars['date']), 'is_market_open'] = True
    df.loc[df['date'].isin(closing_bars['date']), 'is_market_close'] = True

    # print("opening_bars")
    # print(opening_bars.head(3))
    # print("closing_bars")
    # print(closing_bars.head(3))

    df_daily = df[(df['is_market_open'] == True) | (df['is_market_close'] == True)].copy()
    df_daily["prev_close"] = np.nan
    df_daily["gap_pct"] = np.nan
    df_daily.loc[df['is_market_open'] == True, 'prev_close'] = df_daily['close'].shift(1)
    df_daily.loc[df['is_market_open'] == True, 'gap_pct'] = ((df_daily['open'] - df_daily['prev_close']) / df_daily['prev_close']) * 100
    df.loc[df['date'].isin(df_daily['date']), 'gap_pct'] = df_daily['gap_pct']

    df['sma_8'] = Utils.calculate_sma(df['close'], period=8)
    df['sma_20'] = Utils.calculate_sma(df['close'], period=20)
    df['rsi'] = Utils.calculate_rsi(df['close'], period=14)
    df['macd'], df['signal'], df['histogram'] = Utils.calculate_macd(df['close'])

    # display(df[df['gap_pct'] > 0])
    # display(df[df['is_gap_up'] == True])

    return df


df = load_data(csv_file)
# mask = (df['date'] > "2025-09-25") & (df['date'] <= "2025-10-15")
# df = df.loc[mask].copy()
   
# %% drawEntryExitChart
def drawEntryExitChart (pts, strategy:Strategy, summary:StrategySummary):
    trades = summary.trades
    equity_curve = summary.equity_curve


    has_trade = len(trades) > 0
    pts['trade_num'] = np.nan
    pts['entry_price'] = np.nan
    pts['exit_price'] = np.nan
    pts['pnl'] = 0.0
    pts['total_pnl'] = 0.0
    pts['total_pnl_above'] = np.nan
    pts['total_pnl_below'] = np.nan

    i = 0
    for t in trades:
        pts.loc[pts['date'] == t.entry_date, ['entry_price', 'trade_num']] = [t.entry_price, i]
        pts.loc[pts['date'] == t.exit_date, ['exit_price', 'trade_num']] = [t.exit_price, i]
        pts.loc[pts['date'] == t.exit_date, 'pnl'] = t.pnl
        i = i+1


    total_pnl = 0.0
    for i, row in pts.iterrows():
        if (np.isfinite(row['pnl'])):
            total_pnl += row['pnl']
        pts.loc[i, "total_pnl"] = total_pnl

    
    # display(pts)
    rsi_overbought_line = [70] * len(pts)
    rsi_oversold_line = [30] * len(pts)
    




    apd = [
        #sma
        mpf.make_addplot(df['sma_8'], panel=0, color='purple', alpha=0.5, width=0.5, label='SMA 8'),
        mpf.make_addplot(df['sma_20'], panel=0, color='purple', alpha=0.2, width=0.5, label='SMA 20'),

        #rsi panel
        mpf.make_addplot(pts['rsi'], type='line', width=0.8, panel=2, color='b', linestyle="--", label=f"RSI (14)", ylim=(0, 100), 
            fill_between={'y1': rsi_overbought_line, 'y2': rsi_oversold_line, 'color': 'cyan', 'alpha': 0.4, 'edgecolor':'black', 'linestyle':'--'}, 
            secondary_y=False),
        # mpf.make_addplot(rsi_overbought_line, type='line', width=0.5, panel=2, color='orange', linestyle="--", label=f"Overbought (70)", secondary_y=False),
        # mpf.make_addplot(rsi_oversold_line, type='line', width=0.5, panel=2, color='purple', linestyle="--", label=f"Oversold (30)", secondary_y=False),
       
        #macd panel
        mpf.make_addplot(df['macd'], panel=3, color='blue', linestyle="--", width=0.5, label='MACD'),
        mpf.make_addplot(df['signal'], panel=3, color='red', linestyle="--", width=0.5, ),
        mpf.make_addplot(df['histogram'], panel=3, type='bar', color=np.where(pts['histogram'] > 0, 'g', 'r'), alpha=0.4, width=0.7),
        # label='Signal' label=f"MACD Histogram", 

        #gap up panel
        mpf.make_addplot(pts['gap_pct'], type='bar',  width=0.5, panel=4, color=np.where(pts['is_gap_up'], 'b', 'lightsteelblue'), ylabel="Gap %", secondary_y=False, alpha=0.5),
        
        #Equity
        mpf.make_addplot(equity_curve['equity'], type='line', width=0.8, panel=5, color='purple', linestyle="--", label=f"Equity Curve", secondary_y=False),

        #trades panel
        # mpf.make_addplot(pts['trade_num'], type='scatter', width=1.2, panel=5, ylabel="Trades", secondary_y=False, alpha=0.5),
        mpf.make_addplot(pts['pnl'], type='bar', width=1.2, panel=6, color=np.where(pts['pnl'] > 0, 'g', 'r'), ylabel="PNL", secondary_y=False, alpha=0.5),
        mpf.make_addplot(pts['total_pnl'], type='bar', width=0.8, panel=6, color=np.where(pts['total_pnl'] > 0, 'green', 'red'), secondary_y=False, alpha=0.1),
        mpf.make_addplot(pts['total_pnl'], type='line', width=0.8, panel=6, color='purple', linestyle="--", label=f"Total PnL", secondary_y=False),
        
    ]



    s = summary
    info = subtitle1 = subtitle2 = subtitle3 = subtitle4 = subtitle5 = ""
    subtitle4 += f"Inital Capital: ${INITIAL_CAPITAL:,.2f}\n"
    # subtitle5 += f"Gap Threshold: {GAP_THRESHOLD}%\n"
    # subtitle4 += f"Hold Day(s): {params['hold_days']}\n"
    # subtitle4 += f"Stop Loss: {params['stop_loss']}%\n"
    # subtitle4 += f"Take Profit: {params['take_profit']}%\n"
    if has_trade:
        apd.extend([
            mpf.make_addplot(pts['entry_price'], type='scatter', marker='^', markersize=20, color='blue'),
            mpf.make_addplot(pts['exit_price'], type='scatter',  marker='v', markersize=20, color='purple'),
        ])
        info += f"Total Return: {s.total_return:.2f}%"
        subtitle3 += f"Total Trades: {len(trades)}\n"
        subtitle3 += f"Winning Trades: {len(s.winning_trades)}\n"
        subtitle3 += f"Losing Trades: {len(s.losing_trades)}\n"
        subtitle2 += f"Avg Win: ${s.avg_win:.2f}\n"
        subtitle2 += f"Avg Loss: ${s.avg_loss:.2f}\n"
        if s.avg_loss != 0:
            subtitle2 += f"Profit Factor: {s.profit_factor:.2f}\n"
        subtitle1 += f"Total Return: {s.total_return:.2f}%\n"
        subtitle1 += f"Win Rate: {s.win_rate:.2f}%\n"
        subtitle1 += f"Final Capital: ${s.final_capital:,.2f}\n"
        
    else:
        info += f"No trades executed\n"


    if (strategy.type == StrategyGapUp.TYPE):
        stgy = cast(StrategyGapUp, strategy)
        gap_threshold_line = [stgy.gap_threshold] * len(pts)
        apd.extend([
            mpf.make_addplot(gap_threshold_line, type='line', width=0.5, panel=4, color='r', linestyle="--", label=f"Gap up threshold {stgy.gap_threshold}%", secondary_y=False),
        ])


    price_max = df['high'].max() + 50
    price_min = df['low'].min() - 50
    style = mpf.make_mpf_style(base_mpf_style='yahoo', edgecolor='#000000',rc={'axes.linewidth':0.5})
    date_range = "\n" + df.iloc[0, 0].strftime("%d %b %Y") + '  -  ' + df.iloc[-1, 0].strftime("%d %b %Y")
    fig, axlist = mpf.plot(pts, addplot=apd, type='ohlc', figsize=(14, 8), style=style, datetime_format='%d/%m', ylim=(price_min, price_max), 
        xlabel=date_range, volume=True, tight_layout=True, returnfig=True)


    fig.text(0.1,1.1, f'{s.name.upper().replace('_', ' ')}', ha='left', va='top', fontsize=20)
    fig.text(0.1,1.05, info, ha='left', va='top', fontsize=12, color='g' if s.total_return >= 0 else 'r')
    
    fig.text(0.52,1.1, subtitle5, ha='right', va='top', fontsize=10)
    fig.text(0.63,1.1, subtitle4, ha='right', va='top', fontsize=10)
    fig.text(0.75,1.1, subtitle3, ha='right', va='top', fontsize=10)
    fig.text(0.86,1.1, subtitle2, ha='right', va='top', fontsize=10)
    fig.text(1,1.1, subtitle1, ha='right', va='top', fontsize=10)
    

    ax1 = axlist[0]
    ax2 = Utils.get_ax_by_label(fig, "PNL")


    trade_num = 0    
    for t in trades:
        r1 = int(pts[pts["date"]==t.entry_date].iloc[0]['tick_num'])
        r2 = int(pts[pts["date"]==t.exit_date].iloc[0]['tick_num'])
        ax1.text(r1 -1, t.entry_price-20, f'[{trade_num}]', ha='center', va='top', fontsize=8, color='b', weight='bold')
        ax1.text(r2 -1, t.exit_price-20, f'[{trade_num}]{t.exit_reason_code}', ha='center', va='top', fontsize=8, color='r', weight='bold')
        ax2.text(r1 -1, 0, f'[{trade_num}]', ha='center', va='top', fontsize=7, color='b', weight='bold')
        ax2.text(r1 -1, -30, f'{t.entry_date.strftime("%d %b")}', ha='center', va='top', fontsize=7, weight='bold', rotation=45)
        ax2.text(r2 -1, -30, f'[{trade_num}]{t.exit_reason_code}', ha='center', va='top', fontsize=8, color='r', weight='bold')
         # bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.7))
        trade_num += 1

    # display(pts)

# pts = df.copy()
# drawEntryExitChart(df.copy(), "test")
def backtest_rsi_strategy(df, initial_capital):
    """
    Backtest RSI strategy:
    - Buy when RSI < oversold threshold
    - Sell when RSI > overbought threshold
    """
    rsi_oversold=30
    rsi_overbought=70,
    df = df.copy()
   
    # Initialize variables
    position = 0  # 0 = no position, 1 = holding
    shares = 0
    cash = initial_capital
    trades = []
    
    # Generate signals
    df['signal'] = 0
    df.loc[df['rsi'] < rsi_oversold, 'signal'] = 1  # Buy signal
    df.loc[df['rsi'] > rsi_overbought, 'signal'] = -1  # Sell signal
    
    # Execute trades
    for i in range(len(df)):
        date = df.index[i]
        price = float(df['close'].iloc[i])
        signal = int(df['signal'].iloc[i]) if not pd.isna(df['signal'].iloc[i]) else 0
        rsi = float(df['rsi'].iloc[i]) if not pd.isna(df['rsi'].iloc[i]) else np.nan
        
        # Buy logic
        if signal == 1 and position == 0 and not np.isnan(rsi):
            shares = cash / price
            cash = 0
            position = 1
            trades.append({
                'Date': date,
                'Type': 'BUY',
                'Price': price,
                'Shares': shares,
                'RSI': rsi
            })
        
        # Sell logic
        elif signal == -1 and position == 1 and not np.isnan(rsi):
            cash = shares * price
            trades.append({
                'Date': date,
                'Type': 'SELL',
                'Price': price,
                'Shares': shares,
                'RSI': rsi,
                'Profit': cash - initial_capital
            })
            shares = 0
            position = 0
        
        # Calculate portfolio value
        current_value = cash + (shares * price if position == 1 else 0)

    return {
        'trades': trades,
        'final_capital': current_value,
     }
    
    return df, trades


#%% BACKTESTING ALL STRATEGIES
print("\n" + "="*80)
print("BACKTESTING ALL STRATEGIES")
print("="*80)

    
strategies = {
    StrategyGapUp(initial_capital=10000, gap_threshold=0.35, hold_days=1, stop_loss=None, take_profit=None),
    StrategyGapUp(initial_capital=10000, gap_threshold=0.35, hold_days=2, stop_loss=None, take_profit=None)
}

for stgy in strategies:
    result = stgy.backtest(df)
    # results[strategy_name] = result
    summary = StrategySummary(stgy, INITIAL_CAPITAL, result)

    drawEntryExitChart(result.df, stgy, summary)

    print(f"\nSTRATEGY: {summary.name.upper().replace('_', ' ')} ({summary.total_return:.2f}%) ({len(summary.trades)} trades)")
    
    trades_df = pd.DataFrame([{
        'Entry Date': t.entry_date,
        'Exit Date': t.exit_date,
        'Entry Price': f"${t.entry_price:.2f}",
        'Exit Price': f"${t.exit_price:.2f}",
        'Shares': t.shares,
        'P&L': f"${t.pnl:.2f}",
        'Return %': f"{t.return_pct:.2f}%",
        'Exit Reason': t.exit_reason
    } for t in result.trades])
    print("Trade History:")
    print(trades_df.to_string(index=True))


# %% Best Strategy Summary
# best_strategy = max(results.items(), key=lambda x: x[1]['final_capital'])
# print("\n" + "="*80)
# print(f"BEST STRATEGY: {best_strategy[0].upper().replace('_', ' ')}")
# print("="*80)

# trades_df = pd.DataFrame([{
#     'Entry Date': t.entry_date,
#     'Exit Date': t.exit_date,
#     'Entry Price': f"${t.entry_price:.2f}",
#     'Exit Price': f"${t.exit_price:.2f}",
#     'Shares': t.shares,
#     'P&L': f"${t.pnl:.2f}",
#     'Return %': f"{t.return_pct:.2f}%",
#     'Exit Reason': t.exit_reason
# } for t in best_strategy[1]['trades']])

# print("\nTrade History:")
# print(trades_df.to_string(index=True))
