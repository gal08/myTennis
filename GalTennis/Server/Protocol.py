import socket
IP = "0.0.0.0"
PORT = 1235
MSG_LEN = 1024


class Protocol(object):
    @staticmethod
    def send(my_socket, data):
        """Function to send text data over the network"""
        try:
            encoded_msg = data.encode()
            l1 = len(encoded_msg)
            l2 = str(l1)
            l3 = l2.zfill(4)
            l4 = l3.encode()
            my_socket.send(l4 + encoded_msg)
        except socket.error as msg:
            print("socket error:", msg)
        except Exception as msg:
            print("general error:", msg)

    @staticmethod
    def recv(my_socket):
        """Function to receive text data from the network"""
        raw_size = 4
        tot_data = b''

        while raw_size > 0:
            data = my_socket.recv(raw_size)
            raw_size -= len(data)
            tot_data += data
        raw_size = int(tot_data.decode())
        tot_data = b''
        while raw_size > 0:
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
            l3 = l2.zfill(4)
            l4 = l3.encode()
            my_socket.send(l4 + data)
        except socket.error as msg:
            print("socket error:", msg)
        except Exception as msg:
            print("general error:", msg)

    @staticmethod
    def recv_bin(my_socket):
        """Function to receive binary data from the network"""
        raw_size = 4
        tot_data = b''

        while raw_size > 0:
            data = my_socket.recv(raw_size)
            raw_size -= len(data)
            tot_data += data
        raw_size = int(tot_data.decode())
        tot_data = b''
        while raw_size > 0:
            data = my_socket.recv(raw_size)
            raw_size -= len(data)
            tot_data += data
        return tot_data
