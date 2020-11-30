import argparse
import asyncio
import logging
import os
from signal import signal, SIGINT
import sys
from sanic import Sanic
from zmq.asyncio import ZMQEventLoop

from sawtooth_signing import create_context
from sawtooth_signing import ParseError
from sawtooth_signing import CryptoFactory
from sawtooth_rest_api.messaging import Connection

from rest_api.general import get_keyfile, get_signer_from_file
from rest_api.account import ACCOUNTS_BP
from rest_api.token import TOKEN_BP

logging.basicConfig(level=logging.DEBUG)
LOGGER = logging.getLogger(__name__)
DEFAULT_CONFIG = {
    'HOST': 'localhost',
    'PORT': 8000,
    'TIMEOUT': 500,
    'VALIDATOR_URL': 'tcp://localhost:4004',
    'DEBUG': True,
    'BATCHER_PRIVATE_KEY_FILE_NAME': 'clientWEB'
}


async def open_connections(appl):
    appl.config.VAL_CONN = Connection(appl.config.VALIDATOR_URL)
    LOGGER.warning('opening validator connection: ' + str(appl.config.VALIDATOR_URL))
    appl.config.VAL_CONN.open()


def close_connections(appl):
    LOGGER.warning('closing validator connection EHR network')
    appl.config.VAL_CONN.close()


def parse_args(args):
    parser = argparse.ArgumentParser()
    parser.add_argument('--host',
                        help='The host for the api to run on.')
    parser.add_argument('--port',
                        help='The port for the api to run on.')
    parser.add_argument('--timeout',
                        help='Seconds to wait for a validator response')
    parser.add_argument('--validator',
                        help='The url to connect to a running validator network')
    parser.add_argument('--debug',
                        help='Option to run Sanic in debug mode')
    parser.add_argument('--batcher-private-key-file-name',
                        help='The sawtooth key used for transaction signing')
    return parser.parse_args(args)


def load_config(appl):  # pylint: disable=too-many-branches
    appl.config.update(DEFAULT_CONFIG)
    config_file_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.realpath(__file__))),
        'rest_api/config.py')
    try:
        LOGGER.info('Path: ' + str(config_file_path))
        appl.config.from_pyfile(config_file_path)
    except FileNotFoundError:
        LOGGER.warning("No config file provided")

    # CLI Options will override config file options
    opts = parse_args(sys.argv[1:])

    if opts.host is not None:
        appl.config.HOST = opts.host
    if opts.port is not None:
        appl.config.PORT = opts.port
    if opts.timeout is not None:
        appl.config.TIMEOUT = opts.timeout

    if opts.validator is not None:
        appl.config.VALIDATOR_URL = opts.validator

    if opts.debug is not None:
        appl.config.DEBUG = opts.debug

    if opts.batcher_private_key_file_name is not None:
        appl.config.BATCHER_PRIVATE_KEY_FILE_NAME = opts.batcher_private_key_file_name
    if appl.config.BATCHER_PRIVATE_KEY_FILE_NAME is None:
        LOGGER.exception("Batcher private key file name was not provided")
        sys.exit(1)

    try:
        private_key_file_name = get_keyfile(appl.config.BATCHER_PRIVATE_KEY_FILE_NAME)
        private_key = get_signer_from_file(private_key_file_name)
    except ParseError as err:
        LOGGER.exception('Unable to load private key: %s', str(err))
        sys.exit(1)
    appl.config.CONTEXT = create_context('secp256k1')
    appl.config.SIGNER = CryptoFactory(
        appl.config.CONTEXT).new_signer(private_key)


app = Sanic(__name__)
app.config['CORS_AUTOMATIC_OPTIONS'] = True


@app.middleware('request')
async def print_on_request(request):
    LOGGER.debug('Request: ' + str({"parsed": True,
                                    "args": request.args,
                                    "url": request.url,
                                    "query_string": request.query_string,
                                    "json": request.json}))


@app.middleware('response')
async def print_on_response(request, response):
    LOGGER.debug('Response: ' + str({"body": response.body}))


def main():
    LOGGER.info('Starting DA Rest API server...')
    app.blueprint(ACCOUNTS_BP)
    app.blueprint(TOKEN_BP)
    load_config(app)
    zmq = ZMQEventLoop()
    asyncio.set_event_loop(zmq)
    server = app.create_server(
        host=app.config.HOST, port=app.config.PORT, debug=app.config.DEBUG, return_asyncio_server=True)
    loop = asyncio.get_event_loop()
    asyncio.ensure_future(open_connections(app))
    asyncio.ensure_future(server)
    signal(SIGINT, lambda s, f: loop.close())
    try:
        LOGGER.info('DA Rest API server starting')
        loop.run_forever()
    except KeyboardInterrupt:
        LOGGER.info('DA Rest API started interrupted')
        close_connections(app)
        loop.stop()


if __name__ == "__main__":
    main()
