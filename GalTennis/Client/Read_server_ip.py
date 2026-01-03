"""
Gal Haham
Server IP configuration reader.
Reads the server IP address from a configuration file.
REFACTORED: Added constants and comprehensive documentation.
"""


# File Configuration
SERVER_IP_FILE = "serverIp.txt"
FILE_ENCODING = "utf-8"
FILE_MODE_READ = "r"


def readServerIp():
    """
    Read the server IP address from configuration file.

    Reads the server IP from serverIp.txt file, strips whitespace,
    and returns it as a string. This allows for easy configuration
    of the server address without modifying code.

    Returns:
        str: Server IP address (e.g., "127.0.0.1" or "192.168.1.100")

    Raises:
        FileNotFoundError: If serverIp.txt does not exist
        IOError: If file cannot be read

    """
    with open(SERVER_IP_FILE, FILE_MODE_READ, encoding=FILE_ENCODING) as f:
        ip = f.read().strip()
    return ip
