import socket
import sys
import threading
import gzip
import zlib
# import concurrent.futures

NOT_FOUND = b"HTTP/1.1 404 Not Found\r\n\r\n"

def main():
    _socket = socket.socket()
    _socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_address = ("localhost", 4221)
    _socket.bind(server_address)
    _socket.listen()
    sys_args = sys.argv
    while True:
        client_socket, host_address_and_port = _socket.accept()
        threading.Thread(target=handle_request, args=(client_socket, sys_args)).start()
        if threading.active_count() == 0:
            break
    _socket.close()

def handle_request(request: socket, sys_args: list[str]):
    _encodings_list = ["identity", "gzip", "deflate", "br", "zstd"]
    
    data = request.recv(2048).decode('utf-8') # read up to 4096 bytes, convert bytes to string
    response = NOT_FOUND
    if not data:
        return
    
    data = data.split("\r\n")
    type = data[0].split()[0]
    cmd = data[0].split()[1]
    
    if type == "GET":    
        if "/echo/" in cmd:
            string = cmd[6:]
            _f = False
            for i in data:
                if "Accept-Encoding: " in i:
                    encoding_type = i[17:].split(", ")
                    _available_encoding = list(set(encoding_type) & set(_encodings_list))
                    if _available_encoding != []:
                        _f = True
                        if "gzip" in _available_encoding:
                            gzip_encoded_string = gzip.compress(bytes(string, 'utf-8'))
                            print(gzip_encoded_string)
                            response = bytes(f"HTTP/1.1 200 OK\r\nContent-Encoding: gzip\r\nContent-Type: text/plain\r\nContent-Length: {len(gzip_encoded_string)}\r\n\r\n", 'utf-8') + gzip_encoded_string
                        else:
                            response = bytes(f"HTTP/1.1 200 OK\r\nContent-Encoding: {', '.join(_available_encoding)}\r\nContent-Type: text/plain\r\nContent-Length: {len(string)}\r\n\r\n{string}", 'utf-8')
                        break
                    else:
                        break
            if not _f:
                response = f"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nContent-Length: {len(string)}\r\n\r\n{string}\r\n\r\n".encode()
        elif "/user-agent" in cmd:
            _f = False
            for i in data:
                if "User-Agent: " in i:
                    _f = True
                    user_agent = i[12:]
                    response = f"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nContent-Length: {len(user_agent)}\r\n\r\n{user_agent}".encode()
            if not _f:
                response = f"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nContent-Length: 0\r\n\r\n".encode()
                
        elif "--directory" in sys_args and "files" in cmd:
            directory = sys_args[sys_args.index("--directory") + 1]
            if directory[-1] == "/":
                directory = directory[:-1]
            string = directory + cmd[6:]
            try:
                file = open(file=string, mode='r')
                file_content = ''.join(file.readlines())
                response = f"HTTP/1.1 200 OK\r\nContent-Type: application/octet-stream\r\nContent-Length: {len(file_content)}\r\n\r\n{file_content}".encode()
                file.close()
            except:
                response = NOT_FOUND
        elif cmd == "/": # if not root cmd
            response = b"HTTP/1.1 200 OK\r\n\r\n" # default response
        else:
            response = NOT_FOUND # not found
    elif type == "POST":
        if "--directory" in sys_args and "files" in cmd:
            directory = sys_args[sys_args.index("--directory") + 1]
            if directory[-1] == "/":
                directory = directory[:-1]
            path = directory + cmd[6:]
            file_content = data[data.index("") + 1]
            file = open(file=path, mode='w')
            file.write(file_content)
            file.close()
            response = f"HTTP/1.1 201 Created\r\n\r\n".encode()
        else:
            response = NOT_FOUND
    
    request.send(response)
    request.close()


if __name__ == "__main__":
    main()
