# -*- coding: utf-8 -*-

import sys
from crypto.cipher.aes import AES
from crypto.cipher.base import noPadding

def printDBG(strDat):
    print("%s" % strDat)
    #print("%s" % strDat, file=sys.stderr)

def decrypt_file(file, key):
    cipher = AES(key, keySize=len(key), padding=noPadding())

    f = open(file, 'r+b')
    while True:
        for enc in [True, False]:
            if enc:
                data = f.read(len(key))
            else:
                data = f.read(len(key)*100)
            if len(data) == len(key):
                data = cipher.decrypt(data)
                f.seek(f.tell() - len(key))
                f.write(data)
        if not data:
            break
    f.close()

if __name__ == "__main__":
    if len(sys.argv) < 4:
        printDBG('Please provide libsPath, filePath, key')
        sys.exit(1)

    libsPath = sys.argv[1]
    file = sys.argv[2]
    key = sys.argv[3]
    sys.path.insert(1, libsPath)
    decrypt_file(file, key)
    sys.exit(0)

