# sudo pip install apscheduler
import sys,sqlite3
import mysql.connector
import server_setting as SS

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
        sys.stdout.write("\n\nSQLITE VACUUM COMPLETE ====\n")
        
if __name__ == "__main__":
    vacuum_database()