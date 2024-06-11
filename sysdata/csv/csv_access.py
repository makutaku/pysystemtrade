import os
import pandas as pd
from syscore.fileutils import (
    files_with_extension_in_pathname,
    resolve_path_and_filename_for_package,
    get_resolved_pathname
)
from pathlib import Path

EXTENSION = "csv"


class CsvAccess(object):
    def __init__(self, csv_store_path: str):
        self.csv_store = get_resolved_pathname(csv_store_path)

    def get_all_identifiers_with_data_type(self, data_type: str):
        path = self._get_pathname_given_data_type(data_type)
        return files_with_extension_in_pathname(path, extension=EXTENSION)

    def does_idenitifier_with_data_type_exist(
        self, data_type: str, identifier: str
    ) -> bool:
        filename = self._get_filename_given_data_type_and_identifier(
            data_type=data_type, identifier=identifier
        )
        return os.path.isfile(filename)

    def delete_data_given_data_type_and_identifier(
        self, data_type: str, identifier: str
    ):
        filename = self._get_filename_given_data_type_and_identifier(
            data_type=data_type, identifier=identifier
        )
        os.remove(filename)

    def write_data_given_data_type_and_identifier(
        self, data_to_write: pd.DataFrame, data_type: str, identifier: str
    ):
        filename = self._get_filename_given_data_type_and_identifier(
            data_type=data_type, identifier=identifier
        )
        data_to_write.to_csv(filename)

    def read_data_given_data_type_and_identifier(
        self, data_type: str, identifier: str
    ) -> pd.DataFrame:
        filename = self._get_filename_given_data_type_and_identifier(
            data_type=data_type, identifier=identifier
        )
        return pd.read_csv(filename)

    def _get_filename_given_data_type_and_identifier(
        self, data_type: str, identifier: str
    ):
        path = self._get_pathname_given_data_type(data_type)
        return resolve_path_and_filename_for_package(
            path, seperate_filename="%s.%s" % (identifier, EXTENSION)
        )

    def _get_pathname_given_data_type(self, data_type: str):
        root = self.csv_store
        path = os.path.join(root, data_type)
        Path(path).mkdir(parents=True, exist_ok=True)

        return path
