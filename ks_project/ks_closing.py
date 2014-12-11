from threading import Thread
from bs4 import BeautifulSoup as BS
import sys, sqlite3, Queue, time
import requests # $ pip install requests
import mysql.connector
import server_setting as SS

class KickstarterProjectClosing(Thread): # multithreading
    def __init__(self,inque):
        Thread.__init__(self)
        self.inque = inque
        self.running = True
    def stop(self):
        self.running = False
    def run(self):
        inque = self.inque
        while self.running:
            try:
                project_url,project_id = inque.get(block=True,timeout=1)
                new_state,fp,bc = self.check_state(project_url)
                sys.stdout.write(".[%d = %s,%f,%d]."%(project_id,new_state,fp,bc))
                sys.stdout.flush()
                if new_state != "live":
                    self.update_db(project_id,new_state,fp,bc)
                inque.task_done()
            except Queue.Empty:
                pass
    def check_state(self,project_url):
        while 1:
            trial = 5
            headers = { 'User-Agent' : 'Mozilla/5.0 (X11; U; Linux i686) Gecko/20071127 Firefox/2.0.0.11',
                             'connection' : 'close',
                             'charset' : 'utf-8'}         
            while 1:
                try:
                    r = requests.get(project_url,headers=headers)
                    break
                except:
                    trial -= 1
                    if trial < 0:
                        return "error"
                    else:
                        continue
            content = r.text
            r.close()
            soup = BS(content,'html.parser')
            eles = soup.select("div.NS_projects__funding_bar")
            if len(eles) > 0:
                t = eles[0].text.lower()
                if t.find('unsuccessful') >= 0:
                    new_state = "unsuccessful"
                elif t.find('successful') >= 0:
                    new_state = "successful"
                elif t.find('funded') >= 0:
                    new_state = "successful"
                elif t.find('canceled') >= 0:
                    new_state = "canceled"
                elif t.find('failed') >= 0:
                    new_state = "failed"
                elif t.find('suspended') >= 0:
                    new_state = "suspended"
            else:
                new_state = "live"
            eles = soup.select("div#pledged")
            if len(eles) == 0:
                continue
            fp = float(eles[0]['data-pledged'])
            eles = soup.select("div#backers_count")
            if len(eles) == 0:
                continue
            bc = int(eles[0]['data-backers-count'])
            break
        return (new_state,fp,bc)
    def update_db(self,project_id,new_state,fp,bc):
        if SS.SQLITE_MYSQL == "sqlite":
            con = sqlite3.connect(SS.DATABASE_NAME,timeout = SS.LOCK_TIMEOUT)
            sql  = "UPDATE project_benchmark SET state = ?, pledged = ?, backers = ?, currently = ? WHERE project_id = ?"
            cur = con.cursor()
            cur.execute(sql,(new_state,fp,bc,0,project_id,))
            con.commit()
            cur.close()
            con.close()
        else:
            con = mysql.connector.connect(user=SS.USER,
                                password=SS.PASSWORD,
                                host=SS.HOST,
                                database=SS.DATABASE,
                                connection_timeout=SS.LOCK_TIMEOUT)
            sql = "UPDATE project_benchmark SET state = %s, pledged = %s, backers = %s, currently = %s WHERE project_id = %s"
            cur = con.cursor()
            cur.execute(sql,(new_state,fp,bc, 0, project_id,))
            con.commit()
            cur.close()
            con.close()
def do_close(nthread = 10):
    now_ts = time.localtime()
    today = "%04d-%02d-%02d 99:99"%(now_ts.tm_year,now_ts.tm_mon,now_ts.tm_mday,)     
    print "START"
    inque = Queue.Queue()
    if SS.SQLITE_MYSQL == "sqlite":
        sql = "SELECT project_url,project_id FROM project_benchmark WHERE currently = 1 AND deadline_str <= ?"
        con = sqlite3.connect(SS.DATABASE_NAME,timeout = SS.LOCK_TIMEOUT)
        cur = con.cursor()
        cur.execute(sql,(today,))
        rows = cur.fetchall()
        for row in rows:
            inque.put((row[0],row[1]))
        cur.close()
        con.close()
    else:
        con = mysql.connector.connect(user=SS.USER,
                        password=SS.PASSWORD,
                        host=SS.HOST,
                        database=SS.DATABASE,
                        connection_timeout=SS.LOCK_TIMEOUT)
        sql = "SELECT project_url,project_id FROM project_benchmark WHERE currently = 1 AND deadline_str <= %s"
        cur = con.cursor()
        cur.execute(sql,(today,))
        rows = cur.fetchall()
        for row in rows:
            inque.put((row[0],row[1]))
        cur.close()
        con.close()
    if inque.qsize() > 0:
        tasks = []
        for i in range(nthread):
            task = KickstarterProjectClosing(inque)
            task.setDaemon(True)
            task.start()
            tasks.append(task)
        inque.join()
        for task in tasks:
            task.stop()
    print "END"
if __name__ == "__main__":
    do_close()