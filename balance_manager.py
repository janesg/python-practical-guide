class BalanceManager:
    def __init__(self):
        # Dictionary of transaction participants -> their confirmed balance
        self.balances = {}

    def initialize_balances(self, block_chain):
        print('Initialising balances...')
        for block in block_chain:
            self.update_balances_for_block(block)

    def update_balances_for_block(self, block):
        for txn in block.txns:
            txn_sender = txn.sender
            txn_recipient = txn.recipient
            txn_amount = txn.amount

            self.balances[txn_sender] = self.get_balance(txn_sender) - txn_amount
            self.balances[txn_recipient] = self.get_balance(txn_recipient) + txn_amount

    def participants(self):
        return sorted(self.balances.keys())

    def get_balance(self, participant):
        return self.balances[participant] if participant in self.balances else 0.0

    def display_balances(self):
        for participant in self.participants():
            print('* {:15} has a balance of {:>15.2f}'.format(participant, self.get_balance(participant)))
