from token_processor.common import helper
from token_processor.common.protobuf.payload_pb2 import Account, Token, Balance, Transfer
import logging

logging.basicConfig(level=logging.DEBUG)
LOGGER = logging.getLogger(__name__)


class TokenState(object):
    TIMEOUT = 3

    def __init__(self, context):
        """Constructor.
        Args:
            context (sawtooth_sdk.processor.context.Context): Access to
                validator state from within the transaction processor.
        """

        self._context = context

    def set_manager(self, account):
        static_hex = helper.make_manager_address()
        account_hex = helper.make_account_address(account_pkey=account.public_key)

        state_account = account.SerializeToString()
        self._context.set_state(
            {account_hex: state_account,
             static_hex: state_account},
            timeout=self.TIMEOUT)

    def set_issuer(self, account):
        static_hex = helper.make_issuer_address()
        account_hex = helper.make_account_address(account_pkey=account.public_key)

        state_account = account.SerializeToString()
        self._context.set_state(
            {account_hex: state_account,
             static_hex: state_account},
            timeout=self.TIMEOUT)

    def set_account(self, account):
        account_hex = helper.make_account_address(account_pkey=account.public_key)

        state_account = account.SerializeToString()
        self._context.set_state(
            {account_hex: state_account},
            timeout=self.TIMEOUT)

    def set_immutables(self, token):
        token_hex = helper.make_token_address(identifier=token.name)

        state_token = token.SerializeToString()
        self._context.set_state(
            {token_hex: state_token},
            timeout=self.TIMEOUT)

    def set_endorsement(self, account):
        account_hex = helper.make_account_address(account_pkey=account.public_key)

        state_account = account.SerializeToString()
        self._context.set_state(
            {account_hex: state_account},
            timeout=self.TIMEOUT)

    def get_token(self, identifier):
        token = None
        token_hex = helper.make_token_address(identifier)
        state_entries = self._context.get_state(
            [token_hex],
            timeout=self.TIMEOUT)
        if state_entries:
            token = Token()
            token.ParseFromString(state_entries[0].data)
        return token

    def get_manager(self):
        manager = None
        static_hex = helper.make_manager_address()
        state_entries = self._context.get_state(
            [static_hex],
            timeout=self.TIMEOUT)
        if state_entries:
            manager = Account()
            manager.ParseFromString(state_entries[0].data)
        return manager

    def get_issuer(self):
        issuer = None
        static_hex = helper.make_issuer_address()
        state_entries = self._context.get_state(
            [static_hex],
            timeout=self.TIMEOUT)
        if state_entries:
            issuer = Account()
            issuer.ParseFromString(state_entries[0].data)
        return issuer

    def get_account(self, account_pkey):
        account = None
        account_hex = helper.make_account_address(account_pkey)
        state_entries = self._context.get_state(
            [account_hex],
            timeout=self.TIMEOUT)
        if state_entries:
            account = Account()
            account.ParseFromString(state_entries[0].data)
        return account

    def set_token_status(self, token):
        token_hex = helper.make_token_address(identifier=token.name)

        state_token = token.SerializeToString()
        self._context.set_state(
            {token_hex: state_token},
            timeout=self.TIMEOUT)

    def issue_token(self, token):
        token_hex = helper.make_token_address(token.name)
        account_token_rel_hex = \
            helper.make_account_tokenhex__relation_address(account_pkey=token.issuer_pkey, token_hex=token_hex)

        token_account_rel_hex = \
            helper.make_tokenhex_account__relation_address(token_hex=token_hex, account_pkey=token.issuer_pkey)

        state_token = token.SerializeToString()
        tkn = Token()
        tkn.name = token.name
        tkn.total_supply = token.total_supply

        balance = Balance()
        balance.owner_pkey = token.issuer_pkey
        balance.asset.CopyFrom(tkn)

        state_balance = balance.SerializeToString()
        self._context.set_state(
            {token_hex: state_token,
             account_token_rel_hex: state_balance,
             token_account_rel_hex: state_balance},
            timeout=self.TIMEOUT)
        LOGGER.debug('token_hex: ' + str(token_hex))

    def get_balance(self, public_key, identifier):
        token_hex = helper.make_token_address(identifier)
        balance = None
        balance_hex = helper.make_account_tokenhex__relation_address(account_pkey=public_key, token_hex=token_hex)
        state_entries = self._context.get_state(
            [balance_hex],
            timeout=self.TIMEOUT)
        if state_entries:
            balance = Balance()
            balance.ParseFromString(state_entries[0].data)
        LOGGER.debug('token: ' + str(balance))
        return balance

    def transfer(self, transfer, sender_name, receiver_name, infinite_token=False):
        sender_balance = self.get_balance(transfer.sender_pkey, transfer.asset.name)
        receiver_balance = self.get_balance(transfer.receiver_pkey, transfer.asset.name)

        if receiver_balance is None:
            token = Token()
            token.name = sender_balance.asset.name
            token.total_supply = 0.0

            receiver_balance = Balance()
            receiver_balance.owner_pkey = transfer.receiver_pkey
            receiver_balance.asset.CopyFrom(token)

        transfer_balance = transfer.asset
        if not infinite_token:
            sender_balance.asset.total_supply = sender_balance.asset.total_supply - transfer_balance.total_supply
        receiver_balance.asset.total_supply = receiver_balance.asset.total_supply + transfer_balance.total_supply

        token_hex = helper.make_token_address(identifier=transfer.asset.name)

        sender_account_token_rel_hex = \
            helper.make_account_tokenhex__relation_address(account_pkey=transfer.sender_pkey,
                                                           token_hex=token_hex)
        receiver_account_token_rel_hex = \
            helper.make_account_tokenhex__relation_address(account_pkey=transfer.receiver_pkey,
                                                           token_hex=token_hex)

        sender_token_account_rel_hex = \
            helper.make_tokenhex_account__relation_address(token_hex=token_hex,
                                                           account_pkey=transfer.sender_pkey)
        receiver_token_account_rel_hex = \
            helper.make_tokenhex_account__relation_address(token_hex=token_hex,
                                                           account_pkey=transfer.receiver_pkey)

        state_receiver_balance = receiver_balance.SerializeToString()
        state_sender_balance = sender_balance.SerializeToString()

        # Init transfer event
        transfer_event = Transfer(
            sender_pkey=transfer.sender_pkey,
            sender_name=sender_name,
            receiver_pkey=transfer.receiver_pkey,
            receiver_name=receiver_name,
            asset=transfer.asset,
            date=transfer.date
        )

        transfer_event_hex = \
            helper.make_transfer__relation_address(token_hex=token_hex,
                                                   from_pkey=transfer.sender_pkey,
                                                   to_pkey=transfer.receiver_pkey,
                                                   timestamp=transfer.date)
        LOGGER.debug('transfer_event_hex: ' + str(transfer_event_hex))
        state_transfer_event = transfer_event.SerializeToString()

        LOGGER.debug('transfer_event: ' + str(transfer_event))
        LOGGER.debug('state_transfer_event: ' + str(state_transfer_event))

        self._context.set_state(
            {
                sender_account_token_rel_hex: state_sender_balance,
                receiver_account_token_rel_hex: state_receiver_balance,
                sender_token_account_rel_hex: state_sender_balance,
                receiver_token_account_rel_hex: state_receiver_balance,
                transfer_event_hex: state_transfer_event
            },
            timeout=self.TIMEOUT)

    def set_balance(self, balance):
        token_hex = helper.make_token_address(identifier=balance.asset.name)

        account_token_rel_hex = \
            helper.make_account_tokenhex__relation_address(account_pkey=balance.owner_pkey,
                                                           token_hex=token_hex)
        token_account_rel_hex = \
            helper.make_tokenhex_account__relation_address(token_hex=token_hex,
                                                           account_pkey=balance.owner_pkey)

        state_balance = balance.SerializeToString()
        LOGGER.debug('state_balance: ' + str(state_balance))

        self._context.set_state(
            {
                account_token_rel_hex: state_balance,
                token_account_rel_hex: state_balance
            },
            timeout=self.TIMEOUT)
