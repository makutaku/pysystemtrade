"""
Get FX prices from investing.com files, and from csv, merge and write to Arctic and/or optionally overwrite csv files
"""
import argparse
import os

from syscore.constants import arg_not_supplied
from sysdata.csv.csv_spot_fx import csvFxPricesData, ConfigCsvFXPrices
from sysdata.parquet.parquet_spotfx_prices import parquetFxPricesData


def spot_fx_from_csv_to_db(
        input_path=arg_not_supplied,
        config: ConfigCsvFXPrices = arg_not_supplied,
        csv_fx_path=arg_not_supplied,
        add_to_db=True,
        add_to_csv=True
):
    # There must be ONLY fx prices here, with filenames "GBPUSD.csv" etc
    input_csv_fx_prices = csvFxPricesData(datapath=input_path, config=config) \
        if input_path is not arg_not_supplied else None

    db_fx_prices_data = parquetFxPricesData()
    csv_fx_prices_data = csvFxPricesData(csv_fx_path)

    list_of_ccy_codes = input_csv_fx_prices.get_list_of_fxcodes()
    for currency_code in list_of_ccy_codes:
        print(currency_code)
        input_fx_prices = input_csv_fx_prices.get_fx_prices(currency_code)

        if add_to_csv:
            csv_fx_prices_data.add_fx_prices(currency_code, input_fx_prices, ignore_duplication=True)

        if add_to_db:
            db_fx_prices_data.add_fx_prices(code=currency_code, fx_price_data=input_fx_prices, ignore_duplication=True)


def main():
    output_modes = {
        'db_only': {'add_to_csv': False, 'add_to_db': True},
        'csv_only': {'add_to_csv': True, 'add_to_db': False},
        'db_and_csv': {'add_to_csv': True, 'add_to_db': True},
    }

    parser = argparse.ArgumentParser(description="Load spot FX prices from CSV to DB storage.")
    parser.add_argument('--input-path', type=str, default=arg_not_supplied,
                        help='Path to the CSV data file.')
    parser.add_argument('--output-mode', type=str, choices=output_modes.keys(), default='db_and_csv',
                        help='Determines the output mode: db_only (default), csv_only, or db_and_csv.')
    parser.add_argument('--csv-fx-path', type=str, default=arg_not_supplied,
                        help='Path where CSV data will be written.')

    args = parser.parse_args()

    if args.input_path is not arg_not_supplied and not os.path.exists(args.input_path):
        parser.error(f"The specified input path to the CSV spotFX prices does not exist: {args.input_path}")

    if args.csv_fx_path is not arg_not_supplied and not os.path.exists(args.csv_fx_path):
        parser.error(f"The specified output path for the CSV spotFX prices does not exist: {args.csv_fx_path}")

    extra_fx_prices_csv_config = ConfigCsvFXPrices(
        price_column="Close",
        date_column="DATETIME",
        date_format="ISO8601"
    ) if args.input_path is not arg_not_supplied else arg_not_supplied

    mode_config = output_modes[args.output_mode]
    spot_fx_from_csv_to_db(
        input_path=args.input_path,
        config=extra_fx_prices_csv_config,
        csv_fx_path=args.csv_fx_path,
        add_to_csv=mode_config['add_to_csv'],
        add_to_db=mode_config['add_to_db']
    )


if __name__ == "__main__":
    main()
