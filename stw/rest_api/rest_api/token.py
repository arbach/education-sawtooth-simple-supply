from sanic import Blueprint
from sanic import response
import logging
from rest_api.common import transaction, helper
from rest_api import general, security_messaging
from rest_api.common.protobuf.payload_pb2 import Token
from rest_api.errors import ApiBadRequest, ApiInternalError, ApiForbidden, ApiNotFound

logging.basicConfig(level=logging.DEBUG)
LOGGER = logging.getLogger(__name__)

TOKEN_BP = Blueprint('token')


@TOKEN_BP.get('token/balance/<token_hex>')
async def get_balance(request, token_hex):
    client_pkey = request.app.config.SIGNER.get_public_key().as_hex()
    balance = await security_messaging.get_balance(request.app.config.VAL_CONN, client_pkey, token_hex)
    balance_value = None if balance is None else str(balance.asset.total_supply)
    return response.json(body={'data': {
        "token_hex": token_hex,
        "total_supply": balance_value
    }},
        headers=general.get_response_headers())


@TOKEN_BP.get('token/balances/<token_hex>')
async def get_balances(request, token_hex):
    client_pkey = request.app.config.SIGNER.get_public_key().as_hex()
    manager = await security_messaging.get_manager(request.app.config.VAL_CONN)
    if manager is None:
        raise ApiForbidden("Manager not exists")
    else:
        if manager.public_key != client_pkey:
            raise ApiForbidden("Manager's role is required")
    balances = await security_messaging.get_balances(request.app.config.VAL_CONN, token_hex)
    balances_json = []
    for address, bal in balances.items():
        balances_json.append({
            "owner_pkey": bal.owner_pkey,
            "owner_name": bal.name,
            "total_supply": bal.asset.total_supply
        })

    return response.json(body={'data': balances_json},
                         headers=general.get_response_headers())


@TOKEN_BP.get('token/details/<token_hex>')
async def get_details(request, token_hex):
    token = await security_messaging.get_token(request.app.config.VAL_CONN, token_hex)
    if token is None:
        raise ApiNotFound('Token hex does not exist: ' + token_hex)
    attributes = []
    for attr_level_1 in token.attributes:
        attributes_level2 = []
        for attr_level_2 in attr_level_1.value:
            attributes_level2.append({"key": attr_level_2.key,
                                       "value": attr_level_2.value})
        attributes.append({"key": attr_level_1.key,
                            "value": attributes_level2})

    immutables = []
    for attr_level_1 in token.immutables:
        attributes_level2 = []
        for attr_level_2 in attr_level_1.value:
            attributes_level2.append({"key": attr_level_2.key,
                                       "value": attr_level_2.value})
        immutables.append({"key": attr_level_1.key,
                            "value": attributes_level2})

    return response.json(body={'data': {
        "token_hex": token_hex,
        "identifier": token.name,
        "issuer_pkey": token.issuer_pkey,
        "status": Token.StatusType.Name(token.status),
        "total_supply": str(token.total_supply),
        "attributes": attributes,
        "immutables": immutables
    }},
        headers=general.get_response_headers())


@TOKEN_BP.post('token/issue')
async def issue_token(request):
    """Updates auth information for the authorized account"""
    required_fields = ['identifier', 'total_supply', 'attributes']
    general.validate_fields(required_fields, request.json)

    identifier = request.json.get('identifier')
    total_supply = request.json.get('total_supply')
    attributes = request.json.get('attributes')

    required_fields = ['key', 'value']

    for attribute in attributes:
        general.validate_fields(required_fields, attribute)
        for attribute_level_2 in attribute['value']:
            general.validate_fields(required_fields, attribute_level_2)

    signer = request.app.config.SIGNER

    token_txn, token_hex = transaction.issue_token(
        txn_signer=signer,
        batch_signer=signer,
        identifier=identifier,
        attributes=attributes,
        total_supply=float(total_supply)
    )

    batch, batch_id = transaction.make_batch_and_id([token_txn], signer)

    await security_messaging.issue_token(
        request.app.config.VAL_CONN,
        request.app.config.TIMEOUT,
        [batch])

    try:
        await security_messaging.check_batch_status(
            request.app.config.VAL_CONN, [batch_id])
    except (ApiBadRequest, ApiInternalError) as err:
        raise err

    return response.json(body={'status': general.DONE,
                               'token_hex': token_hex},
                         headers=general.get_response_headers())


@TOKEN_BP.post('token/set_status')
async def set_token_status(request):
    required_fields = ['identifier', 'status']
    general.validate_fields(required_fields, request.json)

    identifier = request.json.get('identifier')
    status = request.json.get('status')

    signer = request.app.config.SIGNER

    token_txn, token_hex = transaction.set_token_status(
        txn_signer=signer,
        batch_signer=signer,
        identifier=identifier,
        status=status
    )

    batch, batch_id = transaction.make_batch_and_id([token_txn], signer)

    await security_messaging.set_token_status(
        request.app.config.VAL_CONN,
        request.app.config.TIMEOUT,
        [batch])

    try:
        await security_messaging.check_batch_status(
            request.app.config.VAL_CONN, [batch_id])
    except (ApiBadRequest, ApiInternalError) as err:
        raise err

    return response.json(body={'status': general.DONE,
                               'token_hex': token_hex},
                         headers=general.get_response_headers())


@TOKEN_BP.post('token/set_immutables')
async def set_immutables(request):
    """Updates auth information for the authorized account"""
    required_fields = ['identifier', 'immutables']
    general.validate_fields(required_fields, request.json)

    identifier = request.json.get('identifier')
    immutables = request.json.get('immutables')

    required_fields = ['key', 'value']

    for attribute in immutables:
        general.validate_fields(required_fields, attribute)
        for attribute_level_2 in attribute['value']:
            general.validate_fields(required_fields, attribute_level_2)
    signer = request.app.config.SIGNER

    token_txn = transaction.set_immutables(
        txn_signer=signer,
        batch_signer=signer,
        identifier=identifier,
        immutables=immutables
    )

    batch, batch_id = transaction.make_batch_and_id([token_txn], signer)

    await security_messaging.set_immutables(
        request.app.config.VAL_CONN,
        request.app.config.TIMEOUT,
        [batch])

    try:
        await security_messaging.check_batch_status(
            request.app.config.VAL_CONN, [batch_id])
    except (ApiBadRequest, ApiInternalError) as err:
        raise err

    return response.json(body={'status': general.DONE},
                         headers=general.get_response_headers())


@TOKEN_BP.post('token/transfer')
async def transfer(request):
    """Updates auth information for the authorized account"""
    required_fields = ['receiver_pkey', 'identifier', 'amount']
    general.validate_fields(required_fields, request.json)

    receiver_pkey = request.json.get('receiver_pkey')
    identifier = request.json.get('identifier')
    total_supply = request.json.get('amount')

    signer = request.app.config.SIGNER

    data_txn = transaction.transfer(
        txn_signer=signer,
        batch_signer=signer,
        receiver_pkey=receiver_pkey,
        identifier=identifier,
        total_supply=total_supply
    )

    batch, batch_id = transaction.make_batch_and_id([data_txn], signer)

    await security_messaging.transfer(
        request.app.config.VAL_CONN,
        request.app.config.TIMEOUT,
        [batch])

    try:
        await security_messaging.check_batch_status(
            request.app.config.VAL_CONN, [batch_id])
    except (ApiBadRequest, ApiInternalError) as err:
        raise err

    return response.json(body={'status': general.DONE},
                         headers=general.get_response_headers())


@TOKEN_BP.get('token/transfer/<token_hex>')
async def get_transfers(request, token_hex):
    transfers = await security_messaging.get_transfers(request.app.config.VAL_CONN, token_hex)

    transfers_json = []
    for address, trans in transfers.items():
        transfers_json.append({
            "date": helper.get_date_time_string_from_timestamp(float(trans.date)),
            "from_name": trans.sender_name,
            "from_address": trans.sender_pkey,
            "to_name": trans.receiver_name,
            "to_address": trans.receiver_pkey,
            "amount": trans.asset.total_supply
        })
    return response.json(body={'data': transfers_json},
                         headers=general.get_response_headers())


@TOKEN_BP.get('token/wallet')
async def get_wallet(request):
    tokens = await security_messaging.get_wallet(request.app.config.VAL_CONN)
    tokens_json = []
    for address, token in tokens.items():
        attributes = []
        for attr_level_1 in token.attributes:
            attributes_level2 = []
            for attr_level_2 in attr_level_1.value:
                attributes_level2.append({"key": attr_level_2.key,
                                           "value": attr_level_2.value})
            attributes.append({"key": attr_level_1.key,
                                "value": attributes_level2})

        immutables = []
        for attr_level_1 in token.immutables:
            attributes_level2 = []
            for attr_level_2 in attr_level_1.value:
                attributes_level2.append({"key": attr_level_2.key,
                                           "value": attr_level_2.value})
            immutables.append({"key": attr_level_1.key,
                                "value": attributes_level2})
        tokens_json.append({
            "token_hex": address,
            "identifier": token.name,
            "issuer_pkey": token.issuer_pkey,
            "status": Token.StatusType.Name(token.status),
            "total_supply": str(token.total_supply),
            "attributes": attributes,
            "immutables": immutables
        })
    return response.json(body={'data': tokens_json},
                         headers=general.get_response_headers())


@TOKEN_BP.post('token/<account_pkey>/attributes')
async def set_balance_attributes(request, account_pkey):
    required_fields = ['attributes']
    general.validate_fields(required_fields, request.json)

    attributes = request.json.get('attributes')

    signer = request.app.config.SIGNER
    client_pkey = signer.get_public_key().as_hex()
    manager = await security_messaging.get_manager(request.app.config.VAL_CONN)
    if manager is None:
        raise ApiForbidden("Manager not exists")
    else:
        if manager.public_key != client_pkey:
            raise ApiForbidden("Manager's role is required")

    holder_balances = await security_messaging.get_account_balances(request.app.config.VAL_CONN, account_pkey)
    identifiers = []

    for address, balance in holder_balances.items():
        identifiers.append(balance.asset.name)

    set_balance_attributes_txn = transaction.set_balance_attributes(
        txn_signer=signer,
        batch_signer=signer,
        account_pkey=account_pkey,
        identifiers=identifiers,
        attributes=attributes
    )

    batch, batch_id = transaction.make_batch_and_id([set_balance_attributes_txn], signer)

    await security_messaging.set_balance_attributes(
        request.app.config.VAL_CONN,
        request.app.config.TIMEOUT,
        [batch])

    try:
        await security_messaging.check_batch_status(
            request.app.config.VAL_CONN, [batch_id])
    except (ApiBadRequest, ApiInternalError) as err:
        raise err

    return response.json(body={'status': general.DONE},
                         headers=general.get_response_headers())


@TOKEN_BP.get('token/<account_pkey>/attributes')
async def get_balance_attributes(request, account_pkey):
    client_pkey = request.app.config.SIGNER.get_public_key().as_hex()
    manager = await security_messaging.get_manager(request.app.config.VAL_CONN)
    if manager is None:
        raise ApiForbidden("Manager not exists")
    else:
        if manager.public_key != client_pkey:
            raise ApiForbidden("Manager's role is required")
    balances = await security_messaging.get_account_balances(request.app.config.VAL_CONN, account_pkey)

    attributes_json = []
    # Get first balance from the dict
    for address, bal in balances.items():
        for attr in bal.attributes:
            attributes_json.append({"key": attr.key,
                                    "value": attr.value})
        break

    return response.json(body={'data': attributes_json},
                         headers=general.get_response_headers())
