# Python 3 code to demonstrate
# SHA hash algorithms.

import hashlib

class Hasha256:
    @staticmethod
    def get_hash(st):
        """ encoding and sending to SHA256() """
        result = hashlib.sha256(st.encode())
        return result.digest()

    def get_hash_hex(st):
        """ printing the equivalent hexadecimal value. """
        result = hashlib.sha256(st.encode())
        return result.hexdigest()

def main():
    """ hashing tests """
    # initializing string
    st = "hello my name is inigo montoya"
    print(Hasha256.get_hash(st))
    print(Hasha256.get_hash_hex(st))

if __name__ == "__main__":
    main()
