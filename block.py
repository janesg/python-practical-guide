from time import time


class Block:
    def __init__(self, idx, prev_hash, txns, proof, timestamp=None):
        # Python convention is that, by default, attributes are publicly accessible.
        # - i.e. we don't try to hide them using some mechanism like name mangling
        #   (which is invoked by prefixing with double underscore)
        # If at some point access has to be controlled we use properties
        self.idx = idx
        self.prev_hash = prev_hash
        # Alternatives:
        #   list copy function: txns.copy()
        #   open-ended range: txns[:]
        self.txns = [elem for elem in txns]
        self.proof = proof
        self.timestamp = time() if timestamp is None else timestamp

    def __str__(self):
        return '{}:{}:{}:{}:{}'.format(
            self.idx,
            self.prev_hash,
            self.proof,
            [str(txn) for txn in self.txns],
            self.timestamp)
