import sys,sqlite3,time,socket
import mysql.connector
import server_setting as SS

def get_time_stamp():
    now_ts = time.localtime()
    ts_id = "%04d/%02d/%02d"%(now_ts.tm_year,now_ts.tm_mon,now_ts.tm_mday,) 
    return ts_id

def recover_error():
    host = socket.gethostname()
    ts_id = get_time_stamp()
    print "RECOVERY STARTS..."
    if SS.SQLITE_MYSQL == 'sqlite':
        con = sqlite3.connect(SS.DATABASE_NAME, timeout = SS.LOCK_TIMEOUT)
        cur = con.cursor()
        cur.execute("SELECT ts_id,project_id,project_url,error_msg,recover_trial FROM error_log WHERE ts_id = ?",(ts_id,))
        rows = cur.fetchall()
        for k,row in enumerate(rows):
            error_msg = row[3]
            recover_trial = row[4]
            if error_msg == "no page" or error_msg == "404":
                continue
            if recover_trial == 0: #recovered
                continue
            client = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
            client.connect((host,SS.PROJECT_PAGE_PORT))
            recover_data = [row[0],row[1],row[2]]
            client.send(repr(recover_data))
            client.shutdown(socket.SHUT_RDWR) #disconnet
            client.close() #stream socket out
            print "recover try ID: %d"%k
            time.sleep(0.5)
        cur.close()
        con.close()
    else:
        con = mysql.connector.connect(user=SS.USER,
                                              password=SS.PASSWORD,
                                              host=SS.HOST,
                                              database=SS.DATABASE,
                                              connection_timeout = SS.LOCK_TIMEOUT)
        cur = con.cursor()
        cur.execute("SELECT ts_id,project_id,project_url,error_msg,recover_trial FROM error_log WHERE ts_id = %s",(ts_id,))
        rows = cur.fetchall()
        for k,row in enumerate(rows):
            error_msg = row[3]
            recover_trial = row[4]
            if error_msg == "no page" or error_msg == "404":
                continue
            if recover_trial == 0: #recovered
                continue
            client = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
            client.connect((host,SS.PROJECT_PAGE_PORT))
            recover_data = [row[0],row[1],row[2]]
            client.send(repr(recover_data))
            client.shutdown(socket.SHUT_RDWR) #disconnet
            client.close() #stream socket out
            print "recover try ID: %d"%k
            time.sleep(0.5)
        cur.close()
        con.close()
if __name__ == "__main__":
    recover_error()