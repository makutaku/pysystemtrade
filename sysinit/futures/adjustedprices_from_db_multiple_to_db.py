"""
We create adjusted prices using multiple prices stored in database

We then store those adjusted prices in database and/or csv

"""
import argparse
import os
from syscore.constants import arg_not_supplied
from sysdata.csv.csv_adjusted_prices import csvFuturesAdjustedPricesData

from sysobjects.adjusted_prices import futuresAdjustedPrices

from sysproduction.data.prices import diagPrices

diag_prices = diagPrices()


def _get_data_inputs(csv_adj_data_path):
    db_multiple_prices = diag_prices.db_futures_multiple_prices_data
    db_adjusted_prices = diag_prices.db_futures_adjusted_prices_data
    csv_adjusted_prices = csvFuturesAdjustedPricesData(csv_adj_data_path)

    return db_multiple_prices, db_adjusted_prices, csv_adjusted_prices


def process_adjusted_prices_all_instruments(
    csv_adj_data_path=arg_not_supplied, add_to_db=True, add_to_csv=False
):
    db_multiple_prices, _notused, _alsonotused = _get_data_inputs(csv_adj_data_path)
    instrument_list = db_multiple_prices.get_list_of_instruments()
    for instrument_code in instrument_list:
        print(instrument_code)
        process_adjusted_prices_single_instrument(
            instrument_code,
            csv_adj_data_path=csv_adj_data_path,
            add_to_db=add_to_db,
            add_to_csv=add_to_csv,
        )


def process_adjusted_prices_single_instrument(
    instrument_code,
    csv_adj_data_path=arg_not_supplied,
    multiple_prices=arg_not_supplied,
    add_to_db=True,
    add_to_csv=False,
):
    (
        arctic_multiple_prices,
        parquet_adjusted_prices,
        csv_adjusted_prices,
    ) = _get_data_inputs(csv_adj_data_path)
    if multiple_prices is arg_not_supplied:
        multiple_prices = arctic_multiple_prices.get_multiple_prices(instrument_code)
    adjusted_prices = futuresAdjustedPrices.stitch_multiple_prices(
        multiple_prices, forward_fill=True
    )

    print(adjusted_prices)

    if add_to_db:
        parquet_adjusted_prices.add_adjusted_prices(
            instrument_code, adjusted_prices, ignore_duplication=True
        )
    if add_to_csv:
        csv_adjusted_prices.add_adjusted_prices(
            instrument_code, adjusted_prices, ignore_duplication=True
        )

    return adjusted_prices


def main():
    output_modes = {
        'db_only': {'add_to_csv': False, 'add_to_db': True},
        'csv_only': {'add_to_csv': True, 'add_to_db': False},
        'db_and_csv': {'add_to_csv': True, 'add_to_db': True},
    }

    parser = argparse.ArgumentParser(description="Generate adjusted-prices into DB, from DB multiple-prices.")
    parser.add_argument('--no-confirm', action='store_true', help='Skip confirmation prompt.')
    parser.add_argument('--output-mode', type=str, choices=output_modes.keys(), default='db_and_csv',
                        help='Determines the output mode: db_only (default), csv_only, or db_and_csv.')
    parser.add_argument('--csv-adj-data-path', type=str, default=arg_not_supplied,
                        help='Path to output CSV adjusted prices. Change if you want to output them elsewhere.')
    args = parser.parse_args()

    if args.csv_adj_data_path is not arg_not_supplied and not os.path.exists(args.csv_adj_data_path):
        parser.error(f"The specified CSV roll data path does not exist: {args.csv_adj_data_path}")

    if not args.no_confirm:
        input("Will overwrite existing prices are you sure?! CTL-C to abort")

    mode_config = output_modes[args.output_mode]
    process_adjusted_prices_all_instruments(
        csv_adj_data_path=args.csv_adj_data_path,
        add_to_csv=mode_config['add_to_csv'],
        add_to_db=mode_config['add_to_db']
    )


if __name__ == "__main__":
    main()
