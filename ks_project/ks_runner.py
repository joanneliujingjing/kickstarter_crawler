'''
KICKSTARTER SCHEDULER
AUTHOR: DRTAGKIM
2014
'''
from apscheduler.scheduler import Scheduler
# sudo pip install apscheduler
from datetime import datetime
import sys,socket,sqlite3, logging, time
import mysql.connector
import server_setting as SS
import ks_recover

logging.basicConfig()

def call_log():
    host = socket.gethostname() # local computer
    sys.stdout.write(host+"\n")
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
def call_page():
    host = socket.gethostname()
    sys.stdout.write("KICKSTARTER PAGE LOG =======\n")
    sys.stdout.write("[%s]\n"%datetime.now().__str__())
    sys.stdout.flush()    
    #
    sql_read_project_search = """
        SELECT ts_id,project_id,project_url FROM project_search_temp
    """
    if SS.SQLITE_MYSQL == 'sqlite':
        con = sqlite3.connect(SS.DATABASE_NAME, timeout = SS.LOCK_TIMEOUT)
        cur = con.cursor()
        cur.execute(sql_read_project_search)
        rows = cur.fetchall()
        for k,row in enumerate(rows):
            client = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
            client.connect((host,SS.PROJECT_PAGE_PORT))
            client.send(repr(row))
            client.shutdown(socket.SHUT_RDWR) #disconnet
            client.close() #stream socket out
            sys.stdout.write(".%d."%k)
            sys.stdout.flush()
            time.sleep(0.5)
    else:
        con = mysql.connector.connect(user=SS.USER,
                                      password=SS.PASSWORD,
                                      host=SS.HOST,
                                      database=SS.DATABASE,
                                      connection_timeout = SS.LOCK_TIMEOUT)
        cur = con.cursor()
        cur.execute(sql_read_project_search)
        rows = cur.fetchall()
        for k,row in enumerate(rows):
            client = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
            client.connect((host,SS.PROJECT_PAGE_PORT))
            client.send(repr(row))
            client.shutdown(socket.SHUT_RDWR) #disconnet
            client.close() #stream socket out
            print k
            time.sleep(0.1)
    sys.stdout.write("\n\nKICKSTARTER PAGE CALL COMPLETE ====\n")
    sys.stdout.flush()
def vacuum_database():
    if SS.SQLITE_MYSQL == 'sqlite':
        con = sqlite3.connect(SS.DATABASE_NAME, timeout = SS.LOCK_TIMEOUT)
        cur = con.cursor()
        cur.execute("DELETE FROM project_search_temp")
        con.commit()
        cur.execute("VACUUM")
        con.commit()
        cur.close()
        con.close()
    else:
        con = mysql.connector.connect(user=SS.USER,
                                              password=SS.PASSWORD,
                                              host=SS.HOST,
                                              database=SS.DATABASE,
                                              connection_timeout = SS.LOCK_TIMEOUT)
        cur = con.cursor()
        cur.execute("TRUNCATE TABLE project_search_temp")
        con.commit()
        cur.close()
        con.close()
        sys.stdout.write("\n\nTEMP CLEAN UP COMPLETE ====\n")
def get_time_stamp():
    now_ts = time.localtime()
    ts_id = "%04d/%02d/%02d"%(now_ts.tm_year,now_ts.tm_mon,now_ts.tm_mday,) 
    return ts_id

def recover_error():
    ks_recover.main()

if __name__ == "__main__":
    sched = Scheduler()
    sched.start()
    # project_log
    sched.add_cron_job(call_log,
                       month = '1-12',
                       day = '1-31',
                       hour = SS.PROJECT_LOG_START_HOUR,
                       minute = SS.PROJECT_LOG_START_MIN,
                       second = SS.PROJECT_LOG_START_SEC)
    sched.add_cron_job(call_page,
                       month = '1-12',
                       day = '1-31',
                       hour = SS.PROJECT_PAGE_START_HOUR,
                       minute = SS.PROJECT_PAGE_START_MIN,
                       second = SS.PROJECT_PAGE_START_SEC)
    sched.add_cron_job(vacuum_database,
                       month = '1-12',
                       day = '1-31',
                       hour = SS.VACUUM_DATABASE_HOUR,
                       minute = SS.VACUUM_DATABASE_MIN,
                       second = SS.VACUUM_DATABASE_SEC)
    sched.add_cron_job(recover_error,
                       month = '1-12',
                       day = '1-31',
                       hour = SS.RECOVER_ERROR_HOUR,
                       minute = SS.RECOVER_ERROR_MIN,
                       second = SS.RECOVER_ERROR_SEC)
    while 1:
        try:
            pass
        except KeyboardInterrupt:
            sched.shutdown()
            break
# END OF PROGRAM ==================