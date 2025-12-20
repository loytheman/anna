
import numpy as np

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

class StrategySummary:
    def __init__(self, name, initial_capital, result):
        trades = result['trades']
        final_capital = result['final_capital']
        equity_curve = result['equity_curve']

        win_rate = profit_factor =0.0
        
        winning_trades = [t for t in trades if t.pnl > 0]
        losing_trades = [t for t in trades if t.pnl <= 0]

        total_return = ((final_capital - initial_capital) / initial_capital) * 100
        avg_win = np.mean([t.pnl for t in winning_trades]) if winning_trades else 0
        avg_loss = np.mean([t.pnl for t in losing_trades]) if losing_trades else 0
        if (avg_win > 0):
            win_rate = (len(winning_trades) / len(trades)) * 100
            profit_factor = abs(avg_win/avg_loss)
        
        peak = equity_curve['equity'].max()
        trough = equity_curve['equity'].min()
        drawdown = ((peak - trough) / peak) * 100

        self.name = name

        self.trades = trades
        self.equity_curve = equity_curve
        self.winning_trades = winning_trades
        self.losing_trades = losing_trades

        self.final_capital = final_capital
        self.total_return = total_return
        self.win_rate = win_rate
        self.avg_win = avg_win
        self.avg_loss = avg_loss
        self.profit_factor = profit_factor
        self.peak = peak
        self.trough = trough
        self.drawdown = drawdown        