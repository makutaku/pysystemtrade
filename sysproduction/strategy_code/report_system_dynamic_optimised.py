import pandas as pd

from syscore.objects import header, table, body_text
from sysdata.data_blob import dataBlob
from sysobjects.production.backtest_storage import interactiveBacktest
from sysproduction.strategy_code.report_system_classic import report_system_classic
from sysproduction.data.positions import dataOptimalPositions

def report_system_dynamic(data: dataBlob, backtest: interactiveBacktest):
    format_output = report_system_classic(data=data,
                                          backtest=backtest)

    optimal_positions_df = get_optimal_positions_table_as_df(data=data,
                                                          strategy_name =
                                                          backtest.strategy_name)
    optimal_positions_table = table("Optimal positions", optimal_positions_df)
    format_output.append(optimal_positions_table)

    return format_output

def get_optimal_positions_table_as_df(data: dataBlob,
                                        strategy_name: str) -> pd.DataFrame:

    data_optimal_positions = dataOptimalPositions(data)

    list_of_positions = data_optimal_positions.get_list_of_current_optimal_positions_for_strategy_name(strategy_name)
    as_verbose_pd = list_of_positions.as_verbose_pd()

    subset_of_pd = as_verbose_pd[['dont_trade',
                                  'reduce_only',

                                  'optimal_position',
                                  'position_limit_contracts',
                                  'previous_position',

                                    'weight_per_contract',
                                  'position_limit_weight',
                                  'optimum_weight',
                                  'start_weight',
                                  'maximum_weight',
                                  'minimum_weight',

                                  'previous_weight',
                                  'optimised_weight',
                                  'optimised_position'
                                  ]]

    things_to_round = ['optimal_position',
                                    'weight_per_contract',
                                  'position_limit_weight',
                                  'optimum_weight',
                                  'start_weight',
                                  'maximum_weight',
                                  'minimum_weight',
                                  'previous_weight',
                                  'optimised_weight']

    for column_name in things_to_round:
        subset_of_pd[column_name] = subset_of_pd[column_name].round(2)

    subset_of_pd = subset_of_pd.sort_values('optimum_weight')

    return subset_of_pd
