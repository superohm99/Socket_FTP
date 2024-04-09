import socket
import random
import time
import os
import getpass


def rate_ftp(start_time, end_time, size):
        elapsed = end_time - start_time
        if elapsed == 0:
            elapsed = 0.000000001
        tf_rate = (size/1000)/elapsed
        if tf_rate > size: 
            tf_rate = size
        print(f"ftp: {size} bytes received in {elapsed:.2f}Seconds {tf_rate:.2f}Kbytes/sec.")


status_open = False
host = None
while True:
    line = input('ftp> ').strip()

    if (len(line) == 0):
        continue
    args = line.split()
    command = args[0]
    if command == 'quit':
        break

    elif command == 'binary':
        clientSocket.sendall("TYPE I\r\n".encode())
        resp_binary= clientSocket.recv(1024).decode().strip()
        print(resp_binary)


    elif command == 'open':
        if len(args) > 3:
            print('Usage: open host name [port]')
            continue
        if (status_open == True):
            print(f'Already connected to {host}, use disconnect first.')
        else:
            clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            clientSocket.connect((args[1], int(args[2])))
            print('Connected to {}.'.format(args[1]))
            host = args[1]
            resp = clientSocket.recv(1024)
            print(resp.decode().strip())
            clientSocket.send(f'OPTS UTF8 ON\r\n'.encode())
            resp = clientSocket.recv(1024)
            print(resp.decode(),end="")
            username = input("User ({}:(none)):".format(args[1]))
            # print("331 Password required for '{}'.".format(username))
            clientSocket.sendall(f"USER {username}\r\n".encode())
            resp_user = clientSocket.recv(1024)
            print(resp_user.decode().strip())
            if username == '':
                print("Login failed.")
                status_open = True
                continue

            password = getpass.getpass("Password: ")
            print('')
            clientSocket.sendall(f"PASS {password}\r\n".encode())
            resp_password = clientSocket.recv(1024)
            status_open = True
            print(resp_password.decode().strip())
            if (resp_password.decode().strip() == "530 Login incorrect."):
                print("Login failed.")
                continue
            server_ip = args[1]
            server_port = int(args[2])
            # print("230 User '{}' logged in.".format(args[1]))

    elif command == 'pwd' and status_open == True:
        clientSocket.sendall("XPWD\r\n".encode())
        resp_pwd = clientSocket.recv(1024).decode().strip()
        print(resp_pwd)
    
    elif command == 'rename' and status_open == True:
        if len(args) == 3:
            filename = args[1]
            newname = args[2]
        if len(args) == 2:
            filename = args[1]
            newname = None
        if len(args) == 1:
            filename = input('From name ')
            newname = None
        if filename == '':
            print('rename from-name to-name.')
        if newname is None:
            newname = input('To name ')
        if newname == '':
            print('rename from-name to-name.')
        if (filename != '' or newname != ''):
            clientSocket.sendall(f"RNFR {filename}\r\n".encode())
            clientSocket.sendall(f"RNTO {newname}\r\n".encode())
            resp_newname = clientSocket.recv(1024).decode().strip()
            print(resp_newname)
            resp_rename = clientSocket.recv(1024).decode().strip()
            if (resp_rename != "503 Use RNFR first."):
                print(resp_rename)


    elif command == 'put' and status_open == True:
        if len(args) == 1:
            file = input('Local file ')
            if file == '':
                print('Local file put: remote file.')
                # return
            new = input('Remote file ')
            if new == '':
                new = file

        if file != '': 

            if not os.path.exists(file):
                print(f'{file}: File not found')

            else:
                number = random.randint(0,65535)
                ipaddr = socket.gethostbyname(socket.gethostname())+f".{number//256}.{number%256}"
                ipaddr = ipaddr.replace('.',',')
                clientSocket.send(f'PORT {ipaddr}\r\n'.encode())
                port_status = clientSocket.recv(1024)
                print(port_status.decode(),end="")


                with open(file,'rb') as f:
                    try:

                        clientSocket.sendall(b'PASV\r\n')
                        response = clientSocket.recv(1024).decode()
                        port_start = response.find('(') + 1
                        port_end = response.find(')')
                        port_str = response[port_start:port_end].split(',')
                        data_port = int(port_str[-2]) * 256 + int(port_str[-1])
                        data_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        data_socket.connect((socket.gethostbyname(host), data_port))
                        clientSocket.sendall((f'STOR {new}\r\n').encode())
                        response = clientSocket.recv(4096).decode()
                        print(response,end='')
                
                        size = 0  
                        start_time = time.time()
                        data = f.read(4096)
                        while data:
                            data_socket.sendall(data)
                            data = f.read(4096)
                    finally:
                        data_socket.close()
                    response = clientSocket.recv(1024)
                    print(response.decode(),end='')
                    
                    end_time = time.time()
                    rate_ftp(start_time, end_time, size+10)



    elif command == 'cd' and status_open == True:
        if (len(args) == 2):
            path = args[1]
        if len(args) == 1:
            path = input('Remote directory ')
        if path == '':
            print("cd remote directory.")
        if path != '':
            clientSocket.sendall(f"CWD {path}\r\n".encode())
            resp_cd = clientSocket.recv(1024).decode().strip()
            print(resp_cd)
        
    elif command == 'delete' and status_open == True:
        if len(args) == 2:
            file = args[1]
        if len(args) == 1:
            file = input('Remote file ')
        if file == '':
            print("delete remote file.")
        if file != '':
            clientSocket.sendall(f"DELE {file}\r\n".encode())
            resp_cd = clientSocket.recv(1024).decode().strip()
            print(resp_cd)
    
    elif command == 'get' and status_open == True:
        number = random.randint(0,65535)
        ipaddr = socket.gethostbyname(socket.gethostname())+f".{number//256}.{number%256}"
        ipaddr = ipaddr.replace('.',',')

        if len(args) ==  1:
            remote = input('Remote file ')
            if remote == '':
                print('Remote file get [ local-file ].')
                continue
        else:
            remote = args[1]
            local = remote

        if len(args) ==  1:
            local = input('Local file ')
            if local == '':
                local = remote

        clientSocket.sendall(f"PORT {ipaddr}\r\n".encode())
        resp_pasv_get = clientSocket.recv(1024).decode().strip()
        print(resp_pasv_get)

        clientSocket.sendall(b'PASV\r\n')
        pasv_response = clientSocket.recv(1024).decode()
        parts = pasv_response.split('(')[1].split(')')[0].split(',')
        host = '.'.join(parts[:4])
        port = int(parts[4])*256 + int(parts[5])
        clientSocket.sendall(f"RETR {remote}\r\n".encode())
        a = clientSocket.recv(1024).decode()
        print(a.strip())
        if (a.strip() != "550 This function is not supported on this system."):
            data_sockety = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            data_sockety.settimeout(10)
            data_sockety.connect((host, port))
            with open(local, 'wb') as lf:
                while True:
                    data = data_sockety.recv(1024)
                    size = 0
                    start_time = time.time()
                    if not data:
                        break
                    lf.write(data)


            data_sockety.close()
            resp = clientSocket.recv(1024).decode()
            print(resp,end='')

            end_time = time.time()
            rate_ftp(start_time, end_time, size+10)


    elif command == 'ls' and status_open == True:
        number = random.randint(0,65535)
        ipaddr = socket.gethostbyname(socket.gethostname())+f".{number//256}.{number%256}"
        ipaddr = ipaddr.replace('.',',')
        
        clientSocket.send(f'PORT {ipaddr}\r\n'.encode())
        resp = clientSocket.recv(1024).decode()
        print(resp,end='')

        clientSocket.sendall(b'PASV\r\n')
        pasv_response = clientSocket.recv(1024).decode()
        parts = pasv_response.split('(')[1].split(')')[0].split(',')
        host = '.'.join(parts[:4])
        port = int(parts[4])*256 + int(parts[5])
        with socket.create_connection((host, port)) as data_socket:
            if (len(args) == 1):
                clientSocket.sendall(f"NLST\r\n".encode())
            if (len(args) == 2):
                clientSocket.sendall(f"NLST {args[1]}\r\n".encode())
            dir_response = clientSocket.recv(1024).decode()
            print(dir_response, end='')
            size = 0 
            start_time = time.time()
            while True:
                data = data_socket.recv(4096)
                if not data:
                    break
                print(data.decode(), end='')

    
        control_response = clientSocket.recv(1024).decode()
        print(control_response, end='')
        end_time = time.time()
        
        rate_ftp(start_time, end_time, size+10)

    elif command == 'user' and status_open == True:
        if len(args) > 4:
            print('Usage: user username [password] [account]')
        if (len(args) == 1):
            username = None
            password  = None
        if (len(args) == 2):
            username = args[1]
            password = None
        if (len(args) == 3):
            username = args[1]
            password = args[2]
        if username is None:
            username = input('Username ')
            if username == '':
                print('Usage: user username [password] [account]')
        if len(args) < 4:
            clientSocket.send(f'User {username}\r\n'.encode())
            respp = clientSocket.recv(1024)
            print(respp.decode(),end="")
            if not respp.decode().startswith('331'):
                print('Login failed.')
        
        if password is None and resp.decode().startswith('331'):
            password = getpass.getpass("Password: ")
            print()
        if (username != '' or resp.decode().startswith('331')) and len(args) < 4:
            clientSocket.send(f'PASS {password}\r\n'.encode())
            resp = clientSocket.recv(1024)
            if resp.decode().startswith('5') and respp.decode().startswith('331'):
                print(resp.decode(),end="")
                print('Login failed.')
            else:
                status_open = True
            if (not resp.decode().startswith('5')):
                username = username
                password = password
                print(resp.decode(),end="")
    
    elif command == 'ascii' and status_open == True:
        clientSocket.sendall("TYPE A\r\n".encode())
        resp_ascii= clientSocket.recv(1024)
        print(resp_ascii.decode().strip())
    

    elif status_open == False:
        print("Not connected.")

    elif command == 'disconnect' or command == 'close' or command == 'bye':
        clientSocket.sendall(f"QUIT\r\n".encode())
        resp_quit = clientSocket.recv(1024)
        print(resp_quit.decode().strip())
        clientSocket.close()
        status_open = False