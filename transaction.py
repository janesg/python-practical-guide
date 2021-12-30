from collections import OrderedDict
from time import time


class Transaction:
    def __init__(self, sender, recipient, amount, signature, timestamp=None):
        self.sender = sender
        self.recipient = recipient
        self.amount = amount
        self.signature = signature
        self.timestamp = time() if timestamp is None else timestamp

    def __str__(self):
        return '{}:{}:{}:{}:{}'.format(
            self.sender,
            self.recipient,
            self.amount,
            self.signature,
            self.timestamp)

    def to_ordered_dict(self):
        # As we are hashing transactions, ensure we force the order of key-value pairs in dictionary
        return OrderedDict([
            ('sender', self.sender),
            ('recipient', self.recipient),
            ('amount', self.amount),
            ('signature', self.signature),
            ('timestamp', self.timestamp)
        ])
