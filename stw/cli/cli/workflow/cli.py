import argparse
import getpass
import logging
import os
import sys
import traceback

import pkg_resources
from colorlog import ColoredFormatter
from sawtooth_signing import create_context

from cli.common.helper import DISTRIBUTION_NAME, DEFAULT_URL
from cli.common.exceptions import DaException
from cli.workflow.client import DaClient


def create_console_handler(verbose_level):
    clog = logging.StreamHandler()
    formatter = ColoredFormatter(
        "%(log_color)s[%(asctime)s %(levelname)-8s%(module)s]%(reset)s "
        "%(white)s%(message)s",
        datefmt="%H:%M:%S",
        reset=True,
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'red',
        })

    clog.setFormatter(formatter)

    if verbose_level == 0:
        clog.setLevel(logging.WARN)
    elif verbose_level == 1:
        clog.setLevel(logging.INFO)
    else:
        clog.setLevel(logging.DEBUG)

    return clog


def setup_loggers(verbose_level):
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    logger.addHandler(create_console_handler(verbose_level))


def add_set_manager_parser(subparsers, parent_parser):
    parser = subparsers.add_parser(
        'set_manager',
        help='Set Manager',
        description='Create first account on the blockchain which has manager role by default',
        parents=[parent_parser])

    parser.add_argument(
        '--name',
        type=str,
        required=True,
        help='specify account name')

    parser.add_argument(
        '--key-dir',
        type=str,
        help="identify directory of user's private key file")

    parser.add_argument(
        '--url',
        type=str,
        help='specify URL of REST API')

    parser.add_argument(
        '--username',
        type=str,
        help="identify name of user's private key file")

    parser.add_argument(
        '--wait',
        nargs='?',
        const=sys.maxsize,
        type=int,
        help='set time, in seconds, to wait for game to commit')


def add_set_issuer_parser(subparsers, parent_parser):
    parser = subparsers.add_parser(
        'set_issuer',
        help='Set Issuer',
        description='Create first account on the blockchain which has issuer role by default',
        parents=[parent_parser])

    parser.add_argument(
        '--name',
        type=str,
        required=True,
        help='specify account name')

    parser.add_argument(
        '--key-dir',
        type=str,
        help="identify directory of user's private key file")

    parser.add_argument(
        '--url',
        type=str,
        help='specify URL of REST API')

    parser.add_argument(
        '--username',
        type=str,
        help="identify name of user's private key file")

    parser.add_argument(
        '--wait',
        nargs='?',
        const=sys.maxsize,
        type=int,
        help='set time, in seconds, to wait for game to commit')


def add_set_account_parser(subparsers, parent_parser):
    parser = subparsers.add_parser(
        'set_account',
        help='Set Account',
        description='Create new account on the blockchain',
        parents=[parent_parser])

    parser.add_argument(
        '--name',
        type=str,
        required=True,
        help='specify account name')

    parser.add_argument(
        '--key-dir',
        type=str,
        help="identify directory of user's private key file")

    parser.add_argument(
        '--url',
        type=str,
        help='specify URL of REST API')

    parser.add_argument(
        '--username',
        type=str,
        help="identify name of user's private key file")

    parser.add_argument(
        '--wait',
        nargs='?',
        const=sys.maxsize,
        type=int,
        help='set time, in seconds, to wait for game to commit')


def add_issue_token_parser(subparsers, parent_parser):
    parser = subparsers.add_parser(
        'issue_token',
        help='Issue new token',
        description='Sends a transaction to issue new token',
        parents=[parent_parser])

    parser.add_argument(
        '--identifier',
        type=str,
        required=True,
        help='specify token name')

    parser.add_argument(
        '--total_supply',
        type=str,
        required=True,
        default='100',
        help='total supply')

    parser.add_argument(
        '--key-dir',
        type=str,
        help="identify directory of user's private key file")

    parser.add_argument(
        '--url',
        type=str,
        help='specify URL of REST API')

    parser.add_argument(
        '--username',
        type=str,
        help="identify name of user's private key file")

    parser.add_argument(
        '--wait',
        nargs='?',
        const=sys.maxsize,
        type=int,
        help='set time, in seconds, to wait for game to commit')


def add_transfer_parser(subparsers, parent_parser):
    parser = subparsers.add_parser(
        'transfer',
        help='Transfer asset',
        description='Sends a transaction to transfer an asset',
        parents=[parent_parser])

    parser.add_argument(
        '--identifier',
        type=str,
        required=True,
        help='specify token name')

    parser.add_argument(
        '--total_supply',
        type=str,
        required=True,
        help='total supply')

    parser.add_argument(
        '--receiver_pkey',
        type=str,
        required=True,
        help='Receiver public key')

    parser.add_argument(
        '--key-dir',
        type=str,
        help="identify directory of user's private key file")

    parser.add_argument(
        '--url',
        type=str,
        help='specify URL of REST API')

    parser.add_argument(
        '--username',
        type=str,
        help="identify name of user's private key file")

    parser.add_argument(
        '--sender_private_key',
        type=str,
        help="Sender's private key. Used in scheduled job")

    parser.add_argument(
        '--wait',
        nargs='?',
        const=sys.maxsize,
        type=int,
        help='set time, in seconds, to wait for game to commit')


def add_heartbeat_parser(subparsers, parent_parser):
    parser = subparsers.add_parser(
        'heartbeat',
        help='Heartbeat program',
        description='Sends an asset to balance holders proportionally',
        parents=[parent_parser])

    parser.add_argument(
        '--identifier',
        type=str,
        required=True,
        help='specify token name')

    parser.add_argument(
        '--key-dir',
        type=str,
        help="identify directory of user's private key file")

    parser.add_argument(
        '--url',
        type=str,
        help='specify URL of REST API')

    parser.add_argument(
        '--username',
        type=str,
        help="identify name of user's private key file")

    parser.add_argument(
        '--issuer_public_key',
        type=str,
        help="Issuer's public key. Used in scheduled job")

    parser.add_argument(
        '--date',
        type=str,
        help="Payment date. Used in scheduled job. Current date by default")

    parser.add_argument(
        '--wait',
        nargs='?',
        const=sys.maxsize,
        type=int,
        help='set time, in seconds, to wait for game to commit')


def create_parent_parser(prog_name):
    parent_parser = argparse.ArgumentParser(prog=prog_name, add_help=False)
    parent_parser.add_argument(
        '-v', '--verbose',
        action='count',
        help='enable more verbose output')

    try:
        version = pkg_resources.get_distribution(DISTRIBUTION_NAME).version
    except pkg_resources.DistributionNotFound:
        version = 'UNKNOWN'

    parent_parser.add_argument(
        '-V', '--version',
        action='version',
        version=(DISTRIBUTION_NAME + ' (Hyperledger Sawtooth) version {}').format(version),
        help='display version information')

    return parent_parser


def create_parser(prog_name):
    parent_parser = create_parent_parser(prog_name)

    parser = argparse.ArgumentParser(
        description='Provides subcommands to Da.',
        parents=[parent_parser])

    subparsers = parser.add_subparsers(title='subcommands', dest='command')

    subparsers.required = True

    add_set_manager_parser(subparsers, parent_parser)
    add_set_issuer_parser(subparsers, parent_parser)
    add_set_account_parser(subparsers, parent_parser)
    add_issue_token_parser(subparsers, parent_parser)
    add_transfer_parser(subparsers, parent_parser)
    add_heartbeat_parser(subparsers, parent_parser)
    return parser


def do_set_manager(args):
    name = args.name

    url = _get_url(args)
    keyfile = _generate_keyfile(args)

    client = DaClient(base_url=url, keyfile=keyfile)

    if args.wait and args.wait > 0:
        response = client.set_manager(
            name, wait=args.wait)
    else:
        response = client.set_manager(name)

    print("Response: {}".format(response))


def do_set_issuer(args):
    name = args.name

    url = _get_url(args)
    keyfile = _generate_keyfile(args)

    client = DaClient(base_url=url, keyfile=keyfile)

    if args.wait and args.wait > 0:
        response = client.set_issuer(
            name, wait=args.wait)
    else:
        response = client.set_issuer(name)

    print("Response: {}".format(response))


def do_set_account(args):
    name = args.name

    url = _get_url(args)
    keyfile = _generate_keyfile(args)

    client = DaClient(base_url=url, keyfile=keyfile)

    if args.wait and args.wait > 0:
        response = client.set_account(
            name, wait=args.wait)
    else:
        response = client.set_account(name)

    print("Response: {}".format(response))


def do_issue_token(args):
    identifier = args.identifier
    total_supply = float(args.total_supply)

    url = _get_url(args)
    keyfile = _get_keyfile(args)

    client = DaClient(base_url=url, keyfile=keyfile)

    if args.wait and args.wait > 0:
        response = client.issue_token(
            identifier=identifier,
            total_supply=total_supply,
            wait=args.wait)
    else:
        response = client.issue_token(
            identifier=identifier,
            total_supply=total_supply)

    print("Response: {}".format(response))


def do_transfer(args):
    receiver_pkey = args.receiver_pkey
    identifier = args.identifier
    total_supply = float(args.total_supply)

    url = _get_url(args)
    keyfile = _get_keyfile(args)
    key = args.sender_private_key

    client = DaClient(base_url=url, keyfile=keyfile, key=key)

    if args.wait and args.wait > 0:
        response = client.transfer(
            receiver_pkey=receiver_pkey,
            total_supply=total_supply,
            identifier=identifier,
            wait=args.wait)
    else:
        response = client.transfer(
            receiver_pkey=receiver_pkey,
            identifier=identifier,
            total_supply=total_supply)

    print("Response: {}".format(response))


def do_heartbeat(args):
    identifier = args.identifier
    url = _get_url(args)
    keyfile = _get_keyfile(args)
    issuer_public_key = args.issuer_public_key
    date_str = args.date
    client = DaClient(base_url=url, keyfile=keyfile)

    if args.wait and args.wait > 0:
        response = client.heartbeat(
            issuer_public_key=issuer_public_key,
            identifier=identifier,
            date=date_str,
            wait=args.wait)
    else:
        response = client.heartbeat(
            issuer_public_key=issuer_public_key,
            identifier=identifier,
            date=date_str)

    print("Response: {}".format(response))


def _get_url(args):
    return DEFAULT_URL if args.url is None else args.url


def _get_keyfile(args):
    name = getpass.getuser() if args.username is None else args.username
    if args.key_dir is None:
        home = os.path.expanduser("~")
        key_dir = os.path.join(home, ".sawtooth", "keys")
        return '{}/{}.priv'.format(key_dir, name)
    else:
        folder = args.key_dir
        return '{}/{}.priv'.format(folder, name)


def _generate_keyfile(args):
    keyfilename = _get_keyfile(args)
    if not (os.path.exists(keyfilename) and os.path.isfile(keyfilename)):
        os.makedirs(os.path.dirname(keyfilename), exist_ok=True)
        keyfile = open(keyfilename, "w")
        keyfile.write(_make_key())
        keyfile.close()
    return keyfilename


def _make_key():
    context = create_context('secp256k1')
    private_key = context.new_random_private_key()
    return private_key.as_hex()


def main(prog_name=os.path.basename(sys.argv[0]), args=None):
    if args is None:
        args = sys.argv[1:]
    parser = create_parser(prog_name)
    args = parser.parse_args(args)

    if args.verbose is None:
        verbose_level = 0
    else:
        verbose_level = args.verbose

    setup_loggers(verbose_level=verbose_level)

    if args.command == 'set_manager':
        do_set_manager(args)
    elif args.command == 'set_account':
        do_set_account(args)
    elif args.command == 'set_issuer':
        do_set_issuer(args)
    elif args.command == 'issue_token':
        do_issue_token(args)
    elif args.command == 'transfer':
        do_transfer(args)
    elif args.command == 'heartbeat':
        do_heartbeat(args)
    else:
        raise DaException("invalid command: {}".format(args.command))


def main_wrapper():
    try:
        main()
    except DaException as err:
        print("Error: {}".format(err), file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        pass
    except SystemExit as err:
        raise err
    except BaseException as err:
        print("Error: {}".format(err), file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
