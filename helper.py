from pickle import STOP
from re import L
import pandas as pd
from talib import MACD, RSI, EMA
from datetime import datetime

# ----- CONSTANTS -----
MS_IN_5_MIN = 300000
MS_IN_1_MIN = 60000
TAKE_PROFIT_PERCENTAGE = 0.004
TRADE_TIME_HORIZON = 100
EXCHANGE_FEE = 0.002

# ----- ORDER CONSTANTS ------
ORDER_NOT_FILLED_IN_TIME = "ORDER_NOT_FILLED_IN_TIME"
STOP_LOSS_TRIGGERED = "STOP_LOSS_TRIGGERED"
TAKE_PROFIT_TRIGGERED = "TAKE_PROFIT_TRIGGERED"
TRADE_UNDECIDED = "TRADE_UNDECIDED"

# DDM point values
INDICATOR_SAME_EMA = 10
INDICATOR_NO_EMA = 7.5
INDICATOR_AGAINST_EMA = 5


LONG_DECISION = 50
SHORT_DECISION = -50

# DDM functions


def get_score(indicator_trend, ema_trend):
    if ema_trend == None:
        if indicator_trend == "bullish":
            return INDICATOR_NO_EMA
        else:
            return -INDICATOR_NO_EMA
    elif indicator_trend == ema_trend:
        if indicator_trend == "bullish":
            return INDICATOR_SAME_EMA
        else:
            return -INDICATOR_SAME_EMA
    else:
        if indicator_trend == "bullish":
            return INDICATOR_AGAINST_EMA
        else:
            return -INDICATOR_AGAINST_EMA


def check_sar_trend(last_candle, last_candle_sar, current_candle, current_candle_sar):
    if last_candle_sar > last_candle.high and current_candle_sar < current_candle.low:
        return "bullish"
    elif last_candle_sar < last_candle.low and current_candle_sar > current_candle.high:
        return "bearish"
    return None


def ddm_reached_long(ddm_score):
    return ddm_score >= LONG_DECISION


def ddm_reached_short(ddm_score):
    return ddm_score <= SHORT_DECISION


def get_long_trade_outcome(current_candle, profit_trigger_price, loss_trigger_price):
    if current_candle.high >= profit_trigger_price:
        return "profit"
    elif current_candle.low <= loss_trigger_price:
        return "loss"
    return None


def get_short_trade_outcome(current_candle, profit_trigger_price, loss_trigger_price):
    if current_candle.low <= profit_trigger_price:
        return "profit"
    elif current_candle.high >= loss_trigger_price:
        return "loss"
    return None

# ----- CANDLES -----


def candle_is_green(candle):
    return candle.close > candle.open


def candle_is_red(candle):
    return candle.close < candle.open


def low_wick_is_valid(possible_engulfing_candle):
    """Verifies if the lower wick of the engulfing candle is at maximum half of the body
        Used for bearish engulfing pattern"""
    accepted_wick = (possible_engulfing_candle.open -
                     possible_engulfing_candle.close)/2
    low_wick = possible_engulfing_candle.close - possible_engulfing_candle.low
    return low_wick < accepted_wick


def high_wick_is_valid(possible_engulfing_candle):
    """Verifies if the upper wick of the engulfing candle is at maximum half of the body
        Used for bullish engulfing pattern"""
    accepted_wick = (possible_engulfing_candle.close -
                     possible_engulfing_candle.open)/2
    high_wick = possible_engulfing_candle.high - possible_engulfing_candle.close
    return high_wick < accepted_wick


def is_bullish_engulfing(possible_engulfed_candle, possible_engulfing_candle):
    """Checks for bullish engulfing candle pattern"""
    return possible_engulfing_candle.close > possible_engulfed_candle.open and candle_is_red(possible_engulfed_candle) and candle_is_green(possible_engulfing_candle) and high_wick_is_valid(possible_engulfing_candle)


def is_bearish_engulfing(possible_engulfed_candle, possible_engulfing_candle):
    """Checks for bearish engulfing candle pattern"""
    return possible_engulfed_candle.open > possible_engulfing_candle.close and candle_is_green(possible_engulfed_candle) and candle_is_red(possible_engulfing_candle) and low_wick_is_valid(possible_engulfing_candle)


def type_of_engulfing(possible_engulfed_candle, possible_engulfing_candle):
    if is_bullish_engulfing(possible_engulfed_candle, possible_engulfing_candle):
        return "bullish"
    elif is_bearish_engulfing(possible_engulfed_candle, possible_engulfing_candle):
        return "bearish"

    return None


# ----- ORDERS -----

def calc_long_entry_price(engulfed_candle, engulfing_candle):
    """Calculating the entry price for a long position"""
    if engulfed_candle.high < (engulfing_candle.close - (engulfing_candle.close - engulfing_candle.open) * 5 / 100):
        return (engulfed_candle.high + engulfing_candle.close)/2
    else:
        return (engulfed_candle.open + engulfing_candle.close)/2


def calc_short_entry_price(engulfed_candle, engulfing_candle):
    """Calculating the entry price for a short position"""
    if engulfed_candle.low < (engulfing_candle.close + (engulfing_candle.open - engulfing_candle.close) * 5 / 100):
        return (engulfed_candle.low + engulfing_candle.close)/2
    else:
        return (engulfed_candle.open + engulfing_candle.close)/2


def calc_entry_price(trend, engulfed_candle, engulfing_candle):
    if trend == "bullish":
        return calc_long_entry_price(engulfed_candle, engulfing_candle)

    return calc_long_entry_price(engulfed_candle, engulfing_candle)


def calc_long_take_profit(long_entry_price):
    return long_entry_price + (long_entry_price * TAKE_PROFIT_PERCENTAGE)


def calc_short_take_profit(short_entry_price):
    return short_entry_price - (short_entry_price * TAKE_PROFIT_PERCENTAGE)


def calc_take_profit(trend, entry_price):
    if trend == "bullish":
        return calc_long_take_profit(entry_price)
    return calc_short_take_profit(entry_price)


def calc_long_loss(entry_price):
    return entry_price - (entry_price * TAKE_PROFIT_PERCENTAGE)


def calc_short_loss(entry_price):
    return entry_price + (entry_price * TAKE_PROFIT_PERCENTAGE)


def calc_loss_price(trend, entry_price):
    if trend == "bullish":
        return calc_long_loss(entry_price)
    return calc_short_loss(entry_price)


def calc_long_stop_loss(engulfed_candle, engulfing_candle):
    return min(engulfed_candle.low, engulfing_candle.low)


def calc_short_stop_loss(engulfed_candle, engulfing_candle):
    return max(engulfed_candle.high, engulfing_candle.high)


def calc_stop_loss(trend, engulfed_candle, engulfing_candle):
    if trend == "bullish":
        return calc_long_stop_loss(engulfed_candle, engulfing_candle)
    return calc_short_stop_loss(engulfed_candle, engulfing_candle)


def calc_loss(entry_price, stop_loss_price):
    loss = abs(stop_loss_price - entry_price)
    loss_in_percentage = loss*100/entry_price
    return loss, loss_in_percentage


def order_was_filled_on_candle(trend, current_candle, entry_price):
    # intentionally excluding =
    if trend == "bullish" and current_candle.low < entry_price:
        return True
    elif trend == "bearish" and current_candle.high > entry_price:
        return True

    return False


def stop_loss_was_triggered(trend, current_candle, stop_loss_price):
    if trend == "bullish" and current_candle.low <= stop_loss_price:
        return True
    elif trend == "bearish" and current_candle.high >= stop_loss_price:
        return True

    return False


def take_profit_was_triggered(trend, current_candle, take_profit_price):
    if trend == "bullish" and current_candle.high > take_profit_price:
        return True
    elif trend == "bearish" and current_candle.low < take_profit_price:
        return True

    return False

# ----- INDICATORS -----


def volume_is_bigger(engulfed_candle, engulfing_candle):
    return engulfing_candle.volume > engulfed_candle.volume


def emas_are_bullish_lined(ema_20_value, ema_50_value, ema_200_value):
    """"Verifies if the given EMAs are positioned bullish
        Used to determine bullish market structure"""
    return ema_20_value > ema_50_value and ema_50_value > ema_200_value


def emas_are_bearish_lined(ema_20_value, ema_50_value, ema_200_value):
    """"Verifies if the given EMAs are positioned bullish
        Used to determine bearish market structure"""
    return ema_20_value < ema_50_value and ema_50_value < ema_200_value


def candle_is_trending_bullish(subject_candle, ema_200_value):
    """"Verifies if candle is trending bullish"""
    return subject_candle.open > ema_200_value and subject_candle.close > ema_200_value


def candle_is_trending_bearish(subject_candle, ema_200_value):
    """"Verifies if candle is trending bearish"""
    return subject_candle.open < ema_200_value and subject_candle.close < ema_200_value


def values_are_negative(value1, value2, value3):
    return value1 < 0 and value2 < 0 and value3 < 0


def values_are_positive(value1, value2, value3):
    return value1 > 0 and value2 > 0 and value3 > 0


def macd_values_are_bullish_lined(engulfed_macd_value, engulfing_macd_value, extra_macd_value):
    """Verifies for MACD bullish trend reversal"""
    return extra_macd_value > engulfed_macd_value and engulfed_macd_value < engulfing_macd_value and values_are_negative(extra_macd_value, engulfed_macd_value, engulfing_macd_value)


def macd_values_are_bearish_lined(engulfed_macd_value, engulfing_macd_value, extra_macd_value):
    """Verifies for MACD bullish trend reversal"""
    return extra_macd_value < engulfed_macd_value and engulfed_macd_value > engulfing_macd_value and values_are_positive(extra_macd_value, engulfed_macd_value, engulfing_macd_value)


def rsi_is_valid(indicator_candles, trend):
    """"Verifies that engulfing candle's RSI respects the trend"""
    # subtract candles needed for macd
    rsi_needed_candles = indicator_candles.tail(70)
    rsi_value = RSI(rsi_needed_candles)[69]

    if trend == "bearish":
        return rsi_value < 60
    elif trend == "bullish":
        return rsi_value > 40

    return False


def return_emas_trend_and_check_candle(subject_candle, indicator_candles):
    """Computes 20, 50, 200 EMA. Verifies market structure trend & if candle is trending accordingly.
        Returns trend
    """

    ema_20_value = EMA(indicator_candles, timeperiod=20).iloc[399]
    ema_50_value = EMA(indicator_candles, timeperiod=50).iloc[399]
    ema_200_value = EMA(indicator_candles, timeperiod=200).iloc[399]

    if emas_are_bullish_lined(ema_20_value, ema_50_value, ema_200_value) and candle_is_trending_bullish(subject_candle, ema_200_value):
        return "bullish", ema_20_value
    elif emas_are_bearish_lined(ema_20_value, ema_50_value, ema_200_value) and candle_is_trending_bearish(subject_candle, ema_200_value):
        return "bearish", ema_20_value
    else:
        return "not trending", ema_20_value


def return_emas_trend(indicator_candles):
    """Computes 20, 50, 200 EMA. Verifies EMAs trend.
    """

    ema_20_value = EMA(indicator_candles, timeperiod=20).iloc[399]
    ema_50_value = EMA(indicator_candles, timeperiod=50).iloc[399]
    ema_200_value = EMA(indicator_candles, timeperiod=200).iloc[399]

    if emas_are_bullish_lined(ema_20_value, ema_50_value, ema_200_value):
        return "bullish", ema_20_value
    elif emas_are_bearish_lined(ema_20_value, ema_50_value, ema_200_value):
        return "bearish", ema_20_value
    else:
        return "not trending", ema_20_value


def macd_is_lined(indicator_candles, trend):
    """Checks for MACD line-up validation."""
    # subtract candles needed for macd

    macd_needed_candles = indicator_candles.tail(37)
    _, _, macd_hist = MACD(macd_needed_candles)
    macd_hist = macd_hist.tail(3)
    extra_macd_hist_value = macd_hist.iloc[0]
    engulfed_macd_hist_value = macd_hist.iloc[1]
    engulfing_macd_hist_value = macd_hist.iloc[2]

    if trend == "bullish":
        return macd_values_are_bullish_lined(engulfed_macd_hist_value, engulfing_macd_hist_value, extra_macd_hist_value)
    elif trend == "bearish":
        return macd_values_are_bearish_lined(engulfed_macd_hist_value, engulfing_macd_hist_value, extra_macd_hist_value)
    return False


def rsi_is_wrong(engulfing_type, rsi_value):
    return (engulfing_type == 'bullish' and (rsi_value < 40 or rsi_value > 75)) or (engulfing_type == 'bearish' and (rsi_value > 60 or rsi_value < 30))


def volume_is_not_engulfing(engulfing_candle, engulfed_candle):
    return engulfing_candle.volume < engulfed_candle.volume

# ----- DATA RELATED -----


def get_candles_dataframe(client, symbol, interval, start_time, end_time=None):
    """Requesting candles and returning them as pandas dataframe"""
    klines = client.futures_historical_klines(
        symbol, interval, start_time, end_time)
    df = pd.DataFrame(klines)
    df = df.iloc[:, :6]
    df.columns = ['time', 'open', 'high', 'low', 'close', 'volume']
    df['time'] = pd.to_datetime(df['time'], unit='ms')
    df.set_index('time', inplace=True)
    df = df.astype(float)
    return df


def get_candles_for_indicator(client, symbol, timeframe, number_of_candles, subject_candle):
    end_time = int(subject_candle.name.timestamp())*1000 + 1
    # +1 to contain the subject candle

    start_time = end_time - (number_of_candles-1) * timeframe * MS_IN_1_MIN - 2
    if timeframe == 60:
        return get_candles_dataframe(client, symbol, "1h", start_time, end_time)
    return get_candles_dataframe(client, symbol, str(timeframe) + "m", start_time, end_time)


def get_1m_follow_up_candles_for_candle(client, signal_candle, time_horizon_in_minutes):
    start_time = int(signal_candle.name.timestamp())*1000 + MS_IN_5_MIN - 1
    # - 1 to include the first candle after the signal candle

    end_time = start_time + (time_horizon_in_minutes - 1) * MS_IN_1_MIN + 2
    return get_candles_dataframe(client, "BTCUSDT", "1m", start_time, end_time)


def trade_result(trend, trade_horizon_candles, entry_price, stop_loss_price, take_profit_price):
    time_horizon = trade_horizon_candles.shape[0]
    order_was_filled = False
    for i in range(time_horizon):
        current_candle = trade_horizon_candles.iloc[i]

        if not order_was_filled:
            if i >= 25:
                return ORDER_NOT_FILLED_IN_TIME
            order_was_filled = order_was_filled_on_candle(
                trend, current_candle, entry_price)
            take_profit_triggered = take_profit_was_triggered(
                trend, current_candle, take_profit_price)
            if order_was_filled and take_profit_triggered:
                return TRADE_UNDECIDED
            # elif take_profit_triggered:
            #     return TRADE_UNDECIDED

        if order_was_filled:
            if stop_loss_was_triggered(trend, current_candle, stop_loss_price) and take_profit_was_triggered(trend, current_candle, take_profit_price):
                return TRADE_UNDECIDED
            elif stop_loss_was_triggered(trend, current_candle, stop_loss_price):
                print("next trade close at: ", end=" ")
                print(current_candle.name)
                return STOP_LOSS_TRIGGERED
            elif take_profit_was_triggered(trend, current_candle, take_profit_price):
                return TAKE_PROFIT_TRIGGERED
    return ORDER_NOT_FILLED_IN_TIME
    # return TRADE_UNDECIDED


def max_take_profit(candle_trend, trade_horizon_candles, stop_loss_price, entry_price):
    time_horizon = trade_horizon_candles.shape[0]
    max_take_profit = -1
    diff = 0
    profit_percentage = 0

    # 1RR ratio
    _, take_profit_percentage = calc_loss(entry_price, stop_loss_price)
    if candle_trend == "bullish":
        take_profit_price = entry_price + take_profit_percentage/100 * entry_price
    else:
        take_profit_price = entry_price - take_profit_percentage/100 * entry_price

    for i in range(time_horizon):
        current_candle = trade_horizon_candles.iloc[i]

        if candle_trend == "bullish":
            if current_candle.low <= stop_loss_price:
                return max_take_profit, True
            elif current_candle.high > take_profit_price:
                return take_profit_percentage, False
            diff = current_candle.high - entry_price
        elif candle_trend == "bearish":
            if current_candle.high >= stop_loss_price:
                return max_take_profit, True
            elif current_candle.low < take_profit_price:
                return take_profit_percentage, False
            diff = entry_price - current_candle.low

        profit_percentage = diff * 100 / entry_price
        max_take_profit = max(max_take_profit, profit_percentage)
    return max_take_profit, False


def max_loss(candle_trend, trade_horizon_candles, entry_price):
    time_horizon = trade_horizon_candles.shape[0]
    max_loss_percentage = -1
    diff = 0
    loss_percentage = 0
    for i in range(time_horizon):
        current_candle = trade_horizon_candles.iloc[i]
        if candle_trend == "bullish":
            diff = entry_price - current_candle.low
        else:
            diff = current_candle.high - entry_price

        loss_percentage = diff * 100 / entry_price
        max_loss_percentage = max(max_loss_percentage, loss_percentage)
    return max_loss_percentage
