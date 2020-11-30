import logging

from sawtooth_rest_api.protobuf import client_state_pb2
from sawtooth_rest_api.protobuf import validator_pb2

from rest_api.common import helper
from rest_api.common.protobuf.payload_pb2 import Token, Balance, Account, BalanceWithAccountDetails, \
    BalanceWithTokenDetails, Transfer
from rest_api import messaging
from rest_api.errors import ApiInternalError

logging.basicConfig(level=logging.DEBUG)
LOGGER = logging.getLogger(__name__)


async def _send(conn, timeout, batches):
    await messaging.send(conn, timeout, batches)


async def check_batch_status(conn, batch_ids):
    retry_num = 6
    for i in range(retry_num):
        try:
            await messaging.check_batch_status(conn, batch_ids)
            break
        except ApiInternalError as e:
            LOGGER.warning("ApiInternalError: " + str(e))
            if e.message == 'Something went wrong. Try again later' and i < (retry_num - 1):
                LOGGER.warning("Retry: " + str(i + 1))
                continue
            else:
                raise e


async def get_state_by_address(conn, address_suffix):
    status_request = client_state_pb2.ClientStateListRequest(address=address_suffix)
    validator_response = await conn.send(
        validator_pb2.Message.CLIENT_STATE_LIST_REQUEST,
        status_request.SerializeToString())

    status_response = client_state_pb2.ClientStateListResponse()
    status_response.ParseFromString(validator_response.content)

    return status_response


async def set_account(conn, timeout, batches):
    await _send(conn, timeout, batches)


async def set_immutables(conn, timeout, batches):
    await _send(conn, timeout, batches)


async def set_endorsement(conn, timeout, batches):
    await _send(conn, timeout, batches)


async def set_manager(conn, timeout, batches):
    await _send(conn, timeout, batches)


async def set_issuer(conn, timeout, batches):
    await _send(conn, timeout, batches)


async def issue_token(conn, timeout, batches):
    await _send(conn, timeout, batches)


async def set_token_status(conn, timeout, batches):
    await _send(conn, timeout, batches)


async def transfer(conn, timeout, batches):
    await _send(conn, timeout, batches)


async def set_balance_attributes(conn, timeout, batches):
    await _send(conn, timeout, batches)


async def get_balances(conn, token_hex):
    rel_address = helper.make_accounts_list_by_tokenhex(token_hex)
    balances = {}
    LOGGER.debug('rel_address: ' + str(rel_address))
    balance_resources = await messaging.get_state_by_address(conn, rel_address)
    LOGGER.debug('balance_resources: ' + str(balance_resources))
    for entity in balance_resources.entries:
        bal = BalanceWithAccountDetails()
        bal.ParseFromString(entity.data)
        account = await get_account(conn, bal.owner_pkey)
        if account is not None:
            bal.name = account.name
        LOGGER.debug('bal: ' + str(bal))
        balances[bal.owner_pkey] = bal
    return balances


async def get_account_balances(conn, public_pkey):
    rel_address = helper.make_token_list_by_account_address(public_pkey)
    balances = {}
    LOGGER.debug('rel_address: ' + str(rel_address))
    balance_resources = await messaging.get_state_by_address(conn, rel_address)
    LOGGER.debug('balance_resources: ' + str(balance_resources))
    for entity in balance_resources.entries:
        bal = BalanceWithTokenDetails()
        bal.ParseFromString(entity.data)
        bal.token_hex = helper.make_token_address(bal.asset.name)
        LOGGER.debug('bal: ' + str(bal))
        balances[bal.token_hex] = bal
    return balances


async def get_transfers(conn, token_hex):
    rel_address = helper.make_transfers_list_by_tokenhex(token_hex)
    transfers = {}
    LOGGER.debug('rel_address: ' + str(rel_address))
    transfer_resources = await messaging.get_state_by_address(conn, rel_address)
    LOGGER.debug('transfer_resources: ' + str(transfer_resources))
    for entity in transfer_resources.entries:
        trans = Transfer()
        trans.ParseFromString(entity.data)
        LOGGER.debug('trans: ' + str(trans))
        transfers[entity.address] = trans
    return transfers


async def get_account(conn, public_key):
    public_key_hex = helper.make_account_address(public_key)
    LOGGER.debug('public_key_hex: ' + str(public_key_hex))
    account_resources = await messaging.get_state_by_address(conn, public_key_hex)
    LOGGER.debug('account_resources: ' + str(account_resources))
    for entity in account_resources.entries:
        acc = Account()
        acc.ParseFromString(entity.data)
        LOGGER.debug('acc: ' + str(acc))
        return acc
    return None


async def get_manager(conn):
    public_key_hex = helper.make_manager_address()
    LOGGER.debug('public_key_hex: ' + str(public_key_hex))
    manager_resources = await messaging.get_state_by_address(conn, public_key_hex)
    LOGGER.debug('manager_resources: ' + str(manager_resources))
    for entity in manager_resources.entries:
        acc = Account()
        acc.ParseFromString(entity.data)
        LOGGER.debug('acc: ' + str(acc))
        return acc
    return None


async def get_issuer(conn):
    public_key_hex = helper.make_issuer_address()
    LOGGER.debug('public_key_hex: ' + str(public_key_hex))
    issuer_resources = await messaging.get_state_by_address(conn, public_key_hex)
    LOGGER.debug('issuer_resources: ' + str(issuer_resources))
    for entity in issuer_resources.entries:
        acc = Account()
        acc.ParseFromString(entity.data)
        LOGGER.debug('acc: ' + str(acc))
        return acc
    return None


async def get_balance(conn, client_pkey, token_hex):
    rel_address = helper.make_account_tokenhex__relation_address(client_pkey, token_hex)
    LOGGER.debug('rel_address: ' + str(rel_address))
    client_resources = await messaging.get_state_by_address(conn, rel_address)
    LOGGER.debug('client_resources: ' + str(client_resources))
    for entity in client_resources.entries:
        bal = Balance()
        bal.ParseFromString(entity.data)
        LOGGER.debug('bal: ' + str(bal))
        return bal
    return None


async def get_token(conn, token_hex):
    LOGGER.debug('token_hex: ' + str(token_hex))
    token_resources = await messaging.get_state_by_address(conn, token_hex)
    LOGGER.debug('token_resources: ' + str(token_resources))
    for entity in token_resources.entries:
        tok = Token()
        tok.ParseFromString(entity.data)
        LOGGER.debug('tok: ' + str(tok))
        return tok
    return None


async def get_wallet(conn):
    rel_address = helper.make_token_list_address()
    LOGGER.debug('rel_address: ' + str(rel_address))
    token_resources = await messaging.get_state_by_address(conn, rel_address)
    tokens = {}
    LOGGER.debug('token_resources: ' + str(token_resources))
    for entity in token_resources.entries:
        tok = Token()
        tok.ParseFromString(entity.data)
        LOGGER.debug('tok: ' + str(tok))
        tokens[entity.address] = tok
    return tokens
