import hashlib
import random
import logging
from sawtooth_sdk.protobuf.batch_pb2 import BatchHeader, Batch
from sawtooth_sdk.protobuf.transaction_pb2 import Transaction, TransactionHeader

from . import helper as helper
from .protobuf.payload_pb2 import TransactionPayload, Account, Token, Transfer, Heartbeat, BalanceAttributes

logging.basicConfig(level=logging.DEBUG)
LOGGER = logging.getLogger(__name__)


def _make_transaction(payload, inputs, outputs, txn_signer, batch_signer):
    txn_header_bytes, signature = _transaction_header(txn_signer, batch_signer, inputs, outputs, payload)

    txn = Transaction(
        header=txn_header_bytes,
        header_signature=signature,
        payload=payload.SerializeToString()
    )

    return txn


def make_batch_and_id(transactions, batch_signer):
    batch_header_bytes, signature = _batch_header(batch_signer, transactions)

    batch = Batch(
        header=batch_header_bytes,
        header_signature=signature,
        transactions=transactions
    )

    return batch, batch.header_signature


def _transaction_header(txn_signer, batch_signer, inputs, outputs, payload):
    txn_header_bytes = TransactionHeader(
        family_name=helper.TP_FAMILYNAME,
        family_version=helper.TP_VERSION,
        inputs=inputs,
        outputs=outputs,
        signer_public_key=txn_signer.get_public_key().as_hex(),
        batcher_public_key=batch_signer.get_public_key().as_hex(),
        dependencies=[],
        nonce=random.random().hex().encode(),
        payload_sha512=hashlib.sha512(payload.SerializeToString()).hexdigest()
    ).SerializeToString()

    signature = txn_signer.sign(txn_header_bytes)
    return txn_header_bytes, signature


def _batch_header(batch_signer, transactions):
    batch_header_bytes = BatchHeader(
        signer_public_key=batch_signer.get_public_key().as_hex(),
        transaction_ids=[txn.header_signature for txn in transactions],
    ).SerializeToString()

    signature = batch_signer.sign(batch_header_bytes)

    return batch_header_bytes, signature


def set_manager(txn_signer, batch_signer, name, endorsement):
    account_pkey = txn_signer.get_public_key().as_hex()
    LOGGER.debug('account_pkey: ' + str(account_pkey))
    static_manager_hex = helper.make_manager_address()
    account_hex = helper.make_account_address(account_pkey=account_pkey)
    LOGGER.debug('account_hex: ' + str(account_hex))

    manager = Account(
        public_key=account_pkey,
        name=name,
        endorsement=endorsement
    )

    payload = TransactionPayload(
        payload_type=TransactionPayload.SET_MANAGER,
        set_manager=manager)

    return _make_transaction(
        payload=payload,
        inputs=[account_hex, static_manager_hex],
        outputs=[account_hex, static_manager_hex],
        txn_signer=txn_signer,
        batch_signer=batch_signer)


def set_issuer(txn_signer, batch_signer, name, endorsement):
    account_pkey = txn_signer.get_public_key().as_hex()
    LOGGER.debug('account_pkey: ' + str(account_pkey))
    static_issuer_hex = helper.make_issuer_address()
    account_hex = helper.make_account_address(account_pkey=account_pkey)
    LOGGER.debug('account_hex: ' + str(account_hex))

    issuer = Account(
        public_key=account_pkey,
        name=name,
        endorsement=endorsement
    )

    payload = TransactionPayload(
        payload_type=TransactionPayload.SET_ISSUER,
        set_issuer=issuer)

    token_hex = helper.make_token_address(identifier=helper.CASH_TOKEN)
    account_token_rel_hex = \
        helper.make_account_tokenhex__relation_address(account_pkey=account_pkey, token_hex=token_hex)

    token_account_rel_hex = \
        helper.make_tokenhex_account__relation_address(token_hex=token_hex, account_pkey=account_pkey)

    return _make_transaction(
        payload=payload,
        inputs=[account_hex, static_issuer_hex, token_hex, account_token_rel_hex, token_account_rel_hex],
        outputs=[account_hex, static_issuer_hex, token_hex, account_token_rel_hex, token_account_rel_hex],
        txn_signer=txn_signer,
        batch_signer=batch_signer)


def set_account(txn_signer, batch_signer, name, endorsement):
    account_pkey = txn_signer.get_public_key().as_hex()
    LOGGER.debug('account_pkey: ' + str(account_pkey))
    account_hex = helper.make_account_address(account_pkey=account_pkey)
    LOGGER.debug('account_hex: ' + str(account_hex))

    manager = Account(
        public_key=account_pkey,
        name=name,
        endorsement=endorsement
    )

    payload = TransactionPayload(
        payload_type=TransactionPayload.SET_ACCOUNT,
        set_account=manager)

    return _make_transaction(
        payload=payload,
        inputs=[account_hex],
        outputs=[account_hex],
        txn_signer=txn_signer,
        batch_signer=batch_signer)


def set_token_status(txn_signer, batch_signer, identifier, status):
    manager_hex = helper.make_manager_address()
    token_hex = helper.make_token_address(identifier=identifier)

    token = Token(
        name=identifier,
        status=Token.StatusType.Value(status)
    )

    LOGGER.debug('token: ' + str(token))

    payload = TransactionPayload(
        payload_type=TransactionPayload.SET_TOKEN_STATUS,
        set_token_status=token)

    return _make_transaction(
        payload=payload,
        inputs=[token_hex, manager_hex],
        outputs=[token_hex, manager_hex],
        txn_signer=txn_signer,
        batch_signer=batch_signer), token_hex


def issue_token(txn_signer, batch_signer, identifier, attributes, total_supply):
    owner_pkey = txn_signer.get_public_key().as_hex()
    manager_hex = helper.make_manager_address()
    token_hex = helper.make_token_address(identifier=identifier)
    account_token_rel_hex = \
        helper.make_account_tokenhex__relation_address(account_pkey=owner_pkey, token_hex=token_hex)

    token_account_rel_hex = \
        helper.make_tokenhex_account__relation_address(token_hex=token_hex, account_pkey=owner_pkey)

    token = Token(
        name=identifier,
        issuer_pkey=owner_pkey,
        total_supply=total_supply,
        attributes=attributes
    )

    LOGGER.debug('token: ' + str(token))

    payload = TransactionPayload(
        payload_type=TransactionPayload.ISSUE_TOKEN,
        issue_token=token)

    return _make_transaction(
        payload=payload,
        inputs=[token_hex, account_token_rel_hex, token_account_rel_hex, manager_hex],
        outputs=[token_hex, account_token_rel_hex, token_account_rel_hex, manager_hex],
        txn_signer=txn_signer,
        batch_signer=batch_signer), token_hex


def set_immutables(txn_signer, batch_signer, identifier, immutables):
    manager_hex = helper.make_manager_address()
    token_hex = helper.make_token_address(identifier=identifier)

    token = Token(
        name=identifier,
        immutables=immutables
    )

    LOGGER.debug('token: ' + str(token))

    payload = TransactionPayload(
        payload_type=TransactionPayload.ADD_IMMUTABLE,
        add_immutables=token)

    return _make_transaction(
        payload=payload,
        inputs=[token_hex, manager_hex],
        outputs=[token_hex, manager_hex],
        txn_signer=txn_signer,
        batch_signer=batch_signer)


def set_endorsement(txn_signer, batch_signer, account_pkey, endorsement):
    manager_hex = helper.make_manager_address()
    account_hex = helper.make_account_address(account_pkey=account_pkey)

    account = Account(
        public_key=account_pkey,
        endorsement=endorsement
    )

    LOGGER.debug('account: ' + str(account))

    payload = TransactionPayload(
        payload_type=TransactionPayload.SET_ENDORSEMENT,
        set_endorsement=account)

    return _make_transaction(
        payload=payload,
        inputs=[account_hex, manager_hex],
        outputs=[account_hex, manager_hex],
        txn_signer=txn_signer,
        batch_signer=batch_signer)


def set_balance_attributes(txn_signer, batch_signer, account_pkey, identifiers, attributes):
    account_hex = helper.make_account_address(account_pkey=account_pkey)
    manager_hex = helper.make_manager_address()

    account_token_rel_hex_list = []
    token_account_rel_hex_list = []

    for identifier in identifiers:
        token_hex = helper.make_token_address(identifier)
        account_token_rel_hex_list.append(
            helper.make_account_tokenhex__relation_address(account_pkey=account_pkey, token_hex=token_hex))
        token_account_rel_hex_list.append(
            helper.make_tokenhex_account__relation_address(token_hex=token_hex, account_pkey=account_pkey))

    balances = BalanceAttributes(
        owner_pkey=account_pkey,
        identifiers=identifiers,
        attributes=attributes
    )

    LOGGER.debug('balances: ' + str(balances))

    payload = TransactionPayload(
        payload_type=TransactionPayload.SET_BALANCE_ATTRIBUTES,
        set_balance_attributes=balances)

    return _make_transaction(
        payload=payload,
        inputs=[account_hex, manager_hex] + account_token_rel_hex_list + token_account_rel_hex_list,
        outputs=[account_hex, manager_hex] + account_token_rel_hex_list + token_account_rel_hex_list,
        txn_signer=txn_signer,
        batch_signer=batch_signer)


def transfer(txn_signer, batch_signer, receiver_pkey, identifier, total_supply):
    sender_pkey = txn_signer.get_public_key().as_hex()
    token_hex = helper.make_token_address(identifier)

    sender_token_rel_hex = \
        helper.make_account_tokenhex__relation_address(account_pkey=sender_pkey, token_hex=token_hex)
    receiver_token_rel_hex = \
        helper.make_account_tokenhex__relation_address(account_pkey=receiver_pkey, token_hex=token_hex)

    token_sender_rel_hex = \
        helper.make_tokenhex_account__relation_address(token_hex=token_hex, account_pkey=sender_pkey)
    token_receiver_rel_hex = \
        helper.make_tokenhex_account__relation_address(token_hex=token_hex, account_pkey=receiver_pkey)

    ts = str(helper.get_current_timestamp())
    transfer_hex = helper.make_transfer__relation_address(
        token_hex=token_hex, from_pkey=sender_pkey,
        to_pkey=receiver_pkey, timestamp=ts)

    sender_hex = helper.make_account_address(sender_pkey)
    receiver_hex = helper.make_account_address(receiver_pkey)

    asset = Token(
        name=identifier,
        total_supply=total_supply
    )

    transfer_asset = Transfer(
        sender_pkey=sender_pkey,
        receiver_pkey=receiver_pkey,
        asset=asset,
        date=ts
    )

    payload = TransactionPayload(
        payload_type=TransactionPayload.TRANSFER,
        transfer=transfer_asset)

    inputs = outputs = [sender_token_rel_hex, receiver_token_rel_hex, token_sender_rel_hex,
                        token_receiver_rel_hex, token_hex, transfer_hex, sender_hex, receiver_hex]

    LOGGER.debug('inputs: ' + str(inputs))
    return _make_transaction(
        payload=payload,
        inputs=inputs,
        outputs=outputs,
        txn_signer=txn_signer,
        batch_signer=batch_signer)


def heartbeat(txn_signer, batch_signer, issuer_public_key, holder_pkey_list, identifier, date):
    issuer_hex = helper.make_issuer_address()
    token_hex = helper.make_token_address(identifier)
    cash_token_hex = helper.make_token_address(helper.CASH_TOKEN)

    sender_token_rel_hex = \
        helper.make_account_tokenhex__relation_address(account_pkey=issuer_public_key, token_hex=cash_token_hex)

    token_sender_rel_hex = \
        helper.make_tokenhex_account__relation_address(token_hex=cash_token_hex, account_pkey=issuer_public_key)

    receiver_token_rel_hex_list = []
    receiver__cash_token_rel_hex_list = []
    token_receiver_rel_hex_list = []
    cash_token__receiver_rel_hex_list = []
    transfer_hex_list = []
    LOGGER.debug('date: ' + str(date))
    ts = str(helper.get_current_timestamp()) if date is None \
        else str(helper.get_timestamp_from_date_string_with_current_time(date))
    LOGGER.debug('ts: ' + str(ts))
    receiver_hex_list = []

    for holder_pkey in holder_pkey_list:
        receiver_token_rel_hex_list.append(
            helper.make_account_tokenhex__relation_address(account_pkey=holder_pkey, token_hex=token_hex))
        receiver__cash_token_rel_hex_list.append(
            helper.make_account_tokenhex__relation_address(account_pkey=holder_pkey, token_hex=cash_token_hex))
        token_receiver_rel_hex_list.append(
            helper.make_tokenhex_account__relation_address(token_hex=token_hex, account_pkey=holder_pkey))
        cash_token__receiver_rel_hex_list.append(
            helper.make_tokenhex_account__relation_address(token_hex=cash_token_hex, account_pkey=holder_pkey))
        transfer_hex_list.append(helper.make_transfer__relation_address(
            token_hex=cash_token_hex, from_pkey=issuer_public_key,
            to_pkey=holder_pkey, timestamp=ts))
        receiver_hex_list.append(helper.make_account_address(holder_pkey))

    sender_hex = helper.make_account_address(issuer_public_key)

    asset = Token(
        name=identifier
    )

    heartbeat_asset = Heartbeat(
        sender_pkey=issuer_public_key,
        receivers_pkey=holder_pkey_list,
        asset=asset,
        date=ts
    )

    payload = TransactionPayload(
        payload_type=TransactionPayload.HEARTBEAT,
        heartbeat=heartbeat_asset)

    inputs = outputs = [issuer_hex, sender_token_rel_hex, token_sender_rel_hex,
                        token_hex, sender_hex, cash_token_hex] + \
        receiver_token_rel_hex_list + \
        receiver__cash_token_rel_hex_list + \
        cash_token__receiver_rel_hex_list + \
        token_receiver_rel_hex_list + \
        transfer_hex_list + \
        receiver_hex_list

    LOGGER.debug('inputs: ' + str(inputs))
    return _make_transaction(
        payload=payload,
        inputs=inputs,
        outputs=outputs,
        txn_signer=txn_signer,
        batch_signer=batch_signer)
