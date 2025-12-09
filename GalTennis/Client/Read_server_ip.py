def readServerIp():
    with open("serverIp.txt", "r", encoding="utf-8") as f:
        ip = f.read().strip()
    return ip
