import binascii
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5
import Crypto.Random


# Data file info
DATA_DIR = './data'
DATA_FILE = 'wallet'
DATA_FILE_PATH = DATA_DIR + '/' + DATA_FILE


class Wallet:

    def __init__(self, node_id):
        self.private_key = None
        self.public_key = None
        self.__node_id = node_id

    @staticmethod
    def generate_keys():
        private_key = RSA.generate(1024, Crypto.Random.new().read)
        public_key = private_key.publickey()
        return (
            binascii.hexlify(private_key.exportKey(format='DER')).decode('ascii'),
            binascii.hexlify(public_key.exportKey(format='DER')).decode('ascii')
        )

    def create_keys(self):
        self.private_key, self.public_key = Wallet.generate_keys()

    def save_keys(self):
        if self.public_key is None or self.private_key is None:
            print('WARN: Failed to save invalid wallet keys')
            return False
        else:
            try:
                with open('{}_{}'.format(DATA_FILE_PATH, self.__node_id), mode='w') as f:
                    f.write(self.public_key + '\n')
                    f.write(self.private_key)
                return True
            except (IOError, IndexError):
                print('ERROR: Failed to save wallet to file')
                return False

    def load_keys(self):
        try:
            with open('{}_{}'.format(DATA_FILE_PATH, self.__node_id), mode='r') as f:
                keys = f.readlines()
                self.public_key = keys[0][:-1]
                self.private_key = keys[1]
            return True
        except (IOError, IndexError):
            print('ERROR: Failed to load wallet from file')
            return False

    def sign_txn(self, sender, recipient, amount):
        signer = PKCS1_v1_5.new(RSA.import_key(binascii.unhexlify(self.private_key)))
        generated_hash = SHA256.new((str(sender) + str(recipient) + str(amount)).encode('utf8'))
        signature = signer.sign(generated_hash)
        return binascii.hexlify(signature).decode('ascii')
