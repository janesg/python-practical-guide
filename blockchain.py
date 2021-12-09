# This our initial blockchain implementation
# - formatting follows PEP 8 standards
import re

# Regex for validating amount input
int_pattern = re.compile("^[0-9]*$")
float_pattern = re.compile("^[0-9]*.[0-9]*$")

# Start with an empty blockchain
blockchain = []


def get_transaction_amount():
    txn_amount = input('Please enter transaction amount : ')

    if txn_amount == '':
        return
    elif float_pattern.match(txn_amount) or int_pattern.match(txn_amount):
        return float(txn_amount)
    else:
        print('! Invalid transaction amount... try again')
        return get_transaction_amount()


def add_value(value=33.33):
    """
    This is the way that we document our function using a multi-line description.
    When we hover over function call, the IDE will display this documentation.

    Arguments:
        :value: the transaction amount to be added (default = 33.33).
    """
    if len(blockchain) == 0:
        blockchain.append([value])
    else:
        blockchain.append([blockchain[-1], value])


while True:
    print('==========================================')
    print('| Please choose an option:')
    print('| 1 : Add a new transaction value')
    print('| 2 : Output the current blockchain blocks')
    print('| X : Quit')
    print('==========================================')

    option = input('> ')

    if option.upper() == 'X':
        break
    elif option == '1':
        txn_amt = get_transaction_amount()
        # Use ternary operator
        add_value(txn_amt) if txn_amt is not None else add_value()
    elif option == '2':
        bc_len = len(blockchain)
        if bc_len == 0:
            print('Blockchain is currently empty')
        else:
            print('Blockchain has ' + str(bc_len) + ' block' + ('s' if bc_len > 1 else ''))
            for block in blockchain:
                print(block)
    else:
        print('! Invalid option... try again')
