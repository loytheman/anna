
import numpy as np
import pandas as pd
from _Utils import Utils
from _Class import Trade, Strategy, StrategySummary, BacktestResult


class StrategyGapUp(Strategy):
    TYPE = "gap-up"

    def __init__(self, initial_capital=10000, gap_threshold=0.35, hold_days=1, stop_loss=None, take_profit=None, fade=False):

        fade_txt = "fade" if fade else ""
        self.type = self.TYPE
        self.name = f"GAP UP {hold_days}D {gap_threshold}GT {stop_loss}SL {take_profit}TP {fade_txt}"
        self.initial_capital = initial_capital
        self.gap_threshold = gap_threshold
        self.hold_days = hold_days
        self.stop_loss = stop_loss
        self.take_profit = take_profit
        self.fade = fade


    def backtest(self, df):  
        df = df.copy()
        capital = self.initial_capital
        trades = []
        active_trade = None
        equity_curve = []
        
        hold_days = self.hold_days
        stop_loss = self.stop_loss
        take_profit = self.take_profit
        fade = self.fade

        df_daily = df[(df['is_market_open'] == True) | (df['is_market_close'] == True)].copy()
        df_daily["is_gap_up"] = False
        df_daily['is_gap_up'] = df_daily['gap_pct'] > self.gap_threshold
        df.loc[df['date'].isin(df_daily['date']), 'is_gap_up'] = df_daily['is_gap_up']

        
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
            elif not active_trade and current_row['is_gap_up'] == True and i > 0:
                # and current_row['histogram'] > 0                 
                entry_price = current_row['open']
                shares = int(capital / entry_price)
                
                if shares > 0:
                    active_trade = Trade(date, entry_price, shares, self.name)
                    capital -= shares * entry_price
                    # print("trade current_row", active_trade)
        
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
        equity_curve = pd.DataFrame(equity_curve)

        return BacktestResult(strategy_name=self.name, trades=trades, final_capital=capital, equity_curve=equity_curve, df=df)
