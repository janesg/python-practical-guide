from balance_manager import BalanceManager
from blockchain import BlockChain
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from http import HTTPStatus
from wallet import Wallet

py_coin_app = Flask(__name__)
CORS(py_coin_app)

wallet = Wallet()
block_chain = None
balance_manager = BalanceManager()


def init_block_chain():
    global block_chain
    block_chain = BlockChain(wallet.public_key)
    block_chain.load_data()
    # Notice that we initialize balances using a copy of the chain (via getter)
    balance_manager.initialize_balances(block_chain.chain)


@py_coin_app.route('/', methods=['GET'])
def get_ui():
    return send_from_directory('ui', 'node.html')


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


@py_coin_app.route('/mine', methods=['POST'])
def mine():
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


if __name__ == '__main__':
    init_block_chain()
    py_coin_app.run(host='0.0.0.0', port=5000)
