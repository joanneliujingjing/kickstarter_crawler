import sys,socket,sqlite3
import server_setting as SS
def stop():
    host = socket.gethostname()
    client = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    client.connect((host,SS.PROJECT_PAGE_PORT))
    client.send(repr('off'))
    client.shutdown(socket.SHUT_RDWR) #disconnet
    client.close() #stream socket out
if __name__ == "__main__":
    stop()
    