"""
Vigenere Cipher
"""


def vigenere_encrypt(message, key):
    new_message = ""
    key = key.upper()
    message = message.upper()
    key_index = 0  # Tracks position in the key

    for ch in message:
        if ch.isalpha():  # Only encrypt letters
            # Convert letter to number (A=0, B=1, ..., Z=25)
            msg_index = ord(ch) - ord('A')

            # Get the current key character (wraps around using modulo)
            key_char = key[key_index % len(key)]

            # Calculate shift amount from key character
            key_shift = ord(key_char) - ord('A')

            # Apply the shift and wrap around the alphabet
            new_code = (msg_index + key_shift) % 26
            new_message += chr(new_code + ord('A'))

            # Move to next key character (only for letters)
            key_index += 1
        else:
            # Preserve non-alphabetic characters (spaces, punctuation, numbers)
            new_message += ch

    return new_message


def vigenere_decrypt(encrypted, key):
    new_message = ""
    key = key.upper()
    encrypted = encrypted.upper()
    key_index = 0  # Tracks position in the key

    for ch in encrypted:
        if ch.isalpha():  # Only decrypt letters
            # Convert letter to number (A=0, B=1, ..., Z=25)
            msg_index = ord(ch) - ord('A')

            # Get the current key character (wraps around using modulo)
            key_char = key[key_index % len(key)]

            # Calculate shift amount from key character
            key_shift = ord(key_char) - ord('A')

            # Apply the reverse shift (subtract instead of add) and wrap around
            # The +26 ensures we don't get negative numbers before the modulo
            new_code = (msg_index - key_shift + 26) % 26
            new_message += chr(new_code + ord('A'))

            # Move to next key character (only for letters)
            key_index += 1
        else:
            # Preserve non-alphabetic characters (spaces, punctuation, numbers)
            new_message += ch

    return new_message


def main():
    # Example usage
    message = "HELLO WORLD"
    key = "RUN"

    # Encrypt the message
    encrypted = vigenere_encrypt(message, key)
    print(f"Encrypted: {encrypted}")  # Output: "YYYCI JFLYU"

    # Decrypt the message
    decrypt = vigenere_decrypt(encrypted, key)
    print(f"Decrypted: {decrypt}")  # Output: "HELLO WORLD"


if __name__ == '__main__':
    main()
