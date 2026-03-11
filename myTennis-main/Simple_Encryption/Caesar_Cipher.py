"""
Caesar Cipher
"""


def encrypt_Caesar(message1, shift):
    new_message = ""

    # Loop through each character in the message
    # (after converting to uppercase)
    for ch in message1.upper():
        if ch.isalpha():  # Check if the character is a letter
            # Calculate the new ASCII code after shifting
            code = ord(ch) + shift

            # If we've passed the letter Z,
            # wrap back to the start of the alphabet
            if code > ord('Z'):
                code = code - 26

            # Add the encrypted letter to the new message
            new_message += chr(code)
        else:
            # If it's not a letter (space, punctuation, etc.) - keep it as-is
            new_message += ch

    return new_message


def encrypt_upside(message2, shift):
    new_message = ""

    # Loop through each character in the encrypted
    # message (after converting to uppercase)
    for ch in message2.upper():
        if ch.isalpha():  # Check if the character is a letter
            # Calculate the new ASCII code after shifting backward
            code = ord(ch) - shift

            # If we've gone before the letter A,
            # wrap to the end of the alphabet
            if code < ord('A'):
                code = code + 26

            # Add the decrypted letter to the new message
            new_message += chr(code)
        else:
            # If it's not a letter (space, punctuation, etc.) - keep it as-is
            new_message += ch

    return new_message


def main():
    # Encryption
    encrypted = encrypt_Caesar("HELLO WORLD", 3)
    print(f"Encrypted: {encrypted}")  # Output: "KHOOR ZRUOG"

    # Decryption
    decrypted = encrypt_upside("KHOOR ZRUOG", 3)
    print(f"Decrypted: {decrypted}")  # Output: "HELLO WORLD"


if __name__ == '__main__':
    main()
