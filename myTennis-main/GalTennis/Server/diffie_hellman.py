from secrets import token_bytes

from cryptography.hazmat.primitives import hashes, padding
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.serialization import (
    Encoding,
    PublicFormat,
    load_pem_public_key
)


class DiffieHellman:
    def __init__(self):
        """ constructor"""
        self.diffieHellman = ec.generate_private_key(ec.SECP384R1())
        self.public_key = self.diffieHellman.public_key()

    def serialize_public_key(self):
        """ serialize public key object """
        return self.public_key.public_bytes(Encoding.PEM,
                                            PublicFormat.SubjectPublicKeyInfo)

    def deserialize_public_key(self, data):
        """ deserialize public key object """
        return load_pem_public_key(data)

    def get_key(self, public_key):
        """ return generated shared key, hashed """
        shared_key = self.diffieHellman.exchange(ec.ECDH(), public_key)

        derived_key = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=None,
            info=None
        ).derive(shared_key)
        return derived_key


def main():
    """ unit testing """
    alice = DiffieHellman()
    bob = DiffieHellman()

    bob_key = bob.get_key(alice.public_key)
    print(bob_key)

    alice_key = alice.get_key(bob.public_key)
    print(alice_key)


if __name__ == "__main__":
    main()
