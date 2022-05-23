from tracemalloc import start
from binance.client import Client
import config
import helper as h
from talib import RSI, MACD, SAR, EMA
import pandas as pd
import math

client = Client(config.API_KEY, config.SECRET_KEY)
symbol = 'BTCUSDT'


def find_engulfing_candles(candles_df):
    number_of_candles = candles_df.shape[0]
    total_wins = 0
    total_losses = 0
    total_undecided = 0
    total_not_taken = 0
    for i in range(number_of_candles-1):
        possible_engulfed_candle = candles_df.iloc[i]
        possible_engulfing_candle = candles_df.iloc[i+1]

        engulfing_type = h.type_of_engulfing(
            possible_engulfed_candle, possible_engulfing_candle)

        if engulfing_type != None:
            #  400 candles for EMA.
            indicator_candles = h.get_candles_for_indicator(client, symbol, 5, 400, possible_engulfing_candle)[
                "close"]
            trend, _ = h.return_emas_trend_and_check_candle(
                possible_engulfing_candle, indicator_candles)

            if engulfing_type == trend:
                if h.macd_is_lined(indicator_candles, trend) and h.rsi_is_valid(indicator_candles, trend):
                    entry_price = h.calc_entry_price(
                        trend, possible_engulfed_candle, possible_engulfing_candle)
                    take_profit_price = h.calc_take_profit(trend, entry_price)
                    stop_loss_price = h.calc_stop_loss(
                        trend, possible_engulfed_candle, possible_engulfing_candle)

                    trade_candles = h.get_1m_follow_up_candles_for_candle(
                        client, possible_engulfing_candle, h.TRADE_TIME_HORIZON)
                    result = h.trade_result(
                        trend, trade_candles, entry_price, stop_loss_price, take_profit_price)

                    if result == h.TRADE_UNDECIDED:
                        total_undecided += 1
                    elif result == h.TAKE_PROFIT_TRIGGERED:
                        total_wins += 1
                    elif result == h.STOP_LOSS_TRIGGERED:
                        total_losses += 1
                    else:
                        total_not_taken += 1

                    print("POSSIBLE TRADE AT: ", end=" ")
                    print(possible_engulfing_candle.name)
                    print("ENTRY PRICE AT: " + str(entry_price) + " -- TAKE PROFIT PRICE AT: " +
                          str(take_profit_price) + " -- STOP LOSS PRICE AT: " + str(stop_loss_price) + " | " + str(abs(stop_loss_price-entry_price)*100/entry_price) + " -- RESULT:" + result, end="\n\n")
    print("total wins: " + str(total_wins))
    print("total losses: " + str(total_losses))
    print("total undecided: " + str(total_undecided))
    print("total not taken: " + str(total_not_taken))
    return


# e1_trade_candles = pd.DataFrame()
# e2_trade_candles = pd.DataFrame()
# e3_trade_candles = pd.DataFrame()


# def study_engulfing_candles_no_trend(candles_df):
#     '''experiment 1. studying only engulfing candles, no matter the trend'''
#     number_of_candles = candles_df.shape[0]
#     e1_number_of_trades = 0
#     e1_number_of_wins = 0
#     e1_number_of_losses = 0
#     e1_number_of_undecided_trades = 0
#     e1_total_win_percentage = 0
#     e1_total_loss_percentage = 0
#     e1_w_wrong_rsi = 0
#     e1_l_wrong_rsi = 0
#     e1_w_wrong_vol = 0
#     e1_l_wrong_vol = 0

#     '''experiment 2. studying engulfing candles according to ema trend'''
#     e2_number_of_trades = 0
#     e2_number_of_wins = 0
#     e2_number_of_losses = 0
#     e2_number_of_undecided_trades = 0
#     e2_total_win_percentage = 0
#     e2_total_loss_percentage = 0
#     e2_w_wrong_rsi = 0
#     e2_l_wrong_rsi = 0
#     e2_w_wrong_vol = 0
#     e2_l_wrong_vol = 0

#     '''experiment 2. studying engulfing candles according to parabolic SAR trend'''
#     e3_number_of_trades = 0
#     e3_number_of_wins = 0
#     e3_number_of_losses = 0
#     e3_number_of_undecided_trades = 0
#     e3_total_win_percentage = 0
#     e3_total_loss_percentage = 0
#     e3_w_wrong_rsi = 0
#     e3_l_wrong_rsi = 0
#     e3_w_wrong_vol = 0
#     e3_l_wrong_vol = 0

#     for i in range(number_of_candles-1):
#         possible_engulfed_candle = candles_df.iloc[i]
#         possible_engulfing_candle = candles_df.iloc[i+1]

#         engulfing_type = h.type_of_engulfing(
#             possible_engulfed_candle, possible_engulfing_candle)

#         if engulfing_type != None:
#             # candles for indicators
#             indicator_candles = h.get_candles_for_indicator(
#                 client, symbol, 5, 400, possible_engulfing_candle)
#             close_indicator_candles = indicator_candles["close"]
#             high_indicator_candles = indicator_candles["high"]
#             low_indicator_candles = indicator_candles["low"]

#             '''e1'''
#             stop_loss_price = h.calc_stop_loss(
#                 engulfing_type, possible_engulfed_candle, possible_engulfing_candle)
#             _, loss_in_percentage = h.calc_loss(
#                 possible_engulfing_candle.close, stop_loss_price)

#             trade_candles = h.get_1m_follow_up_candles_for_candle(
#                 client, possible_engulfing_candle, 100)
#             max_profit, stop_loss_hit = h.max_take_profit(
#                 engulfing_type, trade_candles, stop_loss_price, possible_engulfing_candle.close)

#             # some extra indicator data for better trade studyying to further use in DDM
#             rsi_value = RSI(close_indicator_candles.tail(70))[69]

#             e1_frame = pd.DataFrame({'time': possible_engulfing_candle.name, 'index': e1_number_of_trades, 'engulfing type': engulfing_type, 'RSI': rsi_value, 'VOLUME is bigger: ': h.volume_is_bigger(possible_engulfed_candle, possible_engulfing_candle),
#                                      'max profit': max_profit, 'stop loss hit': stop_loss_hit}, index=[possible_engulfing_candle.name])
#             if max_profit == loss_in_percentage:
#                 e1_number_of_wins += 1
#                 e1_total_win_percentage += max_profit
#                 if h.rsi_is_wrong(engulfing_type, rsi_value):
#                     e1_w_wrong_rsi += 1
#                 if h.volume_is_bigger(possible_engulfed_candle, possible_engulfing_candle):
#                     e1_w_wrong_vol += 1
#             elif stop_loss_hit:
#                 e1_number_of_losses += 1
#                 e1_total_loss_percentage += loss_in_percentage
#                 if h.rsi_is_wrong(engulfing_type, rsi_value):
#                     e1_l_wrong_rsi += 1
#                 if h.volume_is_bigger(possible_engulfed_candle, possible_engulfing_candle):
#                     e1_l_wrong_vol += 1
#             else:
#                 e1_number_of_undecided_trades += 1
#             e1_number_of_trades += 1

#             # adding trade of experiment 1 to trading data
#             global e1_trade_candles
#             e1_trade_candles = pd.concat(
#                 [e1_trade_candles, e1_frame])

#             '''e2'''
#             # EMAs
#             ema_trend, _ = h.return_emas_trend(
#                 close_indicator_candles)
#             if ema_trend == engulfing_type:
#                 e2_frame = pd.DataFrame({'time': possible_engulfing_candle.name, 'index': e2_number_of_trades, 'engulfing type': engulfing_type, 'EMAs trend': ema_trend,
#                                          'RSI': rsi_value, 'VOLUME is bigger: ': h.volume_is_bigger(possible_engulfed_candle, possible_engulfing_candle), 'max profit': max_profit, 'stop loss hit': stop_loss_hit}, index=[possible_engulfing_candle.name])
#                 if max_profit == loss_in_percentage:
#                     e2_number_of_wins += 1
#                     e2_total_win_percentage += max_profit
#                     if h.rsi_is_wrong(engulfing_type, rsi_value):
#                         e2_w_wrong_rsi += 1
#                     if h.volume_is_bigger(possible_engulfed_candle, possible_engulfing_candle):
#                         e2_w_wrong_vol += 1
#                 elif stop_loss_hit:
#                     e2_number_of_losses += 1
#                     e2_total_loss_percentage += loss_in_percentage
#                     if h.rsi_is_wrong(engulfing_type, rsi_value):
#                         e2_l_wrong_rsi += 1
#                     if h.volume_is_bigger(possible_engulfed_candle, possible_engulfing_candle):
#                         e2_l_wrong_vol += 1
#                 else:
#                     e2_number_of_undecided_trades += 1
#                 e2_number_of_trades += 1
#                 # adding trade of experiment 2 to trading data
#                 global e2_trade_candles
#                 e2_trade_candles = pd.concat(
#                     [e2_trade_candles, e2_frame])

#             '''e3'''
#             # parabolic SAR
#             parabolic_sar = SAR(high_indicator_candles.tail(
#                 26), low_indicator_candles.tail(26))
#             sar_trend = "bullish"

#             if sar_trend == engulfing_type:
#                 e3_frame = pd.DataFrame({'time': possible_engulfing_candle.name, 'index': e3_number_of_trades, 'engulfing type': engulfing_type, 'SAR trend': sar_trend,  'RSI': rsi_value,
#                                         'VOLUME is bigger: ': h.volume_is_bigger(possible_engulfed_candle, possible_engulfing_candle), 'max profit': max_profit, 'stop loss hit': stop_loss_hit}, index=[possible_engulfing_candle.name])
#                 if max_profit == loss_in_percentage:
#                     e3_number_of_wins += 1
#                     e3_total_win_percentage += max_profit
#                     if h.rsi_is_wrong(engulfing_type, rsi_value):
#                         e3_w_wrong_rsi += 1
#                     if h.volume_is_bigger(possible_engulfed_candle, possible_engulfing_candle):
#                         e3_w_wrong_vol += 1
#                 elif stop_loss_hit:
#                     e3_number_of_losses += 1
#                     e3_total_loss_percentage += loss_in_percentage
#                     if h.rsi_is_wrong(engulfing_type, rsi_value):
#                         e3_l_wrong_rsi += 1
#                     if h.volume_is_bigger(possible_engulfed_candle, possible_engulfing_candle):
#                         e3_l_wrong_vol += 1
#                 else:
#                     e3_number_of_undecided_trades += 1
#                 e3_number_of_trades += 1

#                 # adding trade of experiment 3 to trading data
#                 global e3_trade_candles
#                 e3_trade_candles = pd.concat(
#                     [e3_trade_candles, e3_frame])

#     print("Experiment 1: ")
#     print("Number of Trades: " + str(e1_number_of_trades))
#     print("Number of Ws: " +
#           str(e1_number_of_wins))
#     print("Number of Ws that had an invalid RSI: " +
#           str(e1_w_wrong_rsi) + " . Percentage: " + str(e1_w_wrong_rsi/e1_number_of_wins))
#     print("Number of Ws that had an invalid VOLUME: " +
#           str(e1_w_wrong_vol) + " . Percentage: " + str(e1_w_wrong_vol/e1_number_of_wins))
#     print("Number of Ls: " +
#           str(e1_number_of_losses))
#     print("Number of Ls that had an invalid RSI: " +
#           str(e1_l_wrong_rsi) + " . Percentage: " + str(e1_l_wrong_rsi/e1_number_of_losses))
#     print("Number of Ls that had an invalid VOLUME: " +
#           str(e1_l_wrong_vol) + " . Percentage: " + str(e1_l_wrong_vol/e1_number_of_losses))
#     print("Number of Undecided Trades: " +
#           str(e1_number_of_undecided_trades))
#     print("Total Gain: " +
#           str(e1_total_win_percentage - e1_total_loss_percentage))
#     print("WR: " + str(e1_number_of_wins /
#           e1_number_of_trades))

#     print("\nExperiment 2: ")
#     print("Number of Trades: " + str(e2_number_of_trades))
#     print("Number of Ws: " +
#           str(e2_number_of_wins))
#     print("Number of Ws that had an invalid RSI: " +
#           str(e2_w_wrong_rsi) + " . Percentage: " + str(e2_w_wrong_rsi/e2_number_of_wins))
#     print("Number of Ws that had an invalid VOLUME: " +
#           str(e2_w_wrong_vol) + " . Percentage: " + str(e2_w_wrong_vol/e2_number_of_wins))
#     print("Number of Ls: " +
#           str(e2_number_of_losses))
#     print("Number of Ls that had an invalid RSI: " +
#           str(e2_l_wrong_rsi) + " . Percentage: " + str(e2_l_wrong_rsi/e2_number_of_losses))
#     print("Number of Ls that had an invalid VOLUME: " +
#           str(e2_l_wrong_vol) + " . Percentage: " + str(e2_l_wrong_vol/e2_number_of_losses))
#     print("Number of Undecided Trades: " +
#           str(e2_number_of_undecided_trades))
#     print("Total Gain: " +
#           str(e2_total_win_percentage - e2_total_loss_percentage))
#     print("WR: " + str(e2_number_of_wins /
#           e2_number_of_trades))

#     print("\nExperiment 3: ")
#     print("Number of trades: " + str(e3_number_of_trades))
#     print("Number of winning trades: " +
#           str(e3_number_of_wins))
#     print("Number of Ws that had an invalid RSI: " +
#           str(e3_w_wrong_rsi) + " . Percentage: " + str(e3_w_wrong_rsi/e3_number_of_wins))
#     print("Number of Ws that had an invalid VOLUME: " +
#           str(e3_w_wrong_vol) + " . Percentage: " + str(e3_w_wrong_vol/e3_number_of_wins))
#     print("Number of Ls: " +
#           str(e3_number_of_losses))
#     print("Number of Ls that had an invalid RSI: " +
#           str(e3_l_wrong_rsi) + " . Percentage: " + str(e3_l_wrong_rsi/e3_number_of_losses))
#     print("Number of Ls that had an invalid VOLUME: " +
#           str(e3_l_wrong_vol) + " . Percentage: " + str(e3_l_wrong_vol/e3_number_of_losses))
#     print("Number of Undecided Trades: " +
#           str(e3_number_of_undecided_trades))
#     print("Total Gain: " +
#           str(e3_total_win_percentage - e3_total_loss_percentage))
#     print("WR: " + str(e3_number_of_wins /
#           e3_number_of_trades))

#     return e1_trade_candles, e2_trade_candles, e3_trade_candles


# e1_trades, e2_trades, e3_trades = study_engulfing_candles_no_trend(
#     candles)
# e1_trades.sort_values('stop loss hit').to_csv(
#     "e1Data.csv", encoding='utf-8')
# e2_trades.sort_values('stop loss hit').to_csv(
#     "e2Data.csv", encoding='utf-8')
# e3_trades.sort_values('stop loss hit').to_csv(
#     "e3Data.csv", encoding='utf-8')

study_df = pd.DataFrame()

# -------------- FAILED EXPERIMENT -----------------
# def study_engulfing_candles(candles_df):
#     number_of_candles = candles_df.shape[0]
#     global number_of_trades
#     for i in range(number_of_candles-1):
#         possible_engulfed_candle = candles_df.iloc[i]
#         possible_engulfing_candle = candles_df.iloc[i+1]

#         engulfing_type = h.type_of_engulfing(
#             possible_engulfed_candle, possible_engulfing_candle)
#         if engulfing_type != None:
#             stop_loss_price = h.calc_stop_loss(
#                 engulfing_type, possible_engulfed_candle, possible_engulfing_candle)
#             _, loss_in_percentage = h.calc_loss(
#                 possible_engulfing_candle.close, stop_loss_price)

#             if loss_in_percentage > 0.25:
#                 indicator_candles = h.get_candles_for_indicator(
#                     client, symbol, 5, 400, possible_engulfing_candle)
#                 close_indicator_candles = indicator_candles["close"]
#                 high_indicator_candles = indicator_candles["high"]
#                 low_indicator_candles = indicator_candles["low"]

#                 rsi_value = RSI(close_indicator_candles.tail(70))[69]

#                 ema_trend, _ = h.return_emas_trend(
#                     close_indicator_candles)

#                 parabolic_sar = SAR(high_indicator_candles.tail(
#                     26), low_indicator_candles.tail(26))
#                 sar_trend = "bullish"
#                 sar_distance = possible_engulfing_candle.low - \
#                     parabolic_sar[25]
#                 sar_distance_in_percentage = sar_distance/possible_engulfing_candle.low * 100
#                 if(parabolic_sar[25] > possible_engulfing_candle.high):
#                     sar_trend = "bearish"
#                     sar_distance = parabolic_sar[25] - \
#                         possible_engulfing_candle.high
#                     sar_distance_in_percentage = sar_distance/possible_engulfing_candle.high * 100

#                 trade_candles = h.get_1m_follow_up_candles_for_candle(
#                     client, possible_engulfing_candle, 100)
#                 result, stop_loss_hit = h.max_take_profit(
#                     engulfing_type, trade_candles, stop_loss_price, possible_engulfing_candle.close)
#                 if stop_loss_hit == True:
#                     result = loss_in_percentage

#                 if (stop_loss_hit == False and loss_in_percentage == result) or stop_loss_hit == True:
#                     frame_to_concat = pd.DataFrame({'time': possible_engulfing_candle.name, 'index': number_of_trades, 'engulfing type': engulfing_type, 'EMAs': ema_trend, 'SAR': sar_trend, 'SAR distance': sar_distance_in_percentage, "Trends match": (engulfing_type == ema_trend) and (engulfing_type == sar_trend),
#                                                     'RSI': rsi_value, 'Bigger Volume': h.volume_is_bigger(possible_engulfed_candle, possible_engulfing_candle),
#                                                     'stop loss': loss_in_percentage,  'result': result - 0.2, 'stop loss hit': stop_loss_hit}, index=[possible_engulfing_candle.name])
#                     global study_df
#                     study_df = pd.concat([study_df, frame_to_concat])
#                 number_of_trades += 1


# candles = h.get_candles_dataframe(
#     client, "BTCUSDT", "5m", "2022-04-01 09:00:00", "2022-04-14 09:00:00")
# study_engulfing_candles(candles)
# study_df.sort_values('stop loss hit').to_csv("finalData.csv")

# e1_t = study_df.shape[0]
# e1_w = study_df.loc[study_df['stop loss hit'] == False].shape[0]
# e1_l = study_df.loc[study_df['stop loss hit'] == True].shape[0]
# print("T: " + str(e1_t))
# print("W: " + str(e1_w))
# print("L: " + str(e1_l))
# print("WR: " + str(e1_w/e1_t))
# print("P: " + str(study_df['result'].sum()))

# e2_filter = (study_df['EMAs'] == study_df['engulfing type'])
# e2_df = study_df.loc[e2_filter]
# e2_t = e2_df.shape[0]
# e2_w = e2_df.loc[e2_df['stop loss hit'] == False].shape[0]
# e2_l = e2_df.loc[e2_df['stop loss hit'] == True].shape[0]
# print("T: " + str(e2_t))
# print("W: " + str(e2_w))
# print("L: " + str(e2_l))
# print("WR: " + str(e2_w/e2_t))
# print("P: " + str(e2_df['result'].sum()))
# e2_df.sort_values('stop loss hit').to_csv("e2.csv")

# e3_filter = (study_df['SAR'] == study_df['engulfing type'])
# e3_df = study_df.loc[e3_filter]
# e3_t = e3_df.shape[0]
# e3_w = e3_df.loc[e3_df['stop loss hit'] == False].shape[0]
# e3_l = e3_df.loc[e3_df['stop loss hit'] == True].shape[0]
# print("T: " + str(e3_t))
# print("W: " + str(e3_w))
# print("L: " + str(e3_l))
# print("WR: " + str(e3_w/e3_t))
# print("P: " + str(e3_df['result'].sum()))
# e3_df.sort_values('stop loss hit').to_csv("e3.csv")


# e4_filter = ((study_df['SAR'] == study_df['engulfing type']) & (
#     study_df['EMAs'] == study_df['engulfing type']))
# e4_df = study_df.loc[e4_filter]
# e4_t = e4_df.shape[0]
# e4_w = e4_df.loc[e4_df['stop loss hit'] == False].shape[0]
# e4_l = e4_df.loc[e4_df['stop loss hit'] == True].shape[0]
# print("T: " + str(e4_t))
# print("W: " + str(e4_w))
# print("L: " + str(e4_l))
# print("WR: " + str(e4_w/e4_t))
# print("P: " + str(e4_df['result'].sum()))
# e4_df.sort_values('stop loss hit').to_csv("e4.csv")

trade_df = pd.DataFrame()
number_of_trades = 0


def trade_with_ddm(candles):
    number_of_candles = candles.shape[0]
    global number_of_trades

    # represents closing price of candles
    close_candles = candles["close"]
    high_candles = candles["high"]
    low_candles = candles["low"]

    # building EMAs
    ema_20 = EMA(close_candles, timeperiod=20)
    ema_50 = EMA(close_candles, timeperiod=50)
    ema_200 = EMA(close_candles, timeperiod=200)

    # building SAR
    parabolic_sar = SAR(high_candles, low_candles)

    # we want to start whenever we are at the beginning of a relatively neutral market, so we are looking for a non trending EMA structure
    starting_candle = 398
    entering_trade_timestamp = 0
    while entering_trade_timestamp == 0:
        if(not h.emas_are_bearish_lined(ema_20.iloc[starting_candle], ema_50.iloc[starting_candle], ema_200.iloc[starting_candle])
                and not h.emas_are_bullish_lined(ema_20.iloc[starting_candle], ema_50.iloc[starting_candle], ema_200.iloc[starting_candle])):
            entering_trade_timestamp = -1
        else:
            starting_candle += 1

    ddm_score = 0
    closing_trade_timestamp = -1
    profit_trigger_price = 0
    loss_trigger_price = 0
    trade_trend = None

    for i in range(starting_candle, number_of_candles - 1):
        current_candle = candles.iloc[i]
        last_candle = candles.iloc[i-1]
        if entering_trade_timestamp == 0:
            if(not h.emas_are_bearish_lined(ema_20.iloc[starting_candle], ema_50.iloc[starting_candle], ema_200.iloc[starting_candle])
                    and not h.emas_are_bullish_lined(ema_20.iloc[starting_candle], ema_50.iloc[starting_candle], ema_200.iloc[starting_candle])):
                entering_trade_timestamp = -1

        elif(entering_trade_timestamp < 0):

            engulfing_trend = h.type_of_engulfing(
                last_candle, current_candle)

            ema_trend = None
            if h.emas_are_bearish_lined(ema_20.iloc[i], ema_50.iloc[i], ema_200.iloc[i]) == True:
                ema_trend = "bearish"
            elif h.emas_are_bullish_lined(ema_20.iloc[i], ema_50.iloc[i], ema_200.iloc[i]) == True:
                ema_trend = "bullish"

            if engulfing_trend != None:
                engulfing_score = h.get_score(
                    engulfing_trend, ema_trend)
                ddm_score += engulfing_score

            sar_trend = h.check_sar_trend(
                last_candle, parabolic_sar.iloc[i-1], current_candle, parabolic_sar.iloc[i])
            if sar_trend != None:
                sar_score = h.get_score(sar_trend, ema_trend)
                ddm_score += sar_score

            ddm_long_reached = h.ddm_reached_long(ddm_score)
            ddm_short_reached = h.ddm_reached_short(ddm_score)
            if(ddm_long_reached or ddm_short_reached):
                trade_trend = "bullish"
                if ddm_short_reached:
                    trade_trend = "bearish"
                profit_trigger_price = h.calc_take_profit(
                    trade_trend, current_candle.close)
                loss_trigger_price = h.calc_loss_price(
                    trade_trend, current_candle.close)
                entering_trade_timestamp = int(
                    candles.iloc[i + 1].name.timestamp())*1000
        else:
            if trade_trend == "bullish":
                outcome = h.get_long_trade_outcome(
                    current_candle, profit_trigger_price, loss_trigger_price)
                if outcome != None:
                    closing_trade_timestamp = int(
                        candles.iloc[i+1].name.timestamp()) * 1000
                    trade_duration_in_minutes = (
                        closing_trade_timestamp - entering_trade_timestamp) / 60000
                    drift_rate = math.sqrt(
                        2500 + trade_duration_in_minutes*trade_duration_in_minutes)
            if trade_trend == "bearish":
                outcome = h.get_short_trade_outcome(
                    current_candle, profit_trigger_price, loss_trigger_price)
                if outcome != None:
                    closing_trade_timestamp = int(
                        candles.iloc[i+1].name.timestamp()) * 1000
                    trade_duration_in_minutes = (
                        closing_trade_timestamp - entering_trade_timestamp) / 60000
                    drift_rate = math.sqrt(
                        2500 + trade_duration_in_minutes*trade_duration_in_minutes)
            if outcome != None:
                trade_duration_in_minutes = (
                    closing_trade_timestamp - entering_trade_timestamp) / 60000
                frame_to_concat = pd.DataFrame({'opening time': pd.to_datetime(entering_trade_timestamp, unit='ms'), 'closing time': pd.to_datetime(
                    closing_trade_timestamp, unit='ms'), 'drift rate': drift_rate, 'result': outcome, 'trade duration (min)': trade_duration_in_minutes}, index=[number_of_trades+1])
                global trade_df
                trade_df = pd.concat([trade_df, frame_to_concat])
                entering_trade_timestamp = 0
                number_of_trades += 1
                ddm_score = 0
    return trade_df


candles = h.get_candles_dataframe(
    client, "BTCUSDT", "5m", "2021-01-01 09:00:00", "2022-01-01 09:00:00")
trade_df = trade_with_ddm(candles)
trade_df.sort_values('result').to_csv("ddmResults.csv")

# filter out winning trades
w_filter = trade_df['result'] == "profit"
winning_trades_df = trade_df.loc[w_filter]
number_of_w = winning_trades_df.shape[0]

# filter out winning trades
l_filter = trade_df['result'] == "loss"
losing_trades_df = trade_df.loc[l_filter]
number_of_l = losing_trades_df.shape[0]

print("T: " + str(trade_df.shape[0]))
print("W: " + str(winning_trades_df.shape[0]))
print("L: " + str(losing_trades_df.shape[0]))
print("WR: " + str(number_of_w/trade_df.shape[0]))
print("Average Trade Duration: " +
      str(trade_df['trade duration (min)'].sum()/trade_df.shape[0]))
