'''
KICKSTARTER PAGE DATA COLLECTION
AUTHOR: DRTAGKIM
2014
'''
# SETTING =====



# IMPORT MODULES =====
from datetime import datetime
from threading import Thread

import re, sys, time, sqlite3, socket, os
import requests # $ pip install requests

class KickstarterProjectCollectorJson(Thread): # multithreading
    def __init__(self,category_id,politeness = 60):
        Thread.__init__(self)
        self.url="https://www.kickstarter.com/discover/advanced"
        self.category_id = category_id
        self.rv_static = []
        self.rv_dynamic = []
        self.politeness = politeness
        self.running = True
    def read(self,page):
        parameters = {
            "category_id":str(self.category_id),
            "sort":"end_date",
            "format":"json",
            "page":str(page)}
        trial = 10
        while 1:
            try:
                r = requests.get(self.url,params=parameters)
                break
            except:
                time.sleep(self.politeness)
                trial -= 1
                if trial < 0:
                    assert False,"No connection"
        rv  = r.json()
        r.close()
        return rv
    def scrap(self,full=False,time_lag = -1):
        """
|  Main
|  To collect everything, set full as True otherwise False
|  Set time lag for concurrent monitoring (default: yesterday)
        """
        politeness = self.politeness
        rv_static_append = self.rv_static.append
        rv_dynamic_append = self.rv_dynamic.append
        page = 1
        hit = 0
        hit_temp = 0
        breaker = False
        #timestamp doday
        now_ts = time.localtime()
        ts_id = "%04d/%02d/%02d"%(now_ts.tm_year,now_ts.tm_mon,now_ts.tm_mday,) 
        ts_comp = datetime.fromtimestamp(time.mktime(now_ts))
        tick = 0
        while 1:
            data = self.read(page)
            if data == "-1":
                print self.url
                print "Bad Connection"
                assert False,""
            self.total_num = data["total_hits"]
            projects = data["projects"]
            if len(projects) <=0:
                break
            else:
                page += 1 #pagination
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
                currently = ((deadline_comp - ts_comp).days < time_lag ) # including yesterday...
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
                if not full:
                    if not currently:
                        breaker = True
                        break
                rv_static_append([project_id,project_name,project_slug,country,created_at_unix,created_at_str,
                        project_url,desc,photo,category_parent,category_name,category_id,launched_at_unix,launched_at_str,
                        goal,currency,backers,pledged,state,currently,state_changed_unix,
                        state_changed_str,deadline_unix,deadline_str,creator_id,creator_url_slug,
                        creator_name,creator_url_api,creator_url_web,location_country,
                        location_name,location_slug,location_nearby_api,location_nearby_web1,location_nearby_web2,])
                rv_dynamic_append([ts_id,project_id,backers,pledged,state,currently,
                                   state_changed_unix,state_changed_str,deadline_unix,deadline_str,
                                   ])
                tick += 1
                sys.stdout.write("\r[%06d/%06d]"%(tick,self.total_num))
                sys.stdout.flush()                  
            if breaker:
                break

            #time.sleep(politeness)
    def export_sqlite(self,db_name):
        """
|  TEST
        """
        con = sqlite3.connect(db_name)
        #create schema
        sql_create_staic = """
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
                CONSTRAINT update_rule UNIQUE(project_id) ON CONFLICT REPLACE);
        """
        sql_create_dynamic = """
            CREATE TABLE IF NOT EXISTS project_history (
                ts_id TEXT,
                project_id NUMBER,
                backers NUMBER,
                pledged NUMBER,
                state NUMBER,
                currently NUMBER,
                state_changed_unix NUMBER,
                state_changed_str TEXT,
                deadline_unix NUMBER,
                deadline_str TEXT,
                CONSTRAINT update_rule UNIQUE(ts_id,project_id) ON CONFLICT REPLACE);
        """
        sql_insert_static = """
            INSERT INTO project_benchmark (
            project_id,project_name,project_slug,country,created_at_unix,created_at_str,
                        project_url,desc,photo,category_parent,category_name,category_id,launched_at_unix,launched_at_str,
                        goal,currency,backers,pledged,state,currently,state_changed_unix,
                        state_changed_str,deadline_unix,deadline_str,creator_id,creator_url_slug,
                        creator_name,creator_url_api,creator_url_web,location_country,
                        location_name,location_slug,location_nearby_api,location_nearby_web1,location_nearby_web2
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?);
        """
        sql_insert_dynamic = """
            INSERT INTO project_history (
                ts_id,project_id,backers,pledged,state,currently,
                state_changed_unix,state_changed_str,deadline_unix,deadline_str
            ) VALUES (?,?,?,?,?,?,?,?,?,?);
        """
        cur = con.cursor()
        cur.execute(sql_create_staic)
        con.commit()
        cur.execute(sql_create_dynamic)
        con.commit()
        cur.executemany(sql_insert_static,self.rv_static)
        con.commit()
        cur.executemany(sql_insert_dynamic,self.rv_dynamic)
        con.commit()
        cur.close()
        con.close()
        def stop(self):
            self.running = False
        def run(self):
            pass
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
    
if __name__ == "__main__":
    category_id = -1
    while 1:
        category = raw_input("Art=1\nComics=2\nDance=3\nDesign=4\nFashion=5\nFilm=6\nFood=7\nGames=8\nMusic=9\nPhoto=10\nPublishing=11\nTechnology=12\nTheater=13\n>")
        if category == "1":
            category_id = KICKSTARTER.CATEGORY_ART
            break
        elif category == "2":
            category_id = KICKSTARTER.CATEGORY_COMICS
            break
        elif category == "3":
            category_id = KICKSTARTER.CATEGORY_DANCE
            break
        elif category == "4":
            category_id = KICKSTARTER.CATEGORY_DESIGN
            break
        elif category == "5":
            category_id = KICKSTARTER.CATEGORY_FASHION
            break
        elif category == "6":
            category_id = KICKSTARTER.CATEGORY_FILM
            break
        elif category == "7":
            category_id = KICKSTARTER.CATEGORY_FOOD
            break
        elif category == "8":
            category_id = KICKSTARTER.CATEGORY_GAMES
            break
        elif category == "9":
            category_id = KICKSTARTER.CATEGORY_MUSIC
            break
        elif category == "10":
            category_id = KICKSTARTER.CATEGORY_PHOTOGRAPHY
            break
        elif category == "11":
            category_id = KICKSTARTER.CATEGORY_PUBLISHING
            break
        elif category == "12":
            category_id = KICKSTARTER.CATEGORY_TECHNOLOGY
            break
        elif category == "13":
            category_id = KICKSTARTER.CATEGORY_THEATER
            break
        else:
            print "Input again!"
    rule = raw_input("Which data do you want to collect: all data (=yes) or current projects (=no)?\n(yes/no)>")
    if rule.lower() == "yes":
        full = True
    else:
        full = False
    database = raw_input("Database location\n>")
    kpcj = KickstarterProjectCollectorJson(category_id)
    kpcj.scrap(full = full)
    kpcj.export_sqlite(database)
    print "Bye"
