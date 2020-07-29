import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from scipy.special import binom


def moving_average(data_set, periods=3):
    weights = np.ones(periods) / periods
    return np.convolve(data_set, weights, mode='valid')


def round_minutes(tm):
    tm = tm - timedelta(minutes=tm.minute % 10, seconds=tm.second)
    return tm


def merge_data(csv_1, csv_2, csv_3):
    merge = pd.merge(csv_1, csv_2, how='inner', left_index=True, right_index=True)
    merged = pd.merge(merge, csv_3, how='inner', left_index=True, right_index=True)
    return merged


def load_raw_data(soil_path, pressure_path, air_path):
    soil = pd.read_csv(soil_path)
    pressure = pd.read_csv(pressure_path)
    air = pd.read_csv(air_path)
    return soil, pressure, air


def dt_diff(y1, y2):
    return (y1 - y2).total_seconds() / 3600.


def holoborodko_diff(y, t):
    """Holoborodko scheme for the 1st order numerical derivation.

    Params
    ------
    numpy.ndarray: y
        Sampled data to be differentiated
    pandas.core.series.Series: t
        Irregular time deltas

    Returns
    -------
    numpy.ndarray: y_t
        First order differentiated data
    """
    N = 5
    M = (N - 1) // 2
    m = (N - 3) // 2
    ck = [1 / 2 ** (2 * m + 1) * (binom(2 * m, m - k + 1) - binom(2 * m, m - k - 1)) for k in range(1, M + 1)]
    if not isinstance(y, (np.ndarray,)):
        raise Exception('Samples should be stored into numpy.ndarray.')
    else:
        y_t = np.zeros((y.size), dtype='float')
    # finite differences
    y_t[0] = (y[1] - y[0]) / dt_diff(t.iloc[1], t.iloc[0])
    y_t[1] = (y[2] - y[0]) / dt_diff(t.iloc[2], t.iloc[0])
    y_t[-2] = (y[-1] - y[-3]) / dt_diff(t.iloc[-1], t.iloc[-3])
    y_t[-1] = (y[-1] - y[-2]) / dt_diff(t.iloc[-1], t.iloc[-2])
    # holoborodko scheme
    for i in range(M, len(y) - M):
        y_t[i] = sum([ck[k - 1] * ((y[i + k] - y[i - k]) / dt_diff(t.iloc[i + k], t.iloc[i - k]) * 2 * k) for k in
                      range(1, M + 1)])
    return y_t
