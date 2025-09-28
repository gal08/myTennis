"""
Our message is going to be "hello world" and we want a Caesar cipher with a shift of 3
"""


def encrypt(message1, shift):
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
encrypted = encrypt(message1, 3)
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
encrypted_u = encrypt_upside(message2, 3)
print(encrypted_u)