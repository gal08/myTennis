import base64
import hashlib

# install pycryptodome
from Crypto import Random
from Crypto.Cipher import AES


class AESCipher(object):

    @staticmethod
    def encrypt(key, raw):
        raw = AESCipher._pad(raw)
        iv = Random.new().read(AES.block_size)
        cipher = AES.new(key, AES.MODE_CBC, iv)
        b = base64.b64encode(iv + cipher.encrypt(raw))
        # ("encrypted", b)
        return b

    @staticmethod
    def decrypt(key, enc):
        # print("received enc", enc)
        enc = base64.b64decode(enc)
        iv = enc[:AES.block_size]
        # print("key len =", len(key), "block size =", AES.block_size)
        cipher = AES.new(key, AES.MODE_CBC, iv)
        return AESCipher._unpad(cipher.decrypt(enc[AES.block_size:]))

    @staticmethod
    def _pad(s):
        bs = AES.block_size
        k = s + (bs - len(s) % bs) * chr(bs - len(s) % bs).encode()
        # print("pad before -", s)
        # print("pad after  -", k)
        return k

    @staticmethod
    def _unpad(s):
        return s[:-ord(s[len(s)-1:])]

    @staticmethod
    def generate_key():
        key = Random.new().read(32)
        key = hashlib.sha256(key).digest()
        return key



def main():
    # Nominal way to generate a fresh key. This calls the system's random number
    # generator (RNG).
    key = AESCipher.generate_key()

    enc = AESCipher.encrypt(key, ("aa"*100).encode())
    dec = AESCipher.decrypt(key, enc)
    print(enc, dec)

if __name__ == "__main__":
    main()


