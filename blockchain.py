# The blockchain implementation
# - code formatting follows PEP 8 standards
from block import Block
from http import HTTPStatus
import json
import os
import requests
from transaction import Transaction
from utility.hash_util import calc_hash
from utility.verification import Verification

# Reward earned by the node owner for mining a block
MINING_SENDER = 'MINER'
MINING_REWARD = 10.0

# Data file info
DATA_DIR = './data'
DATA_FILE = 'blockchain'
DATA_FILE_PATH = DATA_DIR + '/' + DATA_FILE


class BlockChain:
    def __init__(self, public_key, node_id):
        self.__public_key = public_key
        self.__node_id = node_id
        # Start with an empty blockchain
        self.__chain = []
        # Current open (unconfirmed) transactions
        self.__open_txns = []
        # The set of peers this node knows about
        self.__peer_nodes = set()
        self.resolve_conflicts = False

    @property
    def chain(self):
        return self.__chain[:]

    # Explicitly disallow setter
    @chain.setter
    def chain(self, val):
        pass

    # If we were to allow a setter, this is what it might look like
    # - notice the range copy of passed list to prevent leaking a reference
    # @chain.setter
    # def chain(self, val):
    #     self.__chain = val[:]

    @property
    def open_txns(self):
        return self.__open_txns[:]

    def load_data(self):
        if not os.path.exists(DATA_DIR):
            os.makedirs(DATA_DIR)
        else:
            try:
                with open('{}_{}'.format(DATA_FILE_PATH, self.__node_id), mode='r') as f:
                    lines = f.readlines()
                    if len(lines) == 3:
                        # Use range to exclude the terminating new line character
                        block_chain_loaded = json.loads(lines[0][:-1])
                        open_transactions_loaded = json.loads(lines[1][:-1])
                        peers_nodes_loaded = json.loads(lines[2])

                        self.__chain.clear()
                        for dict_block in block_chain_loaded:
                            self.__chain.append(
                                Block(
                                    dict_block['idx'],
                                    dict_block['prev_hash'],
                                    [Transaction(
                                        dict_txn['sender'],
                                        dict_txn['recipient'],
                                        dict_txn['amount'],
                                        dict_txn['signature'],
                                        dict_txn['timestamp']
                                    ) for dict_txn in dict_block['txns']],
                                    dict_block['proof'],
                                    dict_block['timestamp']
                                )
                            )

                        self.__open_txns.clear()
                        for dict_txn in open_transactions_loaded:
                            txn = Transaction(
                                dict_txn['sender'],
                                dict_txn['recipient'],
                                dict_txn['amount'],
                                dict_txn['signature'],
                                dict_txn['timestamp']
                            )
                            if Verification.is_txn_signature_valid(txn, MINING_SENDER):
                                self.__open_txns.append(txn)
                            else:
                                print('WARN: Discarding open transaction with invalid signature')

                        # Create a new set from the deserialized list
                        self.__peer_nodes = set(peers_nodes_loaded)
                    else:
                        print('ERROR: Invalid data file contents')

            except IOError:
                print('No existing data file to load')

    def save_data(self):
        # Only save the block chain if it is valid
        # - Note: we are passing a copy of the chain (using getter) to external function to prevent reference leak
        if Verification.is_block_chain_valid(self.chain):
            # Mode 'w' ensures we overwrite the contents of the file
            with open('{}_{}'.format(DATA_FILE_PATH, self.__node_id), mode='w') as f:
                # Create dictionary version of each block and transaction
                # - can only serialize certain Python objects to JSON
                # Note: take copy of block dict so we can convert the block's transactions
                serializable_chain = [block.__dict__.copy() for block in self.__chain]
                for dict_block in serializable_chain:
                    dict_block['txns'] = [txn.__dict__ for txn in dict_block['txns']]
                f.write(json.dumps(serializable_chain) + '\n')
                serializable_open_txns = [txn.__dict__ for txn in self.__open_txns]
                f.write(json.dumps(serializable_open_txns) + '\n')
                # Convert set to list so that it can be serialized to JSON
                f.write(json.dumps(list(self.__peer_nodes)))
        else:
            print('Unable to save data as block chain is not valid')

    @staticmethod
    def proof_of_work(txns, prev_block_hash):
        nonce = 0
        while not Verification.is_pow_valid(txns, prev_block_hash, nonce):
            nonce += 1

        return nonce

    def add_transaction(self, sender, recipient, amount, signature, timestamp=None):
        """
        Create a new open transaction.

        Arguments:
            :sender: the sender of the transaction amount.
            :recipient: the intended recipient of the transaction amount.
            :amount: the transaction amount
            :signature: the signature of the transaction
        """
        if self.__public_key is None:
            print('WARN: Unable to add transaction. Public key is not set')
            return None
        else:
            txn = Transaction(sender, recipient, amount, signature, timestamp)
            if Verification.is_txn_signature_valid(txn, MINING_SENDER):
                self.__open_txns.append(txn)
                self.save_data()
                # Notify peer nodes of transaction only if it originated from this node
                if txn.sender == self.__public_key:
                    self.notify_peers_of_txn(txn)
                return txn
            else:
                print('WARN: Unable to add transaction. Signature is invalid')
                return None

    def notify_peers_of_txn(self, txn):
        json_data = txn.__dict__
        for node in self.__peer_nodes:
            url = 'http://{}/notify/txn'.format(node)
            self.notify_peer(url, json_data)

    def notify_peer(self, url, json_data):
        try:
            response = requests.post(url, json=json_data)
            if response.status_code == HTTPStatus.BAD_REQUEST or \
                    response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR:
                print('ERROR: Peer notification failed: {}'.format(url))
                return False
            elif response.status_code == HTTPStatus.CONFLICT:
                self.resolve_conflicts = True
                return False
            else:
                return True
        except requests.exceptions.ConnectionError:
            print('ERROR: Peer connection failed: {}'.format(url))
            return False

    def mine_block(self, get_balance):
        if self.__public_key is None:
            print('WARN: Unable to mine block. Public key is not set')
            return None

        prev_block_hash = calc_hash(str(self.__chain[-1])) if len(self.__chain) > 0 else ''

        # Calculate POW on current open transactions before adding the reward transaction
        pow_value = self.proof_of_work(self.open_txns, prev_block_hash)

        # Add in the mining reward transaction as it will impact the hosting node's obligation
        # - Note: mining reward transaction doesn't require a signature
        self.add_transaction(MINING_SENDER, self.__public_key, MINING_REWARD, '')

        # Validate that each transaction sender has necessary funds to meet
        # their obligation when open transactions are netted
        if not Verification.check_open_txn_funds_available(self.open_txns, get_balance, MINING_SENDER):
            print('WARN: Unable to mine block. Invalid open transactions ... clearing all open transactions')
            self.__open_txns.clear()
            return None

        block = Block(len(self.__chain), prev_block_hash, self.open_txns, pow_value)
        self.__chain.append(block)
        self.__open_txns.clear()
        self.save_data()
        self.notify_peers_for_block(block)

        return block

    def add_block(self, block):
        # Validate the POW for the block's transactions
        txns = [Transaction(
            txn['sender'], txn['recipient'], txn['amount'], txn['signature'], txn['timestamp'])
                for txn in block['txns']]
        # Remember to exclude the mining reward transaction (...the last in list) when validating POW
        pow_valid = Verification.is_pow_valid(txns[:-1], block['prev_hash'], block['proof'])

        # Does previous hash for block received match the previous hash of our local last block ?
        local_prev_block_hash = calc_hash(str(self.__chain[-1])) if len(self.__chain) > 0 else ''
        prev_hash_match = local_prev_block_hash == block['prev_hash']

        if not pow_valid or not prev_hash_match:
            return None
        else:
            # Convert the received block from dictionary to Block object before appending to chain
            block_obj = Block(block['idx'], block['prev_hash'], txns, block['proof'], block['timestamp'])
            self.__chain.append(block_obj)
            # We now need to remove, from open transactions, any transaction that was part of the received block
            open_txns_snapshot = self.__open_txns[:]
            for itx in block['txns']:
                for opentx in open_txns_snapshot:
                    # Check for match. Should be enough to just check equality of signatures
                    if opentx.signature == itx['signature']:
                        try:
                            self.__open_txns.remove(opentx)
                        except ValueError:
                            print('WARN: Transaction was already removed')
            self.save_data()
            return block_obj

    def notify_peers_for_block(self, block):
        json_block_data = block.__dict__.copy()
        json_block_data['txns'] = [txn.__dict__ for txn in json_block_data['txns']]
        for node in self.__peer_nodes:
            url = 'http://{}/notify/block'.format(node)
            self.notify_peer(url, { 'block': json_block_data })

    def resolve_block_chain(self):
        winning_chain = self.__chain
        replace_chain = False

        # Get the block chain held on each peer node
        for node in self.__peer_nodes:
            url = 'http://{}/chain'.format(node)
            try:
                response = requests.get(url)
                node_chain = response.json()
                # Check whether peer node has a valid chain that is longer
                if len(node_chain) > len(winning_chain):
                    # Convert to block and transaction objects before verifying
                    node_chain = [Block(
                        block['index'], block['prev_hash'], block['txns'], block['proof'], block['timestamp'])
                            for block in node_chain]
                    for block in node_chain:
                        block.txns = [Transaction(
                            txn['sender'], txn['recipient'], txn['amount'], txn['signature'], txn['timestamp'])
                                for txn in block.txns]
                    if Verification.is_block_chain_valid(node_chain):
                        winning_chain = node_chain
                        replace_chain = True

            except requests.exceptions.ConnectionError:
                print('ERROR: Peer connection failed: {}'.format(url))

        self.resolve_conflicts = False
        if replace_chain:
            self.__chain = winning_chain
            self.__open_txns.clear()
            self.save_data()

        return replace_chain

    def add_peer_node(self, node):
        """
        Adds a node to the set of known peer nodes

        :param node: the node to be added
        :return:
        """
        self.__peer_nodes.add(node)
        self.save_data()

    def remove_peer_node(self, node):
        """
        Removes a node from the set of known peer nodes

        :param node: the node to be removed
        :return:
        """
        self.__peer_nodes.discard(node)
        self.save_data()

    def get_peer_nodes(self):
        """
        Get a list of the known peer nodes

        :return: a list of the current peer node set
        """
        return list(self.__peer_nodes)
