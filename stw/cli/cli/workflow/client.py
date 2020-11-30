import logging
import time
import requests
import base64
import yaml
from sawtooth_sdk.protobuf import batch_pb2
from sawtooth_signing import ParseError, CryptoFactory, create_context
from sawtooth_signing.secp256k1 import Secp256k1PrivateKey

from cli.common import transaction, helper
from cli.common.exceptions import DaException
from cli.common.protobuf.payload_pb2 import Balance

logging.basicConfig(level=logging.DEBUG)
LOGGER = logging.getLogger(__name__)


class DaClient:

    def __init__(self, base_url, keyfile=None, key=None):

        self._base_url = base_url

        if keyfile is None and key is None:
            self._signer = None
            return

        private_key_str = None

        try:

            if key is not None:
                private_key_str = key
            elif keyfile is not None:
                with open(keyfile) as fd:
                    private_key_str = fd.read().strip()

        except OSError as err:
            raise DaException(
                'Failed to read private key {}: {}'.format(
                    keyfile, str(err)))

        try:
            private_key = Secp256k1PrivateKey.from_hex(private_key_str)
        except ParseError as e:
            raise DaException(
                'Unable to load private key: {}'.format(str(e)))

        self._signer = CryptoFactory(create_context('secp256k1')) \
            .new_signer(private_key)

    def set_manager(self, name, wait=None):

        txn = transaction.set_manager(
            txn_signer=self._signer,
            batch_signer=self._signer,
            name=name)

        batch, batch_id = transaction.make_batch_and_id([txn], self._signer)

        batch_list = batch_pb2.BatchList(batches=[batch])

        return self._send_batches(batch_list=batch_list,
                                  batch_id=batch_id,
                                  wait=wait)

    def set_issuer(self, name, wait=None):

        txn = transaction.set_issuer(
            txn_signer=self._signer,
            batch_signer=self._signer,
            name=name)

        batch, batch_id = transaction.make_batch_and_id([txn], self._signer)

        batch_list = batch_pb2.BatchList(batches=[batch])

        return self._send_batches(batch_list=batch_list,
                                  batch_id=batch_id,
                                  wait=wait)

    def set_account(self, name, wait=None):

        txn = transaction.set_account(
            txn_signer=self._signer,
            batch_signer=self._signer,
            name=name)

        batch, batch_id = transaction.make_batch_and_id([txn], self._signer)

        batch_list = batch_pb2.BatchList(batches=[batch])

        return self._send_batches(batch_list=batch_list,
                                  batch_id=batch_id,
                                  wait=wait)

    def issue_token(self, identifier, total_supply, wait=None):

        txn, token_hex = transaction.issue_token(
            txn_signer=self._signer,
            batch_signer=self._signer,
            identifier=identifier,
            total_supply=total_supply,
            attributes=[]
        )

        batch, batch_id = transaction.make_batch_and_id([txn], self._signer)

        batch_list = batch_pb2.BatchList(batches=[batch])

        return self._send_batches(batch_list=batch_list,
                                  batch_id=batch_id,
                                  wait=wait)

    def transfer(self, receiver_pkey, identifier, total_supply, wait=None):

        txn = transaction.transfer(
            txn_signer=self._signer,
            batch_signer=self._signer,
            receiver_pkey=receiver_pkey,
            identifier=identifier,
            total_supply=total_supply
        )

        batch, batch_id = transaction.make_batch_and_id([txn], self._signer)

        batch_list = batch_pb2.BatchList(batches=[batch])

        return self._send_batches(batch_list=batch_list,
                                  batch_id=batch_id,
                                  wait=wait)

    def list_balances(self, token_hex):
        balances_list_prefix = helper.make_accounts_list_by_tokenhex(token_hex)

        result = self._send_request(
            "state?address={}".format(balances_list_prefix))
        balances = {}

        try:
            data = yaml.safe_load(result)["data"]
            if data is not None:
                for entity in data:
                    dec_bal = base64.b64decode(entity["data"])
                    bal = Balance()
                    bal.ParseFromString(dec_bal)
                    balances[entity["address"]] = bal

        except BaseException:
            pass
        LOGGER.debug("balances: " + str(balances))
        return balances

    def heartbeat(self, issuer_public_key, identifier, date=None, wait=None):
        token_hex = helper.make_token_address(identifier=identifier)
        holder_balances = self.list_balances(token_hex)

        holder_addresses = []
        for address, balance in holder_balances.items():
            holder_addresses.append(balance.owner_pkey)

        txn = transaction.heartbeat(
            txn_signer=self._signer,
            batch_signer=self._signer,
            issuer_public_key=issuer_public_key,
            holder_pkey_list=holder_addresses,
            identifier=identifier,
            date=date
        )

        batch, batch_id = transaction.make_batch_and_id([txn], self._signer)

        batch_list = batch_pb2.BatchList(batches=[batch])

        return self._send_batches(batch_list=batch_list,
                                  batch_id=batch_id,
                                  wait=wait)

    def _send_request(self,
                      suffix,
                      data=None,
                      content_type=None,
                      name=None):
        if self._base_url.startswith("http://"):
            url = "{}/{}".format(self._base_url, suffix)
        else:
            url = "http://{}/{}".format(self._base_url, suffix)

        headers = {}

        if content_type is not None:
            headers['Content-Type'] = content_type

        try:
            if data is not None:
                result = requests.post(url, headers=headers, data=data)
            else:
                result = requests.get(url, headers=headers)

            if result.status_code == 404:
                raise DaException("No such operator: {}".format(name))

            elif not result.ok:
                raise DaException("Error {}: {}".format(
                    result.status_code, result.reason))

        except requests.ConnectionError as err:
            raise DaException(
                'Failed to connect to {}: {}'.format(url, str(err)))

        except BaseException as err:
            raise DaException(err)

        return result.text

    def _send_batches(self, batch_list, batch_id, wait):
        if wait and wait > 0:
            wait_time = 0
            start_time = time.time()
            response = self._send_request(
                "batches", batch_list.SerializeToString(),
                'application/octet-stream')
            while wait_time < wait:
                status = self._get_status(
                    batch_id,
                    wait - int(wait_time))
                wait_time = time.time() - start_time

                if status != 'PENDING':
                    return response

            return response

        return self._send_request(
            "batches", batch_list.SerializeToString(),
            'application/octet-stream')

    def _get_status(self, batch_id, wait):
        try:
            result = self._send_request(
                'batch_statuses?id={}&wait={}'.format(batch_id, wait))
            return yaml.safe_load(result)['data'][0]['status']
        except BaseException as err:
            raise DaException(err)
