"""
Gal Haham
Custom TCP networking protocol for sending/receiving data.
Implements length-prefixed messaging for text and binary data transmission.
"""
import socket
IP = "0.0.0.0"
PORT = 1235
MSG_LEN = 1024
PADDED_LENGTH = 4
INT_SIZE_BYTES = 4
NO_DATA_LEFT = 0


class Protocol(object):
    # Protocol class: Handles sending and receiving data over TCP sockets.
    # It implements a custom networking protocol where each message is
    # preceded by a fixed-size length header that indicates the payload size.
    # This ensures messages are transmitted and reconstructed correctly
    # regardless of TCP stream boundaries.
    @staticmethod
    def send(my_socket, data):
        """Function to send text data over the network"""
        try:
            encoded_msg = data.encode()
            l1 = len(encoded_msg)
            l2 = str(l1)
            l3 = l2.zfill(PADDED_LENGTH)
            l4 = l3.encode()
            my_socket.send(l4 + encoded_msg)
        except socket.error as msg:
            print("socket error:", msg)
        except Exception as msg:
            print("general error:", msg)

    @staticmethod
    def recv(my_socket):
        """Function to receive text data from the network"""
        raw_size = INT_SIZE_BYTES
        tot_data = b''

        while raw_size > NO_DATA_LEFT:
            data = my_socket.recv(raw_size)
            raw_size -= len(data)
            tot_data += data
        raw_size = int(tot_data.decode())
        tot_data = b''
        while raw_size > NO_DATA_LEFT:
            data = my_socket.recv(raw_size)
            raw_size -= len(data)
            tot_data += data
        return tot_data.decode()

    @staticmethod
    def send_bin(my_socket, data):
        """Function to send binary data over the network"""
        try:
            l1 = len(data)
            l2 = str(l1)
            l3 = l2.zfill(PADDED_LENGTH)
            l4 = l3.encode()
            my_socket.send(l4 + data)
        except socket.error as msg:
            print("socket error:", msg)
        except Exception as msg:
            print("general error:", msg)

    @staticmethod
    def recv_bin(my_socket):
        """Function to receive binary data from the network"""
        raw_size = INT_SIZE_BYTES
        tot_data = b''

        while raw_size > NO_DATA_LEFT:
            data = my_socket.recv(raw_size)
            raw_size -= len(data)
            tot_data += data
        raw_size = int(tot_data.decode())
        tot_data = b''
        while raw_size > NO_DATA_LEFT:
            data = my_socket.recv(raw_size)
            raw_size -= len(data)
            tot_data += data
        return tot_data