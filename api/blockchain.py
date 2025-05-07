import hashlib

class Blockchain:
    def __init__(self):
        self.chain = []

    def create_block(self, data, previous_hash):
        block = {
            'index': len(self.chain) + 1,
            'data': data,
            'previous_hash': previous_hash,
            'hash': self.hash_block(data, previous_hash)
        }
        self.chain.append(block)
        return block

    def get_last_block(self):
        return self.chain[-1] if self.chain else None

    def hash_block(self, data, previous_hash):
        return hashlib.sha256(f"{data}{previous_hash}".encode()).hexdigest()