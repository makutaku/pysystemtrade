"""
IB connection using ib-insync https://ib-insync.readthedocs.io/api.html

"""

import time

from ib_insync import IB

from sysbrokers.IB.ib_connection_defaults import ib_defaults
from syscore.exceptions import missingData
from syscore.constants import arg_not_supplied

from syslogdiag.log_to_screen import logtoscreen
from syslogdiag.pst_logger import pst_logger, BROKER_LOG_LABEL, CLIENTID_LOG_LABEL

from sysdata.config.production_config import get_production_config


class connectionIB(object):
    """
    Connection object for connecting IB
    (A database plug in will need to be added for streaming prices)
    """

    def __init__(
        self,
        client_id: int,
        ib_ipaddress: str = arg_not_supplied,
        ib_port: int = arg_not_supplied,
        account: str = arg_not_supplied,
        log: pst_logger = logtoscreen("connectionIB"),
    ):
        """
        :param client_id: client id
        :param ipaddress: IP address of machine running IB Gateway or TWS. If not passed then will get from private config file, or defaults
        :param port: Port listened to by IB Gateway or TWS
        :param log: logging object
        :param mongo_db: mongoDB connection
        """

        # resolve defaults
        ipaddress, port, __ = ib_defaults(ib_ipaddress=ib_ipaddress, ib_port=ib_port)
        self._ib_connection_config = dict(
            ipaddress=ipaddress, port=port, client=client_id
        )

        # The client id is pulled from a mongo database
        # If for example you want to use a different database you could do something like:
        # connectionIB(mongo_ib_tracker =
        # mongoIBclientIDtracker(database_name="another")

        # If you copy for another broker include these lines
        self._init_log(log, client_id)

        # You can pass a client id yourself, or let IB find one

        self._init_connection(
            ipaddress=ipaddress, port=port, client_id=client_id, account=account
        )

    def _init_log(self, log, client_id: int):
        new_log = log.setup_empty_except_keep_type()
        new_log.label(**{BROKER_LOG_LABEL: "IB", CLIENTID_LOG_LABEL: client_id})
        self._log = new_log

    def _init_connection(
        self, ipaddress: str, port: int, client_id: int, account=arg_not_supplied
    ):
        ib = IB()

        try:
            if account is arg_not_supplied:
                ## not passed get from config
                account = get_broker_account()
        except missingData:
            self.log.error(
                "Broker account ID not found in private config - may cause issues"
            )
            ib.connect(ipaddress, port, clientId=client_id)
        else:
            ## conncect using account
            ib.connect(ipaddress, port, clientId=client_id, account=account)

        # Sometimes takes a few seconds to resolve... only have to do this once per process so no biggie
        time.sleep(5)

        self._ib = ib
        self._account = account

    @property
    def ib(self):
        return self._ib

    @property
    def log(self):
        return self._log

    def __repr__(self):
        return "IB broker connection" + str(self._ib_connection_config)

    def client_id(self):
        return self._ib_connection_config["client"]

    @property
    def account(self):
        return self._account

    def close_connection(self):
        self.log.msg("Terminating %s" % str(self._ib_connection_config))
        try:
            # Try and disconnect IB client
            self.ib.disconnect()
        except BaseException:
            self.log.warn(
                "Trying to disconnect IB client failed... ensure process is killed"
            )


def get_broker_account() -> str:
    production_config = get_production_config()
    account_id = production_config.get_element("broker_account")
    return account_id
