import numpy as np
import pandas as pd
from datetime import datetime, timedelta


class Utils:
    
    def busday_diff(start, end):
        """Calculate business days between two dates using NumPy."""
        # Convert to date if datetime object (removes time component)
        if isinstance(start, datetime):
            start = start.date()
        if isinstance(end, datetime):
            end = end.date()
        return np.busday_count(start, end)




