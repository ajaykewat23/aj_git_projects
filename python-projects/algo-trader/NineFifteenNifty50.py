import os
import sys
import threading
import time
from datetime import date, datetime
import logging

from dateutil.utils import today
from dhanhq import dhanhq
import websockets
import pandas as pd

candle_list = {}
five_min_candle_list = {}
five_minute_counter = 0

fifteen_min_candle_list = {}
fifteen_minute_counter = 0

hourly_min_candle_list = {}
hourly_min_counter = 0

sleep_time_coverup = 1

# change below for temp run to 1, else set as 60
sleep_time_normal = 1

put_option_premium_id = 0
call_option_premium_id = 0

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(funcName)s:%(lineno)d - %(levelname)s - %(message)s',
                    filename='nifty50.log',  # Logs will be saved to app.log
                    filemode='a')  # Overwrite the log file each time

# Create a logger
logger = logging.getLogger(__name__)

# Create and configure the second logger
logger2 = logging.getLogger('Logger2')
logger2.setLevel(logging.INFO)
handler2 = logging.FileHandler('trade_book_nifty.log')
formatter2 = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler2.setFormatter(formatter2)
logger2.addHandler(handler2)

def get_connection():
    t = time.localtime()
    # print('hour ', t.tm_hour, 't-min ', t.tm_min)
    hour = t.tm_hour
    minute = t.tm_min

    current_date = datetime.now().date()

    client_id = "your_client_id"
    access_token = "your_access_token"
    dhan = dhanhq(client_id, access_token)
    # print('Connection Established..!!')
    logger.info('Connection Established..!!')
    return dhan


dhan_con = get_connection()


def get_myHoldings(dhan_con):
    data_holdings = dhan_con.get_holdings()
    print(data_holdings)
    logger.info(data_holdings)
    # check if Holdings available.


def get_market_heartbeat(dhan_con, scrip_id, market, scrip_code, counter):
    time.sleep(2)
    out_test = dhan_con.intraday_daily_minute_charts(
        security_id=scrip_id,
        exchange_segment=market,
        instrument_type=scrip_code
    )

    # print('out_test----', out_test)

    ohlc_list = parse_oclh_data_minute(out_test, counter)
    return ohlc_list


def parse_oclh_data_minute(out_test, counter):
    indented_history_data = pd.DataFrame(out_test['data'])

    # print('Printing daily chart data...')

    open_col = indented_history_data['open']
    high_col = indented_history_data['high']
    low_col = indented_history_data['low']
    close_col = indented_history_data['close']

    # min_counter=10
    # print('Open ', open_col[min_counter], ': high ', high_col[min_counter], ': low ', low_col[min_counter], ': close ', close_col[min_counter])

    # for num in range(0, 20):
    #     # Your code here
    #     print('#', num, 'Open ', open_col[num], ': high ', high_col[num], ': low ', low_col[num], ': close ',
    #           close_col[num])

    # print(open_value, '---')
    ohlc_list = {'open': open_col[counter], 'high': high_col[counter], 'low': low_col[counter],
                 'close': close_col[counter]}

    # print(ohlc_list)

    return ohlc_list


def candle_5_mins(candle_list, start, end, candle_length, candle_counter):
    global five_minute_counter, fifteen_minute_counter, hourly_min_counter

    # print('start --', start,  ' -- end -- ', end)
    stack_data_Open = candle_list[start][0]
    stack_data_close = candle_list[end][3]

    # print('stack_data_Open - ', stack_data_Open)
    # print('stack_data_close - ', stack_data_close)

    all_values_array = []
    for loop_count in range(start, end + 1):
        for inner_count in range(0, 4):
            # print('loop_count - ', loop_count, 'inner_count - ',inner_count, '--', candle_list[loop_count][inner_count])
            all_values_array.append(candle_list[loop_count][inner_count])

    all_values_array.sort()
    # print('start --', start,  ' -- end -- ', end, 'all_values_array ---', len(all_values_array), all_values_array)
    stack_data_high = all_values_array[-1]
    stack_data_low = all_values_array[0]
    # print("The highest number is:", stack_data_high)
    # print("The Lowest number is:", stack_data_low)

    candle_values = [stack_data_Open, stack_data_high, stack_data_low, stack_data_close]

    # print values of 5 min candle values
    if candle_length == 5:
        print("5 Min Candle value - OHLC - ", stack_data_Open, stack_data_high, stack_data_low, stack_data_close)
        logger.info(f'{'5 Min Candle value - OHLC - '}{stack_data_Open}{' -- '}{stack_data_high}'
                    f'{' -- '}{stack_data_low}{' -- '}{stack_data_close}')
        five_min_candle_list[five_minute_counter] = candle_values
        five_minute_counter += 1

    if candle_length == 15:
        print("15 Min Candle value - OHLC - ", stack_data_Open, stack_data_high, stack_data_low, stack_data_close)
        logger.info(f'{'15 Min Candle value - OHLC - '}{stack_data_Open}{' -- '}{stack_data_high}'
                    f'{' -- '}{stack_data_low}{' -- '}{stack_data_close}')
        fifteen_min_candle_list[fifteen_minute_counter] = candle_values
        fifteen_minute_counter += 1

    if candle_length == 60:
        print("60 Min Candle value - OHLC - ", stack_data_Open, stack_data_high, stack_data_low, stack_data_close)
        logger.info(f'{'60 Min Candle value - OHLC - '}{stack_data_Open}{' -- '}{stack_data_high}'
                    f'{' -- '}{stack_data_low}{' -- '}{stack_data_close}')
        hourly_min_candle_list[hourly_min_counter] = candle_values
        hourly_min_counter += 1


def get_all_market_minute_feed(dhan_con, security_id):
    # print('get_all_market_minute_feed..!!')

    out_test = dhan_con.intraday_daily_minute_charts(
        security_id=security_id,
        exchange_segment='IDX_I',
        instrument_type='INDEX'
    )

    indented_history_data = pd.DataFrame(out_test['data'])

    # print('indented_history_data ', indented_history_data)
    total_min_candle_passed = len(indented_history_data)

    # print('length - ', total_min_candle_passed)
    return total_min_candle_passed


def apply_fifteen_min_strategy(list_of_two_candles, second_close, first_close,
                               first_high, first_low, first_open, scipt_id,
                               strategy, candle_end_counter, sl_point, target_point):
    global first_fifteen_min_candle_open
    global first_fifteen_min_candle_close
    global second_fifteen_min_candle_close
    global first_fifteen_min_candle_high
    global first_fifteen_min_candle_low

    # first_fifteen_min_candle_open = first_open
    # first_fifteen_min_candle_close = first_close
    # second_fifteen_min_candle_close = second_close

    break_flag = 'X'
    data_flag = 'X'
    print('len(list_of_two_candles) - ', len(list_of_two_candles))

    # get all values of candles.
    if len(list_of_two_candles) >= 2:

        first_fifteen_min_candle_open = first_open
        first_fifteen_min_candle_close = first_close
        second_fifteen_min_candle_close = second_close
        first_fifteen_min_candle_high = first_high
        first_fifteen_min_candle_low = first_low

        data_flag = 'Y'
        print('Data loaded for strategy for 2 15 min candles')

        print('-------xxx----', second_fifteen_min_candle_close, first_fifteen_min_candle_close,
              first_fifteen_min_candle_close, first_fifteen_min_candle_open, first_fifteen_min_candle_high,
              first_fifteen_min_candle_low)


    else:
        print('Data not found for 15 min strategy completion')
        break_flag = 'Y'

    if data_flag == 'Y':
        # code for checking the logic of conditions to be met.
        print('code for checking the logic of conditions to be met.')

        # check for conditions if met

        cur_candle_counter = 0

        total_passed_candle = get_all_market_minute_feed(dhan_con, scipt_id)

        print('second_fifteen_min_candle_close - ', second_fifteen_min_candle_close,
              ' first_fifteen_min_candle_high - ', first_fifteen_min_candle_high,
              ' first_fifteen_min_candle_close - ', first_fifteen_min_candle_close,
              ' first_fifteen_min_candle_open - ', first_fifteen_min_candle_open,
              ' first_fifteen_min_candle_low - ', first_fifteen_min_candle_low)

        # TEMP TESTING START
        # buy_position(total_passed_candle, scipt_id, call_option_premium_id, 'CALL')
        #
        # print('Stop the code here...!! 120 sec')
        # time.sleep(120)
        # TEMP TESTING END

        if ((second_fifteen_min_candle_close > first_fifteen_min_candle_high) and
                (first_fifteen_min_candle_close < first_fifteen_min_candle_open)):
            print('01---Apply CE position fifteen_min_strategy, 2nd candle closed above high level, first RED, 2nd GREEN candle')
            logger.info(
                '01---Apply CE position fifteen_min_strategy, 2nd candle closed above high level, first RED, 2nd GREEN candle')
            # buy_position('CALL', total_passed_candle, 13)
            buy_position(total_passed_candle, scipt_id, call_option_premium_id,
                         'CALL', candle_end_counter, sl_point, target_point, 'fifteen_min_strategy')
            # print(second_fifteen_min_candle_close, first_fifteen_min_candle_close,
            #       first_fifteen_min_candle_close, first_fifteen_min_candle_open, sl_point, target_point)

        if ((second_fifteen_min_candle_close > first_fifteen_min_candle_close)
                and (first_fifteen_min_candle_close > first_fifteen_min_candle_open)):
            print('02---Apply CE position strategy, 2nd candle closed above close level first GREEN, 2nd GREEN candle')
            logger.info(
                '02---Apply CE position strategy, 2nd candle closed above close level first GREEN, 2nd GREEN candle')
            # buy_call_position(total_passed_candle, scipt_id)
            buy_position(total_passed_candle, scipt_id, call_option_premium_id,
                         'CALL', candle_end_counter, sl_point, target_point, 'fifteen_min_strategy')

        elif ((second_fifteen_min_candle_close < first_fifteen_min_candle_low) and
              (first_fifteen_min_candle_close > first_fifteen_min_candle_open)):
            print('03---Apply PE position strategy, 2nd candle closed below close level, first GREEN, 2nd RED candle')
            logger.info(
                '03---Apply PE position strategy, 2nd candle closed below close level, first GREEN, 2nd RED candle')
            # buy_position('PUT', total_passed_candle, 13)
            buy_position(total_passed_candle, scipt_id, put_option_premium_id,
                         'PUT', candle_end_counter, sl_point, target_point, 'fifteen_min_strategy')

        elif ((second_fifteen_min_candle_close < first_fifteen_min_candle_close)
              and (first_fifteen_min_candle_close < first_fifteen_min_candle_open)):
            print('04---Apply PE position strategy, 2nd candle closed below first close, first RED, second RED')
            logger.info('04---Apply PE position strategy, 2nd candle closed below first close, first RED, second RED')
            # buy_put_position(total_passed_candle, scipt_id)
            buy_position(total_passed_candle, scipt_id, put_option_premium_id,
                         'PUT', candle_end_counter, sl_point, target_point, 'fifteen_min_strategy')

        else:
            print('05--- No breakout found for CE or PE in this fifteen_min_strategy')
            logger.info('05--- No breakout found for CE or PE in this fifteen_min_strategy')

    else:
        # exit the strategy
        print('exit the first_fifteen_minute_breakout strategy')
        logger.info('exit the first_fifteen_minute_breakout strategy')

    print('first_fifteen_minute_breakout end.. !!')
    logger.info('first_fifteen_minute_breakout end.. !!')


def first_fifteen_minute_breakout():
    print('Strategy-1: FirstFifteenMinuteBReakout is running ')
    logger.info('Strategy-1: FirstFifteenMinuteBReakout is running ')
    logger2.info('Strategy-1: FirstFifteenMinuteBReakout is running ')
    global local_15_counter, first_fifteen_min_candle_open
    global current_min_counter
    global first_flag
    global second_flag
    global scipt_id

    scipt_id = 13

    # check at 9:31 AM, 1st fifteen Minute Candle value
    # Record  Open_1, High_1, Low_1 and Close_1
    # At Next Fifteen Minute Closure i.e., at 9:46
    # CHeck Open_2, High_2, Low_2 and Close_2
    # apply strategy - If Close_2 > High_1, Trade for CALL POSITION

    # If Close_2 < Low_1 , Trade for PUT POSITION

    # For taking POSITION, GET THE STRIKE PRICE
    # SET SL as 10% of the STRIKE PRICE
    # SET TARGET as 15% of the STRIKE PRICE

    # ----

    first_flag = 0
    second_flag = 0

    go_ahead_flag = 'X'

    second_fifteen_min_candle_open = 0
    first_fifteen_min_candle_high = 0
    first_fifteen_min_candle_low = 0
    first_fifteen_min_candle_close = 0

    second_fifteen_min_candle_open = 0
    second_fifteen_min_candle_high = 0
    second_fifteen_min_candle_low = 0
    second_fifteen_min_candle_close = 0

    # check length of 15min candle.
    # for cnt in range(35):

    # minute candle counter is 35 for 25 mins of history tracking

    length_15_min = 0
    while 1 == 1:
        length_15_min = len(fifteen_min_candle_list)
        if length_15_min > 1:
            break
        else:
            print('.', end='')
            time.sleep(5)

    print('final length of 15 mins candle.', length_15_min)
    strategy_interval = 33

    old_fifteen_min_length = 0

    flag_fifteen = 'T'

    list_cur_candle = []
    list_of_two_candles = []

    while 1 == 1:
        length_15_min = len(fifteen_min_candle_list)
        # print(' len(15min) - ', length_15_min, end='')

        if length_15_min == 1 and first_flag == 0:
            arr_index = 0
            # print('15 min candle count is ', length_15_min)
            # apply rules for CE or PE position

            first_fifteen_min_candle_open = fifteen_min_candle_list[arr_index][0]
            list_cur_candle.append(first_fifteen_min_candle_open)
            first_fifteen_min_candle_high = fifteen_min_candle_list[arr_index][1]
            list_cur_candle.append(first_fifteen_min_candle_high)
            first_fifteen_min_candle_low = fifteen_min_candle_list[arr_index][2]
            list_cur_candle.append(first_fifteen_min_candle_low)
            first_fifteen_min_candle_close = fifteen_min_candle_list[arr_index][3]
            list_cur_candle.append(first_fifteen_min_candle_close)

            list_of_two_candles.append(list_cur_candle)

            print('--1-open ', first_fifteen_min_candle_open, ' High ', first_fifteen_min_candle_high, ' low - '
                  , first_fifteen_min_candle_low, ' close - ', first_fifteen_min_candle_close)

            first_flag = 1

        print(first_flag, ' first flag', second_flag, ' second flag')

        if length_15_min >= 2:

            print('15 min candle count is ', length_15_min)
            # apply rules for CE or PE position

            if first_flag == 0:
                arr_index = 0

                first_fifteen_min_candle_open = fifteen_min_candle_list[arr_index][0]
                list_cur_candle.append(first_fifteen_min_candle_open)

                first_fifteen_min_candle_high = fifteen_min_candle_list[arr_index][1]
                list_cur_candle.append(first_fifteen_min_candle_high)

                first_fifteen_min_candle_low = fifteen_min_candle_list[arr_index][2]
                list_cur_candle.append(first_fifteen_min_candle_low)

                first_fifteen_min_candle_close = fifteen_min_candle_list[arr_index][3]
                list_cur_candle.append(first_fifteen_min_candle_close)

                list_of_two_candles.append(list_cur_candle)

                print('--1-open ', first_fifteen_min_candle_open, ' High ', first_fifteen_min_candle_high, ' low - '
                      , first_fifteen_min_candle_low, ' close - ', first_fifteen_min_candle_close)
                first_flag = 1

            # print('list_of_two_candles -- ', len(list_of_two_candles))

            arr_index = 1
            print('15 min candle count is ', length_15_min)
            # apply rules for CE or PE position

            if second_flag == 0:
                arr_index = 1

                second_fifteen_min_candle_open = fifteen_min_candle_list[arr_index][0]
                list_cur_candle.append(second_fifteen_min_candle_open)

                second_fifteen_min_candle_high = fifteen_min_candle_list[arr_index][1]
                list_cur_candle.append(second_fifteen_min_candle_high)

                second_fifteen_min_candle_low = fifteen_min_candle_list[arr_index][2]
                list_cur_candle.append(second_fifteen_min_candle_low)

                second_fifteen_min_candle_close = fifteen_min_candle_list[arr_index][3]
                list_cur_candle.append(second_fifteen_min_candle_close)

                list_of_two_candles.append(list_cur_candle)

                first_flag = 1

                # print('list_of_two_candles -- ', len(list_of_two_candles))

                print('--2-open ', second_fifteen_min_candle_open, ' High ', second_fifteen_min_candle_high, ' low - '
                      , second_fifteen_min_candle_low, ' close - ', second_fifteen_min_candle_close)

            # print('wait 5 sec.')
            second_flag = 1
            go_ahead_flag = 'T'
            # time.sleep(5)
            break

        print('.', end='')
        time.sleep(5)

    print('After break statement.')

    # apply strategy - If Close_2 > High_1, Trade for CALL POSITION
    candle_end_counter = 60
    print('Applying strategy..!!', ' first flag - ', first_flag,
          ' second flag ', second_flag, ' end candle of this strategy ', candle_end_counter)

    logger.info(f'{'Applying strategy..!!  first flag - '}{first_flag}'
                f'{' second flag '}{second_flag}{' end candle of this strategy '}{candle_end_counter}')
    # print('length of 15 min candles , before strategy..', length_15_min)
    # print('list_of_two_candles --- ', list_of_two_candles)
    print('-------', second_fifteen_min_candle_close, first_fifteen_min_candle_close,
          first_fifteen_min_candle_close, first_fifteen_min_candle_open)

    # THIS IS TEMP, SET THIS TO 4
    if length_15_min < 4:
        if first_flag == 1 and second_flag == 1:
            logger.info('Applying 15 min breakout strategy')
            apply_fifteen_min_strategy(list_of_two_candles, second_fifteen_min_candle_close,
                                       first_fifteen_min_candle_close, first_fifteen_min_candle_high,
                                       first_fifteen_min_candle_low, first_fifteen_min_candle_open,
                                       scipt_id, 'REAL', candle_end_counter, 16, 24)
        else:
            print('conditions do not meet for strategy apply')
            logger.info('conditions do not meet for strategy apply')
            print('End of 15 min breakout strategy... !!')
            logger.info('End of 15 min breakout strategy... !!')
            logger2.info('End of 15 min breakout strategy...')
            sys.exit()
    else:
        print('conditions do not meet for strategy apply')
        logger.info('conditions do not meet for strategy apply')
        print('End of 15 min breakout strategy... !!')
        logger.info('End of 15 min breakout strategy... !!')
        logger2.info('End of 15 min breakout strategy...')

        sys.exit()

    # RUN THIS ONLY TO TEST THE STRATEGY
    # if first_flag == 1 and second_flag == 1:
    #     apply_fifteen_min_strategy(list_of_two_candles, second_fifteen_min_candle_close,
    #                                first_fifteen_min_candle_close, first_fifteen_min_candle_high,
    #                                first_fifteen_min_candle_low, first_fifteen_min_candle_open,
    #                                scipt_id, 'REAL')
    # END OF TEST STRATEGY


def apply_hour_end_strategy(hour_open, hour_high, hour_low, hour_close,
                            len_hour_candle, scrip_id, strategy, break_candle_counter,
                            sl_point, target_point):
    global first_hour_candle_open
    global first_hour_candle_high
    global first_hour_candle_low
    global first_hour_candle_close
    global length_hour_candle, trade_complete_flag

    logger.info('Start of apply_hour_end_strategy')
    length_hour_candle = len_hour_candle
    print('length_hour_candle----', length_hour_candle, ' break_candle_counter ', break_candle_counter)

    data_flag = 'X'
    trade_complete_flag = 'N'

    # get all values of candles.
    if length_hour_candle >= 1:
        first_hour_candle_open = hour_open
        first_hour_candle_high = hour_high
        first_hour_candle_low = hour_low
        first_hour_candle_close = hour_close

        data_flag = 'Y'
        print('Data loaded for hour end strategy for 60min candle')

        print('----60min data-O-C----', first_hour_candle_open, first_hour_candle_high,
              first_hour_candle_low, first_hour_candle_close, 'data flag - ', data_flag)
    else:
        print('Data not found for 60 min strategy completion')

    if data_flag == 'Y':
        # code for checking the logic of conditions to be met.
        print('code for checking the logic of conditions to be met for hour strategy')

        # check for conditions if met

        cur_candle_counter = 0

        total_passed_candle = get_all_market_minute_feed(dhan_con, scipt_id)
        print('Total candle passed ', total_passed_candle)

        # Get the length of 15min candle,  by 10:15+ mins, the len should be 4,
        # Check in Loop the closing of 15 min candle, If close of 15min candle break HIGH of HOUR, CALL
        # IF 15min close below low of hour, go for PUT

        len_15_min_list = len(fifteen_min_candle_list)
        cur_len_15min_candle = len_15_min_list
        new_length_15min_candle = 0
        while 1 == 1:

            # print('inside while check loop')
            # Get the length of 15min candle,  by 10:15+ mins, the len should be 4,

            if trade_complete_flag == 'Y':
                print('Hour breakout strategy Completed.., trade_complete_flag ', trade_complete_flag)
                break

            if total_passed_candle > break_candle_counter:
                print('Hour breakout strategy Completed.. beyond 1:15 PM')
                break

            len_15_min_list = len(fifteen_min_candle_list)
            # print('len - len_15_min_list ', len_15_min_list, ' cur_len_15min_candle ', cur_len_15min_candle,
            #       ' new length ', )

            if len_15_min_list > cur_len_15min_candle:
                time.sleep(2)
                print('Length---changed...')
                cur_len_15min_candle = len_15_min_list

                # get the values of the 15 min last candle, OHLC
                fifteen_min_latest_candle = fifteen_min_candle_list[len_15_min_list - 1]
                fifteen_open = fifteen_min_latest_candle[0]
                fifteen_high = fifteen_min_latest_candle[1]
                fifteen_low = fifteen_min_latest_candle[2]
                fifteen_close = fifteen_min_latest_candle[3]

                print('15 open ', fifteen_open, ' 15 close - ', fifteen_close,
                      ' hour low - ', first_hour_candle_low, ' 15 low - ', fifteen_low,
                      ' 15 high - ', fifteen_high, ' hour high - ', first_hour_candle_high)

                # check if 15min high is closed above hour HIGH, then take CE
                # check if 15min low is closed below hour LOW, take PE

                if fifteen_close > first_hour_candle_high:
                    print('01---Apply CE Hour position strategy, 15min candle closed above HOUR HIGH level')
                    logger.info('01---Apply CE Hour position strategy, 15min candle closed above HOUR HIGH level')
                    buy_position(total_passed_candle, scipt_id,
                                 call_option_premium_id, 'CALL', break_candle_counter,
                                 sl_point, target_point, 'first_hour_breakout')
                    trade_complete_flag = 'Y'
                    break

                elif fifteen_close < first_hour_candle_low:
                    print('02---Apply PE Hour position strategy, 15min candle closed below HOUR LOW level')
                    logger.info('02---Apply PE Hour position strategy, 15min candle closed below HOUR LOW level')
                    buy_position(total_passed_candle, scipt_id,
                                 put_option_premium_id, 'PUT', break_candle_counter,
                                 sl_point, target_point, 'first_hour_breakout')
                    trade_complete_flag = 'Y'
                    break
                elif len_15_min_list >= 16:
                    print('03---Condition did not meet.. End Time reached for first_hour_breakout, 1:15 PM')
                    trade_complete_flag = 'Y'
                    break
                else:
                    print('03---Condition did not meet for first_hour_breakout.. awaiting next loop.')
            else:
                # print('length not changed.. wait..')
                print(',', end='')

            # print(',', end='')
            # DO NOT CHANGE BELOW TIME, NIFTY 5 SEC
            time.sleep(5)

        print('Hour strategy Exit---')
        logger.info('Hour strategy Exit---')

    else:
        # exit the strategy
        print('exit the Hour End strategy')
        logger.info('exit the Hour End strategy')

        # print('Hour End strategy end.. !!')
        # logger.info('exit the Hour End strategy')
        # return 'X'


def first_hour_breakout():
    print('Strategy-2: first_hour_breakout is running ')
    logger.info('Strategy-2: first_hour_breakout is running ')
    logger2.info('Strategy-2: first_hour_breakout is running ')
    global scipt_id
    global hour_flag
    global first_hour_min_candle_open
    global first_hour_min_candle_high
    global first_hour_min_candle_low
    global first_hour_min_candle_close

    first_hour_min_candle_open = 0
    first_hour_min_candle_high = 0
    first_hour_min_candle_low = 0
    first_hour_min_candle_close = 0

    scipt_id = 13

    # check at 10:15 AM, when len 15 min candle is >=4 or hour candle is >=1
    # Check if hour candle Close is Greater than Open, LOOK FOR CALL OPTION
    # Check if hour candle Close is Less than close, LOOK FOR PUT OPTION

    # SL will be Premium - 20 points
    # target will be Premium + 20 points

    length_15_min = 0
    while 1 == 1:
        length_60_min = len(hourly_min_candle_list)
        if length_60_min >= 1:
            print('First hour candle created.. !!')
            break
        else:
            print('.', end='')
            time.sleep(15)

    print('final length of 60 min candle.', length_60_min)

    list_cur_candle = []
    list_of_two_candles = []

    hour_flag = 0

    while 1 <= length_60_min < 4:
        length_60_min = len(hourly_min_candle_list)
        print(' len(60Min) - ', length_60_min, end='')

        if 1 <= length_60_min < 4:
            arr_index = 0

            first_hour_min_candle_open = hourly_min_candle_list[arr_index][0]
            list_cur_candle.append(first_hour_min_candle_open)

            first_hour_min_candle_high = hourly_min_candle_list[arr_index][1]
            list_cur_candle.append(first_hour_min_candle_high)

            first_hour_min_candle_low = hourly_min_candle_list[arr_index][2]
            list_cur_candle.append(first_hour_min_candle_low)

            first_hour_min_candle_close = hourly_min_candle_list[arr_index][3]
            list_cur_candle.append(first_hour_min_candle_close)

            print('--1-hour--open ', first_hour_min_candle_open, ' close - ', first_hour_min_candle_close,
                  ' - first_hour_min_candle_high ', first_hour_min_candle_high, ' first_hour_min_candle_low - ',
                  first_hour_min_candle_low)

            hour_flag = 1
            break

        print(hour_flag, ' hour flag')

        print('.', end='')
        time.sleep(5)

    print('After break statement.... first_hour_breakout')

    # apply strategy - If Close_2 > High_1, Trade for CALL POSITION
    print('Applying first_hour_breakout..!!', ' hour flag ', hour_flag)

    print('-------', 'first_hour_min_candle_open - ', first_hour_min_candle_open,
          ' first_hour_min_candle_close - ', first_hour_min_candle_close,
          ' - first_hour_min_candle_high ', first_hour_min_candle_high,
          ' first_hour_min_candle_low - ', first_hour_min_candle_low)
    logger.info(f'{'-------'} {'first_hour_min_candle_open - '} {first_hour_min_candle_open}'
                f'{' first_hour_min_candle_close - '}{first_hour_min_candle_close}'
                f'{' - first_hour_min_candle_high '}{first_hour_min_candle_high}'
                f'{' first_hour_min_candle_low - '}{first_hour_min_candle_low}')

    if 1 <= length_60_min < 4:
        if hour_flag == 1:
            print('Applying 1 hour first_hour_breakout..!!')
            break_min_counter = 180
            logger.info('Applying 1 hour first_hour_breakout..!!')
            apply_hour_end_strategy(first_hour_min_candle_open, first_hour_min_candle_high,
                                    first_hour_min_candle_low, first_hour_min_candle_close,
                                    length_60_min, scipt_id, 'REAL', break_min_counter,
                                    16, 24)

        else:
            print('conditions do not meet for First Hour strategy apply')
            logger.info('conditions do not meet for First Hour strategy apply')
            print('End of First Hour strategy... !!')
            logger.info('End of First Hour strategy... !!')
            logger2.info('End of First Hour strategy... !!')
            sys.exit()
    else:
        print('conditions do not meet for First Hour strategy apply')
        logger.info('conditions do not meet for First Hour strategy apply')
        print('End of First Hour strategy... !!')
        logger.info('End of First Hour strategy... !!')
        logger2.info('End of First Hour strategy... !!')

    sys.exit()


def one_pm_high_low_breakout():
    print('Strategy-3: one_pm_high_low_breakout is running ')
    logger.info('Strategy-3: one_pm_high_low_breakout is running ')
    logger2.info('Strategy-3: one_pm_high_low_breakout is running ')
    global scipt_id
    global hour_flag, trade_close_flag
    global highest_value, lowest_value

    highest_value = 0
    lowest_value = 0

    scipt_id = 13
    end_counter_value = 353

    # At 1 PM (HH:45 th min candle), get the HIGH & Low Index for the day.
    # At 1 PM (HH:45 th min candle), check if 15min candle (no, 15) is closed above HIGH Index, Plan for CALL Position
    # At 1 PM (HH:45 th min candle), check if 15min candle (no, 15) is closed below LOW Index, Plan for PUT Position

    length_15_min = 0

    while 1 == 1:
        count_15_min = len(fifteen_min_candle_list)
        # print('count of 15 min candle - ', count_15_min, ' end_counter_value - ', end_counter_value)
        if count_15_min >= 15:
            print('Entry eligible for one_pm_high_low_breakout,, !!')
            logger.info('Entry eligible for one_pm_high_low_breakout,, !!')

            # find the high low index., 210 is the count of candle to find the higest,Lowest value
            highest_value, lowest_value = get_high_low_latest(dhan_con, scipt_id, 210)

            # change_percentage = (highest_value - lowest_value)*100/highest_value

            print(' highest index - ', highest_value, ' lowest value ', lowest_value)
            logger.info(f'{' highest index - '}{highest_value}{' lowest value '}{lowest_value}')

            # logger.info(f'{' highest index - '}{highest_value}{' lowest value '}{lowest_value}'
            #             f'{' change percentage ' }{change_percentage}')
            # print(' highest index - ', highest_value, ' lowest value ', lowest_value,
            #       ' change_percentage - ', change_percentage)

            fifteen_min_arr_index = count_15_min-1

            trade_close_flag = 'N'

            # loop start to check conditions meet.

            count_15_min = len(fifteen_min_candle_list)
            print_counter = 0

            # if change_percentage >= 1:
            #     print('Market already moved more than 0.85 %, Do not take trade. Setting trade_close_flag = Y')
            #     logger.info('Market already moved more than 0.85 %, Do not take trade. Setting trade_close_flag = Y')
            #     trade_close_flag = 'Y'

            while 1 == 1 and trade_close_flag == 'N':
                total_passed_candle = get_all_market_minute_feed(dhan_con, scipt_id)
                if total_passed_candle > end_counter_value:
                    print('one_pm_high_low_breakout time reached. Exit now.')
                    logger.info('one_pm_high_low_breakout time reached. Exit now.')
                    trade_close_flag = 'Y'
                    break

                count_15_min_new = len(fifteen_min_candle_list)

                if count_15_min_new - count_15_min == 1:
                    count_15_min = count_15_min_new
                    fifteen_min_arr_index += 1
                    print_counter = 0

                # print(' count_15_min - ', count_15_min, ' count_15_min_new - ', count_15_min_new,
                #       ' fifteen_min_arr_index - ', fifteen_min_arr_index, ' end_counter_value - ', end_counter_value)

                fifteen_min_close = fifteen_min_candle_list[fifteen_min_arr_index][3]

                if print_counter % 4 == 0:
                    print('fifteen_min_close - ', fifteen_min_close, ' highest index - ', highest_value,
                          ' lowest value ', lowest_value)

                    logger.info(f'{'fifteen_min_close - '}{fifteen_min_close}'
                                f'{' highest index - '}{highest_value}{' lowest value '}{lowest_value}')

                # Check if 19th, 15 min candle closed above HIGHEST idndex value, LOOK FOR CALL OPTION
                if fifteen_min_close > highest_value:
                    print('BUY Trade, CALL POSITION premium id ', call_option_premium_id)
                    logger.info(f'{'BUY Trade, CALL POSITION premium id '}{call_option_premium_id}')
                    buy_position(total_passed_candle, scipt_id,
                                 call_option_premium_id, 'CALL', end_counter_value,
                                 15, 22, 'one_pm_high_low_breakout')
                    trade_close_flag = 'Y'
                    break
                elif fifteen_min_close < lowest_value:
                    print('BUY Trade, PUT POSITION premium id ', put_option_premium_id)
                    logger.info(f'{'BUY Trade, PUT POSITION premium id '}{put_option_premium_id}')
                    buy_position(total_passed_candle, scipt_id,
                                 put_option_premium_id, 'PUT', end_counter_value,
                                 15, 22, 'one_pm_high_low_breakout')
                    trade_close_flag = 'Y'
                    break
                elif total_passed_candle > end_counter_value:
                    print('Time completed for one_pm_high_low_breakout... 3 PM')
                    trade_close_flag = 'Y'
                    break
                else:
                    print('.', end='')
                    time.sleep(10)

                print_counter += 1

            if trade_close_flag == 'Y':
                print('Trade closed for the one_pm_high_low_breakout')
                break
            else:
                print('.', end='')
                time.sleep(10)

        else:
            # print('total count of 15 min candle not achieved as 19, current count ', count_15_min)
            # logger.info('total count of 15 min candle not achieved as 19')
            print('-', end='')
            time.sleep(5)

    print('End of one_pm_high_low_breakout strategy... !!')
    logger.info('End of one_pm_high_low_breakout strategy... !!')
    logger2.info('End of one_pm_high_low_breakout strategy... !!')

    sys.exit()


def get_high_low_latest(dhan_con, security_id, till_candle_counter):
    global index_name
    print('This method returns the HIGH and LOW of the index.')

    total_passed_candle = get_all_market_minute_feed(dhan_con, security_id)
    # print('Total passed candle ', total_passed_candle)

    start_counter = 0
    all_min_candle_data = []

    out_test = dhan_con.intraday_daily_minute_charts(
        security_id=security_id,
        exchange_segment='IDX_I',
        instrument_type='INDEX'
    )

    indented_history_data = pd.DataFrame(out_test['data'])

    for counter in range(start_counter, till_candle_counter):
        open_col = indented_history_data['open']
        all_min_candle_data.append(open_col[counter])

        high_col = indented_history_data['high']
        all_min_candle_data.append(high_col[counter])

        low_col = indented_history_data['low']
        all_min_candle_data.append(low_col[counter])

        close_col = indented_history_data['close']
        all_min_candle_data.append(close_col[counter])

        # print('Counter-', counter, ' Open ', open_col[counter], ': high ', high_col[counter], ': low ', low_col[counter], ': close ', close_col[counter])

    print('all_min_candle_data loaded with all candles - total length - ', len(all_min_candle_data))

    # sort this array.
    sorted_all_min_candle_data = sorted(all_min_candle_data)

    # get the highest value of the index.
    highest_candle_index = sorted_all_min_candle_data[-1]

    # get the lowest value of the index
    lowest_candle_index = sorted_all_min_candle_data[0]

    print(' highest index value - ', highest_candle_index, ' lowest index value - ', lowest_candle_index)

    return highest_candle_index, lowest_candle_index


def buy_position(curCounter, scrip_id, strike_option_premium_id, option_side,
                 break_candle_counter, sl_point, target_point, strategy_type):
    global target_price, premium_counter, total_passed_candle, trade_complete_flag
    global stop_loss_price, order_id, trade_buy_flag, curCounterCandle
    global lot_qty_size, stop_loss_update_flag
    # global passedCandle

    stop_loss_update_flag = 'N'
    lot_qty_size = 25
    print('This method is used for buying a position of ', option_side, ' lot size - ',
          lot_qty_size, ' sl point ', sl_point, ' target point - ', target_point)
    logger.info(f'{'This method is used for buying a position of '}{option_side}{' lot size - '}{lot_qty_size}'
                f'{' sl point '}{sl_point}{' target point - '}{target_point}'
                f'{'strategy - '}{strategy_type}')

    logger2.info(f'{'This method is used for buying a position of '}{option_side}{' lot size - '}{lot_qty_size}'
                f'{' sl point '}{sl_point}{' target point - '}{target_point}'
                 f'{'strategy - '}{strategy_type}')
    # THIS METHOD IS USED TO BUY FOR BUY AND CALL BOTH POSITIONS

    option_premium_id = strike_option_premium_id

    # dhan_con = get_connection()
    # get current price of the market
    # get strike price of the put position
    # Buy position, via setting Stop Loss & Target

    # counter -= 1

    trade_complete_flag = 'N'
    print('Buy Trade position is running...!!---- ')
    logger.info('Buy Trade position is running...!!---- ')
    logger2.info('Buy Trade position is running...!!---- ')

    # get the values of

    total_passed_candle = get_all_market_minute_feed(dhan_con, scrip_id)
    curCounterCandle = total_passed_candle
    while 1 == 1:

        if trade_complete_flag == 'Y':
            print('Trade Completed.. !! Exit')
            break

        total_passed_candle = get_all_market_minute_feed(dhan_con, scrip_id)
        print('---- total_passed_candle ', total_passed_candle, ' curCounterCandle ', curCounterCandle)
        if total_passed_candle - curCounterCandle == 1:
            time.sleep(10)

            # GET THE PREMIUM counter
            premium_counter = curCounterCandle - 1

            print('total_passed_candle is now greater than curCounterCandle')
            time.sleep(2)
            out_list_opt = get_market_heartbeat(dhan_con, option_premium_id, 'NSE_FNO',
                                                'OPTIDX', premium_counter)
            opt_candle_open = out_list_opt['open']
            opt_candle_high = out_list_opt['high']
            opt_candle_low = out_list_opt['low']
            opt_candle_close = out_list_opt['close']

            print('premium.. - minute#', premium_counter, '-', opt_candle_open, '-', opt_candle_high, '-',
                  opt_candle_low, '-', opt_candle_close)
            logger.info(f'{'premium.. - minute#'}{premium_counter}{'-'}{opt_candle_open}{'-'}'
                        f'{'-'}{opt_candle_high}{'-'}{opt_candle_low}{'-'}{opt_candle_close}')

            print('--- BUY TRADE ORDER POSITION --- option_premium_id ', option_premium_id)
            logger.info(f'{'--- BUY TRADE ORDER POSITION --- option_premium_id '}{option_premium_id}')
            logger2.info(f'{'--- BUY TRADE ORDER POSITION --- option_premium_id '}{option_premium_id}')
            get_result = place_order(dhan_con, option_premium_id, 'NSE_FNO',
                                     'BUY', lot_qty_size, 1, 'MARKET',
                                     'MARGIN', 0)

            print('BUY TRADE completed --- ', get_result)
            logger.info(f'{'BUY TRADE completed --- '}{get_result}')
            logger2.info(f'{'BUY TRADE completed --- '}{get_result}')


            out_status = get_result['status']
            print('Status of Order - ', out_status)
            logger.info(f'{'Status of Order - '}{out_status}')

            order_result = get_result['data']
            print('order_result orderId - ', order_result['orderId'])
            order_id = order_result['orderId']

            # Plan for getting SL and TARGET.
            print('Plan for getting SL and TARGET.')
            logger.info('Plan for getting SL and TARGET.')
            logger2.info('Plan for getting SL and TARGET.')

            traded_price = get_traded_price_by_order_id(dhan_con, order_id)
            # print('traded_price ', traded_price)

            trade_buy_flag = 'N'

            if traded_price != 0:
                # print('Traded price value - ', traded_price)
                # set SL and Target Price
                stop_loss_price = traded_price - sl_point
                target_price = traded_price + target_point
                trade_buy_flag = 'Y'
            else:
                print('Traded price not found..!!')

            # all_positions = {}

            # print('trade_buy_flag -- ', trade_buy_flag, 'SL, Target is now set')
            print(' trade buy price - ', traded_price, ' stop_loss_price - ', stop_loss_price,
                  'target_price - ', target_price, ' trade_buy_flag ', trade_buy_flag)
            logger.info(f'{'trade buy price - '}{traded_price}{' stop_loss_price '}{stop_loss_price}'
                        f'{' target_price - '}{target_price}{' trade_buy_flag '}{trade_buy_flag}'
                        f'{' strategy type - '}{strategy_type}')
            logger2.info(f'{'trade buy price - '}{traded_price}{' stop_loss_price '}{stop_loss_price}'
                        f'{' target_price - '}{target_price}{' trade_buy_flag '}{trade_buy_flag}'
                        f'{' strategy type - '}{strategy_type}')

            if trade_buy_flag == 'Y':

                while 1 == 1:
                    time.sleep(10)

                    # start checking for the premium price
                    out_list_opt = get_market_heartbeat(dhan_con, option_premium_id, 'NSE_FNO',
                                                        'OPTIDX', premium_counter)

                    # opt_candle_open = out_list_opt['open']
                    # opt_candle_high = out_list_opt['high']
                    # opt_candle_low = out_list_opt['low']
                    opt_candle_close = out_list_opt['close']

                    print('premium #', premium_counter, '- opt_candle_close ', opt_candle_close,
                          ' trade buy - ', traded_price, ' stop loss - ', stop_loss_price,
                          ' target price ', target_price)
                    logger.info(f'{'premium #'}{premium_counter}{'- opt_candle_close '}{opt_candle_close}'
                                f'{' trade buy - '}{traded_price}{' stop loss - '}{stop_loss_price}'
                                f'{' target price '}{target_price}')
                    # check if target or SL achieved.
                    # print('checking if target or SL achieved.??')

                    # BOOK PROFIT LOGIC, THIS WILL BE USED FOR MUlTIPLE LOT BUY

                    half_of_target = target_price - (target_point/2)

                    if stop_loss_update_flag == 'N' and opt_candle_close >= half_of_target:
                        three_fourth_of_sl_point = (sl_point*3)/4
                        old_stop_loss_price = stop_loss_price
                        stop_loss_price = stop_loss_price + three_fourth_of_sl_point
                        print('50% of target Achieved, SL modified..!! new stoploss - ', stop_loss_price,
                              ' old stop loss loss - ', old_stop_loss_price)
                        logger.info(f'{'50% of target Achieved, SL modified..!!  new stoploss - '}{stop_loss_price}'
                                    f'{' old stop loss price '}{old_stop_loss_price}'
                                    f'{' strategy type - '}{strategy_type}')
                        logger2.info(f'{'50% of target Achieved, SL modified..!!  new stoploss - '}{stop_loss_price}'
                                    f'{' old stop loss price '}{old_stop_loss_price}'
                                    f'{' strategy type - '}{strategy_type}')
                        stop_loss_update_flag = 'Y'

                    if opt_candle_close < stop_loss_price:
                        print('---------------------Stop LOSS HIT of ', sl_point, ' Points, Exit the trade.. !!')
                        logger.info(f'{'---------------------Stop LOSS HIT of '}{sl_point}'
                                    f'{' Points, Exit the trade.. !!'}{'strategy type - '}{strategy_type}')
                        logger2.info(f'{'---------------------Stop LOSS HIT of '}{sl_point}'
                                    f'{' Points, Exit the trade.. !!'}{'strategy type - '}{strategy_type}')
                        get_result = place_order(dhan_con, option_premium_id, 'NSE_FNO',
                                                 'SELL', lot_qty_size, 1, 'MARKET',
                                                 'MARGIN', 0)
                        print('get_result --- ', get_result)
                        logger.info(f'{'get_result --- '}{get_result}')
                        trade_complete_flag = 'Y'
                        break
                    elif opt_candle_close > target_price:
                        # code for Exit trade logic here
                        # if partial booking, TBD, in this case, change the SL too.
                        print('---------------------Target of ', target_point, ' Points, Exit the trade.. !!')
                        logger.info(f'{'---------------------Target HIT of '}{target_point}'
                                    f'{' Points, Exit the trade.. !!'}{' strategy type - '}{strategy_type}')
                        logger2.info(f'{'---------------------Target HIT of '}{target_point}'
                                    f'{' Points, Exit the trade.. !!'}{' strategy type - '}{strategy_type}')
                        get_result = place_order(dhan_con, option_premium_id, 'NSE_FNO',
                                                 'SELL', lot_qty_size, 1, 'MARKET',
                                                 'MARGIN', 0)

                        print('get_result --- ', get_result)
                        logger.info(f'{'get_result --- '}{get_result}')
                        trade_complete_flag = 'Y'
                        break
                    elif premium_counter >= break_candle_counter:
                        print('End time reached for the strategy..!!, selling the positions !!')
                        logger.info(f'{'End time reached for the strategy..!!, selling the positions !!'}'
                                     f'{' strategy type - '}{strategy_type}')
                        logger2.info(f'{'End time reached for the strategy..!!, selling the positions !!'}'
                                     f'{' strategy type - '}{strategy_type}')
                        get_result = place_order(dhan_con, option_premium_id, 'NSE_FNO',
                                                 'SELL', lot_qty_size, 1, 'MARKET',
                                                 'MARGIN', 0)

                        print('get_result --- ', get_result)
                        logger.info(f'{'get_result --- '}{get_result}')
                        trade_complete_flag = 'Y'
                        break
                    else:
                        # ADD LOGIC for SL Trail
                        # If 50% of target is achieved, trail SL by 50%
                        # wait for next iteration, check
                        print('.', end='')

                    time.sleep(2)

                    total_passed_candle = get_all_market_minute_feed(dhan_con, scrip_id)
                    if (total_passed_candle - premium_counter) > 1:
                        premium_counter += 1
                        time.sleep(10)

                # add condition if above while loop breaks, brak again


            else:
                print('Trade buy flag not set to Y ,', trade_buy_flag)
                break

        else:
            if total_passed_candle > 375:
                print('Day already Ended....!!')
                break
            print('.', end='')
            time.sleep(10)

    print('End of buy position..!!')
    logger.info(f'{'End of buy position..!!'}'
                 f'{' strategy type - '}{strategy_type}')
    logger2.info(f'{'End of buy position..!!'}'
                 f'{' strategy type - '}{strategy_type}')


def get_traded_price_by_order_id(dhan_con, order_id):
    global traded_price

    time.sleep(2)
    details_of_order = dhan_con.get_trade_book(order_id)
    # print('details_of_order - ', details_of_order)
    # print('details_of_order - status ', details_of_order['status'])
    # print('details_of_order - data ', details_of_order['data'])

    position_data = details_of_order['data']
    # print('position_data ', position_data)

    if len(position_data) > 0:
        live_data = position_data[0]
        # print('security id - ', live_data['securityId'])
        # print('orderId - ', live_data['orderId'])
        # print('tradedPrice - ', live_data['tradedPrice'])
        traded_price = live_data['tradedPrice']
    else:
        print('Order ID not found..!!', order_id)
        traded_price = 0

    return traded_price


def get_position_price(position_data, option_premium_id, position_state):
    for element in position_data:
        # print(f'Element: {element}')
        live_data = element
        # print('---', live_data['tradingSymbol'])
        # print('---', live_data['positionType'])
        # print('---', live_data['securityId'], '---', live_data['buyAvg'])

        sec_id = live_data['securityId']
        buy_avg_position = ''
        if sec_id == option_premium_id:
            if live_data['positionType'] != 'CLOSED':
                buy_avg_position = live_data['buyAvg']
            else:
                print('Position Status not LIVE - ', live_data['positionType'])
        else:
            print('Position not found - ', option_premium_id)

        return buy_avg_position


# Guide for creating strategies
def list_of_strategies():
    print('strategies')
    # 15 min breakout
    # 1 hr breakout strategy
    # Previous Day High breakout
    # Previous Day Low breakout
    # 1-hr 2 PM breakout for 5 min candle.


def load_initial_data(dhan_con, total_passed_candle, scrip_id):
    # print('total_passed_candle ', total_passed_candle)

    out_test = dhan_con.intraday_daily_minute_charts(
        security_id=scrip_id,
        exchange_segment='IDX_I',
        instrument_type='INDEX'
    )

    indented_history_data = pd.DataFrame(out_test['data'])

    # print('Printing daily chart data...')

    open_col = indented_history_data['open']
    high_col = indented_history_data['high']
    low_col = indented_history_data['low']
    close_col = indented_history_data['close']

    # min_counter=10
    # print('Open ', open_col[min_counter], ': high ', high_col[min_counter], ': low ', low_col[min_counter], ': close ', close_col[min_counter])

    cur_record_minute = 0

    # loop till current counter is NOT EQUAL to total_passed_candle-1
    flag = 'T'
    start = 0
    while flag == 'T':

        for num in range(start, total_passed_candle - 1):
            # Your code here
            # time.sleep(1)

            print('# ', num, ' Open ', open_col[num], ': high ', high_col[num], ': low ', low_col[num], ': close ',
                  close_col[num])
            logger.debug(f'{'# '} {num} {' Open '}{open_col[num]} {': high '} {high_col[num]} {': low '} '
                        f'{low_col[num]} {': close '} {close_col[num]}')

            candle_values = [open_col[num], high_col[num], low_col[num], close_col[num]]
            candle_list[num] = candle_values
            #
            # # # # print values of 5 min candle values
            if (num + 1) % 5 == 0:
                print("5 Min Candle value - OHLC - ", [open_col[num], high_col[num], low_col[num], close_col[num]])
                candle_5_mins(candle_list, (num - 4), num, 5, five_minute_counter)
                print('len(five_min_candle_list) ', len(five_min_candle_list))

            if (num + 1) % 15 == 0:
                # print("15 Min Candle value - OHLC - ", [open_col[num], high_col[num], low_col[num], close_col[num]])
                candle_5_mins(candle_list, (num - 14), num, 15, fifteen_minute_counter)
                print('len(fifteen_min_candle_list) ', len(fifteen_min_candle_list))
            #
            if (num + 1) % 60 == 0:
                # print("60 Min Candle value - OHLC - ", [open_col[num], high_col[num], low_col[num], close_col[num]])
                candle_5_mins(candle_list, (num - 59), num, 60, hourly_min_counter)
                print('len(hourly_min_candle_list) ', len(hourly_min_candle_list))

            cur_record_minute += 1

            # print(open_value, '---')
            # ohlc_list = {'open': open_col[num], 'high': high_col[num], 'low': low_col[num],
            #              'close': close_col[num]}

        total_passed_candle = get_all_market_minute_feed(dhan_con, scrip_id)
        # print('cur_record_minute - ', cur_record_minute, ' total_passed_candle ', total_passed_candle)

        if cur_record_minute == total_passed_candle - 1:
            flag = 'N'
            break
        else:
            start = total_passed_candle - 1

    return cur_record_minute

    # print('Final - ', cur_record_minute)


def print_daily_market_data_to_file(security_id):
    global index_name
    print('This method prints the daily data to file date wise.')

    dhan_con = get_connection()
    total_passed_candle = get_all_market_minute_feed(dhan_con, security_id)
    # print('Total passed candle ', total_passed_candle)

    start_counter = 0

    out_test = dhan_con.intraday_daily_minute_charts(
        security_id=security_id,
        exchange_segment='IDX_I',
        instrument_type='INDEX'
    )

    indented_history_data = pd.DataFrame(out_test['data'])

    # print('Printing daily chart data...')

    # Open a file in write mode
    today = date.today()
    # print('todays date ' , today)

    path = 'daily_market_data'

    try:
        os.mkdir(path)
        print(f"Directory '{path}' created")
    except FileExistsError:
        print(f"Directory '{path}' already exists")

    if security_id == 13:
        index_name = 'nifty'
    elif security_id == 25:
        index_name = 'banknifty'

    file_name = f"{path}{"//"}{index_name}{"_market_data_"}{today}{".txt"}"
    file = open(file_name, "w")
    print('File opened.. !!')

    for counter in range(start_counter, total_passed_candle - 1):
        open_col = indented_history_data['open']
        high_col = indented_history_data['high']
        low_col = indented_history_data['low']
        close_col = indented_history_data['close']

        # print('Counter-', counter, ' Open ', open_col[counter], ': high ', high_col[counter], ': low ', low_col[counter], ': close ', close_col[counter])

        # Write some text to the file
        seperator_str = ","
        str_line_feed = "\n"
        minute_data: str = f"{counter}{seperator_str}{open_col[counter]}{seperator_str}{high_col[counter]}{seperator_str}{low_col[counter]}{seperator_str}{close_col[counter]}{str_line_feed}"
        # lines[counter] = minute_data
        file.writelines(minute_data)

    print('Writing to file ', file_name, ' completed.!!')
    # Close the file
    file.close()


# IN USE, After End of the Day.
def generate_daily_data_post_market():
    global flag
    flag = 'open'

    for start_timer in range(10000):

        t = time.localtime()
        # print('hour ', t.tm_hour, 't-min ', t.tm_min)
        hour = t.tm_hour
        minute = t.tm_min

        print('Waiting for file to print daily data.. wait 10 sec.')
        time.sleep(10)

        if (hour >= 15 and minute > 32) or (hour >= 16):
            print_daily_market_data_to_file(13)
            break


def run_time_market_nifty(dhan_con, cur_record_minute, old_passed_candle, scrip_id):
    global flag

    flag = 'T'
    start = 0

    while flag == 'T':
        # print('wait for 60 sec')
        time.sleep(5)

        total_passed_candle = get_all_market_minute_feed(dhan_con, scrip_id)

        if total_passed_candle >= 375:
            print('Day already ended..!!')
            break

        # print('total_passed_candle ', total_passed_candle, 'cur_record_minute - ',cur_record_minute, ' old_passed_candle ', old_passed_candle)
        diff = total_passed_candle - old_passed_candle

        # print(total_passed_candle, ',', old_passed_candle)
        print('.', end='')
        if (total_passed_candle - old_passed_candle) == 1:
            # get the new counter value of total_passed_candle-1 th record

            time.sleep(10)
            out_test = []
            out_test = dhan_con.intraday_daily_minute_charts(
                security_id=scrip_id,
                exchange_segment='IDX_I',
                instrument_type='INDEX'
            )

            indented_history_data = pd.DataFrame(out_test['data'])

            # print('Printing daily chart data...', indented_history_data)

            open_col = indented_history_data['open']
            high_col = indented_history_data['high']
            low_col = indented_history_data['low']
            close_col = indented_history_data['close']

            # print(' cur_record_minute - ', cur_record_minute,
            #       ' close_col - ', close_col)

            print('#', cur_record_minute, 'Open ', open_col[cur_record_minute], ': high ', high_col[cur_record_minute],
                  ': low ', low_col[cur_record_minute], ': close ', close_col[cur_record_minute])
            logger.debug(f'{'# '}{cur_record_minute}{' Open '}{open_col[cur_record_minute]}'
                        f'{': high '}{high_col[cur_record_minute]}{': low '}{low_col[cur_record_minute]}'
                        f'{': close '}{close_col[cur_record_minute]}')

            num = cur_record_minute
            candle_values = [open_col[num], high_col[num], low_col[num], close_col[num]]
            candle_list[num] = candle_values
            #
            # # # # print values of 5 min candle values
            if (num + 1) % 5 == 0:
                print("5 Min Candle value - OHLC - ", [open_col[num], high_col[num], low_col[num], close_col[num]])
                candle_5_mins(candle_list, (num - 4), num, 5, five_minute_counter)
                print('len(five_min_candle_list) ', len(five_min_candle_list))

            if (num + 1) % 15 == 0:
                print("15 Min Candle value - OHLC - ", [open_col[num], high_col[num], low_col[num], close_col[num]])
                candle_5_mins(candle_list, (num - 14), num, 15, fifteen_minute_counter)
                print('len(fifteen_min_candle_list) ', len(fifteen_min_candle_list))
            #
            if (num + 1) % 60 == 0:
                print("60 Min Candle value - OHLC - ", [open_col[num], high_col[num], low_col[num], close_col[num]])
                candle_5_mins(candle_list, (num - 59), num, 60, hourly_min_counter)
                print('len(hourly_min_candle_list) ', len(hourly_min_candle_list))

            cur_record_minute += 1
            # print('New data added....... ', cur_record_minute)

            old_passed_candle = total_passed_candle

            if cur_record_minute > 370:
                flag = 'END'
                break

        # break


def start_main_nifty(scrip_id):
    # get total candle passed and load into the 15min and 5 min candle list
    print('test')
    dhan_con = get_connection()

    old_passed_candle = 0
    market_feed_flag = 'Y'
    total_passed_candle = -1
    while market_feed_flag == 'Y':
        try:
            total_passed_candle = get_all_market_minute_feed(dhan_con, scrip_id)
            break
        except:
            print('No data found..!!, wait 10 sec')
            time.sleep(10)

    cur_record_minute = load_initial_data(dhan_con, total_passed_candle, scrip_id)

    print('Load initial completed.')
    old_passed_candle = total_passed_candle

    # print('-------------old_passed_candle - ', old_passed_candle, ' total_passed_candle ', total_passed_candle)

    print('Real time in progress..')
    run_time_market_nifty(dhan_con, cur_record_minute, old_passed_candle, scrip_id)

    print('End of main Program..!!')


def place_order(dhan, security_id, exch_segment, buy_sell, lot_qty, lot_size, order_type, product_type, order_price):
    global price_value

    if order_type == 'MARKET':
        price_value = 0
    else:
        price_value = order_price
    total_qty = lot_qty * lot_size
    get_order_place_out = dhan.place_order(security_id=security_id,  # NiftyPE
                                           exchange_segment=exch_segment,
                                           transaction_type=buy_sell,
                                           quantity=total_qty,
                                           order_type=order_type,
                                           product_type=product_type,
                                           price=price_value)

    # print('get_order_place_out - ', get_order_place_out)
    return get_order_place_out


# NOT IN USE
def back_testing_15min_strategy():
    print('Back testing of the strategy')
    # load the day data in ArrayList after reading of data from file.
    # provide date, and market type for strategy testing.

    file_dir = 'E://workspace//ProjectTrader//daily_market_data'
    file_name = 'nifty_market_data_2024-09-17.txt'
    absolute_file_name = f"{file_dir}{"\\"}{file_name}"
    minute_data_list_all = []

    with open(absolute_file_name, 'r') as file:
        counter = 0
        for line in file:
            # print(line)
            candle_info = line.split(',')
            # print('-',candle_info[0].strip(),'-')
            # print(candle_info[1])
            # print(candle_info[2])
            # print(candle_info[3])
            # print(candle_info[4])

            minute_data_list = []
            minute_data_list.append(candle_info[1])
            minute_data_list.append(candle_info[2])
            minute_data_list.append(candle_info[3])
            minute_data_list.append(candle_info[4])
            counter += 1

            minute_data_list_all.append(minute_data_list)

    # print(len(minute_data_list_all))
    # print(minute_data_list_all[0][0])

    # work on storing the 15min cadles data.
    # TBD

    arr_index = 14
    first_fifteen_min_candle_open = minute_data_list_all[arr_index][0]
    first_fifteen_min_candle_high = minute_data_list_all[arr_index][1]
    first_fifteen_min_candle_low = minute_data_list_all[arr_index][2]
    first_fifteen_min_candle_close = minute_data_list_all[arr_index][3]

    arr_index = 29
    second_fifteen_min_candle_open = minute_data_list_all[arr_index][0]
    second_fifteen_min_candle_high = minute_data_list_all[arr_index][1]
    second_fifteen_min_candle_low = minute_data_list_all[arr_index][2]
    second_fifteen_min_candle_close = minute_data_list_all[arr_index][3]

    print(first_fifteen_min_candle_open, first_fifteen_min_candle_high,
          first_fifteen_min_candle_low, first_fifteen_min_candle_close)

    print(second_fifteen_min_candle_open, second_fifteen_min_candle_high,
          second_fifteen_min_candle_low, second_fifteen_min_candle_close)


# NOT IN USE
def get_premium_quotes(security_id, exchange, int_type):
    # get the quotes POC

    out_test = dhan_con.intraday_daily_minute_charts(
        security_id=security_id,
        exchange_segment=exchange,
        instrument_type=int_type
    )

    print('out_test - ', out_test)

    indented_history_data = pd.DataFrame(out_test['data'])

    print('indented_history_data ', indented_history_data)


# NOT IN USE
def buy_put_position(curCounterCandle, scrip_id):
    global target_price
    global stop_loss_price
    # global passedCandle

    print('This method is used for buying a PUT position', )
    option_premium_id = put_option_premium_id
    # dhan_con = get_connection()
    # get current price of the market
    # get strike price of the put position
    # Buy position, via setting Stop Loss & Target

    # counter -= 1

    print('Buy Trade position is running...!!---- ')

    # get the values of

    while 1 == 1:

        total_passed_candle = get_all_market_minute_feed(dhan_con, scrip_id)
        # print('---- total_passed_candle ', total_passed_candle, ' passedCandle - ', curCounterCandle)

        if total_passed_candle - curCounterCandle == 1:
            time.sleep(2)
            out_list = get_market_heartbeat(dhan_con, scrip_id, 'IDX_I', 'INDEX', curCounterCandle)

            candle_open = out_list['open']
            candle_high = out_list['high']
            candle_low = out_list['low']
            candle_close = out_list['close']

            # print('minute#',counter, '-', out_list['open'],'-','-',out_list['low'],'-',out_list['close'])
            # print('inside 15min strategy - minute#', total_passed_candle-1, '-', candle_open, '-', candle_high, '-', candle_low, '-', candle_close)

            # BUY TRADE HERE
            # ---------------

            # ---------------

            # time.sleep(5)
            out_list_opt = get_market_heartbeat(dhan_con, option_premium_id, 'NSE_FNO', 'OPTIDX', curCounterCandle - 1)
            opt_candle_open = out_list_opt['open']
            opt_candle_high = out_list_opt['high']
            opt_candle_low = out_list_opt['low']
            opt_candle_close = out_list_opt['close']

            print('premium.. - minute#', curCounterCandle - 1, '-', opt_candle_open, '-', opt_candle_high, '-',
                  opt_candle_low, '-', opt_candle_close)

            # ----------------
            # ----------------

            trade_buy_price = opt_candle_open

            stop_loss_price = trade_buy_price - 26
            # print('Trade stop loss will be -20 Points from candle_open - ', stop_loss_price)

            target_price = trade_buy_price + 36
            # target price will be + in case of actual strike price.

            print('Trade Bought at ', trade_buy_price, ' stop loss price - ', stop_loss_price, ' target price - ',
                  target_price)

            # take trade here in while loop.

            # curCounterCandle = total_passed_candle - 1
            # counter = curCounterCandle

            premium_counter = curCounterCandle - 1

            while 1 == 1:
                time.sleep(10)
                # out_list = get_market_heartbeat(dhan_con, scrip_id, 'IDX_I', 'INDEX', counter)
                #
                # # candle_open = out_list['open']
                # # candle_high = out_list['high']
                # # candle_low = out_list['low']
                # candle_close = out_list['close']
                # # print('candle_close ', candle_close, ' stop_loss_price - ', stop_loss_price, ' target_price ', target_price)

                # print(' premium_counter ', premium_counter)

                # get the premium price before exit.

                out_list_opt = get_market_heartbeat(dhan_con, option_premium_id, 'NSE_FNO', 'OPTIDX'
                                                    , premium_counter - 1)

                # opt_candle_open = out_list_opt['open']
                # opt_candle_high = out_list_opt['high']
                # opt_candle_low = out_list_opt['low']
                opt_candle_close = out_list_opt['close']

                total_passed_candle = get_all_market_minute_feed(dhan_con, scrip_id)
                # print('premium.. - minute#', premium_counter, '-', opt_candle_open, '-', opt_candle_high, '-', opt_candle_low, '-' , opt_candle_close, ' total_passed_candle - ', total_passed_candle)
                # print('premium.. - minute#', premium_counter, '- opt_candle_close ', opt_candle_close,
                #       ' stop loss - ', stop_loss_price, ' target price ', target_price,
                #       ' total_passed_candle - ', total_passed_candle)
                print('premium #', premium_counter, '- opt_candle_close ', opt_candle_close, ' trade buy - ',
                      trade_buy_price
                      , ' stop loss - ', stop_loss_price, ' target price ', target_price)

                if (total_passed_candle - premium_counter) > 1:

                    # check if target or SL achieved.
                    if opt_candle_close < stop_loss_price:
                        print('---------------------Stop LOSS HIT of 20 Points, Exit the trade.. !!')
                        break
                    elif opt_candle_close > target_price:
                        # code for Exit trade logic here
                        # if partial booking, TBD, in this case, change the SL too.

                        print('---------------------Target of 20 Points, Exit the trade.. !!')
                        break
                    else:
                        print('#', end='')

                    premium_counter += 1

                else:
                    print(',', end='')
                    time.sleep(15)

            time.sleep(sleep_time_normal)
            break

        else:
            print('X', end='')
            time.sleep(5)

    print('End of buy_put_position..!! Trade Bought at ', trade_buy_price, ' SL set as ', stop_loss_price,
          ' target_price set as ', target_price)


# NOT IN USE
def buy_call_position(curCounterCandle, scrip_id):
    global target_price
    global stop_loss_price
    # global passedCandle

    print('This method is used for buying a CALL position', )
    option_premium_id = call_option_premium_id
    # dhan_con = get_connection()
    # get current price of the market
    # get strike price of the put position
    # Buy position, via setting Stop Loss & Target

    # counter -= 1

    print('Buy Trade position is running...!!---- ')

    # get the values of

    while 1 == 1:

        total_passed_candle = get_all_market_minute_feed(dhan_con, scrip_id)
        # print('---- total_passed_candle ', total_passed_candle, ' passedCandle - ', curCounterCandle)

        if total_passed_candle - curCounterCandle == 1:
            time.sleep(2)
            out_list = get_market_heartbeat(dhan_con, scrip_id, 'IDX_I', 'INDEX', curCounterCandle)

            candle_open = out_list['open']
            candle_high = out_list['high']
            candle_low = out_list['low']
            candle_close = out_list['close']

            # print('minute#',counter, '-', out_list['open'],'-','-',out_list['low'],'-',out_list['close'])
            # print('inside 15min strategy - minute#', total_passed_candle-1, '-', candle_open, '-', candle_high, '-', candle_low, '-', candle_close)

            # BUY TRADE HERE
            # ---------------

            # ---------------

            # time.sleep(5)
            out_list_opt = get_market_heartbeat(dhan_con, option_premium_id, 'NSE_FNO', 'OPTIDX', curCounterCandle - 1)
            opt_candle_open = out_list_opt['open']
            opt_candle_high = out_list_opt['high']
            opt_candle_low = out_list_opt['low']
            opt_candle_close = out_list_opt['close']

            print('premium.. - minute#', curCounterCandle - 1, '-', opt_candle_open, '-', opt_candle_high, '-',
                  opt_candle_low, '-', opt_candle_close)

            # ----------------
            # ----------------

            trade_buy_price = opt_candle_open

            stop_loss_price = trade_buy_price - 26
            # print('Trade stop loss will be -20 Points from candle_open - ', stop_loss_price)

            target_price = trade_buy_price + 36
            # target price will be + in case of actual strike price.

            print('Trade Bought at ', trade_buy_price, ' stop loss price - ', stop_loss_price, ' target price - ',
                  target_price)

            # take trade here in while loop.

            # curCounterCandle = total_passed_candle - 1
            # counter = curCounterCandle

            premium_counter = curCounterCandle - 1

            while 1 == 1:
                time.sleep(1)
                # out_list = get_market_heartbeat(dhan_con, scrip_id, 'IDX_I', 'INDEX', counter)
                #
                # # candle_open = out_list['open']
                # # candle_high = out_list['high']
                # # candle_low = out_list['low']
                # candle_close = out_list['close']
                # # print('candle_close ', candle_close, ' stop_loss_price - ', stop_loss_price, ' target_price ', target_price)

                # print(' premium_counter ', premium_counter)

                # get the premium price before exit.

                out_list_opt = get_market_heartbeat(dhan_con, option_premium_id, 'NSE_FNO', 'OPTIDX'
                                                    , premium_counter - 1)

                # opt_candle_open = out_list_opt['open']
                # opt_candle_high = out_list_opt['high']
                # opt_candle_low = out_list_opt['low']
                opt_candle_close = out_list_opt['close']

                total_passed_candle = get_all_market_minute_feed(dhan_con, scrip_id)
                # print('premium.. - minute#', premium_counter, '-', opt_candle_open, '-', opt_candle_high, '-', opt_candle_low, '-' , opt_candle_close, ' total_passed_candle - ', total_passed_candle)
                # print('premium.. - minute#', premium_counter, '- opt_candle_close ', opt_candle_close,
                #       ' stop loss - ', stop_loss_price, ' target price ', target_price,
                #       ' total_passed_candle - ', total_passed_candle)
                print('premium #', premium_counter, '- opt_candle_close ', opt_candle_close, ' trade buy - ',
                      trade_buy_price
                      , ' stop loss - ', stop_loss_price, ' target price ', target_price)

                if (total_passed_candle - premium_counter) > 1:

                    # check if target or SL achieved.
                    if opt_candle_close < stop_loss_price:
                        print('---------------------Stop LOSS HIT of 20 Points, Exit the trade.. !!')
                        break
                    elif opt_candle_close > target_price:
                        # code for Exit trade logic here
                        # if partial booking, TBD, in this case, change the SL too.

                        print('---------------------Target of 20 Points, Exit the trade.. !!')
                        break
                    else:
                        print('#', end='')

                    premium_counter += 1

                else:
                    print(',', end='')
                    time.sleep(15)

            time.sleep(sleep_time_normal)
            break

        else:
            print('X', end='')
            time.sleep(5)

    print('End of buy_put_position..!! Trade Bought at ', trade_buy_price, ' SL set as ', stop_loss_price,
          ' target_price set as ', target_price)


if __name__ == "__main__":
    # main()

    print('------------------x-------------------------x--------------------')
    print('Main program started...for NIFTY 50  -- ', datetime.now().date())
    print('------------------x-------------------------x--------------------')

    logger.info('------------------x-------------------------x--------------------')
    logger.info(f'{'Main program started...for NIFTY 50  -- '}{datetime.now().date()}')
    logger.info('------------------x-------------------------x--------------------')

    logger2.info('------------------x-------------------------x--------------------')
    logger2.info(f'{'Main program started...for NIFTY 50  -- '}{datetime.now().date()}')
    logger2.info('------------------x-------------------------x--------------------')

    thread = threading.Thread(target=first_fifteen_minute_breakout)
    thread.start()

    thread2 = threading.Thread(target=first_hour_breakout)
    thread2.start()

    thread3 = threading.Thread(target=one_pm_high_low_breakout)
    thread3.start()

    # CALL STRIKE OPTION ID, NIFTY 24 OCT 24600 CALL
    call_option_premium_id = 43751

    # PUT STRIKE OPTION ID, NIFTY 24 OCT 24800 PUT
    put_option_premium_id = 43900

    # sample order place example
    # place_order(dhan_con, put_option_premium_id, 'NSE_FNO',
    #             'BUY', 13, 1, 'MARKET',
    #             'MARGIN', 0)

    # script id for BankNIFTY - 25
    # time.sleep(2)
    start_main_nifty(13)

    # get quotes for premium
    # get_premium_quotes(58538, 'NSE_FNO', 'OPTIDX')

    generate_daily_data_post_market()

    # test back strategy.
    # back_testing_15min_strategy()

# NSE,I,25,INDEX,0,BANKNIFTY,1.0,Nifty Bank,,7.00000,,1.0000,NA,INDEX,X,BANKNIFTY
# NSE,I,13,INDEX,0,NIFTY,1.0,Nifty 50,,7.00000,,1.0000,NA,INDEX,X,NIFTY

# NSE,D,44430,OPTIDX,0,NIFTY-Oct2024-25800-CE,25.0,NIFTY 24 OCT 25800 CALL,2024-10-24 14:30:00,25800.00000,CE,5.0000,W,OP,,
# NSE,D,56046,OPTIDX,0,NIFTY-Sep2024-25800-CE,25.0,NIFTY 26 SEP 25800 CALL,2024-09-26 14:30:00,25800.00000,CE,5.0000,M,OP,,

# NSE,D,58548,OPTIDX,0,NIFTY-Oct2024-25800-CE,25.0,NIFTY 03 OCT 25800 CALL,2024-10-03 14:30:00,25800.00000,CE,5.0000,W,OP,,
# NSE,D,58549,OPTIDX,0,NIFTY-Oct2024-25800-PE,25.0,NIFTY 03 OCT 25800 PUT,2024-10-03 14:30:00,25800.00000,PE,5.0000,W,OP,,


# 58538 --- 25600 CALL
# 58563 ---- 26100 PUT
