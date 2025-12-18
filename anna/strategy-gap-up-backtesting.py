# %%
# Gap Up Identifier - Jupyter Notebook
import pandas as pd
pd.set_option('display.width', 160)
pd.set_option('display.max_rows', 10) 
import numpy as np
import matplotlib as mpl
import matplotlib.dates as mdates
from datetime import datetime
import mplfinance as mpf
import datetime as dt
from _Utils import Utils
from IPython.display import display


pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)

# %%
strategies = {
    'hold_1_days': {'hold_days': 1, 'stop_loss': 2.0, 'take_profit': None},
    # 'hold_2_days': {'hold_days': 2, 'stop_loss': None, 'take_profit': None},
    # 'hold_3_days': {'hold_days': 3, 'stop_loss': 2.0, 'take_profit': None},
    # 'hold_5_days': {'hold_days': 5, 'stop_loss': 2.0, 'take_profit': None},
    # 'hold_10_days': {'hold_days': 10, 'stop_loss': 2.0, 'take_profit': 3},
    # 'stop_loss_2pct': {'hold_days': 10, 'stop_loss': 2.0, 'take_profit': 5.0},
    # 'aggressive': {'hold_days': 1, 'stop_loss': None, 'take_profit': None},
    # 'fade_gap': {'hold_days': 1, 'stop_loss': 3.0, 'take_profit': 2.0, 'fade': True}
}

#csv_file = 'ES(495512563)(1 hour)_historical_data.csv'
# csv_file = 'ES(495512563)(1 hour)(1 Y)_historical_data.csv'
# csv_file = 'ES(495512563)(1 hour)(6 M)_historical_data.csv'
# csv_file = 'ES(495512563)(1 hour)(3 M)_historical_data.csv'
# csv_file = 'ES(495512563)(1 day)(3 M)_historical_data.csv'
csv_file = 'ES(495512563)(1 day)(4 M)_historical_data.csv'
# csv_file = 'test.csv'


initial_capital = 10000  
position_size = 0.95 
gap_threshold = 0.35


# %%
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
    df_daily["prev_close"] = None
    df_daily["gap_pct"] = None
    df_daily.loc[df['is_market_open'] == True, 'prev_close'] = df_daily['close'].shift(1)
    df_daily.loc[df['is_market_open'] == True, 'gap_pct'] = ((df_daily['open'] - df_daily['prev_close']) / df_daily['prev_close']) * 100
    df_daily["is_gap_up"] = False
    df_daily['is_gap_up'] = df_daily['gap_pct'] > gap_threshold

    df.loc[df['date'].isin(df_daily['date']), ['gap_pct', 'is_gap_up']] = df_daily[['gap_pct', 'is_gap_up']]

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
   

# %%
def drawEntryExitChart (pts, stgy_name, stgy_params, trades=[], result={}):
    has_trade = len(trades) > 0
    pts['trade_num'] = np.nan
    pts['pnl'] = 0.0
    pts['entry_price'] = np.nan
    # pts['exit_price'] = 0.0
    pts['total_pnl'] = 0.0
    pts['total_pnl_above'] = np.nan
    pts['total_pnl_below'] = np.nan

    i = 1
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
    support_line = [gap_threshold] * len(pts)


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
        mpf.make_addplot(support_line, type='line', width=0.5, panel=4, color='r', linestyle="--", label=f"Gap up threshold {gap_threshold}%", secondary_y=False),
        
        #trades panel
        # mpf.make_addplot(pts['trade_num'], type='scatter', width=1.2, panel=5, ylabel="Trades", secondary_y=False, alpha=0.5),
        mpf.make_addplot(pts['pnl'], type='bar', width=1.2, panel=5, color=np.where(pts['pnl'] > 0, 'g', 'r'), ylabel="PNL", secondary_y=False, alpha=0.5),
        ### WTF!!!
        # mpf.make_addplot([50]*len(pts), type='scatter', width=1.2, panel=5, markersize=100, marker=pts['trade_2'], color='b',secondary_y=False, alpha=0.5),
        mpf.make_addplot(pts['total_pnl'], type='bar', width=0.8, panel=5, color=np.where(pts['total_pnl'] > 0, 'green', 'red'), secondary_y=False, alpha=0.1),
        mpf.make_addplot(pts['total_pnl'], type='line', width=0.8, panel=5, color='purple', linestyle="--", label=f"Total PnL", secondary_y=False),
    ]


    
    summary = subtitle1 = subtitle2 = subtitle3 = subtitle4 = subtitle5 = ""
    subtitle5 += f"Inital Capital: ${initial_capital:,.2f}\n"
    subtitle5 += f"Position Size: {position_size}%\n"
    subtitle5 += f"Gap Threshold: {gap_threshold}%\n"
    subtitle4 += f"Hold Day(s): {params['hold_days']}\n"
    subtitle4 += f"Stop Loss: {params['stop_loss']}%\n"
    subtitle4 += f"Take Profit: {params['take_profit']}%\n"
    if has_trade:
        apd.extend([
            mpf.make_addplot(pts['entry_price'], type='scatter', marker='^', markersize=20, color='blue'),
            mpf.make_addplot(pts['exit_price'], type='scatter',  marker='v', markersize=20, color='purple'),
        ])

        winning_trades = [t for t in trades if t.pnl > 0]
        losing_trades = [t for t in trades if t.pnl <= 0]

        total_return = ((result['final_capital'] - initial_capital) / initial_capital) * 100
        win_rate = (len(winning_trades) / len(trades)) * 100
        avg_win = np.mean([t.pnl for t in winning_trades]) if winning_trades else 0
        avg_loss = np.mean([t.pnl for t in losing_trades]) if losing_trades else 0
        
        summary += f"Total Return: {total_return:.2f}%"
        subtitle3 += f"Total Trades: {len(trades)}\n"
        subtitle3 += f"Winning Trades: {len(winning_trades)}\n"
        subtitle3 += f"Losing Trades: {len(losing_trades)}\n"
        subtitle2 += f"Avg Win: ${avg_win:.2f}\n"
        subtitle2 += f"Avg Loss: ${avg_loss:.2f}\n"
        if avg_loss != 0:
            subtitle2 += f"Profit Factor: {abs(avg_win/avg_loss):.2f}\n"
        subtitle1 += f"Total Return: {total_return:.2f}%\n"
        subtitle1 += f"Win Rate: {win_rate:.2f}%\n"
        subtitle1 += f"Final Capital: ${result['final_capital']:,.2f}\n"
        
    else:
        summary += f"No trades executed\n"

    s = mpf.make_mpf_style(base_mpf_style='yahoo', edgecolor='#000000',rc={'axes.linewidth':0.5})
    date_range = "\n" + df.iloc[0, 0].strftime("%d %b %Y") + '  -  ' + df.iloc[-1, 0].strftime("%d %b %Y")
    fig, axlist = mpf.plot(pts, addplot=apd, type='ohlc', figsize=(14, 8), style=s, datetime_format='%d/%m', xlabel=date_range, volume=True, tight_layout=True, returnfig=True)


    fig.text(0.1,1.1, f'{stgy_name.upper().replace('_', ' ')}', ha='left', va='top', fontsize=20)
    fig.text(0.1,1.05, summary, ha='left', va='top', fontsize=12, color='g' if total_return >= 0 else 'r')
    
    fig.text(0.52,1.1, subtitle5, ha='right', va='top', fontsize=10)
    fig.text(0.63,1.1, subtitle4, ha='right', va='top', fontsize=10)
    fig.text(0.75,1.1, subtitle3, ha='right', va='top', fontsize=10)
    fig.text(0.86,1.1, subtitle2, ha='right', va='top', fontsize=10)
    fig.text(1,1.1, subtitle1, ha='right', va='top', fontsize=10)
    

    ax1 = axlist[0]
    ax2 = Utils.get_ax_by_label(fig, "PNL")

    trade_num = 0    
    for t in trades:
        trade_num += 1
        r1 = pts[pts["date"]==t.entry_date]
        r2 = pts[pts["date"]==t.exit_date]
        ax1.text(r1['tick_num']-1, t.entry_price * 0.995, f'[{trade_num}]', ha='center', va='top', fontsize=8, color='b', weight='bold')
        ax1.text(r2['tick_num']-1, t.exit_price * 0.995, f'[{trade_num}]{t.exit_reason_code}', ha='center', va='top', fontsize=8, color='r', weight='bold')
        ax2.text(r1['tick_num']-1, 0, f'[{trade_num}]', ha='center', va='top', fontsize=7, color='b', weight='bold')
         # bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.7))

# pts = df.copy()
# drawEntryExitChart(df.copy(), "test")

# %%
class Trade:
    def __init__(self, entry_date, entry_price, shares, strategy_name):
        self.entry_date = entry_date
        self.entry_price = entry_price
        self.shares = shares
        self.exit_date = None
        self.exit_price = None
        self.pnl = 0
        self.return_pct = 0
        self.strategy_name = strategy_name
        self.exit_reason = None
        self.exit_reason_code = None

#%% """Backtest a single strategy"""
def backtest_strategy(df, strategy_params, initial_capital, position_size, strategy_name):  
    capital = initial_capital
    trades = []
    active_trade = None
    equity_curve = []
    
    hold_days = strategy_params['hold_days']
    stop_loss = strategy_params.get('stop_loss')
    take_profit = strategy_params.get('take_profit')
    fade = strategy_params.get('fade', False)  # Fade = short the gap
    
    for i in range(len(df)):
        current_row = df.iloc[i]
        date = current_row['date']
        
        # Track equity
        if active_trade:
            current_value = capital + (active_trade.shares * current_row['close'])
        else:
            current_value = capital
        equity_curve.append({'date': date, 'equity': current_value})
        
        # Check if we need to exit an active trade
        if active_trade:
            days_held = Utils.busday_diff(active_trade.entry_date, date)
            # print(active_trade.entry_date, date, "days_held", days_held)
            current_price = current_row['close']
            
            # Calculate current return
            if fade:
                current_return = ((active_trade.entry_price - current_price) / active_trade.entry_price) * 100
            else:
                current_return = ((current_price - active_trade.entry_price) / active_trade.entry_price) * 100
            
            should_exit = False
            exit_reason = None
            exit_reason_code = None
            
            # Check stop loss
            if stop_loss and current_return <= -stop_loss:
                should_exit = True
                exit_reason = 'Stop Loss'
                exit_reason_code = 'SL'
            
            # Check take profit
            elif take_profit and current_return >= take_profit:
                should_exit = True
                exit_reason = 'Take Profit'
                exit_reason_code = 'TP'
            
            # Check holding period
            elif days_held >= hold_days:
                should_exit = True
                exit_reason = f'Hold Period ({hold_days}d)'
                exit_reason_code = 'H'
            
            if should_exit:
                # Exit trade
                active_trade.exit_date = date
                active_trade.exit_price = current_price
                
                if fade:
                    active_trade.pnl = active_trade.shares * (active_trade.entry_price - current_price)
                else:
                    active_trade.pnl = active_trade.shares * (current_price - active_trade.entry_price)
                
                active_trade.return_pct = current_return
                active_trade.exit_reason = exit_reason
                active_trade.exit_reason_code = exit_reason_code
                
                capital += active_trade.shares * active_trade.entry_price + active_trade.pnl
                trades.append(active_trade)
                active_trade = None
        
        # Check for new gap up signal (only if no active trade) and MACD > 0
        elif not active_trade and current_row['is_gap_up'] == True and current_row['histogram'] > 0 and i > 0:
            # print("current_row", current_row)
            entry_price = current_row['open']
            shares = int((capital * position_size) / entry_price)
            
            if shares > 0:
                active_trade = Trade(date, entry_price, shares, strategy_name)
                capital -= shares * entry_price
    
    # Close any remaining open trade
    if active_trade:
        last_row = df.iloc[-1]
        active_trade.exit_date = last_row['date']
        active_trade.exit_price = last_row['close']
        
        if fade:
            active_trade.pnl = active_trade.shares * (active_trade.entry_price - last_row['close'])
            active_trade.return_pct = ((active_trade.entry_price - last_row['close']) / active_trade.entry_price) * 100
        else:
            active_trade.pnl = active_trade.shares * (last_row['close'] - active_trade.entry_price)
            active_trade.return_pct = ((last_row['close'] - active_trade.entry_price) / active_trade.entry_price) * 100
        
        active_trade.exit_reason = 'End of Data'
        capital += active_trade.shares * active_trade.entry_price + active_trade.pnl
        trades.append(active_trade)

    # print("------------- trade --------------")
    # for t in trades:
    #     print(t.entry_date, t.exit_date)
    
    trades = [t for t in trades if t.exit_reason_code != None]
    
    return {
        'trades': trades,
        'final_capital': capital,
        'equity_curve': pd.DataFrame(equity_curve)
    }


#%%  BACKTESTING ALL STRATEGIES
print("\n" + "="*80)
print("BACKTESTING ALL STRATEGIES")
print("="*80)

results = {}
for strategy_name, params in strategies.items():
    result = backtest_strategy(df, params, initial_capital, position_size, strategy_name)
    results[strategy_name] = result
    
    trades = result['trades']

    drawEntryExitChart(df, strategy_name, params, trades, result)

# %%
best_strategy = max(results.items(), key=lambda x: x[1]['final_capital'])
print("\n" + "="*80)
print(f"BEST STRATEGY: {best_strategy[0].upper().replace('_', ' ')}")
print("="*80)

trades_df = pd.DataFrame([{
    'Entry Date': t.entry_date,
    'Exit Date': t.exit_date,
    'Entry Price': f"${t.entry_price:.2f}",
    'Exit Price': f"${t.exit_price:.2f}",
    'Shares': t.shares,
    'P&L': f"${t.pnl:.2f}",
    'Return %': f"{t.return_pct:.2f}%",
    'Exit Reason': t.exit_reason
} for t in best_strategy[1]['trades']])

print("\nTrade History:")
print(trades_df.to_string(index=False))
