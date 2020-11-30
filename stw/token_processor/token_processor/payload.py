from token_processor.common.protobuf.payload_pb2 import TransactionPayload


class TokenPayload(object):

    def __init__(self, payload):
        self._transaction = TransactionPayload()
        self._transaction.ParseFromString(payload)

    def set_manager(self):
        return self._transaction.set_manager

    def set_issuer(self):
        return self._transaction.set_issuer

    def set_account(self):
        return self._transaction.set_account

    def add_immutables(self):
        return self._transaction.add_immutables

    def issue_token(self):
        return self._transaction.issue_token

    def set_token_status(self):
        return self._transaction.set_token_status

    def set_endorsement(self):
        return self._transaction.set_endorsement

    def set_balance_attributes(self):
        return self._transaction.set_balance_attributes

    def transfer(self):
        return self._transaction.transfer

    def heartbeat(self):
        return self._transaction.heartbeat

    def is_set_manager(self):
        return self._transaction.payload_type == TransactionPayload.SET_MANAGER

    def is_set_issuer(self):
        return self._transaction.payload_type == TransactionPayload.SET_ISSUER

    def is_set_account(self):
        return self._transaction.payload_type == TransactionPayload.SET_ACCOUNT

    def is_add_immutables(self):
        return self._transaction.payload_type == TransactionPayload.ADD_IMMUTABLE

    def is_set_endorsement(self):
        return self._transaction.payload_type == TransactionPayload.SET_ENDORSEMENT

    def is_set_balance_attributes(self):
        return self._transaction.payload_type == TransactionPayload.SET_BALANCE_ATTRIBUTES

    def is_issue_token(self):
        return self._transaction.payload_type == TransactionPayload.ISSUE_TOKEN

    def is_set_token_status(self):
        return self._transaction.payload_type == TransactionPayload.SET_TOKEN_STATUS

    def is_transfer(self):
        return self._transaction.payload_type == TransactionPayload.TRANSFER

    def is_heartbeat(self):
        return self._transaction.payload_type == TransactionPayload.HEARTBEAT

    def transaction_type(self):
        return self._transaction.payload_type
