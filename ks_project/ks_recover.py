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
        cur.execute("SELECT ts_id,project_id,project_url,error_msg,recover_trial FROM error_log WHERE ts_id = ? AND recover_trial = 1",(ts_id,))
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
        cur.execute("SELECT ts_id,project_id,project_url,error_msg,recover_trial FROM error_log WHERE ts_id = %s AND recover_trial = 1",(ts_id,))
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
            print "recover try ID: %d"%row[1]
            time.sleep(0.5)
        cur.close()
        con.close()
def check():
    ts_id = get_time_stamp()
    rv = False
    if SS.SQLITE_MYSQL == 'sqlite':
        con = sqlite3.connect(SS.DATABASE_NAME, timeout = SS.LOCK_TIMEOUT)
        cur = con.cursor()
        cur.execute("SELECT COUNT(*) FROM error_log WHERE ts_id = ? AND recover_trial = 1",(ts_id,))
        rows = cur.fetchall()
        if len(rows) > 0:
            if rows[0][0] > 0:
                rv = True
            else:
                rv = False
        cur.close()
        con.close()
    else:
        con = mysql.connector.connect(user=SS.USER,
                                              password=SS.PASSWORD,
                                              host=SS.HOST,
                                              database=SS.DATABASE,
                                              connection_timeout = SS.LOCK_TIMEOUT)
        cur = con.cursor()
        cur.execute("SELECT COUNT(*) FROM error_log WHERE ts_id = %s AND recover_trial = 1",(ts_id,))
        rows = cur.fetchall()
        if len(rows) > 0:
            if rows[0][0] > 0:
                rv = True
            else:
                rv = False
        cur.close()
        con.close()
    return rv
    
def main():
    recover_error()
    trial = SS.RECOVER_TRIAL
    if trial == 0:
        return
    cnt = 0
    while 1:
        if trial > 0:
            if cnt >= trial:
                break
        state = ""
        with open("temp_page_server_record.log") as f:
            state = f.read()
        if state == "sleep":
            if check():
                recover_error()
                cnt += 1
            else:
                break
        print "Waiting..."
        time.sleep(60)
if __name__ == "__main__":
    print "========================="
    print "       RECOVERY          "
    print "========================="
    main()
    print "         OK              "
    print "========================="