"""
We create multiple prices using:

- roll calendars, stored in csv
- individual futures contract prices, stored in arctic

We then store those multiple prices in: (depending on options)

- arctic
- .csv
"""
import os
import argparse

from syscore.constants import arg_not_supplied
from sysobjects.dict_of_futures_per_contract_prices import (
    dictFuturesContractFinalPrices,
)

import datetime
import pandas as pd

from sysproduction.data.prices import diagPrices
from sysobjects.rolls import rollParameters, contractDateWithRollParameters
from sysobjects.contract_dates_and_expiries import contractDate

from sysdata.csv.csv_roll_calendars import csvRollCalendarData
from sysdata.csv.csv_multiple_prices import csvFuturesMultiplePricesData
from sysdata.csv.csv_roll_parameters import csvRollParametersData
from sysinit.futures.build_roll_calendars import adjust_to_price_series
from sysobjects.multiple_prices import futuresMultiplePrices

from sysdata.data_blob import dataBlob

diag_prices = diagPrices()


def _get_data_inputs(csv_roll_data_path, csv_multiple_data_path):
    csv_roll_calendars = csvRollCalendarData(csv_roll_data_path)
    db_individual_futures_prices = diag_prices.db_futures_contract_price_data
    db_multiple_prices = diag_prices.db_futures_multiple_prices_data
    csv_multiple_prices = csvFuturesMultiplePricesData(csv_multiple_data_path)

    return (
        csv_roll_calendars,
        db_individual_futures_prices,
        db_multiple_prices,
        csv_multiple_prices,
    )


def process_multiple_prices_all_instruments(
    csv_multiple_data_path=arg_not_supplied,
    csv_roll_data_path=arg_not_supplied,
    add_to_db=True,
    add_to_csv=False,
):
    (
        _not_used1,
        db_individual_futures_prices,
        _not_used2,
        _not_used3,
    ) = _get_data_inputs(csv_roll_data_path, csv_multiple_data_path)
    instrument_list = (
        db_individual_futures_prices.get_list_of_instrument_codes_with_merged_price_data()
    )

    for instrument_code in instrument_list:
        print(instrument_code)
        process_multiple_prices_single_instrument(
            instrument_code,
            csv_multiple_data_path=csv_multiple_data_path,
            csv_roll_data_path=csv_roll_data_path,
            add_to_db=add_to_db,
            add_to_csv=add_to_csv,
        )


def process_multiple_prices_single_instrument(
    instrument_code,
    target_instrument_code=arg_not_supplied,
    adjust_calendar_to_prices=True,
    csv_multiple_data_path=arg_not_supplied,
    csv_roll_data_path=arg_not_supplied,
    roll_parameters=arg_not_supplied,
    roll_calendar=arg_not_supplied,
    add_to_db=True,
    add_to_csv=False,
):
    if target_instrument_code is arg_not_supplied:
        target_instrument_code = instrument_code
    (
        csv_roll_calendars,
        db_individual_futures_prices,
        db_multiple_prices,
        csv_multiple_prices,
    ) = _get_data_inputs(csv_roll_data_path, csv_multiple_data_path)

    dict_of_futures_contract_prices = (
        db_individual_futures_prices.get_merged_prices_for_instrument(instrument_code)
    )
    dict_of_futures_contract_closing_prices = (
        dict_of_futures_contract_prices.final_prices()
    )

    if roll_calendar is arg_not_supplied:
        roll_calendar = csv_roll_calendars.get_roll_calendar(instrument_code)

    # Add first phantom row so that the last calendar entry won't be consumed by adjust_roll_calendar()
    if roll_parameters is arg_not_supplied:
        m = csvRollParametersData()
        roll_parameters = m.get_roll_parameters(instrument_code)

    roll_calendar = add_phantom_row(
        roll_calendar, dict_of_futures_contract_closing_prices, roll_parameters
    )

    if adjust_calendar_to_prices:
        roll_calendar = adjust_roll_calendar(instrument_code, roll_calendar)

    # Second phantom row is needed in order to process the whole set of closing prices (and not stop after the last roll-over)
    roll_calendar = add_phantom_row(
        roll_calendar, dict_of_futures_contract_closing_prices, roll_parameters
    )

    multiple_prices = futuresMultiplePrices.create_from_raw_data(
        roll_calendar, dict_of_futures_contract_closing_prices
    )

    print(multiple_prices)

    if add_to_db:
        db_multiple_prices.add_multiple_prices(
            target_instrument_code, multiple_prices, ignore_duplication=True
        )
    if add_to_csv:
        csv_multiple_prices.add_multiple_prices(
            target_instrument_code, multiple_prices, ignore_duplication=True
        )

    return multiple_prices


def adjust_roll_calendar(instrument_code, roll_calendar):
    db_prices_per_contract = diag_prices.db_futures_contract_price_data
    print("Getting prices to adjust roll calendar")
    dict_of_prices = db_prices_per_contract.get_merged_prices_for_instrument(
        instrument_code
    )
    dict_of_futures_contract_prices = dict_of_prices.final_prices()
    roll_calendar = adjust_to_price_series(
        roll_calendar, dict_of_futures_contract_prices
    )

    return roll_calendar


def add_phantom_row(
    roll_calendar,
    dict_of_futures_contract_prices: dictFuturesContractFinalPrices,
    roll_parameters: rollParameters,
):
    final_row = roll_calendar.iloc[-1]
    if datetime.datetime.now() < final_row.name:
        return roll_calendar
    virtual_datetime = datetime.datetime.now() + datetime.timedelta(days=5)
    current_contract_date_str = str(final_row.next_contract)
    current_contract = contractDateWithRollParameters(
        contractDate(current_contract_date_str), roll_parameters
    )
    next_contract = current_contract.next_held_contract()
    carry_contract = current_contract.carry_contract()

    list_of_contract_names = dict_of_futures_contract_prices.keys()
    try:
        assert current_contract.date_str in list_of_contract_names
    except:
        print("Can't add extra row as data missing")
        return roll_calendar

    new_row = pd.DataFrame(
        dict(
            current_contract=current_contract_date_str,
            next_contract=next_contract.date_str,
            carry_contract=carry_contract.date_str,
        ),
        index=[virtual_datetime],
    )

    roll_calendar = pd.concat([roll_calendar, new_row], axis=0)

    return roll_calendar


def main():
    output_modes = {
        'db_only': {'add_to_csv': False, 'add_to_db': True},
        'csv_only': {'add_to_csv': True, 'add_to_db': False},
        'db_and_csv': {'add_to_csv': True, 'add_to_db': True},
    }

    parser = argparse.ArgumentParser(description="Generate multiple-prices into DB, from DB prices and CSV calendars.")
    parser.add_argument('--no-confirm', action='store_true', help='Skip confirmation prompt.')
    parser.add_argument('--output-mode', type=str, choices=output_modes.keys(), default='db_only',
                        help='Determines the output mode: db_only (default), csv_only, or db_and_csv.')
    parser.add_argument('--csv-roll-data-path', type=str, default=arg_not_supplied,
                        help='Path to CSV roll data. Only change if you have written the CSV roll data elsewhere.')
    parser.add_argument('--csv-multiple-data-path', type=str, default=arg_not_supplied,
                        help='Path to CSV multiple data. Change if you want to output them elsewhere.')
    args = parser.parse_args()

    if args.csv_roll_data_path is not arg_not_supplied and not os.path.exists(args.csv_roll_data_path):
        parser.error(f"The specified CSV roll data path does not exist: {args.csv_roll_data_path}")

    if args.csv_multiple_data_path is not arg_not_supplied and not os.path.exists(args.csv_multiple_data_path):
        parser.error(f"The specified CSV multiple data path does not exist: {args.csv_multiple_data_path}")

    if not args.no_confirm:
        input("Will overwrite existing multiple-prices. Are you sure?! CTL-C to abort")

    mode_config = output_modes[args.output_mode]
    process_multiple_prices_all_instruments(
        csv_multiple_data_path=args.csv_multiple_data_path,
        csv_roll_data_path=args.csv_roll_data_path,
        add_to_csv=mode_config['add_to_csv'],
        add_to_db=mode_config['add_to_db']
    )


if __name__ == "__main__":
    main()
