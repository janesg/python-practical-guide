# This our initial blockchain implementation
# - formatting follows PEP 8 standards
import hashlib
import re

# Regex for validating transaction amount input
int_pattern = re.compile("^[0-9]*$")
float_pattern = re.compile("^[0-9]*.[0-9]*$")

# Start with an empty blockchain
blockchain = []

open_transactions = []
balances = {}
node_owner = 'Gary'


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


def add_transaction(sender, recipient, amount=1.0):
    """
    Create a new open transaction.

    Arguments:
        :sender: the sender of the transaction amount.
        :recipient: the intended recipient of the transaction amount.
        :amount: the transaction amount (default = 1.0)
    """
    transaction = {
        'sender': sender,
        'recipient': recipient,
        'amount': amount
    }
    open_transactions.append(transaction)


def mine_block():
    block = {
        'prev_#': calc_hash(blockchain[-1]) if len(blockchain) > 0 else '',
        'idx': len(blockchain),
        # Demo simple list comprehension instead of using open_transactions.copy()
        'txns': [elem for elem in open_transactions]
    }
    blockchain.append(block)
    open_transactions.clear()

    # Now transactions are confirmed, update balances
    for txn in block['txns']:
        txn_sender = txn['sender']
        txn_recipient = txn['recipient']
        txn_amount = txn['amount']

        if txn_sender in balances:
            balances[txn_sender] = balances[txn_sender] - txn_amount
        else:
            balances[txn_sender] = -txn_amount

        if txn_recipient in balances:
            balances[txn_recipient] = balances[txn_recipient] + txn_amount
        else:
            balances[txn_recipient] = txn_amount


def calc_hash(data):
    return hashlib.sha256(str(data).encode()).hexdigest()


def is_chain_valid():
    # Start prev_idx at the second to last element
    prev_idx = len(blockchain) - 2

    # Use a reverse iterator over blockchain elements to process last block first
    for block_to_check in reversed(blockchain):
        # First element of current block must equal the entire previous block
        if prev_idx >= 0 and (block_to_check['prev_#'] != calc_hash(blockchain[prev_idx])):
            return False

        prev_idx -= 1
    else:
        print('Chain validation completed')

    return True


def participants():
    return sorted(balances.keys())


def display_balances():
    for participant in participants():
        print('* ' + participant + ' has a balance of ' + str(balances[participant]))


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
        print(open_transactions)
    elif option == '2':
        if len(open_transactions) == 0:
            print('There are no open transactions to mine')
        else:
            mine_block()
    elif option == '3':
        if bc_len == 0:
            print('Blockchain is currently empty')
        else:
            print('Blockchain has ' + str(bc_len) + ' block' + ('s' if bc_len > 1 else ''))
            block_idx = 1
            for block in blockchain:
                padding = ' ' * (len(blockchain) - block_idx)
                print(('*' * block_idx) + padding + ' : ' + str(block))
                block_idx += 1
    elif option == '4':
        print('Transaction Participants: ' + ', '.join(participants()))
    elif option == '5':
        display_balances()
    elif option.upper() == 'H':
        if bc_len >= 1:
            blockchain[0]['txns'][0]['amount'] = 99.99
    elif option.upper() == 'V':
        if not is_chain_valid():
            print('*** Blockchain is invalid !! ***')
            finished = True
        else:
            print('Blockchain is valid...')
    else:
        print('! Invalid option... try again')
else:
    print("That's it...we're all finished")