import base64
import hashlib
from Crypto import Random
from Crypto.Cipher import AES


class AESCipher(object):
    """
        A utility class for AES encryption and decryption using CBC mode.

        Features:
            - Encrypt and decrypt data with AES-256 in CBC mode.
            - Automatic PKCS#7-style padding and unpadding.
            - Base64 encoding of ciphertext for safe transmission/storage.
            - Secure random key generation.

        All methods are static; no instance of the class is required.
        """

    @staticmethod
    def encrypt(key, raw):
        """
        Encrypts the given raw data using AES CBC mode with the provided key.

        Parameters:
            key (bytes): The AES key to use for
             encryption (must match decrypt key).
            raw (bytes): The plaintext data to encrypt.

        Returns:
            bytes: Base64-encoded ciphertext with IV prepended.
        """
        raw = AESCipher._pad(raw)
        iv = Random.new().read(AES.block_size)
        cipher = AES.new(key, AES.MODE_CBC, iv)
        b = base64.b64encode(iv + cipher.encrypt(raw))
        return b

    @staticmethod
    def decrypt(key, enc):
        """
        Decrypts AES-encrypted data (Base64 encoded) using the provided key.

        Parameters:
            key (bytes): The AES key used for encryption.
            enc (bytes): Base64-encoded ciphertext with IV prepended.

        Returns:
            bytes: The original plaintext data.
        """
        enc = base64.b64decode(enc)
        iv = enc[:AES.block_size]
        cipher = AES.new(key, AES.MODE_CBC, iv)
        return AESCipher._unpad(cipher.decrypt(enc[AES.block_size:]))

    @staticmethod
    def _pad(s):
        """
        Pads the input data to be a multiple of AES block
        size using PKCS#7 style padding.

        Parameters:
            s (bytes): Data to pad.

        Returns:
            bytes: Padded data.
        """
        bs = AES.block_size
        padding_length = bs - len(s) % bs
        return s + bytes([padding_length] * padding_length)

    @staticmethod
    def _unpad(s):
        """
        Removes PKCS#7 style padding from data.

        Parameters:
            s (bytes): Padded data.

        Returns:
            bytes: Original unpadded data.
        """
        return s[:-s[-1]]

    @staticmethod
    def generate_key():
        """
        Generates a secure 32-byte AES key using SHA-256 of random bytes.

        Returns:
            bytes: 32-byte AES key.
        """
        key = Random.new().read(32)
        return hashlib.sha256(key).digest()


def main():
    """
    Example usage of AESCipher: generates a key,
     encrypts and decrypts sample data,
    and prints the results.
    """
    key = AESCipher.generate_key()
    enc = AESCipher.encrypt(key, ("aa"*100).encode())
    dec = AESCipher.decrypt(key, enc)
    print(enc, dec)


if __name__ == "__main__":
    main()
