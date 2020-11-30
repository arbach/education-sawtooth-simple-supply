import logging
from sawtooth_sdk.processor.exceptions import InvalidTransaction
from sawtooth_sdk.processor.handler import TransactionHandler

import token_processor.common.helper as helper
from token_processor.common.protobuf.payload_pb2 import Token, Transfer, Balance
from token_processor.payload import TokenPayload
from token_processor.state import TokenState

logging.basicConfig(level=logging.DEBUG)
LOGGER = logging.getLogger(__name__)


class TokenTransactionHandler(TransactionHandler):
    def __init__(self, namespace_prefix):
        self._namespace_prefix = namespace_prefix

    @property
    def family_name(self):
        return helper.TP_FAMILYNAME

    @property
    def family_versions(self):
        return [helper.TP_VERSION]

    @property
    def namespaces(self):
        return [self._namespace_prefix]

    def apply(self, transaction, context):
        try:
            _display("i'm inside handler _display")

            header = transaction.header
            signer = header.signer_public_key
            LOGGER.debug("signer_public_key: " + str(signer))
            LOGGER.debug("transaction payload: " + str(transaction.payload))
            payload = TokenPayload(payload=transaction.payload)

            state = TokenState(context)

            if payload.is_set_manager():
                manager = payload.set_manager()

                man = state.get_manager()
                if man is not None:
                    raise InvalidTransaction(
                        'Invalid action: Manager already exists: ' + man.name)

                state.set_manager(manager)

            elif payload.is_set_issuer():

                issuer = payload.set_issuer()

                iss = state.get_issuer()

                if iss is not None:
                    raise InvalidTransaction(

                        'Invalid action: Issuer already exists: ' + iss.name)

                state.set_issuer(issuer)
                token = Token(
                    name=helper.CASH_TOKEN,
                    issuer_pkey=signer,
                    total_supply=1000000000.0
                )
                state.issue_token(token)

            elif payload.is_set_account():
                account = payload.set_account()

                acc = state.get_account(signer)
                if acc is not None:
                    raise InvalidTransaction(
                        'Invalid action: Account already exists: ' + acc.name)

                state.set_account(account)

            elif payload.is_add_immutables():
                token_with_immutables = payload.add_immutables()
                LOGGER.debug("token_with_immutables: " + str(token_with_immutables))

                if token_with_immutables.immutables is None or len(token_with_immutables.immutables) == 0:
                    raise InvalidTransaction(
                        'Invalid action: immutables list is empty. Nothing to add')

                man = state.get_manager()
                if man is None:
                    raise InvalidTransaction(
                        'Invalid action: Manager not registered')

                if man.public_key != signer:
                    raise InvalidTransaction(
                        'Invalid action: Your account should have manager role: ' + signer)

                token = state.get_token(token_with_immutables.name)
                LOGGER.debug("token: " + str(token))

                if token.status == Token.INACTIVE:
                    raise InvalidTransaction(
                        'Invalid action: Token has INACTIVE status: ' + token.name)

                final_immutables = token_with_immutables.immutables
                if token.immutables is not None and len(token.immutables) > 0:
                    LOGGER.debug("token.immutables is not empty: " + str(token.immutables))
                    initial_immutables = token.immutables
                    duplicated_immutables = []
                    for attr in token_with_immutables.immutables:
                        LOGGER.debug("attr: " + str(attr))
                        for orig_attr in initial_immutables:
                            LOGGER.debug("orig_attr: " + str(orig_attr))
                            if attr.key == orig_attr.key:
                                LOGGER.debug("attr.key == orig_attr.key: True")
                                duplicated_immutables.append(attr.key)
                                break
                    if len(duplicated_immutables) != 0:
                        raise InvalidTransaction(
                            'Invalid action: immutables already exist(s): ' + str(duplicated_immutables))
                    else:
                        final_immutables.extend(initial_immutables)

                LOGGER.debug("final_immutables: " + str(final_immutables))
                new_token = Token(
                    name=token.name,
                    issuer_pkey=token.issuer_pkey,
                    total_supply=token.total_supply,
                    attributes=token.attributes,
                    immutables=final_immutables
                )
                state.set_immutables(new_token)

            elif payload.is_set_endorsement():
                account = payload.set_endorsement()
                new_endorsement = account.endorsement

                man = state.get_manager()
                if man is None:
                    raise InvalidTransaction(
                        'Invalid action: Manager not registered')

                if man.public_key != signer:
                    raise InvalidTransaction(
                        'Invalid action: Your account should have manager role: ' + signer)

                orig_account = state.get_account(account.public_key)
                if orig_account is None:
                    raise InvalidTransaction(
                        'Invalid action: Account not registered: ' + account.public_key)

                LOGGER.debug("orig_account before update: " + str(orig_account))
                del orig_account.endorsement[:]
                orig_account.endorsement.extend(new_endorsement)
                LOGGER.debug("orig_account after update: " + str(orig_account))
                state.set_endorsement(orig_account)

            elif payload.is_issue_token():
                token = payload.issue_token()

                man = state.get_manager()
                if man is None:
                    raise InvalidTransaction(
                        'Invalid action: Manager not registered')

                if man.public_key != signer:
                    raise InvalidTransaction(
                        'Invalid action: Your account should have manager role: ' + signer)

                tn = state.get_token(token.name)
                if tn is not None:
                    raise InvalidTransaction(
                        'Invalid action: Token already issued: ' + tn.name)
                if token.total_supply <= 0.0:
                    raise InvalidTransaction('Invalid action: Can not issue negative or zero value')

                token.issuer_pkey = signer
                state.issue_token(token)

            elif payload.is_set_token_status():
                token = payload.set_token_status()

                man = state.get_manager()
                if man is None:
                    raise InvalidTransaction(
                        'Invalid action: Manager not registered')

                if man.public_key != signer:
                    raise InvalidTransaction(
                        'Invalid action: Your account should have manager role: ' + signer)

                tn = state.get_token(token.name)
                LOGGER.debug("token: " + str(token))
                if tn is None:
                    raise InvalidTransaction(
                        'Invalid action: Token not issued: ' + token.name)

                tn.status = token.status

                state.set_token_status(tn)

            elif payload.is_transfer():
                transfer = payload.transfer()

                sender = state.get_account(transfer.sender_pkey)
                if sender is None:
                    raise InvalidTransaction(
                        'Invalid action: Sender account not registered: ' + transfer.sender_pkey)

                receiver = state.get_account(transfer.receiver_pkey)
                if receiver is None:
                    raise InvalidTransaction(
                        'Invalid action: Receiver account not registered: ' + transfer.receiver_pkey)

                token = state.get_token(transfer.asset.name)
                if token is None:
                    raise InvalidTransaction(
                        'Invalid action: Token not issued: ' + transfer.asset.name)

                if token.status == Token.INACTIVE:
                    raise InvalidTransaction(
                        'Invalid action: Token has INACTIVE status: ' + token.name)

                sender_balance = state.get_balance(transfer.sender_pkey, transfer.asset.name)
                if sender_balance is None:
                    raise InvalidTransaction(
                        'Invalid action: No balance: ' + transfer.sender_pkey)

                total_transfer = transfer.asset.total_supply
                if total_transfer <= 0.0:
                    raise InvalidTransaction('Invalid action: Can not transfer negative or zero value')
                if sender_balance.asset.total_supply < total_transfer:
                    raise InvalidTransaction('Invalid action: Not enough balance for the transfer')
                res_bool, res_msg = helper.detectTransferRestriction(receiver, token)
                if not res_bool:
                    raise InvalidTransaction('Invalid action: ' + res_msg)
                state.transfer(transfer=transfer, sender_name=sender.name, receiver_name=receiver.name)

            elif payload.is_heartbeat():
                heartbeat = payload.heartbeat()

                iss = state.get_issuer()
                if iss is None:
                    raise InvalidTransaction(
                        'Invalid action: Issuer not registered')

                LOGGER.debug("issuer: " + str(iss.public_key))
                sender_name = iss.name
                # Check all balance holders exist & and have a positive balance
                receiver_names = {}
                for receiver_pkey in heartbeat.receivers_pkey:
                    receiver = state.get_account(receiver_pkey)
                    if receiver is None:
                        raise InvalidTransaction(
                            'Invalid action: Receiver account not registered: ' + receiver_pkey)
                    LOGGER.debug("receiver: " + str(receiver))
                    receiver_balance = state.get_balance(receiver_pkey, heartbeat.asset.name)
                    if receiver_balance is None:
                        raise InvalidTransaction(
                            'Invalid action: Receiver has no balance: ' + receiver_pkey)
                    LOGGER.debug("receiver_balance: " + str(receiver_balance))
                    receiver_names[receiver.public_key] = receiver.name
                # Check 'Cash Token' exists and has payments attribute
                cash_token = state.get_token(helper.CASH_TOKEN)
                if cash_token is None:
                    raise InvalidTransaction(
                        'Invalid action: Cash Token not issued: ' + helper.CASH_TOKEN)
                LOGGER.debug("cash token name: " + str(cash_token))
                if cash_token.status == Token.INACTIVE:
                    raise InvalidTransaction(
                        'Invalid action: Token has INACTIVE status: ' + cash_token.name)

                cash_token_hex = helper.make_token_address(identifier=helper.CASH_TOKEN)
                LOGGER.debug("cash token hex: " + str(cash_token_hex))
                # Check token exists and has payments attribute
                token = state.get_token(heartbeat.asset.name)
                if token is None:
                    raise InvalidTransaction(
                        'Invalid action: Token not issued: ' + heartbeat.asset.name)
                LOGGER.debug("token: " + str(token))
                if token.status == Token.INACTIVE:
                    raise InvalidTransaction(
                        'Invalid action: Token has INACTIVE status: ' + token.name)

                payments = []
                for attribute in token.attributes:
                    LOGGER.debug("attribute: " + str(attribute))
                    if attribute.key is not None \
                            and attribute.value is not None \
                            and attribute.key == 'payments':
                        LOGGER.debug("payment item exist!")
                        payments.extend(attribute.value)
                    LOGGER.debug("attribute.key is not None: " + str((True if attribute.key is not None else False)))
                    LOGGER.debug("attribute.value is not None: " +
                                 str((True if attribute.value is not None else False)))
                    LOGGER.debug("attribute.key == payments: " + str((True if attribute.key == 'payments' else False)))
                    LOGGER.debug("attribute.key: " + str(attribute.key))
                    LOGGER.debug("attribute.value: " + str(attribute.value))
                LOGGER.debug("payments: " + str(payments))
                if len(payments) == 0:
                    raise InvalidTransaction(
                        'Invalid action: "payments" attribute does not exist')
                # For each payment perform
                infinite_token = False
                for payment in payments:
                    LOGGER.debug("payment: " + str(payment))
                    date_str = payment.key
                    amount = float(payment.value)
                    if date_str is None:
                        raise InvalidTransaction(
                            'Invalid action: "date" not specified in "payments" attribute')
                    if payment.value is None:
                        raise InvalidTransaction(
                            'Invalid action: "amount" not specified in "payments" attribute')
                    LOGGER.debug("date_str -> " + date_str + "; amount -> " + str(amount))
                    # If payment outdated "MM/DD/YYYY"
                    ts_date = helper.get_date_from_timestamp(float(heartbeat.date))
                    LOGGER.debug("ts_date: " + str(ts_date))
                    payment_date = helper.get_date_from_date_string(date_str)
                    if ts_date == payment_date:
                        LOGGER.debug("Payment scheduled at this date: " + str(date_str))
                        sender_balance = state.get_balance(cash_token.issuer_pkey, cash_token.name)
                        if sender_balance.asset.total_supply < amount:
                            raise InvalidTransaction(
                                "Invalid action: Issuer does not have enough balance "
                                "to pay the heartbeat: asset_name -> " +
                                sender_balance.asset.name + "; required amount -> " +
                                str(amount) + "; available amount -> " +
                                str(sender_balance.asset.total_supply))
                        else:
                            LOGGER.debug("Issuer does have balance to pay heartbeat -> " +
                                         str(sender_balance.asset.total_supply))
                        # Calculate total holders balance
                        LOGGER.debug("token.total_supply: " + str(token.total_supply))
                        # Apply heartbeat for each holder
                        for receiver_pkey in heartbeat.receivers_pkey:
                            LOGGER.debug("Transfer from " + str(iss.public_key) + " to " + str(receiver_pkey))
                            # Calculate Cash Token heartbeat value
                            receiver_token_balance_value = state.get_balance(receiver_pkey, token.name) \
                                .asset.total_supply
                            LOGGER.debug("receiver_token_balance.asset.total_supply: " +
                                         str(receiver_token_balance_value))
                            heartbeat_value = receiver_token_balance_value / token.total_supply * amount
                            LOGGER.debug("heartbeat_value: " + str(heartbeat_value))

                            asset = Token(
                                name=helper.CASH_TOKEN,
                                total_supply=heartbeat_value
                            )

                            heartbeat_asset = Transfer(
                                sender_pkey=iss.public_key,
                                receiver_pkey=receiver_pkey,
                                asset=asset,
                                date=heartbeat.date
                            )
                            state.transfer(transfer=heartbeat_asset,
                                           sender_name=sender_name,
                                           receiver_name=receiver_names[receiver_pkey],
                                           infinite_token=infinite_token)
                    else:
                        LOGGER.debug("No payments at this date: " + str(ts_date))
            elif payload.is_set_balance_attributes():
                balance_attributes = payload.set_balance_attributes()
                for identifier in balance_attributes.identifiers:
                    balance = state.get_balance(balance_attributes.owner_pkey, identifier)
                    if balance is None:
                        raise InvalidTransaction(
                            'Invalid action: Balance for the user does not exist. Account pkey: ' +
                            balance_attributes.owner_pkey + '; Token name: ' + identifier)
                    LOGGER.debug("balance before update: " + str(balance))
                    new_attributes = []
                    for attr in balance_attributes.attributes:
                        bal_attr = Balance.Attribute(
                            key=attr.key,
                            value=attr.value
                        )
                        new_attributes.append(bal_attr)
                    del balance.attributes[:]
                    balance.attributes.extend(new_attributes)
                    LOGGER.debug("balance after update: " + str(balance))
                    state.set_balance(balance)
            else:
                raise InvalidTransaction('Unhandled action: {}'.format(payload.transaction_type()))
        except Exception as e:
            logging.exception(e)
            raise InvalidTransaction(repr(e))


def _display(msg):
    n = msg.count("\n")

    if n > 0:
        msg = msg.split("\n")
        length = max(len(line) for line in msg)
    else:
        length = len(msg)
        msg = [msg]

    # pylint: disable=logging-not-lazy
    LOGGER.debug("+" + (length + 2) * "-" + "+")
    for line in msg:
        LOGGER.debug("+ " + line.center(length) + " +")
    LOGGER.debug("+" + (length + 2) * "-" + "+")
