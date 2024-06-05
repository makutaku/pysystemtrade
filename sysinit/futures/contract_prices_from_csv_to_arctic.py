import sys
from syscore.constants import arg_not_supplied
from syscore.dateutils import MIXED_FREQ, HOURLY_FREQ, DAILY_PRICE_FREQ, Frequency
from syscore.pandas.frequency import merge_data_with_different_freq
from sysdata.csv.csv_futures_contract_prices import csvFuturesContractPriceData
from sysproduction.data.prices import diagPrices
from sysobjects.contracts import futuresContract

diag_prices = diagPrices()


def init_db_with_csv_futures_contract_prices(
    datapath: str,
    csv_config=arg_not_supplied,
    frequency=MIXED_FREQ,
    require_confirmation=True,
):
    print(f"Initializing DB with data from {datapath} with frequency {frequency}")
    csv_prices = csvFuturesContractPriceData(datapath)

    if require_confirmation:
        input(
            "WARNING THIS WILL ERASE ANY EXISTING DATABASE PRICES WITH DATA FROM %s ARE YOU SURE?! (CTRL-C TO STOP)"
            % csv_prices.datapath
        )

    instrument_codes = (
        csv_prices.get_list_of_instrument_codes_with_price_data_at_frequency(frequency)
    )
    instrument_codes.sort()
    for instrument_code in instrument_codes:
        init_db_with_csv_futures_contract_prices_for_code(
            instrument_code, datapath, csv_config=csv_config, frequency=frequency
        )


def init_db_with_csv_futures_contract_prices_for_code(
    instrument_code: str,
    datapath: str,
    csv_config=arg_not_supplied,
    frequency=MIXED_FREQ,
):
    print(instrument_code)
    csv_prices = csvFuturesContractPriceData(datapath, config=csv_config)
    db_prices = diag_prices.db_futures_contract_price_data

    print(f"Getting {frequency} .csv prices may take some time")
    csv_price_dict = csv_prices.get_prices_at_frequency_for_instrument(
        instrument_code, frequency
    )

    print(f"Have {frequency} .csv prices for the following contracts:")
    print(str(csv_price_dict.keys()))

    for contract_date_str, prices_for_contract in csv_price_dict.items():
        print("Processing %s" % contract_date_str)
        print(".csv prices are \n %s" % str(prices_for_contract))
        contract = futuresContract(instrument_code, contract_date_str)
        print("Contract object is %s" % str(contract))
        print("Writing to db")
        db_prices.write_prices_at_frequency_for_contract_object(
            contract,
            prices_for_contract,
            ignore_duplication=True,
            frequency=frequency,
        )
        print(f"Reading back {frequency} prices from db to check")
        written_prices = db_prices.get_prices_at_frequency_for_contract_object(
            contract, frequency=frequency
        )
        print("Read back prices are \n %s" % str(written_prices))

        # if we're importing hourly or daily, we need to also generate MIXED
        if frequency != MIXED_FREQ:
            create_merged_prices(contract)


def create_merged_prices(contract):
    db_prices = diag_prices.db_futures_contract_price_data
    if db_prices.has_price_data_for_contract_at_frequency(
        contract, DAILY_PRICE_FREQ
    ) and db_prices.has_price_data_for_contract_at_frequency(contract, HOURLY_FREQ):
        print(f"DB has hourly and daily prices for {contract}, creating merged prices")
        list_of_data = [
            diag_prices.get_prices_at_frequency_for_contract_object(
                contract,
                frequency=frequency,
            )
            for frequency in [HOURLY_FREQ, DAILY_PRICE_FREQ]
        ]
        merged_prices = merge_data_with_different_freq(list_of_data)
        print("Writing to db")
        db_prices.write_prices_at_frequency_for_contract_object(
            contract, merged_prices, frequency=MIXED_FREQ, ignore_duplication=True
        )
        print("Reading back prices from db to check")
        written_merged_prices = db_prices.get_prices_at_frequency_for_contract_object(
            contract, frequency=MIXED_FREQ
        )

        print(f"Read back prices (MIXED) are \n{str(written_merged_prices)}")


def main():
    if len(sys.argv) < 3:
        print("Usage: contract_prices_from_csv_to_arctic.py <datapath> <frequency> [--no-confirm]")
        sys.exit(1)

    datapath = sys.argv[1]
    frequency_key = sys.argv[2]
    no_confirm = len(sys.argv) > 3 and sys.argv[3] == '--no-confirm'

    try:
        frequency = Frequency[frequency_key]
    except KeyError:
        valid_frequencies = ', '.join([f.name for f in Frequency])
        print(f"Invalid frequency. Allowed values are: {valid_frequencies}")
        sys.exit(1)

    init_db_with_csv_futures_contract_prices(datapath, frequency=frequency, require_confirmation=not no_confirm)


if __name__ == "__main__":
    main()
