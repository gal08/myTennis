"""
Substitution Cipher
"""

# Define the substitution mapping
# Each letter A-Z is mapped to a different letter
mapping = {
    'A': 'Q', 'B': 'W', 'C': 'E', 'D': 'R', 'E': 'T', 'F': 'Y',
    'G': 'U', 'H': 'I', 'I': 'O', 'J': 'P', 'K': 'A', 'L': 'S',
    'M': 'D', 'N': 'F', 'O': 'G', 'P': 'H', 'Q': 'J', 'R': 'K',
    'S': 'L', 'T': 'Z', 'U': 'X', 'V': 'C', 'W': 'V', 'X': 'B',
    'Y': 'N', 'Z': 'M'
}

# Create reverse mapping for decryption
# This swaps keys and values: if A→Q in mapping,
# then Q→A in reverse_mapping
reverse_mapping = {v: k for k, v in mapping.items()}


def encrypt_subsitution(message1):
    new_message = ""

    # Loop through each character in the message (converted to uppercase)
    for ch in message1.upper():
        if ch.isalpha():  # Only encrypt letters
            # Replace the letter using the mapping dictionary
            new_message += mapping[ch]
        else:
            # Preserve non-alphabetic characters (spaces, punctuation, numbers)
            new_message += ch

    return new_message


def encrypt_upside_subsitution(message1):
    new_message = ""

    # Loop through each character in the message (converted to uppercase)
    for ch in message1.upper():
        if ch.isalpha():  # Only decrypt letters
            # Replace the letter using the reverse mapping dictionary
            new_message += reverse_mapping[ch]
        else:
            # Preserve non-alphabetic characters (spaces, punctuation, numbers)
            new_message += ch

    return new_message


def main():
    # Example message
    message1 = "HELLO WORLD"
    # Encrypt the message
    encrypted = encrypt_subsitution(message1)
    print(f"Encrypted: {encrypted}")  # Output: "ITSSG VGKSR"
    # Decrypt the message
    message2 = encrypt_upside_subsitution(encrypted)
    print(f"Decrypted: {message2}")  # Output: "HELLO WORLD"


if __name__ == '__main__':
    main()
