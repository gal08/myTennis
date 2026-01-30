import Protocol
from diffie_hellman import *


class KeyExchange(object):

    @staticmethod
    def send_recv_key(conn):
        dh = DiffieHellman()
        Protocol.Protocol.send_bin(dh.serialize_public_key(), conn)  # DH public key
        dh_key_bytes = Protocol.Protocol.recv_bin(conn)  # DH public key
        dh_key = dh.deserialize_public_key(dh_key_bytes)

        key = dh.get_key(dh_key)
        return key

    @staticmethod
    def recv_send_key(conn):
        """ recieves client dh key and sends both dh key and aes key """
        dh_key_bytes = Protocol.Protocol.recv_bin(conn)
        dh = DiffieHellman()
        dh_key = dh.deserialize_public_key(dh_key_bytes)
        Protocol.Protocol.send_bin(dh.serialize_public_key(), conn)
        key = dh.get_key(dh_key)
        return key