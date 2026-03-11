"""
Custom TCP networking protocol for sending/receiving data.
Implements length-prefixed messaging for text and binary data transmission.
"""
import socket
import aes_cipher
import json

MSG_LEN = 1024
PADDED_LENGTH = 8
INT_SIZE_BYTES = 8
NO_DATA_LEFT = 0
KEY = 1
SOCK = 0


class Protocol(object):
    @staticmethod
    def send(data, conn):
        """Function to send text data over the network"""
        try:
            encoded_msg = data.encode()
            if conn[KEY] is not None:
                encoded_msg = aes_cipher.AESCipher.encrypt(
                    conn[KEY],
                    encoded_msg
                )
            l1 = len(encoded_msg)
            l2 = str(l1)
            l3 = l2.zfill(PADDED_LENGTH)
            l4 = l3.encode()
            conn[SOCK].sendall(l4 + encoded_msg)
        except socket.error as msg:
            print("socket error:", msg)
        except Exception as msg:
            print("general error:", msg)

    @staticmethod
    def recv(conn):
        """Function to receive text data from the network"""
        raw_size = INT_SIZE_BYTES
        tot_data = b''
        while raw_size > NO_DATA_LEFT:
            data = conn[SOCK].recv(raw_size)
            if not data:
                raise ConnectionError("Connection closed")
            raw_size -= len(data)
            tot_data += data
        raw_size = int(tot_data.decode())
        tot_data = b''
        while raw_size > NO_DATA_LEFT:
            data = conn[SOCK].recv(raw_size)
            if not data:
                raise ConnectionError("Connection closed")
            raw_size -= len(data)
            tot_data += data
        if conn[KEY] is not None:
            tot_data = aes_cipher.AESCipher.decrypt(conn[KEY], tot_data)
        return tot_data.decode()

    @staticmethod
    def send_json(obj, conn):
        """
        Send a python dict/list as JSON string using Protocol.send.
        """
        Protocol.send(json.dumps(obj), conn)

    @staticmethod
    def recv_json(conn):
        """
        Receive JSON string using Protocol.recv and parse it.
        """
        return json.loads(Protocol.recv(conn))

    @staticmethod
    def send_bin(data, conn):
        try:
            l1 = len(data)
            l2 = str(l1)
            l3 = l2.zfill(PADDED_LENGTH)
            l4 = l3.encode()
            conn[SOCK].sendall(l4 + data)
        except socket.error as msg:
            print("socket error:", msg)
        except Exception as msg:
            print("general error:", msg)

    @staticmethod
    def recv_bin(conn):
        raw_size = INT_SIZE_BYTES
        tot_data = b''
        while raw_size > NO_DATA_LEFT:
            data = conn[SOCK].recv(raw_size)
            if not data:
                raise ConnectionError("Connection closed during recv_bin")
            raw_size -= len(data)
            tot_data += data
        raw_size = int(tot_data.decode())
        tot_data = b''
        while raw_size > NO_DATA_LEFT:
            data = conn[SOCK].recv(raw_size)
            if not data:
                raise ConnectionError("Connection closed during recv_bin")
            raw_size -= len(data)
            tot_data += data
        return tot_data
