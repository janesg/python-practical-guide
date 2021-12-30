from balance_manager import BalanceManager
from blockchain import BlockChain
import json
import re
from utility.verification import Verification
from wallet import Wallet


# Regex for validating transaction amount input
int_pattern = re.compile('^[0-9]*$')
float_pattern = re.compile('^[0-9]*.[0-9]*$')


class Node:
    def __init__(self):
        self.wallet = Wallet()
        self.block_chain = None
        self.balance_manager = BalanceManager()

    def init_block_chain(self):
        self.block_chain = BlockChain(self.wallet.public_key)
        self.block_chain.load_data()
        # Notice that we initialize balances using a copy of the chain (via getter)
        self.balance_manager.initialize_balances(self.block_chain.chain)

    def process_input(self):
        finished = False

        while not finished:
            print('==========================================')
            print('| Please choose an option:')
            print('| 1 : Add a new transaction')
            print('| 2 : Mine block')
            print('| 3 : Output the current blockchain blocks')
            print('| 4 : Output the current open transactions')
            print('| 5 : Output the participants')
            print('| 6 : Output balances')
            print('| 7 : Load wallet')
            print('| 8 : Create new wallet')
            print('| 9 : Save wallet')
            print('| V : Verify the blockchain')
            print('| Q : Quit')
            print('==========================================')

            option = input('> ')
            bc_len = len(self.block_chain.chain)

            if option.upper() == 'Q':
                self.block_chain.save_data()
                finished = True
            elif option == '1':
                if self.wallet.public_key is None:
                    print('WARN: No wallet key available. Load or create wallet before adding transaction')
                else:
                    # Tuple unpacking
                    recipient, amount = Node.get_transaction_data()
                    signature = self.wallet.sign_txn(self.wallet.public_key, recipient, amount)
                    # Ternary operator
                    self.block_chain.add_transaction(self.wallet.public_key, recipient, amount, signature)
            elif option == '2':
                if len(self.block_chain.open_txns) == 0:
                    print('INFO: There are no open transactions to mine')
                else:
                    mined_block = self.block_chain.mine_block(self.balance_manager.get_balance)
                    if mined_block is not None:
                        # Now transactions are confirmed, update balances
                        self.balance_manager.update_balances_for_block(mined_block)
            elif option == '3':
                if bc_len == 0:
                    print('INFO: Blockchain is currently empty')
                else:
                    print('Blockchain has {} block{}'.format(bc_len, ('s' if bc_len > 1 else '')))
                    block_idx = 1
                    for block in self.block_chain.chain:
                        padding = ' ' * (len(self.block_chain.chain) - block_idx)
                        print(('*' * block_idx) + padding + ' : ' + str(block))
                        block_idx += 1
            elif option == '4':
                print('Open Txns: ' + json.dumps([txn.to_ordered_dict() for txn in self.block_chain.open_txns]))
            elif option == '5':
                print('Transaction Participants: {}'.format(', '.join(self.balance_manager.participants())))
            elif option == '6':
                self.balance_manager.display_balances()
            elif option == '7':
                self.wallet.load_keys()
                self.init_block_chain()
            elif option == '8':
                self.wallet.create_keys()
                self.init_block_chain()
            elif option == '9':
                self.wallet.save_keys()
            elif option.upper() == 'V':
                if not Verification.is_block_chain_valid(self.block_chain.chain):
                    print('ERROR: Blockchain is invalid...exiting')
                    finished = True
                else:
                    print('Blockchain is valid...')
            else:
                print('WARN: Invalid option... try again')
        else:
            print("That's it...we're all finished")

    @staticmethod
    def get_transaction_data():
        txn_recipient = ''
        while txn_recipient == '':
            txn_recipient = input('Please enter the transaction recipient : ')

        while True:
            txn_amount = input('Please enter the transaction amount : ')

            if txn_amount == '':
                print('You must enter a transaction amount... please try again')
            elif float_pattern.match(txn_amount) or int_pattern.match(txn_amount):
                return txn_recipient, float(txn_amount)
            else:
                print('Invalid transaction amount... please try again')




if __name__ == '__main__':
    node = Node()
    node.init_block_chain()
    node.process_input()
