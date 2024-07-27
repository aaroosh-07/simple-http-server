# Uncomment this to pass the first stage
import socket
import sys
import gzip
from threading import Thread

def parser(httpReq: str):
    reqDict = dict()
    req: list[str] = httpReq.split("\r\n")
    requestLine: list[str] = req[0].split()
    reqDict["verb"] = requestLine[0]
    reqDict["path"] = requestLine[1]

    i = 1
    while i < len(req):
        if req[i] == "":
            break

        header, content = req[i].split(":", 1)
        content = content.lstrip()
        header = header.lower()

        reqDict[header] = content
        i += 1
    
    reqDict["body"] = req[i+1]

    return reqDict

def handle_get_req(httpReq):
    path: str = httpReq["path"]
    httpResponse = b"HTTP/1.1 404 Not Found\r\n\r\n"
    if path == str("/"):
        httpResponse = b"HTTP/1.1 200 OK\r\n\r\n"
    elif "/echo/" in path:
        pathList: list[str] = path.split('/')
        string = pathList[2]
        encoding_sup_client = httpReq.get("accept-encoding", "")
        encoding_list = [x.lstrip() for x in encoding_sup_client.split(',')]
        if "gzip" in encoding_list:
            compressedString = gzip.compress(bytes(string, "utf-8"))
            httpResponse = f"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nContent-Encoding: gzip\r\nContent-Length: {len(compressedString)}\r\n\r\n"
            httpResponse = bytes(httpResponse, "utf-8") + compressedString
        else:
            httpResponse = f"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nContent-Length: {len(string)}\r\n\r\n{string}"
            httpResponse = bytes(httpResponse, "utf-8")
    elif "/user-agent" in path:
        user_agent_value = httpReq["user-agent"]
        httpResponse = f"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nContent-Length: {len(user_agent_value)}\r\n\r\n{user_agent_value}"
        httpResponse = bytes(httpResponse, "utf-8")
    elif "/files/" in path:
        directory = sys.argv[2]
        pathVar: list[str] = path.split("/")
        fileName: str = pathVar[2]
        try:
            with open(f"{directory}/{fileName}", "r") as fileObj:
                body = fileObj.read()
                httpResponse = f"HTTP/1.1 200 OK\r\nContent-Type: application/octet-stream\r\nContent-Length: {len(body)}\r\n\r\n{body}"
                httpResponse = bytes(httpResponse, "utf-8")
        except Exception as e:
            #do not do anything 404 sent by default case
            pass
    
    return httpResponse

def handle_post_req(httpReq):
    path: str = httpReq["path"]
    httpResponse = b"HTTP/1.1 404 Not Found\r\n\r\n"
    if httpReq["verb"] == "POST":
        directory = sys.argv[2]
        pathVar: list[str] = path.split("/")
        fileName: str = pathVar[2]
        try:
            with open(f"{directory}/{fileName}", "w") as fileObj:
                fileObj.write(httpReq["body"])
                httpResponse = b"HTTP/1.1 201 Created\r\n\r\n"
        except Exception as e:
            pass
    else:
        pass
    return httpResponse

def handle_req_from_client(conn):
    data: str = conn.recv(1024).decode()
    httpReq = parser(data)
    path: str = httpReq["path"]
    httpResponse = b"HTTP/1.1 404 Not Found\r\n\r\n"
    if httpReq["verb"] == "GET":
        httpResponse = handle_get_req(httpReq)
    elif httpReq["verb"] == "POST":
        httpResponse = handle_post_req(httpReq)
    else:
        pass
    conn.send(httpResponse)

def main():
    # You can use print statements as follows for debugging, they'll be visible when running tests.
    print("Logs from your program will appear here!")

    # Uncomment this to pass the first stage
    #
    server_socket = socket.create_server(("localhost", 4221), reuse_port=True)
    while True:
        conn, addr = server_socket.accept() # wait for client
        thread = Thread(target=handle_req_from_client, args=[conn])
        thread.start()


if __name__ == "__main__":
    main()
