# The blockchain implementation
# - code formatting follows PEP 8 standards
from collections import OrderedDict
import hashlib as hl
import json
import re

# Regex for validating transaction amount input
int_pattern = re.compile("^[0-9]*$")
float_pattern = re.compile("^[0-9]*.[0-9]*$")

# Reward earned by the node owner for mining a block
MINING_SENDER = 'MINER'
MINING_REWARD = 10.0

# Start with an empty blockchain
blockchain = []

# Current open (unconfirmed) transactions
open_transactions = []
# Dictionary of transaction participants -> their confirmed balance
balances = {}
node_owner = 'Gary'


def is_pow_valid(txns, prev_hash, pow, char="0", char_count=3):
    # Tried using:
    #   "{}{}{}".format(txns, prev_hash, pow)
    # but output string for txns list includes escaped single quotes instead of double quotes.
    # This in turn leads to a different hash being calculated...so use json representation instead
    pow_hash = calc_hash('{}:{}:{}'.format(json.dumps(txns, sort_keys=True), prev_hash, pow))
    return pow_hash[0:char_count] == char * char_count


def pow(txns, hash):
    nonce = 0
    # while not is_pow_valid(
    #         open_transactions,
    #         calc_hash(block_as_str(blockchain[-1])) if len(blockchain) > 0 else '',
    #         nonce):
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
            print('! Invalid transaction amount... try again')


def initialize_balances():
    print("Initialising balances...")
    for block in blockchain:
        update_balances_for_block(block)


def add_transaction(sender, recipient, amount=1.0):
    """
    Create a new open transaction.

    Arguments:
        :sender: the sender of the transaction amount.
        :recipient: the intended recipient of the transaction amount.
        :amount: the transaction amount (default = 1.0)
    """
    # As we are hashing transactions, ensure we force the order of key-value pairs in dictionary
    transaction = OrderedDict([('sender', sender), ('recipient', recipient), ('amount', amount)])
    open_transactions.append(transaction)


def mine_block():
    # Validate that each transaction sender has necessary funds to meet
    # their obligation when open transactions are netted
    ot_senders = set(txn['sender'] for txn in open_transactions)

    prev_block_hash = calc_hash(block_as_str(blockchain[-1])) if len(blockchain) > 0 else ''

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

    block = {
        'prev_#': prev_block_hash,
        'idx': len(blockchain),
        # Uses simple list comprehension
        # Alternatives:
        #   list copy function: open_transactions.copy()
        #   open-ended range: open_transactions[:]
        'txns': [elem for elem in open_transactions],
        'pow': pow_value
    }
    blockchain.append(block)
    open_transactions.clear()

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


def calc_hash(str_data):
    return hl.sha256(str_data.encode()).hexdigest()
    # hash = hl.sha256(str_data.encode()).hexdigest()
    # print("Hash: " + hash + " <<== Str Data: " + str_data)
    # return hash


def is_chain_valid():
    # Start prev_idx at the second to last element
    prev_idx = len(blockchain) - 2

    # Use a reverse iterator over blockchain elements to process last block first
    for block_to_check in reversed(blockchain):
        # First element of current block must equal the entire previous block
        if prev_idx >= 0 and (block_to_check['prev_#'] != calc_hash(block_as_str(blockchain[prev_idx]))):
            print("Block " + str(block_to_check['idx']) + " failed previous hash validation")
            return False

        if not is_pow_valid(
                # We have to exclude the reward txn when validating POW
                # - could use list comprehension to filter the txns
                #   [txn for txn in block_to_check['txns'] if txn['sender'] != MINING_SENDER]
                # Use range selector to exclude last txn in list - which we know is the reward txn
                block_to_check['txns'][:-1],
                block_to_check['prev_#'],
                block_to_check['pow']):
            print("Block " + str(block_to_check['idx']) + " failed POW validation")
            return False

        prev_idx -= 1
    else:
        print('Chain validation completed')

    return True


def participants():
    return sorted(balances.keys())


def get_balance(participant):
    return balances[participant] if participant in balances else 0.0


def display_balances():
    for participant in participants():
        print('* {:15} has a balance of {:>15.2f}'.format(participant, get_balance(participant)))


initialize_balances()
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
    bc_len = len(blockchain)

    if option.upper() == 'Q':
        finished = True
    elif option == '1':
        # Tuple unpacking
        recipient, amount = get_transaction_data()
        # Ternary operator
        add_transaction(node_owner, recipient, amount) if amount is not None else add_transaction(node_owner, recipient)
        print("Open Txns: " + json.dumps(open_transactions))
    elif option == '2':
        if len(open_transactions) == 0:
            print('There are no open transactions to mine')
        else:
            if not mine_block():
                print('Unable to mine invalid open transactions ... clearing all open transactions')
                open_transactions.clear()
    elif option == '3':
        if bc_len == 0:
            print('Blockchain is currently empty')
        else:
            print('Blockchain has {} block{}'.format(bc_len, ('s' if bc_len > 1 else '')))
            block_idx = 1
            for block in blockchain:
                padding = ' ' * (len(blockchain) - block_idx)
                print(('*' * block_idx) + padding + ' : ' + block_as_str(block))
                block_idx += 1
    elif option == '4':
        print('Transaction Participants: {}'.format(', '.join(participants())))
    elif option == '5':
        display_balances()
    elif option.upper() == 'H':
        if bc_len >= 1:
            blockchain[0]['txns'][0]['amount'] = 99.99
    elif option.upper() == 'V':
        if not is_chain_valid():
            print('*** EXITING : Blockchain is invalid !! ***')
            finished = True
        else:
            print('Blockchain is valid...')
    else:
        print('! Invalid option... try again')
else:
    print("That's it...we're all finished")