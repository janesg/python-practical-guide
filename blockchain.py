# The blockchain implementation
# - code formatting follows PEP 8 standards
from collections import OrderedDict
from hash_util import calc_hash
import json
import os
import re

# Regex for validating transaction amount input
int_pattern = re.compile('^[0-9]*$')
float_pattern = re.compile('^[0-9]*.[0-9]*$')

# Reward earned by the node owner for mining a block
MINING_SENDER = 'MINER'
MINING_REWARD = 10.0

# Data file info
DATA_DIR = './data'
DATA_FILE = 'blockchain.txt'
DATA_FILE_PATH = DATA_DIR + '/' + DATA_FILE

# Start with an empty blockchain
block_chain = []

# Current open (unconfirmed) transactions
open_transactions = []

# Dictionary of transaction participants -> their confirmed balance
balances = {}
node_owner = 'Gary'


def load_data():
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

                    global block_chain, open_transactions
                    block_chain.clear()
                    for block in block_chain_loaded:
                        block_chain.append(create_block(block['prev_#'], block['idx'], block['txns'], block['pow']))

                    open_transactions.clear()
                    for txn in open_transactions_loaded:
                        open_transactions.append(create_transaction(txn['sender'], txn['recipient'], txn['amount']))

                    initialize_balances()
                else:
                    print('ERROR: Invalid data file contents')

        except IOError:
            print('No existing data file to load')


def save_data():
    # Only save the block chain if it is valid
    if is_chain_valid():
        # Mode 'w' ensures we overwrite the contents of the file
        with open(DATA_FILE_PATH, mode='w') as f:
            f.write(json.dumps(block_chain) + '\n')
            f.write(json.dumps(open_transactions))
    else:
        print('Unable to save data as block chain is not valid')


# Increasing the char_count increases the 'difficulty' of block mining.
# POW is only valid if the first char_count characters of the generated hash are all the specified character.
def is_pow_valid(txns, prev_hash, pow, char="0", char_count=3):
    # Tried using:
    #   "{}{}{}".format(txns, prev_hash, pow)
    # but output string for txns list includes escaped single quotes instead of double quotes.
    # This in turn leads to a different hash being calculated...so use json representation instead
    # - use of sort_keys ensures that dictionary serialization is always consistent
    pow_hash = calc_hash('{}:{}:{}'.format(json.dumps(txns, sort_keys=True), prev_hash, pow))
    return pow_hash[0:char_count] == char * char_count


def pow(txns, hash):
    nonce = 0
    while not is_pow_valid(txns, hash, nonce):
        nonce += 1

    return nonce


def get_transaction_data():
    txn_recipient = input('Please enter the transaction recipient : ')

    while True:
        txn_amount = input('Please enter the transaction amount : ')

        if txn_amount == '':
            return txn_recipient, None
        elif float_pattern.match(txn_amount) or int_pattern.match(txn_amount):
            return txn_recipient, float(txn_amount)
        else:
            print('Invalid transaction amount... please try again')


def initialize_balances():
    print('Initialising balances...')
    for block in block_chain:
        update_balances_for_block(block)


def create_transaction(sender, recipient, amount):
    # As we are hashing transactions, ensure we force the order of key-value pairs in dictionary
    return OrderedDict([('sender', sender), ('recipient', recipient), ('amount', amount)])


def add_transaction(sender, recipient, amount=1.0):
    """
    Create a new open transaction.

    Arguments:
        :sender: the sender of the transaction amount.
        :recipient: the intended recipient of the transaction amount.
        :amount: the transaction amount (default = 1.0)
    """
    open_transactions.append(create_transaction(sender, recipient, amount))


def create_block(prev_block_hash, idx, txns, pow):
    return {
        'prev_#': prev_block_hash,
        'idx': idx,
        # Uses simple list comprehension
        # Alternatives:
        #   list copy function: open_transactions.copy()
        #   open-ended range: open_transactions[:]
        'txns': [elem for elem in txns],
        'pow': pow
    }


def mine_block():
    # Validate that each transaction sender has necessary funds to meet
    # their obligation when open transactions are netted
    ot_senders = set(txn['sender'] for txn in open_transactions)

    prev_block_hash = calc_hash(block_as_str(block_chain[-1])) if len(block_chain) > 0 else ''

    # Calculate POW on current open transactions before adding the reward transaction
    pow_value = pow(open_transactions, prev_block_hash)

    # Add in the mining reward transaction as it will impact the node owner's obligation
    add_transaction(MINING_SENDER, node_owner, MINING_REWARD)

    for participant in ot_senders:
        sent_total = sum([txn['amount'] for txn in open_transactions if txn['sender'] == participant])
        received_total = sum([txn['amount'] for txn in open_transactions if txn['recipient'] == participant])
        net_sent = sent_total - received_total
        current_balance = get_balance(participant)
        if current_balance < net_sent:
            print('*** {} has an obligation of {:.2f}, but an available balance of only {:.2f}'
                  .format(participant, net_sent, current_balance))
            return False

    block = create_block(prev_block_hash, len(block_chain), open_transactions, pow_value)
    block_chain.append(block)
    open_transactions.clear()
    save_data()

    # Now transactions are confirmed, update balances
    update_balances_for_block(block)

    return True


def block_as_str(block):
    return '{}:{}:{}:{}'.format(block['idx'], block['prev_#'], block['pow'], json.dumps(block['txns'], sort_keys=True))


def update_balances_for_block(block):
    for txn in block['txns']:
        txn_sender = txn['sender']
        txn_recipient = txn['recipient']
        txn_amount = txn['amount']

        balances[txn_sender] = get_balance(txn_sender) - txn_amount
        balances[txn_recipient] = get_balance(txn_recipient) + txn_amount


def is_chain_valid():
    # Start prev_idx at the second to last element
    prev_idx = len(block_chain) - 2

    # Use a reverse iterator over blockchain elements to process last block first
    for block_to_check in reversed(block_chain):
        # First element of current block must equal the entire previous block
        if prev_idx >= 0 and (block_to_check['prev_#'] != calc_hash(block_as_str(block_chain[prev_idx]))):
            print('ERROR: Block ' + str(block_to_check['idx']) + ' failed previous hash validation')
            return False

        if not is_pow_valid(
                # We have to exclude the reward txn when validating POW
                # - could use list comprehension to filter the txns
                #   [txn for txn in block_to_check['txns'] if txn['sender'] != MINING_SENDER]
                # Use range selector to exclude last txn in list - which we know is the reward txn
                block_to_check['txns'][:-1],
                block_to_check['prev_#'],
                block_to_check['pow']):
            print('ERROR: Block ' + str(block_to_check['idx']) + ' failed POW validation')
            return False

        prev_idx -= 1

    return True


def participants():
    return sorted(balances.keys())


def get_balance(participant):
    return balances[participant] if participant in balances else 0.0


def display_balances():
    for participant in participants():
        print('* {:15} has a balance of {:>15.2f}'.format(participant, get_balance(participant)))


load_data()
finished = False

while not finished:
    print('==========================================')
    print('| Please choose an option:')
    print('| 1 : Add a new transaction')
    print('| 2 : Mine block')
    print('| 3 : Output the current blockchain blocks')
    print('| 4 : Output the participants')
    print('| 5 : Output balances')
    print('| H : Hack the blockchain !')
    print('| V : Verify the blockchain')
    print('| Q : Quit')
    print('==========================================')

    option = input('> ')
    bc_len = len(block_chain)

    if option.upper() == 'Q':
        save_data()
        finished = True
    elif option == '1':
        # Tuple unpacking
        recipient, amount = get_transaction_data()
        # Ternary operator
        add_transaction(node_owner, recipient, amount) if amount is not None else add_transaction(node_owner, recipient)
        print('Open Txns: ' + json.dumps(open_transactions))
    elif option == '2':
        if len(open_transactions) == 0:
            print('INFO: There are no open transactions to mine')
        else:
            if not mine_block():
                print('WARN: Unable to mine invalid open transactions ... clearing all open transactions')
                open_transactions.clear()
    elif option == '3':
        if bc_len == 0:
            print('INFO: Blockchain is currently empty')
        else:
            print('Blockchain has {} block{}'.format(bc_len, ('s' if bc_len > 1 else '')))
            block_idx = 1
            for block in block_chain:
                padding = ' ' * (len(block_chain) - block_idx)
                print(('*' * block_idx) + padding + ' : ' + block_as_str(block))
                block_idx += 1
    elif option == '4':
        print('Transaction Participants: {}'.format(', '.join(participants())))
    elif option == '5':
        display_balances()
    elif option.upper() == 'H':
        if bc_len >= 1:
            block_chain[0]['txns'][0]['amount'] = 99.99
    elif option.upper() == 'V':
        if not is_chain_valid():
            print('ERROR: Blockchain is invalid...exiting')
            finished = True
        else:
            print('Blockchain is valid...')
    else:
        print('WARN: Invalid option... try again')
else:
    print("That's it...we're all finished")