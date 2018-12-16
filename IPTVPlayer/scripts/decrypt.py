# -*- coding: utf-8 -*-

import sys

def printDBG(strDat):
    print("%s" % strDat)
    #print("%s" % strDat, file=sys.stderr)

def decrypt_file(file, key):
    from crypto.cipher.aes import AES
    from crypto.cipher.base import noPadding

    cipher = AES(key, keySize=len(key), padding=noPadding())

    f = open(file, 'r+b')
    while True:
        for enc in [True, False]:
            if enc:
                data = f.read(len(key))
            else:
                data = f.read(len(key)*1000)
            if len(data) == len(key):
                data = cipher.decrypt(data)
                f.seek(f.tell() - len(key))
                f.write(data)
        if not data:
            break
    f.close()

if __name__ == "__main__":
    if len(sys.argv) < 4:
        printDBG('Please provide libsPath, filePath, keyPath')
        sys.exit(1)

    libsPath = sys.argv[1]
    file = sys.argv[2]
    keyPath = sys.argv[3]
    with open(keyPath, "rb") as f:
        key = f.read()

    sys.path.insert(1, libsPath)
    decrypt_file(file, key)
    sys.exit(0)

