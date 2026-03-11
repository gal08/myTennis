import Protocol
from diffie_hellman import *


class KeyExchange(object):
    """Handles Diffie-Hellman key exchange over a connection."""

    @staticmethod
    def send_recv_key(conn):
        """Sends own DH public key, receives peer's key,
         and returns shared secret."""
        dh = DiffieHellman()
        Protocol.Protocol.send_bin(dh.serialize_public_key(), conn)
        dh_key_bytes = Protocol.Protocol.recv_bin(conn)
        dh_key = dh.deserialize_public_key(dh_key_bytes)
        key = dh.get_key(dh_key)
        return key

    @staticmethod
    def recv_send_key(conn):
        """Receives peer DH key, sends own key, and returns shared secret."""
        dh_key_bytes = Protocol.Protocol.recv_bin(conn)
        dh = DiffieHellman()
        dh_key = dh.deserialize_public_key(dh_key_bytes)
        Protocol.Protocol.send_bin(dh.serialize_public_key(), conn)
        key = dh.get_key(dh_key)
        return key
