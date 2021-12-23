from hash_util import calc_hash
import json


class Verification:
    # Increasing the char_count increases the 'difficulty' of block mining.
    # POW is only valid if the first char_count characters of the generated hash are all the specified character.
    @staticmethod
    def is_pow_valid(txns, prev_hash, pow, char="0", char_count=3):
        # Tried using:
        #   "{}{}{}".format(txns, prev_hash, pow)
        # but output string for txns list includes escaped single quotes instead of double quotes.
        # This in turn leads to a different hash being calculated...so use json representation instead
        # - use of sort_keys ensures that dictionary serialization is always consistent
        ordered_txns = [txn.to_ordered_dict() for txn in txns]
        pow_hash = calc_hash('{}:{}:{}'.format(json.dumps(ordered_txns, sort_keys=True), prev_hash, pow))
        return pow_hash[0:char_count] == char * char_count

    @staticmethod
    def is_block_chain_valid(block_chain):
        # Start prev_idx at the second to last element
        prev_idx = len(block_chain) - 2

        # Use a reverse iterator over blockchain elements to process last block first
        for block_to_check in reversed(block_chain):
            # First element of current block must equal the entire previous block
            if prev_idx >= 0 and (block_to_check.prev_hash != calc_hash(str(block_chain[prev_idx]))):
                print('ERROR: Block ' + str(block_to_check.idx) + ' failed previous hash validation')
                return False

            if not Verification.is_pow_valid(
                    # We have to exclude the reward txn when validating POW
                    # - could use list comprehension to filter the txns
                    #   [txn for txn in block_to_check['txns'] if txn['sender'] != MINING_SENDER]
                    # Use range selector to exclude last txn in list - which we know is the reward txn
                    block_to_check.txns[:-1],
                    block_to_check.prev_hash,
                    block_to_check.proof):
                print('ERROR: Block ' + str(block_to_check.idx) + ' failed POW validation')
                return False

            prev_idx -= 1

        return True
