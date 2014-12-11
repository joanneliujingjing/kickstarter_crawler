'''
KICKSTARTER PROJECT LOG COLLECTION
AUTHOR: DRTAGKIM
2014
'''
# IMPORT MODULES =====
from datetime import datetime
from threading import Thread, current_thread

import re, sys, time, sqlite3, socket, os, Queue
import requests # $ pip install requests
import mysql.connector
import server_setting as SS

class KickstarterProjectCollectorJson(Thread): # multithreading
    def __init__(self, my_id, inque, politeness = 10):
        Thread.__init__(self)
        self.url="https://www.kickstarter.com/discover/advanced"
        self.inque = inque
        self.my_id = my_id
        self.rv_static = []
        self.rv_dynamic = []
        self.rv_search_temp = []
        self.politeness = politeness
        self.running = True
        self.tname = current_thread().name #current thread name
    def read(self, category_id, page):
        headers = { 'User-Agent' : 'Mozilla/5.0 (X11; U; Linux i686) Gecko/20071127 Firefox/2.0.0.11',
                         'connection' : 'close',
                         'charset' : 'utf-8'}        
        parameters = {
            "category_id":str(category_id),
            "sort":"end_date",
            "format":"json",
            "page":str(page)}
        trial = SS.PAGE_REQUEST_TRIAL
        fatal_error = 0
        rv = ""
        while 1:
            try:
                r = requests.get(self.url,params=parameters,headers=headers)
                rv  = r.json()
                r.close()
                break
            except:
                sys.stdout.write(".?.")
                sys.stdout.flush()
                time.sleep(self.politeness)
                trial -= 1
                if trial < 0:
                    if fatal_error > 10:
                        sys.stdout.write("Network failure!\n")
                        sys.stdout.flush()
                        sys.exit(0)
                    trial = SS.PAGE_REQUEST_TRIAL # reset
                    fatal_error += 1
                    time.sleep(self.politeness * 10) # for ten minutes break
        assert len(rv) > 0, ""
        return rv
    def stop(self):
        self.running = False
    def scrap(self, category_id_input, time_lag = -2):
        """
|  Main
|  To collect everything, set full as True otherwise False
|  Set time lag for concurrent monitoring (default: yesterday)
        """
        # REFERENCE
        politeness = self.politeness
        rv_static_append = self.rv_static.append
        rv_dynamic_append = self.rv_dynamic.append
        rv_search_temp_append = self.rv_search_temp.append
        # CONTROL
        page = 1
        hit = 0
        hit_temp = 0
        breaker = False
        tick = 0
        #timestamp doday
        now_ts = time.localtime()
        ts_id = "%04d/%02d/%02d"%(now_ts.tm_year,now_ts.tm_mon,now_ts.tm_mday,) 
        ts_comp = datetime.fromtimestamp(time.mktime(now_ts))
        self.total_num = -1
        while 1:
            data = self.read(category_id_input, page)
            if data == "-1":
                print self.url
                print "Bad Connection"
                assert False,""
            if self.total_num < 0:
                self.total_num = data["total_hits"]
            projects = data["projects"]
            if len(projects) <=0:
                break
            else:
                page += 1 #pagination
            not_live_set = 0
            compare_set = len(projects)
            for project in projects:
                # ABOUT PROJECT
                project_id = project['id']
                project_name = project['name']
                try:
                    project_slug = project['slug']
                except KeyError:
                    project_slug = ""
                country = project['country']
                created_at_unix = project['created_at']
                created_at_str = (datetime.fromtimestamp(created_at_unix)).strftime("%Y-%m-%d %H:%M")
                project_url = project['urls']['web']['project']
                desc = re.sub(r"\n\n+"," ",(project['blurb']))
                photo = project['photo']['1024x768']
                category_name = project['category']['name']
                category_id = project['category']['id']
                try:
                    category_parent = project['category']['parent_id']
                except KeyError:
                    category_parent = -1
                launched_at_unix = project['launched_at']
                launched_at_str = (datetime.fromtimestamp(launched_at_unix)).strftime("%Y-%m-%d %H:%M")
                # ABOUT PERFORMANCE
                goal = project['goal']
                currency = project['currency']
                backers = project['backers_count']
                pledged = project['pledged']
                state = project['state'] # u'live'
                # ABOUT DEADLINE
                state_changed_unix = project['state_changed_at']
                state_changed_str = (datetime.fromtimestamp(state_changed_unix)).strftime("%Y-%m-%d %H:%M")
                deadline_unix = project['deadline']
                deadline_str = (datetime.fromtimestamp(deadline_unix)).strftime("%Y-%m-%d %H:%M")
                deadline_comp = datetime.fromtimestamp(deadline_unix) 
                currently = 1
                # ABOUT CREATOR
                creator = project['creator']
                creator_id = creator['id']
                try:
                    creator_url_slug = creator['slug']
                except KeyError:
                    creator_url_slug = ""
                creator_name = creator['name']
                creator_url_api = creator['urls']['api']['user']
                creator_url_web = creator['urls']['web']['user']
                # ABOUT NEARBY PROJECTS
                try:
                    location = project['location']
                    location_country = location['country']
                    location_name = location['displayable_name']
                    try:
                        location_slug = location['slug']
                    except KeyError:
                        location_slug = ""
                    try:
                        location_nearby_api = location['urls']['api']['nearby_projects']
                        location_nearby_web1 = location['urls']['web']['discover']
                        location_nearby_web2 = location['urls']['web']['location']
                    except KeyError:
                        location_nearby_api = ""
                        location_nearby_web1 = ""
                        location_nearby_web2 = ""
                except KeyError:
                    location_country =""
                    location_name = ""
                    location_slug = ""
                    location_nearby_api = ""
                    location_nearby_web1 = ""
                    location_nearby_web2 = ""
                #
                if not SS.SCRAP_FULL:
                    if state != 'live':
                        not_live_set += 1
                        continue
                rv_static_append([project_id,project_name,project_slug,country,created_at_unix,created_at_str,
                        project_url,desc,photo,category_parent,category_name,category_id,launched_at_unix,launched_at_str,
                        goal,currency,backers,pledged,state,currently,state_changed_unix,
                        state_changed_str,deadline_unix,deadline_str,creator_id,creator_url_slug,
                        creator_name,creator_url_api,creator_url_web,location_country,
                        location_name,location_slug,location_nearby_api,location_nearby_web1,location_nearby_web2,])
                rv_dynamic_append([ts_id,project_id,backers,pledged,state,
                                   state_changed_unix,state_changed_str,deadline_unix,deadline_str,
                                   ])
                rv_search_temp_append([ts_id,project_id,project_url])
                tick += 1
            if not_live_set >= compare_set:
                break
            if SS.QUIETLY:
                sys.stdout.write(".")
                sys.stdout.flush()
            else:
                sys.stdout.write(".[%03d:%06d/%06d]."%(self.my_id,tick,self.total_num))
                sys.stdout.flush()                  
    def export_mysql(self):
        sql_create_static = """
        CREATE TABLE IF NOT EXISTS `project_benchmark` (
            `project_id` int(11) NOT NULL,
            `project_name` varchar(1000) DEFAULT NULL,
            `project_slug` varchar(400) DEFAULT NULL,
            `country` varchar(100) DEFAULT NULL,
            `created_at_unix` int(11) DEFAULT NULL,
            `created_at_str` varchar(100) DEFAULT NULL,
            `project_url` varchar(1000) DEFAULT NULL,
            `desc_` mediumtext,
            `photo` varchar(2000) DEFAULT NULL,
            `category_parent` int(11) DEFAULT NULL,
            `category_name` varchar(255) DEFAULT NULL,
            `category_id` int(11) DEFAULT NULL,
            `launched_at_unix` int(11) DEFAULT NULL,
            `launched_at_str` varchar(100) DEFAULT NULL,
            `goal` float DEFAULT NULL,
            `currency` varchar(10) DEFAULT NULL,
            `backers` int(11) DEFAULT NULL,
            `pledged` float DEFAULT NULL,
            `state` varchar(50) DEFAULT NULL,
            `currently` int(11) DEFAULT NULL,
            `state_changed_unix` int(11) DEFAULT NULL,
            `state_changed_str` varchar(100) DEFAULT NULL,
            `deadline_unix` int(11) DEFAULT NULL,
            `deadline_str` varchar(100) DEFAULT NULL,
            `creator_id` int(11) DEFAULT NULL,
            `creator_url_slug` varchar(400) DEFAULT NULL,
            `creator_name` varchar(400) DEFAULT NULL,
            `creator_url_api` varchar(1000) DEFAULT NULL,
            `creator_url_web` varchar(1000) DEFAULT NULL,
            `location_country` varchar(200) DEFAULT NULL,
            `location_name` varchar(200) DEFAULT NULL,
            `location_slug` varchar(200) DEFAULT NULL,
            `location_nearby_api` varchar(1000) DEFAULT NULL,
            `location_nearby_web1` varchar(1000) DEFAULT NULL,
            `location_nearby_web2` varchar(1000) DEFAULT NULL,
            PRIMARY KEY (`project_id`)
          ) ENGINE=MyISAM DEFAULT CHARSET=utf8
          PARTITION BY KEY ()
          PARTITIONS 5
        """
        sql_create_dynamic = """
        CREATE TABLE IF NOT EXISTS project_history (
            `ts_id` VARCHAR(100),
            `project_id` INT,
            `backers` INT,
            `pledged` FLOAT,
            `state` TEXT,
            `state_changed_unix` INT,
            `state_changed_str` VARCHAR(100),
            `deadline_unix` INT,
            `deadline_str` VARCHAR(100),
            PRIMARY KEY(`ts_id`,`project_id`)
            ) ENGINE=MyISAM CHARSET=utf8
            PARTITION BY KEY ()
            PARTITIONS 10
        """
        sql_create_project_search = """
        CREATE TABLE IF NOT EXISTS project_search_temp (
            `ts_id` VARCHAR(100),
            `project_id` INT,
            `project_url` VARCHAR(1000),
            PRIMARY KEY(`ts_id`,`project_id`)
            ) ENGINE=MyISAM CHARSET=utf8
        """
        sql_insert_static = """
            REPLACE INTO project_benchmark (
            project_id,project_name,project_slug,country,created_at_unix,created_at_str,
                        project_url,`desc_`,photo,category_parent,category_name,category_id,launched_at_unix,launched_at_str,
                        goal,currency,backers,pledged,state,currently,state_changed_unix,
                        state_changed_str,deadline_unix,deadline_str,creator_id,creator_url_slug,
                        creator_name,creator_url_api,creator_url_web,location_country,
                        location_name,location_slug,location_nearby_api,location_nearby_web1,location_nearby_web2
            ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """
        sql_insert_dynamic = """
            INSERT IGNORE INTO project_history (
                ts_id,project_id,backers,pledged,state,
                state_changed_unix,state_changed_str,deadline_unix,deadline_str
            ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """
        sql_insert_project_search = """
            INSERT IGNORE INTO project_search_temp (
                ts_id, project_id, project_url
            ) VALUES (%s,%s,%s)
        """
        con = mysql.connector.connect(user=SS.USER,
                                      password=SS.PASSWORD,
                                      host=SS.HOST,
                                      database=SS.DATABASE,
                                      connection_timeout=SS.LOCK_TIMEOUT)
        cur = con.cursor()
        if SS.CREATE_SCHEMA:
            cur.execute(sql_create_static)
            con.commit()
            cur.execute(sql_create_dynamic)
            con.commit()
            cur.execute(sql_create_project_search)
            con.commit()
        try:
            cur.executemany(sql_insert_static,self.rv_static)
            con.commit()
            cur.executemany(sql_insert_dynamic,self.rv_dynamic)
            con.commit()
            cur.executemany(sql_insert_project_search,self.rv_search_temp)
            con.commit()
            cur.close()
            con.close()
        except:
            cur.close()
            con.close()
            sys.stdout.write("...MYSQL ERROR!...")
            sys.stdout.flush()
            self.running = False
    def export_sqlite(self):
        """
|  TEST
        """
        
        #create schema
        sql_create_static = """
            CREATE TABLE IF NOT EXISTS project_benchmark (project_id NUMBER,
                project_name TEXT,
                project_slug TEXT,
                country TEXT,
                created_at_unix NUMBER,
                created_at_str TEXT,
                project_url TEXT,
                desc TEXT,
                photo TEXT,
                category_parent NUMBER,
                category_name TEXT,
                category_id NUMBER,
                launched_at_unix NUMBER,
                launched_at_str TEXT,
                goal NUMBER,
                currency NUMBER,
                backers NUMBER,
                pledged NUMBER,
                state TEXT,
                currently NUMBER,
                state_changed_unix NUMBER,
                state_changed_str TEXT,
                deadline_unix NUMBER,
                deadline_str TEXT,
                creator_id NUMBER,
                creator_url_slug TEXT,
                creator_name TEXT,
                creator_url_api TEXT,
                creator_url_web TEXT,
                location_country TEXT,
                location_name TEXT,
                location_slug TEXT,
                location_nearby_api TEXT,
                location_nearby_web1 TEXT,
                location_nearby_web2 TEXT,
                CONSTRAINT update_rule UNIQUE(project_id) ON CONFLICT REPLACE)
        """
        sql_create_dynamic = """
            CREATE TABLE IF NOT EXISTS project_history (
                ts_id TEXT,
                project_id NUMBER,
                backers NUMBER,
                pledged NUMBER,
                state TEXT,
                state_changed_unix NUMBER,
                state_changed_str TEXT,
                deadline_unix NUMBER,
                deadline_str TEXT,
                CONSTRAINT update_rule UNIQUE(ts_id,project_id) ON CONFLICT IGNORE)
        """
        sql_create_project_search = """
            CREATE TABLE IF NOT EXISTS project_search_temp (
                ts_id TEXT,
                project_id NUMBER,
                project_url TEXT,
                CONSTRAINT update_rule UNIQUE(ts_id,project_id) ON CONFLICT IGNORE)
        """
        sql_insert_static = """
            INSERT INTO project_benchmark (
            project_id,project_name,project_slug,country,created_at_unix,created_at_str,
                        project_url,desc,photo,category_parent,category_name,category_id,launched_at_unix,launched_at_str,
                        goal,currency,backers,pledged,state,currently,state_changed_unix,
                        state_changed_str,deadline_unix,deadline_str,creator_id,creator_url_slug,
                        creator_name,creator_url_api,creator_url_web,location_country,
                        location_name,location_slug,location_nearby_api,location_nearby_web1,location_nearby_web2
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """
        sql_insert_dynamic = """
            INSERT INTO project_history (
                ts_id,project_id,backers,pledged,state,
                state_changed_unix,state_changed_str,deadline_unix,deadline_str
            ) VALUES (?,?,?,?,?,?,?,?,?)
        """
        sql_insert_project_search = """
            INSERT INTO project_search_temp (
                ts_id, project_id, project_url
            ) VALUES (?,?,?)
        """
        con = sqlite3.connect(SS.DATABASE_NAME,timeout = SS.LOCK_TIMEOUT)
        cur = con.cursor()
        if SS.CREATE_SCHEMA:
            cur.execute(sql_create_static)
            con.commit()
            cur.execute(sql_create_dynamic)
            con.commit()
            cur.execute(sql_create_project_search)
            con.commit()
        try:
            cur.executemany(sql_insert_static,self.rv_static)
            con.commit()
            cur.executemany(sql_insert_dynamic,self.rv_dynamic)
            con.commit()
            cur.executemany(sql_insert_project_search,self.rv_search_temp)
            con.commit()
            cur.close()
            con.close()
        except:
            cur.close()
            con.close()
            sys.stdout.write("...SQLITE ERROR!...")
            sys.stdout.flush()
            self.running = False
    def run(self):
        # REFERENCE
        inque = self.inque
        waiting_noticed = False
        while self.running:
            try:
                category_id = inque.get(block=True, timeout = 60)
                waiting_noticed = False
                sys.stdout.write("[%03d]>=="%self.my_id)
                sys.stdout.flush()
                self.scrap(category_id)
                if SS.SQLITE_MYSQL == "sqlite":
                    self.export_sqlite()
                else:
                    self.export_mysql()
                inque.task_done()
                sys.stdout.write("[%03d]==<"%self.my_id)
                sys.stdout.flush()
            except Queue.Empty:
                reload(SS)
                if not waiting_noticed:
                    sys.stdout.write(" (^.^) ")
                    sys.stdout.flush()
                    waiting_noticed = True
class KICKSTARTER:
    """
|  General string values for the Kickstarter site
    """
    MAIN = "https://www.kickstarter.com"
    CATEGORY_ART = 1
    CATEGORY_COMICS = 3
    CATEGORY_DANCE = 6
    CATEGORY_DESIGN = 7
    CATEGORY_FASHION = 9
    CATEGORY_FILM = 11
    CATEGORY_FOOD = 10
    CATEGORY_GAMES = 12
    CATEGORY_MUSIC = 14
    CATEGORY_PHOTOGRAPHY = 15
    CATEGORY_PUBLISHING = 18
    CATEGORY_TECHNOLOGY = 16
    CATEGORY_THEATER = 17
    CATEGORY_CRAFTS = 26
    CATEGORY_JOURNALISM = 13
    
if __name__ == "__main__":
    inque = Queue.Queue()
    workers = []
    for i in range(SS.PROJECT_LOG_SERVER_THREAD_POOL):
        worker = KickstarterProjectCollectorJson(i,inque)
        worker.setDaemon(True)
        workers.append(worker)
        worker.start()
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # TCP/IP
    server.bind(('',SS.PROJECT_LOG_PORT))
    server.listen(SS.PROJECT_LOG_SERVER_THREAD_POOL)
    sys.stdout.write("SERVER STARTS\n=============\n")
    sys.stdout.flush()
    category_id = -1
    while 1:
        try:
            conn,addr = server.accept()
            category = conn.recv(1024)
            if category.lower() == "off":
                conn.close()
                break
            sys.stdout.write(".[SERVER RECEIVE: %s]." % category)
            sys.stdout.flush()
            if category == "1":
                category_id = KICKSTARTER.CATEGORY_ART
            elif category == "2":
                category_id = KICKSTARTER.CATEGORY_COMICS
            elif category == "3":
                category_id = KICKSTARTER.CATEGORY_DANCE
            elif category == "4":
                category_id = KICKSTARTER.CATEGORY_DESIGN
            elif category == "5":
                category_id = KICKSTARTER.CATEGORY_FASHION
            elif category == "6":
                category_id = KICKSTARTER.CATEGORY_FILM
            elif category == "7":
                category_id = KICKSTARTER.CATEGORY_FOOD
            elif category == "8":
                category_id = KICKSTARTER.CATEGORY_GAMES
            elif category == "9":
                category_id = KICKSTARTER.CATEGORY_MUSIC
            elif category == "10":
                category_id = KICKSTARTER.CATEGORY_PHOTOGRAPHY
            elif category == "11":
                category_id = KICKSTARTER.CATEGORY_PUBLISHING
            elif category == "12":
                category_id = KICKSTARTER.CATEGORY_TECHNOLOGY
            elif category == "13":
                category_id = KICKSTARTER.CATEGORY_THEATER
            elif category == "14":
                category_id = KICKSTARTER.CATEGORY_CRAFTS
            elif category == "15":
                category_id = KICKSTARTER.CATEGORY_JOURNALISM 
            else:
                conn.close()
                continue
            inque.put(category_id)
            conn.close()
        except KeyboardInterrupt:
            sys.stdout.write("\n\nSERVER OUT.\nTHANK YOU.")
            sys.stdout.flush()
            break
        except socket.error, msg:
            sys.stdout.write(msg)
            sys.stdout.write("\n\nSocket Error.\n")
            sys.stdout.flush()
            break
    for worker in workers:
        worker.stop()
    server.close() # close server
    sys.stdout.write("SERVER STOPS\nBYE.\n")
    sys.stdout.flush()    
# END OF PROGRAM=======================
