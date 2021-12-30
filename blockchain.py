# The blockchain implementation
# - code formatting follows PEP 8 standards
from block import Block
from hash_util import calc_hash
import json
import os
from transaction import Transaction
from verification import Verification

# Reward earned by the node owner for mining a block
MINING_SENDER = 'MINER'
MINING_REWARD = 10.0

# Data file info
DATA_DIR = './data'
DATA_FILE = 'blockchain.txt'
DATA_FILE_PATH = DATA_DIR + '/' + DATA_FILE


class BlockChain:
    def __init__(self, hosting_node_id):
        self.__hosting_node_id = hosting_node_id
        # Start with an empty blockchain
        self.__chain = []
        # Current open (unconfirmed) transactions
        self.__open_txns = []

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
                with open(DATA_FILE_PATH, mode='r') as f:
                    lines = f.readlines()
                    if len(lines) == 2:
                        # Use range to exclude the terminating new line character
                        block_chain_loaded = json.loads(lines[0][:-1])
                        open_transactions_loaded = json.loads(lines[1])

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
                                        dict_txn['timestamp']
                                    ) for dict_txn in dict_block['txns']],
                                    dict_block['proof'],
                                    dict_block['timestamp']
                                )
                            )

                        self.__open_txns.clear()
                        for dict_txn in open_transactions_loaded:
                            self.__open_txns.append(
                                Transaction(
                                    dict_txn['sender'],
                                    dict_txn['recipient'],
                                    dict_txn['amount'],
                                    dict_txn['timestamp']
                                )
                            )
                    else:
                        print('ERROR: Invalid data file contents')

            except IOError:
                print('No existing data file to load')

    def save_data(self):
        # Only save the block chain if it is valid
        # - Note: we are passing a copy of the chain (using getter) to external function to prevent reference leak
        if Verification.is_block_chain_valid(self.chain):
            # Mode 'w' ensures we overwrite the contents of the file
            with open(DATA_FILE_PATH, mode='w') as f:
                # Create dictionary version of each block and transaction
                # - can only serialize certain Python objects to JSON
                # Note: take copy of block dict so we can convert the block's transactions
                serializable_chain = [block.__dict__.copy() for block in self.__chain]
                for dict_block in serializable_chain:
                    dict_block['txns'] = [txn.__dict__ for txn in dict_block['txns']]
                f.write(json.dumps(serializable_chain) + '\n')
                serializable_open_txns = [txn.__dict__ for txn in self.__open_txns]
                f.write(json.dumps(serializable_open_txns))
        else:
            print('Unable to save data as block chain is not valid')

    @staticmethod
    def proof_of_work(txns, prev_block_hash):
        nonce = 0
        while not Verification.is_pow_valid(txns, prev_block_hash, nonce):
            nonce += 1

        return nonce

    def add_transaction(self, sender, recipient, amount=1.0):
        """
        Create a new open transaction.

        Arguments:
            :sender: the sender of the transaction amount.
            :recipient: the intended recipient of the transaction amount.
            :amount: the transaction amount (default = 1.0)
        """
        self.__open_txns.append(Transaction(sender, recipient, amount))

    def mine_block(self, get_balance):
        prev_block_hash = calc_hash(str(self.__chain[-1])) if len(self.__chain) > 0 else ''

        # Calculate POW on current open transactions before adding the reward transaction
        pow_value = self.proof_of_work(self.open_txns, prev_block_hash)

        # Add in the mining reward transaction as it will impact the hosting node's obligation
        self.add_transaction(MINING_SENDER, self.__hosting_node_id, MINING_REWARD)

        # Validate that each transaction sender has necessary funds to meet
        # their obligation when open transactions are netted
        if not Verification.check_open_txn_funds_available(self.open_txns, get_balance, MINING_SENDER):
            print('WARN: Unable to mine invalid open transactions ... clearing all open transactions')
            self.__open_txns.clear()
            return None

        block = Block(len(self.__chain), prev_block_hash, self.open_txns, pow_value)
        self.__chain.append(block)
        self.__open_txns.clear()
        self.save_data()

        return block
