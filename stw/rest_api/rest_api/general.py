import getpass
import os
from sawtooth_signing import ParseError
from sawtooth_signing.secp256k1 import Secp256k1PrivateKey
from rest_api.errors import ApiBadRequest
from rest_api.common.exceptions import DaException
import logging

logging.basicConfig(level=logging.DEBUG)
LOGGER = logging.getLogger(__name__)

DONE = 'DONE'


def get_response_headers():
    return {
        'Connection': 'keep-alive'}


def validate_fields(required_fields, request_json):
    try:
        for field in required_fields:
            if request_json.get(field) is None:
                raise ApiBadRequest("{} is required".format(field))
    except (ValueError, AttributeError):
        raise ApiBadRequest("Improper JSON format")


def get_keyfile(user):
    username = getpass.getuser() if user is None else user
    home = os.path.expanduser("~")
    key_dir = os.path.join(home, ".sawtooth", "keys")

    return '{}/{}.priv'.format(key_dir, username)


def get_signer_from_file(keyfile):
    try:
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

    return private_key
