import hashlib
import logging
import time
from datetime import datetime, timedelta

logging.basicConfig(level=logging.DEBUG)
LOGGER = logging.getLogger(__name__)

DISTRIBUTION_NAME = 'sawtooth-da'
CASH_TOKEN = 'Cash Token'
DATE_FORMAT = '%m/%d/%Y'
DATE_TIME_FORMAT = '%m/%d/%Y, %H:%M:%S'

DEFAULT_URL = 'http://127.0.0.1:8008'

TP_FAMILYNAME = 'da'
TP_VERSION = '1.0'

ACCOUNT_ENTITY_CODE = '01'  # id, name, pkey, manager?
TOKEN_ENTITY_CODE = '02'  # id, name, issuer pkey, amount
MANAGER_ENTITY_CODE = '03'
ISSUER_ENTITY_CODE = '04'

ACCOUNT_TOKEN__RELATION_CODE = '51'  # account pkey, token pkey -> balance
TOKEN_ACCOUNT__RELATION_CODE = '52'
TRANSFER__RELATION_CODE = '53'


def _hash(identifier):
    return hashlib.sha512(identifier.encode('utf-8')).hexdigest()


TP_PREFFIX_HEX6 = _hash(TP_FAMILYNAME)[0:6]


def make_manager_address():
    return TP_PREFFIX_HEX6 + _hash(MANAGER_ENTITY_CODE)[:64]


def make_issuer_address():
    return TP_PREFFIX_HEX6 + _hash(ISSUER_ENTITY_CODE)[:64]


def make_account_address(account_pkey):
    return TP_PREFFIX_HEX6 + ACCOUNT_ENTITY_CODE + _hash(account_pkey)[:62]


def make_account_list_address():
    return TP_PREFFIX_HEX6 + ACCOUNT_ENTITY_CODE


def make_token_address(identifier):
    return TP_PREFFIX_HEX6 + TOKEN_ENTITY_CODE + _hash(identifier)[:62]


def make_token_list_address():
    return TP_PREFFIX_HEX6 + TOKEN_ENTITY_CODE


def make_account_tokenhex__relation_address(account_pkey, token_hex):
    return TP_PREFFIX_HEX6 + ACCOUNT_TOKEN__RELATION_CODE + \
           ACCOUNT_ENTITY_CODE + _hash(account_pkey)[:30] + \
           TOKEN_ENTITY_CODE + token_hex[:28]


def make_token_list_by_account_address(account_pkey):
    return TP_PREFFIX_HEX6 + ACCOUNT_TOKEN__RELATION_CODE + ACCOUNT_ENTITY_CODE + _hash(account_pkey)[:30]


def make_transfer__relation_address(token_hex, from_pkey, to_pkey, timestamp):
    return TP_PREFFIX_HEX6 + TRANSFER__RELATION_CODE + \
           TOKEN_ENTITY_CODE + token_hex[:18] + \
           ACCOUNT_ENTITY_CODE + from_pkey[:14] + \
           ACCOUNT_ENTITY_CODE + to_pkey[:14] + \
           timestamp[:10]


def make_transfers_list_by_tokenhex(token_hex):
    return TP_PREFFIX_HEX6 + TRANSFER__RELATION_CODE + TOKEN_ENTITY_CODE + token_hex[:18]


def make_tokenhex_account__relation_address(token_hex, account_pkey):
    return TP_PREFFIX_HEX6 + TOKEN_ACCOUNT__RELATION_CODE + \
           TOKEN_ENTITY_CODE + token_hex[:28] + \
           ACCOUNT_ENTITY_CODE + _hash(account_pkey)[:30]


def make_accounts_list_by_tokenhex(token_hex):
    return TP_PREFFIX_HEX6 + TOKEN_ACCOUNT__RELATION_CODE + TOKEN_ENTITY_CODE + token_hex[:28]


def get_current_timestamp():
    return round(time.time(), ndigits=1)


def get_date_string_from_timestamp(timestamp):
    return datetime.fromtimestamp(timestamp).strftime(DATE_FORMAT)


def get_date_time_string_from_timestamp(timestamp):
    return datetime.fromtimestamp(timestamp).strftime(DATE_TIME_FORMAT)


def get_date_from_timestamp(timestamp):
    return datetime.fromtimestamp(timestamp).date()


def get_date_from_date_string(date_string):
    return datetime.strptime(date_string, DATE_FORMAT).date()


def get_timestamp_from_date_string(date_string):
    return datetime.strptime(date_string, DATE_FORMAT).timestamp()


def get_timestamp_from_date_string_with_current_time(date_string):
    dt = datetime.strptime(date_string, DATE_FORMAT)
    dt_utc_now = datetime.now()
    dt_time_shift = dt + timedelta(hours=dt_utc_now.hour,
                                   minutes=dt_utc_now.minute,
                                   seconds=dt_utc_now.second,
                                   microseconds=dt_utc_now.microsecond)
    return dt_time_shift.timestamp()


def detectTransferRestriction(account, token):
    for item in account.endorsement:
        LOGGER.debug('detectTransferRestriction #1 check: ' + str(item))
        if item.key == 'blacklist':
            return False, 'account is on blacklist'
    for item in token.attributes:
        LOGGER.debug('detectTransferRestriction #2 check: ' + str(item))
        if item.key == 'basicattributes' and item.value is not None:
            LOGGER.debug("'basicattributes' attribute exists")
            for item2 in item.value:
                if item2.key == 'transferendorsement' and item2.value is not None:
                    LOGGER.debug("'transferendorsement' attribute exists")
                    if item2.value.lower() == 'true':
                        return True, 'Transfer is endorsement'
    for item in account.endorsement:
        LOGGER.debug('detectTransferRestriction #3 check: ' + str(item))
        if item.key == 'whitelist':
            return True, 'account is on whitelist'
    for item in token.immutables:
        LOGGER.debug('detectTransferRestriction #4 check: ' + str(item))
        if item.key == 'endorsement' and len(item.value) == 0:
            return True, 'token endorsement'
    for item in token.immutables:
        LOGGER.debug('detectTransferRestriction #5 check: ' + str(item))
        # if 'endorsement' key exists in Token.immutables
        if item.key == 'endorsement':
            LOGGER.debug("1. 'endorsement' key exists in Token.immutables" + str(item))
            # if 'value' for the key exists
            if item.value is not None:
                LOGGER.debug("2. 'value' for the key exists")
                # If 'value' for the key not empty
                if len(item.value) > 0:
                    LOGGER.debug("3. 'value' for the key not empty")
                    # for each item from 'value' list
                    for token_item in item.value:
                        LOGGER.debug("4. for each item from 'value' list" + str(token_item))
                        # for each item from Account.endorsement
                        for account_item in account.endorsement:
                            LOGGER.debug("5. for each item from Account.endorsement" + str(account_item))
                            # if 'key' key exists for both Account and Token entities
                            if account_item.key is not None and token_item.key is not None:
                                LOGGER.debug("6. 'key' key exists for both Account and Token entities: " +
                                             str(account_item.key) + "; " + token_item.key)
                                # if 'key' values for Account and Token are same
                                if account_item.key == token_item.key:
                                    LOGGER.debug("7. account is endorsement")
                                    return True, 'account is endorsement'
                    LOGGER.debug("8. account is not endorsement")
                    return False, 'account is not endorsement'
    LOGGER.debug("9. account is endorsement")
    return True, 'account is endorsement'
