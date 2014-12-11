import sys,socket,sqlite3,time
from datetime import datetime
import server_setting as SS
import mysql.connector
def call_log():
    host = socket.gethostname() # local computer
    sys.stdout.write("KICKSTARTER PROJECT LOG =======\n")
    sys.stdout.write("[%s]\n"%datetime.now().__str__())
    sys.stdout.flush()
    for category_id in SS.CATEGORIES:
        client = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        client.connect((host,SS.PROJECT_LOG_PORT))
        client.send(category_id)
        client.shutdown(socket.SHUT_RDWR) #disconnet
        client.close() #stream socket out
    sys.stdout.write("PROJECT LOG SERVER CALL COMPLETE\n\n")
    sys.stdout.flush()
    
if __name__ == "__main__":
    call_log()
    #call_page()
