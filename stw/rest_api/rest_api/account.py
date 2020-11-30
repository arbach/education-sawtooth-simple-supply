from sanic import Blueprint
from sanic import response

from rest_api.common import transaction
from rest_api import general, security_messaging
from rest_api.errors import ApiInternalError, ApiBadRequest, ApiForbidden

ACCOUNTS_BP = Blueprint('account')


@ACCOUNTS_BP.post('account/set_account')
async def set_account(request):
    """Updates auth information for the authorized account"""
    required_fields = ['name']
    general.validate_fields(required_fields, request.json)

    name = request.json.get('name')
    endorsement = request.json.get('endorsement')

    signer = request.app.config.SIGNER  # .get_public_key().as_hex()

    account_txn = transaction.set_account(
        txn_signer=signer,
        batch_signer=signer,
        name=name,
        endorsement=endorsement
    )

    batch, batch_id = transaction.make_batch_and_id([account_txn], signer)

    await security_messaging.set_account(
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


@ACCOUNTS_BP.post('account/set_manager')
async def set_manager(request):
    """Updates auth information for the authorized account"""
    required_fields = ['name']
    general.validate_fields(required_fields, request.json)

    name = request.json.get('name')
    endorsement = request.json.get('endorsement')

    signer = request.app.config.SIGNER  # .get_public_key().as_hex()

    account_txn = transaction.set_manager(
        txn_signer=signer,
        batch_signer=signer,
        name=name,
        endorsement=endorsement
    )

    batch, batch_id = transaction.make_batch_and_id([account_txn], signer)

    await security_messaging.set_manager(
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


@ACCOUNTS_BP.post('account/set_issuer')
async def set_issuer(request):
    """Updates auth information for the authorized account"""
    required_fields = ['name']
    general.validate_fields(required_fields, request.json)

    name = request.json.get('name')
    endorsement = request.json.get('endorsement')

    signer = request.app.config.SIGNER

    issuer_txn = transaction.set_issuer(
        txn_signer=signer,
        batch_signer=signer,
        name=name,
        endorsement=endorsement
    )

    batch, batch_id = transaction.make_batch_and_id([issuer_txn], signer)

    await security_messaging.set_issuer(
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


@ACCOUNTS_BP.get('account/wallet/<public_key>')
async def get_all_balances_by_account(request, public_key):
    client_pkey = request.app.config.SIGNER.get_public_key().as_hex()
    manager = await security_messaging.get_manager(request.app.config.VAL_CONN)
    if manager is None:
        raise ApiForbidden("Manager not exists")
    else:
        if manager.public_key != client_pkey:
            raise ApiForbidden("Manager's role is required")
    balances = await security_messaging.get_account_balances(request.app.config.VAL_CONN, public_key)
    balances_json = []
    for address, bal in balances.items():
        balances_json.append({
            "token_hex": bal.token_hex,
            "identifier": bal.asset.name,
            "total_supply": bal.asset.total_supply
        })

    return response.json(body={'data': balances_json},
                         headers=general.get_response_headers())


@ACCOUNTS_BP.get('account/wallet')
async def get_own_balances(request):
    client_pkey = request.app.config.SIGNER.get_public_key().as_hex()
    balances = await security_messaging.get_account_balances(request.app.config.VAL_CONN, client_pkey)
    balances_json = []
    for address, bal in balances.items():
        balances_json.append({
            "token_hex": bal.token_hex,
            "identifier": bal.asset.name,
            "total_supply": bal.asset.total_supply
        })

    return response.json(body={'data': balances_json},
                         headers=general.get_response_headers())


@ACCOUNTS_BP.post('account/<account_pkey>/attributes')
async def set_endorsement(request, account_pkey):
    """Updates auth information for the authorized account"""
    endorsement = request.json.get('endorsement')

    signer = request.app.config.SIGNER
    client_pkey = signer.get_public_key().as_hex()
    manager = await security_messaging.get_manager(request.app.config.VAL_CONN)
    if manager is None:
        raise ApiForbidden("Manager not exists")
    else:
        if manager.public_key != client_pkey:
            raise ApiForbidden("Manager's role is required")

    set_endorsement_txn = transaction.set_endorsement(
        txn_signer=signer,
        batch_signer=signer,
        account_pkey=account_pkey,
        endorsement=endorsement
    )

    batch, batch_id = transaction.make_batch_and_id([set_endorsement_txn], signer)

    await security_messaging.set_endorsement(
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

