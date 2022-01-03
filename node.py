from balance_manager import BalanceManager
from blockchain import BlockChain
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from http import HTTPStatus
from os import environ
from typing import Optional
from wallet import Wallet

HOST_ENV_VAR_NAME = 'hostName'
PORT_ENV_VAR_NAME = 'port'

py_coin_app = Flask(__name__)
CORS(py_coin_app)


def init_block_chain():
    global block_chain
    block_chain = BlockChain(wallet.public_key, node_id)
    block_chain.load_data()
    # Notice that we initialize balances using a copy of the chain (via getter)
    balance_manager.initialize_balances(block_chain.chain)


@py_coin_app.route('/', methods=['GET'])
def get_node_ui():
    return send_from_directory('ui', 'node.html')


@py_coin_app.route('/network', methods=['GET'])
def get_network_ui():
    return send_from_directory('ui', 'network.html')


@py_coin_app.route('/wallet', methods=['POST'])
def create_keys():
    wallet.create_keys()
    if wallet.save_keys():
        init_block_chain()
        response = {
            'public_key': wallet.public_key,
            'private_key': wallet.private_key,
            'funds_available': balance_manager.get_balance(wallet.public_key)
        }
        return jsonify(response), HTTPStatus.CREATED
    else:
        response = {
            'message': 'Failed to save wallet keys'
        }
        return jsonify(response), HTTPStatus.INTERNAL_SERVER_ERROR


@py_coin_app.route('/wallet', methods=['GET'])
def load_keys():
    if wallet.load_keys():
        init_block_chain()
        response = {
            'public_key': wallet.public_key,
            'private_key': wallet.private_key,
            'funds_available': balance_manager.get_balance(wallet.public_key)
        }
        return jsonify(response), HTTPStatus.OK
    else:
        response = {
            'message': 'Failed to load wallet keys'
        }
        return jsonify(response), HTTPStatus.INTERNAL_SERVER_ERROR


@py_coin_app.route('/balance', methods=['GET'])
def get_balance():
    response = {
        'balance': balance_manager.get_balance(wallet.public_key)
    }
    return jsonify(response), HTTPStatus.OK


@py_coin_app.route('/transactions', methods=['POST'])
def add_transaction():
    # Respond straight away if wallet keys are not available
    if wallet.public_key is None:
        response = {
            'message': 'Failed to add transaction. Wallet contains no keys'
        }
        return jsonify(response), HTTPStatus.CONFLICT

    req_body = request.get_json()
    if not req_body:
        response = {
            'message': 'No transaction data provided'
        }
        return jsonify(response), HTTPStatus.BAD_REQUEST

    required_fields = ['recipient', 'amount']
    # Check whether request body contains all required fields
    if not all(field in req_body for field in required_fields):
        response = {
            'message': 'Transaction data is missing one or more required fields: ' + str(required_fields)
        }
        return jsonify(response), HTTPStatus.BAD_REQUEST

    signature = wallet.sign_txn(wallet.public_key, req_body['recipient'], req_body['amount'])
    added_txn = block_chain.add_transaction(wallet.public_key, req_body['recipient'], req_body['amount'], signature)
    if added_txn is not None:
        response = {
            'message': 'Transaction added successfully',
            'txn': added_txn.__dict__.copy()
        }
        return jsonify(response), HTTPStatus.CREATED
    else:
        response = {
            'message': 'Failed to add transaction'
        }
        return jsonify(response), HTTPStatus.INTERNAL_SERVER_ERROR


@py_coin_app.route('/transactions', methods=['GET'])
def get_transactions():
    dict_txns = [txn.__dict__ for txn in block_chain.open_txns]
    return jsonify(dict_txns), HTTPStatus.OK


@py_coin_app.route('/resolve', methods=['POST'])
def resolve_conflicts():
    replaced = block_chain.resolve_block_chain()
    response = {
        'message': 'Local block chain was {}'.format('replaced' if replaced else 'kept')
    }
    return jsonify(response), HTTPStatus.OK


@py_coin_app.route('/mine', methods=['POST'])
def mine():
    if block_chain.resolve_conflicts:
        response = {
            'message': 'Block chain conflict requires resolution. No block mined'
        }
        return jsonify(response), HTTPStatus.CONFLICT

    mined_block = block_chain.mine_block(balance_manager.get_balance)
    if mined_block is not None:
        # Now transactions are confirmed, update balances
        balance_manager.update_balances_for_block(mined_block)
        dict_block = mined_block.__dict__.copy()
        dict_block['txns'] = [txn.__dict__ for txn in dict_block['txns']]
        response = {
            'message': 'Block mined successfully',
            'block': dict_block,
            'funds_available': balance_manager.get_balance(wallet.public_key)
        }
        return jsonify(response), HTTPStatus.CREATED
    else:
        response = {
            'message': 'Mine block failed',
            'wallet_initialized': wallet.public_key is not None
        }
        return jsonify(response), HTTPStatus.INTERNAL_SERVER_ERROR


@py_coin_app.route('/chain', methods=['GET'])
def get_chain():
    chain_snapshot = block_chain.chain
    # Our Block and Transaction objects are not JSON serializable
    # so we must convert them into dictionaries
    dict_chain = [block.__dict__.copy() for block in chain_snapshot]
    for dict_block in dict_chain:
        dict_block['txns'] = [txn.__dict__ for txn in dict_block['txns']]
    return jsonify(dict_chain), HTTPStatus.OK


@py_coin_app.route('/nodes', methods=['GET'])
def get_nodes():
    response = {
        'nodes': block_chain.get_peer_nodes()
    }
    return jsonify(response), HTTPStatus.OK


@py_coin_app.route('/nodes', methods=['POST'])
def add_node():
    # Convert the request body into a dictionary
    req_body = request.get_json()
    if not req_body:
        response = {
            'message': 'No data contained in request'
        }
        return jsonify(response), HTTPStatus.BAD_REQUEST

    # Check whether request body dictionary contains the required key (i.e. node)
    if 'node' not in req_body:
        response = {
            'message': 'Node data is missing required field: node'
        }
        return jsonify(response), HTTPStatus.BAD_REQUEST

    node = req_body['node']
    block_chain.add_peer_node(node)
    response = {
        'message': 'Node, {}, successfully added'.format(node),
        'nodes': block_chain.get_peer_nodes()
    }
    return jsonify(response), HTTPStatus.CREATED


@py_coin_app.route('/nodes/<node_url>', methods=['DELETE'])
def remove_node(node_url):
    # Check whether request body dictionary contains the required key (i.e. node)
    if node_url == '' or node_url is None:
        response = {
            'message': 'Node URL path parameter is missing'
        }
        return jsonify(response), HTTPStatus.BAD_REQUEST

    block_chain.remove_peer_node(node_url)
    response = {
        'message': 'Node, {}, successfully removed'.format(node_url),
        'nodes': block_chain.get_peer_nodes()
    }
    return jsonify(response), HTTPStatus.OK


@py_coin_app.route('/node-id', methods=['GET'])
def get_node_id():
    return jsonify(node_id), HTTPStatus.OK


@py_coin_app.route('/notify/txn', methods=['POST'])
def notify_transaction():
    # Convert the request body into a dictionary
    req_body = request.get_json()
    if not req_body:
        response = {
            'message': 'No data contained in request'
        }
        return jsonify(response), HTTPStatus.BAD_REQUEST

    # Check whether request body dictionary contains all the required keys
    required_fields = ['sender', 'recipient', 'amount', 'signature', 'timestamp']
    if not all(field in req_body for field in required_fields):
        response = {
            'message': 'Data is missing one or more required fields: {}'.format(required_fields)
        }
        return jsonify(response), HTTPStatus.BAD_REQUEST

    added_txn = block_chain.add_transaction(
        req_body['sender'], req_body['recipient'], req_body['amount'], req_body['signature'], req_body['timestamp'])

    if added_txn is not None:
        response = {
            'message': 'Transaction added successfully',
            'txn': added_txn.__dict__.copy()
        }
        return jsonify(response), HTTPStatus.CREATED
    else:
        response = {
            'message': 'Failed to add transaction'
        }
        return jsonify(response), HTTPStatus.INTERNAL_SERVER_ERROR


@py_coin_app.route('/notify/block', methods=['POST'])
def notify_block():
    req_body = request.get_json()
    if not req_body:
        response = {
            'message': 'No data contained in request'
        }
        return jsonify(response), HTTPStatus.BAD_REQUEST

    # Check whether request body dictionary contains the required key
    if 'block' not in req_body:
        response = {
            'message': 'Data is missing required field: block'
        }
        return jsonify(response), HTTPStatus.BAD_REQUEST

    block = req_body['block']

    # Is index of block received one more than the index of the last local block ?
    received_idx = block['idx']
    last_local_idx = block_chain.chain[-1].idx if len(block_chain.chain) > 0 else -1
    if received_idx == last_local_idx + 1:
        added_block = block_chain.add_block(block)
        if added_block is not None:
            balance_manager.update_balances_for_block(added_block)
            response = {'message': 'Block received has been added to the local block chain'}
            return jsonify(response), HTTPStatus.CREATED
        else:
            # Likelihood is that the failure stems from a block publisher with a stale block chain
            # - signal the problem to the block publisher using 'CONFLICT' status
            response = {'message': 'Failed to add block received to local block chain'}
            return jsonify(response), HTTPStatus.CONFLICT
    elif received_idx >= last_local_idx:
        block_chain.resolve_conflicts = True
        # The local block chain is stale... this is not an issue with the block publisher
        response = {'message': 'Local block chain is stale. Block not added'}
        return jsonify(response), HTTPStatus.OK
    else:
        response = {
            'message': 'Block received is from a stale block chain. Block not added'
        }
        return jsonify(response), HTTPStatus.CONFLICT


if __name__ == '__main__':
    host = environ[HOST_ENV_VAR_NAME]
    port = environ[PORT_ENV_VAR_NAME]
    node_id = '{}_{}'.format(host, port)
    wallet = Wallet(node_id)
    # Add a type hint so that IDE is able to suggest auto-completion options
    block_chain: Optional[BlockChain] = None
    balance_manager = BalanceManager()
    init_block_chain()
    py_coin_app.run(host=host, port=port)
