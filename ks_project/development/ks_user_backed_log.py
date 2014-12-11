import sqlite3,sys,time
from threading import Thread, active_count
import requests
import Queue
from bs4 import BeautifulSoup as BS
import re

class KickstarterBackerDataCollectionAgent(Thread):
    def __init__(self,inque,dbname):
        Thread.__init__(self)
        self.dbname = dbname
        self.inque = inque
        #self.outque = outque
        self.running = True
    def stop(self):
        self.running = False
    def read(self,url,page):
        if url.endswith("/"):
            url = "%sbacked.js"%url
        else:
            url = "%s/backed.js"%url
        parameters = {"page":str(page)}
        trial = 10
        while 1:
            try:
                r = requests.get(url,params = parameters)
                break
            except:
                time.sleep(self.politeness)
                trial -= 1
                if trial < 0:
                    assert False, "No connection"
        rv = r.text
        r.close()
        return rv
    def bio(self,url):
        trial  =10
        while 1:
            try:
                r = requests.get(url)
                break
            except:
                time.sleep(self.politeness)
                trial -= 1
                if trial < 0:
                    assert False, "No connection"
        rv = r.text
        r.close()
        s = BS(rv,'html.parser')
        bio_f = s.select("#profile_bio")
        if len(bio_f) > 0:
            profile = bio_f[0]
            name = re.sub(r"\n","",profile('h2').text).strip()
            try:
                celes = profile.select(".creator_tag")
                if len(celes) > 0:
                    if len(celes[0].text) > 0:
                        creator = True
                    else:
                        creator = False
                else:
                    creator = False
            except:
                creator = False
            if len(profile.select(".backed")) > 0:
                try:
                    bt = re.findall(r"[0-9,]",profile.select(".backed")[0].text)[0]
                    bt = int(bt.replace(",",""))
                except:
                    bt = 0
            else:
                bt = 0
            if len(profile.select(".location")) > 0:
                try:
                    location = re.sub(r"\n+","",profile.select(".location")[0].text)
                except:
                    location = ""
            else:
                location = ""
            joined_eles = profile.select(".joined time")
            if len(joined_eles) > 0:
                try:
                    joined = joined_eles[0]['datetime']
                except:
                    joined = ""
            else:
                joined = ""
        else:
            name = ""
            creator = False
            bt = 0
            location = ""
            joined = ""
        return (name,creator,bt,location,joined)
    def scrap(self,url):
        #backed
        rv = []
        page = 1
        rv_append = rv.append
        while 1:
            print page
            data = self.read(url,page)
            soup = BS(data,'html.parser')
            projects = soup.select(".project-card-interior")
            if len(projects) <= 0:
                break
            else:
                page += 1
            for project in projects:
                title_bin = project.select('.project-title')
                link = project('a')[0]
                title = link.text
                href = link['href']
                items = project.select('li')
                
                items_text = [re.sub(r"\n+","",item.text) for item in items]
                try:
                    col1 = items_text[0]
                except:
                    col1 = ""
                try:
                    col2 = items_text[1]
                except:
                    col2 = ""
                try:
                    col3 = re.sub(r"[a-zA-Z,%]","",items_text[2]).strip()
                except:
                    col3 = ""
                try:
                    col4 = re.findall(r"[0-9,]+",items_text[3])[0].strip()
                except:
                    col4 = ""
                try:
                    col5 = re.findall(r"[0-9,]+",items_text[4])[0].strip()
                except:
                    col5 = ""
                rv_append([title,href,col1,col2,col3,col4,col5])
                #title,url,category,location,funded(%),pledged,num_backers
        return rv
    def run(self):
        inque = self.inque
        #outque = self.outque
        while self.running:
            try:
                (user_slug,url) = inque.get(block=True,timeout=1)
                rv = self.scrap(url)
                rv.insert(0,user_slug)
                bio_data = self.bio(url)
                bio_data.insert(0,user_slug)
                #update
                db = UserProjectBackSqlite(self.dbname,url)
                db.insert_data((bio_data,rv,))
                inque.task_done()
            except Queue.Empty:
                pass
class UserProjectBackSqlite:
    def __init__(self,dbname,url):
        self.create_db()
        self.url = url
    def create_db(self):
        con = sqlite3.connect(dbname)
        cur = con.cursor()
        sql_rv = """
            CREATE TABLE IF NOT EXISTS user_backed (
                ts_id TEXT,
                user_slug TEXT,
                user_url TEXT,
                project_title TEXT,
                project_address TEXT,
                project_category TEXT,
                project_location TEXT,
                project_funded TEXT,
                project_pledged TEXT,
                number_backers TEXT,
                CONSTRAINT update_rule UNIQUE(ts_id,user_slug,project_address) ON CONFLICT IGNORE
            );
        """
        sql_bio_benchmark = """
            CREATE TABLE IF NOT EXISTS user_bio_benchmark (
                user_slug TEXT,
                user_url TEXT,
                user_name TEXT,
                user_backed NUMBER,
                user_location TEXT,
                user_joined TEXT,
                CONSTRAINT update_rule UNIQUE(user_slug) ON CONFLICT REPLACE
            );
        """
        sql_bio_history = """
            CREATE TABLE IF NOT EXISTS user_bio_history (
                ts_id TEXT,
                user_slug TEXT,
                user_backed NUMBER,
                creator NUMBER,
                CONSTRAINT update_rule UNIQUE(ts_id,user_slug) ON CONFLICT IGNORE
            );
        """
        cur.execute(sql_rv)
        con.commit()
        cur.execute(sql_bio_benchmark)
        con.commit()
        cur.execute(sql_bio_history)
        con.commit()
        cur.close()
        con.close()
    def insert_data(self,data):
        now_ts = time.localtime()
        ts_id = "%04d/%02d/%02d"%(now_ts.tm_year,now_ts.tm_mon,now_ts.tm_mday,) 
        con = sqlite3.connect(dbname)
        cur = con.cursor()
        sql_rv = """
            INSERT INTO user_backed (ts_id,user_slug,user_url,project_title,project_address,project_category,
            project_location,project_funded,project_pledged,number_backers) VALUES (?,?,?,?,?,?,?,?,?,?);
        """
        sql_bio_bench ="""
            INSERT INTO user_bio_benchmark (user_slug,user_url,user_name,user_backed,user_location,user_joined)
            VALUES (?,?,?,?,?,?)
            )
        """
        sql_bio_hist = """
            INSERT INTO user_bio_history (ts_id,user_slug,user_backed,creator) VALUES (?,?,?,?);
        """
        cur.executemany(sql_rv,data[1])
        con.commit()
        cur.execute(sql_bio_bench,(data[0][0],self.url,data[0][1],data[0][3],data[0][4],data[0][5]))
        con.commit()
        cur.execute(sql_bio_hist,(ts_id,data[0][0],data[0][3],data[0][2]))
        con.commit()
        cur.close()
        con.close()

class KickstarterBackerDataCollection:
    def __init__(self,input_data):
        self.input_data = input_data
        # ([user_slug,url],[user_slug,url],[...]...)
    def run(self, dbname, number_agent = 50):
        inque = list_to_queue(self.input_data)
        outque = Queue.Queue()
        agents = []
        for i in range(number_agent):
            agent = KickstarterBackerDataCollectionAgent(inque,outque)
            agent.setDaemon(True)
            agents.append(agent)
            agent.start()
        inque.join()
        for agent in agents:
            agent.stop()
        
def list_to_queue(list_data):
    """
List to Queue
    """
    queue = Queue.Queue()
    map(lambda x : queue.put(x), list_data)
    return queue

def queue_to_list(queue_data):
    """
Queue to list
    """
    list_data = []
    while True:
        try:
            list_data.append(queue_data.get_nowait())
        except:
            break
    return list_data

