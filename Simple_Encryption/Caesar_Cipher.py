"""
Caesar cipher
"""


def encryptCaesar(message1, shift):
    new_message = ""
    for ch in message1.upper():  # נעבוד עם אותיות גדולות
        if ch.isalpha():
            code = ord(ch) + shift
            if code > ord('Z'):  # אם עברנו את Z
                code = code - 26
            new_message += chr(code)
        else:
            new_message += ch  # משאיר רווחים/סימנים
    return new_message


message1 = "HELLO WORLD"
encrypted = encryptCaesar(message1, 4)
print(encrypted)


def encrypt_upside(message2, shift):
    new_message = ""
    for ch in message2.upper():
        if ch.isalpha():
            code = ord(ch) - shift
            if code < ord('A'):
                code = code + 26
            new_message += chr(code)
        else:
            new_message += ch
    return new_message


message2 = encrypted
encrypted_u = encrypt_upside(message2, 4)
print(encrypted_u)

"""
Subsitution Cipher
"""


def encrypt_subsitution(message1):
    new_message = ""
    for ch in message1.upper():  # נעבוד עם אותיות גדולות
        if ch.isalpha():
            new_message += mapping[ch]
        else:
            new_message += ch  # משאיר רווחים/סימנים
    return new_message


mapping = {
    'A': 'Q', 'B': 'W', 'C': 'E', 'D': 'R', 'E': 'T', 'F': 'Y',
    'G': 'U', 'H': 'I', 'I': 'O', 'J': 'P', 'K': 'A', 'L': 'S',
    'M': 'D', 'N': 'F', 'O': 'G', 'P': 'H', 'Q': 'J', 'R': 'K',
    'S': 'L', 'T': 'Z', 'U': 'X', 'V': 'C', 'W': 'V', 'X': 'B',
    'Y': 'N', 'Z': 'M'
}

message2 = "HELLO WORLD"
encrypted = encrypt_subsitution(message2)
print(encrypted)

reverse_mapping = {v: k for k, v in mapping.items()}


def encrypt_upside_subsitution(message1):
    new_message = ""
    for ch in message1.upper():  # נעבוד עם אותיות גדולות
        if ch.isalpha():
            new_message += reverse_mapping[ch]
        else:
            new_message += ch  # משאיר רווחים/סימנים
    return new_message


encrypted = encrypt_subsitution(message2)
message3 = encrypt_upside_subsitution(encrypted)
print(message3)

"""
Vigenere cipher
"""

def vigenere_encrypt(message, key):
    new_message = ""
    key = key.upper()
    message = message.upper()
    key_index = 0

    for ch in message:
        if ch.isalpha():
            # מוצאים את האינדקס של האות בהודעה ובמילת המפתח
            msg_index = ord(ch) - ord('A')
            key_char = key[key_index % len(key)]
            key_shift = ord(key_char) - ord('A')

            # מוסיפים את ההזזה לפי האות במילת המפתח
            new_code = (msg_index + key_shift) % 26
            new_message += chr(new_code + ord('A'))

            key_index += 1
        else:
            new_message += ch  # משאירים רווחים וסימנים

    return new_message


def vigenere_decrypt(encrypted, key):
    new_message = ""
    key = key.upper()
    encrypted = encrypted.upper()
    key_index = 0

    for ch in encrypted:
        if ch.isalpha():
            msg_index = ord(ch) - ord('A')
            key_char = key[key_index % len(key)]
            key_shift = ord(key_char) - ord('A')

            # מפחיתים את ההזזה כדי לפענח
            new_code = (msg_index - key_shift + 26) % 26
            new_message += chr(new_code + ord('A'))

            key_index += 1
        else:
            new_message += ch

    return new_message


# דוגמה לשימוש
message = "HELLO WORLD"
key = "RUN"

encrypted = vigenere_encrypt(message, key)
print(encrypted)





def encrypt_vigenere(message, key):
    new_message = ""
    key = key.upper()
    message = message.upper()
    key_index = 0

    for ch in message:
        if ch.isalpha():
            # מוצאים את האינדקס של האות בהודעה ובמילת המפתח
            msg_index = ord(ch) - ord('A')
            key_char = key[key_index % len(key)]
            key_shift = ord(key_char) - ord('A')

            # מוסיפים את ההזזה לפי האות במילת המפתח
            new_code = (msg_index + key_shift) % 26
            new_message += chr(new_code + ord('A'))

            key_index += 1
        else:
            new_message += ch  # משאירים רווחים וסימנים

    return new_message


def encrypt_upside_vigenere(encrypted, key):
    new_message = ""
    key = key.upper()
    encrypted = encrypted.upper()
    key_index = 0

    for ch in encrypted:
        if ch.isalpha():
            msg_index = ord(ch) - ord('A')
            key_char = key[key_index % len(key)]
            key_shift = ord(key_char) - ord('A')

            # מפחיתים את ההזזה כדי לפענח
            new_code = (msg_index - key_shift + 26) % 26
            new_message += chr(new_code + ord('A'))

            key_index += 1
        else:
            new_message += ch

    return new_message


# דוגמה לשימוש
message = "YYYCI JFLYU"
key = "RUN"

encrypted = encrypt_upside_vigenere(message, key)
print(encrypted)






