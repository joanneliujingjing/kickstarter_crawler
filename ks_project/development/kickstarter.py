'''
Author: Taekyung Kim 2014
Contact: masan.korea@gmail.com
'''
# -- Web --
from web3 import PhantomBrowser as PB
from web3 import WebReader2 as WR
from web3 import list_to_queue, queue_to_list
from bs4 import BeautifulSoup as BS
# -- System --
import time,sys,re,math,re,csv,zlib
from datetime import datetime
# -- Multithreading --
from threading import Thread, active_count
import Queue,re
# -- Web, Imaging --
from PIL import Image
from StringIO import StringIO
from hsaudiotag import mp4
import requests #Apache requests
import os, glob, shutil, cPickle, sqlite3, zlib
import numpy as NP
# PROGRAM STARTS ===========

# global functions
def time_stamp():
    now = time.localtime()
    return "%04d_%02d_%02d_%02d_%02d" % (now.tm_year,now.tm_mon,now.tm_mday,now.tm_hour,now.tm_min)
def save_image_to_file(image_data,fname):
    """
>>> for i,k in enumerate(kpa.images):
    fname = "d:/%d.jpg"%i
    KS.save_image_to_file(k,fname)
    
    """
    if fname.endswith('.jpg'):
        fname = "%s.jpg"%fname
    i = Image.open(StringIO(image_data))
    i.save(fname)
def get_video_duration(url,buff=2000):
    r = requests.get(url,stream=True)
    a = r.raw.read(buff)
    b = StringIO()
    b.write(a)
    c = mp4.File(b)
    duration = c.duration
    b.close()
    r.close()
    return duration
def filter_number(money):
    money_exps = re.findall(r'([0-9,]+)',money)
    rv = 0.0
    if len(money_exps) > 0:
        money_exp = money_exps[0].replace(",","")
        rv = float(money_exp)
    return rv
class ImageDownloader(Thread):
    def __init__(self,inque,outque,quietly = True,has_image = True):
        Thread.__init__(self)
        self.inque = inque
        self.outque = outque
        self.running = True
        self.quietly = quietly
        self.has_image = has_image
    def stop(self):
        self.running = False
    def run(self):
        inque = self.inque
        outque = self.outque
        while self.running:
            try:
                src = inque.get(block=True,timeout=1)
                if self.has_image:
                    r = requests.get(src)
                    if r.status_code == 200:
                        c = r.content
                        outque.put([c,src])
                    if not self.quietly:
                        sys.stdout.write("i")
                        sys.stdout.flush()
                else:
                    if not self.quietly:
                        sys.stdout.write("o")
                        sys.stdout.flush()
                    outque.put(['',src])
                inque.task_done()
            except Queue.Empty:
                pass
# classes
class KICKSTARTER:
    """
|  General string values for the Kickstarter site
    """
    MAIN = "https://www.kickstarter.com"
    CATEGORY_ART = "https://www.kickstarter.com/discover/advanced?category_id=1&sort=end_date"
    CATEGORY_COMICS = "https://www.kickstarter.com/discover/advanced?category_id=3&sort=end_date"
    CATEGORY_DANCE = "https://www.kickstarter.com/discover/advanced?category_id=6&sort=end_date"
    CATEGORY_DESIGN = "https://www.kickstarter.com/discover/advanced?category_id=7&sort=end_date"
    CATEGORY_FASHION = "https://www.kickstarter.com/discover/advanced?category_id=9&sort=end_date"
    CATEGORY_FILM = "https://www.kickstarter.com/discover/advanced?category_id=11&sort=end_date"
    CATEGORY_FOOD = "https://www.kickstarter.com/discover/advanced?category_id=10&sort=end_date"
    CATEGORY_GAMES = "https://www.kickstarter.com/discover/advanced?category_id=12&sort=end_date"
    CATEGORY_MUSIC = "https://www.kickstarter.com/discover/advanced?category_id=14&sort=end_date"
    CATEGORY_PHOTOGRAPHY = "https://www.kickstarter.com/discover/advanced?category_id=15&sort=end_date"
    CATEGORY_PUBLISHING = "https://www.kickstarter.com/discover/advanced?category_id=18&sort=end_date"
    CATEGORY_TECHNOLOGY = "https://www.kickstarter.com/discover/advanced?category_id=16&sort=end_date"
    CATEGORY_THEATER = "https://www.kickstarter.com/discover/advanced?category_id=17&sort=end_date"
    XPATH_RELOAD_BUTTON = "id('projects')/div/div/a"
    CSS_COUNTER = "b.count"
    CSS_GET_CARD = "div.project-card"
    CSS_TITLE = "h6.project-title a"
    CSS_AUTHOR = "p.mb1"
    CSS_DESC1 = "p.project-blurb"
    CSS_DESC2 = "p.blurb"
    CSS_LOCATION_NAME = "span.location-name"
    CSS_STAT = "ul.project-stats"
    CSS_BOTTOM = "div.absolute-bottom"
    ATT_DUE_DATE = "data-end_time"
    JSON_PROJECT_TOTAL = "total_hits"
    JSON_PROJECT_PROJECTS = "projects"
    #JSON_PROJECT_PROJECTS_BACKER_CNT = "backers_count"
    #JSON_PROJECT_PROJECTS_DESC= "blurb"
    #JSON_PROJECT_PROJECTS_CATEGORY = "category"
    #JSON_PROJECT_PROJECTS_CATEGORY_NAME = "name"
    #JSON_PROJECT_PROJECTS_CATEGORY_PARENT_ID = "parent_id"
    #JSON_PROJECT_PROJECTS_CATEGORY_POSITION = "position"
    
    JSON_PROJECT_SEED = "seed"

    def __init__(self,category_id,politeness = 60):
        self.url="https://www.kickstarter.com/discover/advanced"
        self.category_id = category_id
        self.rv_static = []
        self.rv_dynamic = []
        self.politeness = politeness
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

        
class KickstarterProjectCollector:
    def __init__(self,url):
        self.url = url
    def factory_kickstarter(self,url):
        pb = PB(noimage = True)
        pb.goto(url)
        first_only = True
        try:
            btn_reload = pb.xpath_element(KICKSTARTER.XPATH_RELOAD_BUTTON)
            btn_reload.click()
            first_only = False
        except:
            pass
        return (pb,first_only)
    def target_N(self,phantomB):
        counter_we = phantomB.css_selector_element(KICKSTARTER.CSS_COUNTER)
        counter_str = counter_we.text.strip()
        temp_1 = re.findall(r'[0-9,]+',counter_str)
        if len(temp_1) > 0:
            counter_n = int(temp_1[0].replace(",",""))
        else:
            counter_n = 0
        target_n = int(math.ceil(counter_n / float(20) - 1))
        # COUNTER <= 20 * (N + 1)
        return target_n
    def execute(self,foutput):
        assert len(self.url) > 0, "Error"
        pb, first_only =  self.factory_kickstarter(self.url)
        if not first_only:
            N = self.target_N(pb)
            i = 0
            terminate = False
            while 1:
                politeness = 0
                if pb.scroll_down():
                    sys.stdout.write("\r%s"%(" "*40,))
                    sys.stdout.flush()
                    sys.stdout.write("\rpage: %03d" % (i+1,))
                    sys.stdout.flush()
                    while 1:
                        politeness += 1
                        if pb.check_scroll_complete_ajax():
                            if i < N:
                                time.sleep(politeness)
                                sys.stdout.write(".")
                                sys.stdout.flush()
                            else:
                                terminate = True
                                break
                        else:
                            break
                if terminate:
                    break
                i += 1
            #for i in xrange(N):
                #wait_tolerance = 15
                #politeness = 1
                #pb.scroll_down()
                #sys.stdout.write("page: %03d" % (i,))
                #sys.stdout.flush()
                #if pb.check_scroll_complete_ajax() and i >= N:
                    #break
                ##while not pb.check_scroll_complete_ajax() and i < N:
                    ##time.sleep(politeness)
                    ##politeness +=1 
                    ##sys.stdout.write(".")
                    ##sys.stdout.flush()
                    ##wait_tolerance -= 1
                    ##if wait_tolerance < 0:
                        ##break
                #sys.stdout.write(" OK\n")
                #sys.stdout.flush()
            sys.stdout.write("\nOK\n")
            sys.stdout.flush()
        pb.page_source_save(foutput,remove_js=True)
        del pb


class KickstarterCard:
    def __init__(self,collection_id):
        self.collection_id = collection_id
        self.title_text = " "
        self.title_url = " "
        self.author_text= " "
        self.desc_text = " "
        self.location_text = " "
        self.funded_text = " "
        self.pledged_text = " "
        self.days_to_go_text = " "
        self.on_going = "0"
    def __str__(self):
        rv = "%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n" % (
            self.collection_id,
            self.title_text.encode('utf-8'),
            self.title_url.encode('utf-8'),
            self.author_text.encode('utf-8'),
            self.desc_text.encode('utf-8'),
            self.location_text.encode('utf-8'),
            self.funded_text.encode('utf-8'),
            self.pledged_text.encode('utf-8'),
            self.days_to_go_text.encode('utf-8'))
        return rv
    def line(self):
        return [self.collection_id,
            self.on_going,
            self.title_text.encode('utf-8'),
            self.title_url.encode('utf-8'),
            self.author_text.encode('utf-8'),
            self.desc_text.encode('utf-8'),
            self.location_text.encode('utf-8'),
            self.funded_text.encode('utf-8'),
            self.pledged_text.encode('utf-8'),
            self.days_to_go_text.encode('utf-8')]

class KickstarterProjectFilter:
    def analyze(self,page_source):
        soup = BS(page_source,'html.parser')
        cards = soup.select(KICKSTARTER.CSS_GET_CARD)
        found_completed = False
        if len(cards) > 0:
            for card in cards:
                stat = card.select(KICKSTARTER.CSS_BOTTOM)
                if len(stat) > 0:
                    text_in = stat[0].text.lower()
                    compiled_re = re.findall(r'(\w{3}\s[0-9]{1,2},\s[0-9]{4})',text_in)
                    if len(compiled_re) > 0:
                        # today?
                        current_time_stamp = datetime.strptime(compiled_re[0],'%b %d, %Y')
                        today_time_stamp = datetime.today()
                        tdff = today_time_stamp - current_time_stamp
                        if tdff.days > 0: # containing past data
                            found_completed = True
                            break
        return found_completed
    def only_on_going(self,card):
        rv = "1" # means, yes on going
        stat = card.select(KICKSTARTER.CSS_BOTTOM)
        if len(stat) > 0:
            text_in = stat[0].text.lower()
            compiled_re = re.findall(r'successful',text_in)
            if len(compiled_re) > 0:
                rv = "0"
        return rv
class KickstarterProjectAnalyzer:
    def __init__(self,file_name):
        self.cards = []
        self.results = []
        self.get_soup(file_name)
        self.get_cards()
    def get_soup(self,file_name):
        f = open(file_name)
        self.soup = BS(f,'html.parser')
        f.close()
    def assert_card(self):
        if len(self.cards) <= 0:
            return False
        return True
    def get_cards(self):
        self.cards = self.soup.select(KICKSTARTER.CSS_GET_CARD)
    def execute(self,collection_id):
        assert self.assert_card, "No data!"
        append_result = self.results.append
        kpf = KickstarterProjectFilter()
        for card in self.cards:
            kickstarter_card = KickstarterCard(collection_id)
            kickstarter_card.title_text,kickstarter_card.title_url = self.get_title(card)
            kickstarter_card.author_text = self.get_author(card)
            kickstarter_card.desc_text = self.get_desc(card)
            kickstarter_card.location_text = self.get_location_name(card)
            kickstarter_card.funded_text,kickstarter_card.pledged_text,kickstarter_card.days_to_go_text = self.get_stat(card)
            kickstarter_card.on_going = kpf.only_on_going(card)
            append_result(kickstarter_card)
    def export_result_tsv(self,file_name):
        f = open(file_name,'wb')
        w = csv.writer(f,lineterminator='\n',delimiter='\t')
        for result in self.results:
            w.writerow(result.line())
        f.close()
    def get_title(self,card):
        title = card.select(KICKSTARTER.CSS_TITLE)
        title_text = "no title"
        title_url = "no url"
        if len(title) > 0:
            title_text = title[0].text.strip().replace("\n","").replace("\t","")
            title_url = title[0]['href'].strip()
            if not title_url.startswith("http"):
                title_url = "https://www.kickstarter.com%s"%(title_url)
        return title_text,title_url
    def get_author(self,card):
        author = card.select(KICKSTARTER.CSS_AUTHOR)
        author_text = "anonimous"
        if len(author) > 0:
            author_text = author[0].text.replace("by\n","").strip().replace("\n","").replace("\t","")
        return author_text
    def get_desc(self,card):
        desc1 = card.select(KICKSTARTER.CSS_DESC1)
        desc2 = card.select(KICKSTARTER.CSS_DESC2)
        desc_text = ""
        if len(desc1) > 0:
            desc_text = desc1[0].text.strip().replace("\n","")
        if len(desc2) > 0:
            desc_text = desc2[0].text.strip().replace("\n","")
        return desc_text
    def get_location_name(self,card):
        location_name = card.select(KICKSTARTER.CSS_LOCATION_NAME)
        location_text = ""
        if len(location_name) > 0:
            location_text = location_name[0].text.strip().replace("\n","").replace("\t","")
        return location_text
    def get_stat(self,card):
        stat = card.select(KICKSTARTER.CSS_STAT)
        funded_text = " "
        pledged_text = " "
        days_to_go_text = "funding unsuccessful"
        if len(stat) > 0:
            funded_text_ele = stat[0].select('li.first strong')
            if len(funded_text_ele) > 0:
                funded_text = funded_text_ele[0].text.strip()
            pledged_text_ele = stat[0].select('li.pledged strong')
            if len(pledged_text_ele) > 0:
                pledged_text = pledged_text_ele[0].text.strip()
            days_to_go_text_ele = stat[0].select('li.last strong div.num')
            if len(days_to_go_text_ele) > 0:
                days_to_go_text = days_to_go_text_ele[0].text.strip()
            else:
                days_to_go_text = "funded"
        return (funded_text,pledged_text,days_to_go_text)
class KickstarterPageAnalyzer:
    """
|  Page analyzer
|  For example, https://www.kickstarter.com/projects/1311317428/a-limited-edition-cleverly-designed-leather-collec
|  >>> kpa = KickstarterPageAnalyzer()
|  >>> kpa.read(url)
|  >>> kpa.analyze()

    """
    def __init__(self,quietly=True,has_image=True):
        self.pb = None #phantom browser
        self.quietly = quietly
        self.has_image = has_image
        #data clear
        self.clear()
    def clear(self):
        self.title = " "
        self.founder = " "
        self.url = " "
        self.stat_result = ()
        self.projects_reward_result = []
        self.images = []
        self.condition_desc = " "
        self.full_description = " "
        self.risks = " "
        self.backers = []
        self.image_fnames = []
        self.video_fname = ""
        self.video_length = 0
        self.page_compressed = None
    def terminate(self):
        self.pb.close()
        self.pb == None
    def read(self,url):
        if not self.quietly:
            sys.stdout.write("Get set...")
            sys.stdout.flush()
        if self.pb == None:
            self.pb = PB(noimage=True)
        self.url = url
        self.pb.goto(url)
        if not self.quietly:
            sys.stdout.write("OK\n")
            sys.stdout.flush()
    def analyze(self):
        pb = self.pb
        page = pb.get_page_source()
        self.page_compressed = zlib.compress(page.encode('utf-8'))
        if not self.quietly:
            sys.stdout.write("Page data compressed: self.page_compressed..\n")
            sys.stdout.flush()
        soup = BS(page,'html.parser')
        assert soup != None, "No Page!"
        #main page
        if not self.quietly:
            sys.stdout.write("..Main..")
            sys.stdout.flush()
        self.analyze_main(soup)
        if not self.quietly:
            sys.stdout.write("OK\n")
            sys.stdout.flush()
        #backers
        btn = pb.css_selector_element("#backers_nav")
        soup = None
        if not self.quietly:
            sys.stdout.write("..Visiting backers data..")
            sys.stdout.flush()
        try:
            btn.click()
            no_backers = True #which means, no update yet (still there may be backers)
            last_backer_cursor = "-1"
            #scroll down until we reach bottom
            p = pb.get_page_source()
            s = BS(p,'html.parser')
            current_rows = s.select("div.NS_backers__backing_row")
            if len(current_rows) != 0:
                no_backers = False
            breaker = False
            while 1:
                safety = 1
                if pb.scroll_down():
                    if not self.quietly:
                        sys.stdout.write("^")
                        sys.stdout.flush()
                    #checking...
                    while 1:
                        if pb.check_scroll_complete_ajax():
                            if safety < 0:
                                breaker = True
                                break
                            else:
                                if not self.quietly:
                                    sys.stdout.write(".")
                                    sys.stdout.flush()
                                time.sleep(1)
                                safety -= 1
                        else:
                            break
                if breaker:
                    break
            if not self.quietly:
                sys.stdout.write("$")
                sys.stdout.flush()
            if not no_backers:
                p = pb.get_page_source()
                soup = BS(p,'html.parser')
        except:
            pass
        if not self.quietly:
            sys.stdout.write("OK\n")
            sys.stdout.flush()
        if soup != None:
            if not self.quietly:
                sys.stdout.write("..Backers..")
                sys.stdout.flush()
            self.analyze_backers(soup)
            if not self.quietly:
                sys.stdout.write("OK\n")
                sys.stdout.flush()
    def analyze_backers(self,soup):
        # get backers data
        frame = soup.select("div.NS_backers__backing_row .meta a")
        backers = []
        if len(frame) > 0:
            for backer in frame:
                profile_url = "%s%s"%(KICKSTARTER.MAIN,backer['href'])
                backer_name = backer.text
                backers.append((profile_url,backer_name,))
        self.backers = backers
    def analyze_main(self,soup):
        #title
        title_ele = soup.select('div.title')
        if len(title_ele) > 0:
            title = title_ele[0].text.strip()
            title = re.sub(r"(\n)+"," ",title)
            self.title = title
        #founder
        founder_ele = re.findall(r"/projects/(.+)/",self.url)
        if len(founder_ele) > 0:
            self.founder = "https://www.kickstarter.com/profile/%s"%(founder_ele[0],)
        # statistics
        self.stat_result = self.analyze_stat(soup)
        # projects reward
        frame = soup.select(".NS-projects-reward")
        self.projects_reward_result = self.analyze_project_reward(frame)
        # collect images
        frame = soup.select("img.fit")
        self.images, self.image_fnames = self.analyze_images(frame)
        # video
        frame = soup.select("video.has_webm")
        self.video_length, self.video_fname = self.analyze_video(frame)
        # collect add_data
        frame = soup.select(".tiny_type")
        self.condition_desc = self.analyze_condition(frame)
        # collect full description
        frame = soup.select(".full-description")
        self.full_description = self.analyze_full_description(frame)
        # collect risk
        frame = soup.select("#risks")
        self.risks = self.analyze_full_description(frame)
    def analyze_full_description(self,frame):
        rv = ""
        if len(frame) > 0:
            desc = frame[0].text
            rv = re.sub(r"\n\n\n+","\n",desc)
            try:
                rv = rv.strip()
            except:
                pass
        return rv
    def analyze_condition(self,frame):
        rv = ""
        if len(frame) > 0:
            rv = frame[0].text
        return rv
    def analyze_images(self,frame):
        rv = []
        rv2 = []
        inque = Queue.Queue()
        outque = Queue.Queue()
        if len(frame) > 0:
            for imgf in frame:
                src = imgf['src']
                src = re.sub(r"\?.*$","",src)
                if self.has_image:
                    inque.put(src)
                else:
                    rv.append(src)
                    rv2.append("")
        if self.has_image:
            tasks = []
            for i in range(inque.qsize()):
                imageD = ImageDownloader(inque,outque,self.quietly,self.has_image)
                tasks.append(imageD)
                imageD.start()
            inque.join()
            for task in tasks:
                task.stop()
            outlist = queue_to_list(outque)
            for ol in outlist:
                rv.append(ol[0])
                rv2.append(ol[1])
        return rv,rv2
    def analyze_video(self,frame):
        rv = 0 #seconds
        v_url_first = "no_video"
        if len(frame) > 0:
            sources = frame[0].select("source")
            if len(sources) > 0:
                for source in sources:
                    v_url = source['src']
                    if v_url.endswith(".mp4"):
                        v_url_first = v_url
                        break
                if len(v_url_first) > 0:
                    rv = get_video_duration(v_url_first)
        return rv,v_url_first
    def analyze_stat(self,soup):
        frame = soup.select("div#stats") #move
        if len(frame) > 0:
            frame1 = frame[0].select("div#backers_count")
            if len(frame1) > 0:
                number_of_backers = int(frame1[0]['data-backers-count'])
            else:
                number_of_backers = 0
            frame2 = frame[0].select("div#pledged")
            if len(frame2) > 0:
                try:
                    goal = float(frame2[0]['data-goal'])
                except:
                    goal = 0.0
                try:
                    percent_raised = float(frame2[0]['data-percent-raised'])
                except:
                    percent_raised = 0.0
                try:
                    amount_pledged = float(frame2[0]['data-pledged'])
                except:
                    amount_pledged = 0.0
                frame21 = frame2[0]('data')
                if len(frame21) > 0:
                    try:
                        currency = frame21[0]['data-currency']
                    except:
                        currency = ""
                else:
                    currency = ""
            else:
                goal = 0.0
                percent_raised = 0.0
                amount_pledged = 0.0
                currency = ""
            frame3 = frame[0].select("#project_duration_data")
            if len(frame3) > 0:
                try:
                    duration = float(frame3[0]['data-duration'])
                except:
                    duration = 0.0
                try:
                    end_time = frame3[0]['data-end_time']
                except:
                    end_time = "na"
                try:
                    hours_remaining = float(frame3[0]['data-hours-remaining'])
                except:
                    hours_remaining = 0.0
            else:
                duration = 0.0
                end_time =""
                hours_remaining = 0.0
        else:
            number_of_backers = 0
            goal = 0.0
            percent_raised = 0.0
            amount_pledged = 0.0
            currency = ""
            duration = 0.0
            end_time = ""
            hours_remaining = 0.0
        #Facebook count
        temp_soup_facebook = BS(self.pb.get_page_source(),'html.parser')
        frame = temp_soup_facebook.select("li.facebook.mr2 .count")
        waiting = 1
        while 1:
            if len(frame) > 0:
                try:
                    facebook_count = int(frame[0].text) #error prone
                    break
                except:
                    if not self.quietly:
                        sys.stdout.write("[facebook waiting...%d]\n"%waiting)
                        sys.stdout.flush()
                    time.sleep(waiting)
                    waiting += 1
                    temp_soup_facebook = BS(self.pb.get_page_source(),'html.parser')
                    frame = temp_soup_facebook.select("li.facebook.mr2 .count")
            else:
                facebook_count = 0
                break
            if waiting >= 10:
                if not self.quietly:
                    sys.stdout.write(" [facebook error] ")
                    sys.stdout.flush()
                facebook_count = -1 #means, error
                break
        #minimum pledge
        frame = soup.select("#button-back-this-proj .money")
        if len(frame) > 0:
            minimum_pledge = frame[0].text
        else:
            minimum_pledge = ""
        #update
        return (number_of_backers,goal,percent_raised,
                amount_pledged,currency,duration,end_time,
                hours_remaining,facebook_count,minimum_pledge)
    def analyze_project_reward(self,frame):
        #projects reward
        projects_reward_rv = []
        if len(frame) > 0:
            #
            for card in frame:
                #money
                money_f = card.select(".money")
                if len(money_f) > 0:
                    money = filter_number(money_f[0].text.strip())
                else:
                    money = 0.0
                #backers
                backers_f = card.select(".num-backers")
                if len(backers_f) > 0:
                    num_backers = filter_number(backers_f[0].text.strip())
                else:
                    num_backers = 0.0
                #description
                desc_f = card.select(".desc")
                if len(desc_f) > 0:
                    description = desc_f[0].text.strip()
                else:
                    description = ""
                #delivery
                delivery_f = card.select("time")
                if len(delivery_f) > 0:
                    delivery_estimated = delivery_f[0]['datetime']
                else:
                    delivery_estimated = ""
                #limited
                limited_f = card.select(".limited-number")
                if len(limited_f) > 0:
                    limited_num = int(re.findall(r"of ([0-9]+)",limited_f[0].text)[0])
                else:
                    limited_num = 0
                projects_reward_rv.append([
                    money,
                    num_backers,
                    description,
                    delivery_estimated,
                    limited_num,
                ])
            #for
        #
        return projects_reward_rv
            

class KsProjectProbe(Thread):
    def __init__(self,url_queue,screen,loc_id,continue_=False):
        Thread.__init__(self)
        #self.url = url
        self.url_queue = url_queue
        self.running = True
        self.repository = "" # file repository
        self.continue_ = continue_
        self.screen = screen
        self.loc_id = loc_id
        
        #self.bench_mark = bench_mark #bench mark card (to decide a stopping point)
    #def add(self,url):
        #self.url_queue.put(url)
    def stop(self):
        self.running = False
    def run(self):
        filter = KickstarterProjectFilter()
        screen = self.screen
        while self.running:
            try:
                url,identifier = self.url_queue.get(block=True,timeout=10) #wait for 10 second
                screen.gotoXY(7,self.loc_id)
                screen.cprint(15,0,"ACTIVE  ")
                sys.stdout.flush()
                #sys.stdout.flush()
                start_tstamp = time_stamp()
                assert len(url) > 0, "Error"
                screen.gotoXY(25,self.loc_id)
                screen.cprint(13,0,"Processing at %s%s"%(time.asctime(time.localtime())," "*20))
                sys.stdout.flush()
                pb, first_only =  self.factory_kickstarter(url)
                if self.continue_:
                    if filter.analyze(pb.get_page_source()):
                        first_only = True # cancel the rest
                if not first_only:
                    scroll_line = 0
                    N = self.target_N(pb)
                    i = 0
                    terminate = False
                    while 1:
                        politeness = 0
                        if pb.scroll_down():
                            scroll_line += 1
                            screen.gotoXY(0,self.loc_id)
                            screen.cprint(10,0,"%04d"%scroll_line)
                            sys.stdout.flush()
                            while 1:
                                politeness += 1
                                if pb.check_scroll_complete_ajax():
                                    if i < N:
                                        time.sleep(politeness)
                                    else:
                                        terminate = True
                                        break
                                else:
                                    break
                            screen.gotoXY(5,self.loc_id)
                            screen.cprint(9,0," ")
                            sys.stdout.flush()
                            #check (whether or not continuing...)
                            if self.continue_:
                                if filter.analyze(pb.get_page_source()):
                                    terminate = True
                                    break
                        if terminate:
                            break
                        i += 1
                    screen.gotoXY(0,self.loc_id)
                    screen.cprint(12,0,"OK   ")
                    sys.stdout.flush()
                
                fname = "%s%s_%s_page_source.html" % (self.repository,
                                                      start_tstamp,
                                                      identifier)
                pb.page_source_save(fname,remove_js=True) #for testing...
                del pb # terminate the session
                screen.gotoXY(25,self.loc_id)
                screen.cprint(13,0,"Complete at %s%s"%(time.asctime(time.localtime())," "*30))
                sys.stdout.flush()
                self.url_queue.task_done()
            except Queue.Empty:
                self.screen.gotoXY(0,self.loc_id)
                self.screen.cprint(12,0," "*12)
                screen.gotoXY(7,self.loc_id)
                screen.cprint(15,0,"INACTIVE")
                sys.stdout.flush()                
                sys.stdout.flush()
    def factory_kickstarter(self,url):
        pb = PB(noimage = True)
        pb.goto(url)
        first_only = True
        try:
            btn_reload = pb.xpath_element(KICKSTARTER.XPATH_RELOAD_BUTTON)
            btn_reload.click()
            first_only = False
        except:
            pass
        return (pb,first_only)
    def target_N(self,phantomB):
        counter_we = phantomB.css_selector_element(KICKSTARTER.CSS_COUNTER)
        counter_str = counter_we.text.strip()
        temp_1 = re.findall(r'[0-9,]+',counter_str)
        if len(temp_1) > 0:
            counter_n = int(temp_1[0].replace(",",""))
        else:
            counter_n = 0
        target_n = int(math.ceil(counter_n / float(20) - 1))
        # COUNTER <= 20 * (N + 1)
        return target_n

class KsProjectProbeJson(Thread):
    def __init__(self,url_queue,continue_=False):
        self.url_queue = url_queue
        self.running = True
        self.repository = ""
        self.continue_ = continue_
    
class ksProjectPageAnalyzer(Thread):
    """
|  listen
    """
    def __init__(self,ongoing_dir,listener_dir,speaker_dir,reserver_dir,listen_duration=60):
        Thread.__init__(self)
        self.running = True
        self.ongoing_dir = ongoing_dir #ongoing_data_now
        self.listener_dir = listener_dir #input
        self.speaker_dir = speaker_dir #analysis result
        self.reserver_dir = reserver_dir #move completed ones
        self.listen_duration = listen_duration
        if not os.path.exists(speaker_dir):
            os.mkdir(speaker_dir)
        if not os.path.exists(reserver_dir):
            os.mkdir(reserver_dir)
        if not os.path.exists(self.ongoing_dir):
            os.mkdir(self.ongoing_dir)        
        sys.stdout.write("PROJECT PAGE ANALYZER STARTS...\n")
        sys.stdout.write("\r...WAITING...")
        sys.stdout.flush()
    def stop(self):
        self.running = False
    def run(self):
        while self.running:
            try:
                #collection id
                collection_id = time_stamp()[:10] #year_month_day
                #read file list
                data_files = glob.glob("%s/*.*"%self.listener_dir)
                #current_project_inventory = glob.glob("%s/*.inv"%self.ongoing_dir)
                #for cpi in current_project_inventory:
                    #os.remove(cpi)
                out_dir = "%s/%s"%(self.speaker_dir,collection_id)
                if not os.path.exists(out_dir):
                    os.mkdir(out_dir)
                res_dir = "%s/%s"%(self.reserver_dir,collection_id)
                if not os.path.exists(res_dir):
                    os.mkdir(res_dir)
                current_proj_inv_dir = "%s/%s"%(self.ongoing_dir,collection_id)
                if not os.path.exists(current_proj_inv_dir):
                    os.mkdir(current_proj_inv_dir)
                #working...
                for data_file in data_files:
                    base_file_name = os.path.basename(data_file)
                    remove_int = len("...PROCESSING: %s"%(base_file_name,))
                    sys.stdout.write("\r...PROCESSING: %s"%(base_file_name,))
                    sys.stdout.flush()
                    kpa = KickstarterProjectAnalyzer(data_file)
                    kpa.execute(collection_id)
                    out_fname = "%s/%s.txt" % (out_dir,base_file_name)
                    kpa.export_result_tsv(out_fname)
                    res_fname = "%s/%s"%(res_dir,base_file_name)
                    shutil.move(data_file,res_fname)
                    sys.stdout.write("\r%s"%(" "*remove_int,))
                    sys.stdout.flush()
                    #list up
                    f_inv = open("%s/%s.inv"%(self.ongoing_dir,base_file_name),'wb')
                    f_inv_writer = csv.writer(f_inv,delimiter="\t",lineterminator="\n")
                    for kickstarter_card in kpa.results:
                        if kickstarter_card.on_going == "1":
                            f_inv_writer.writerow([kickstarter_card.title_url])
                    f_inv.close()
                    #list up
                    shutil.copyfile("%s/%s.inv"%(self.ongoing_dir,base_file_name),"%s/%s.inv"%(current_proj_inv_dir,base_file_name))
                    #make backup
                
                sys.stdout.write("\r...WAITING...")
                sys.stdout.flush()
                time.sleep(self.listen_duration)
            except KeyboardInterrupt:
                break
        sys.stdout.write("\nTHANK YOU.\n")
        sys.stdout.flush()
    
class KsPageAnalyzerWrapper(Thread):
    def __init__(self,inque,sqlite_db,quietly=True,has_image=True):
        Thread.__init__(self)
        self.inque = inque
        self.running = True
        self.kpa = KickstarterPageAnalyzer(quietly=quietly,has_image=has_image) #default analyzer
        self.sqlite_db = sqlite_db
        self.quietly = quietly #for later use or remove it...
        self.has_image = has_image #for later use or remove it...
    def stop(self):
        self.running = False
    def stat_reward(self,projects_reward_result):
        money_list = []
        num_backers_list = []
        variety_of_offer = len(projects_reward_result)
        for reward in projects_reward_result:
            money_list.append(reward[0])
            num_backers_list.append(reward[1])
        money_np = NP.array(money_list)
        if len(money_np) > 0:
            min_money = float(NP.min(money_np))
            max_money = float(NP.max(money_np))
            avg_money = float(NP.mean(money_np))
            std_money = float(NP.std(money_np))
            total_money = float(NP.sum(money_np))            
        else:
            min_money = 0.0
            max_money = 0.0
            avg_money = 0.0
            std_money = 0.0
            total_money = 0.0
        num_backers_np = NP.array(num_backers_list)
        if len(num_backers_np) > 0:
            total_num_backer = float(NP.sum(num_backers_np))
            min_num_backer = float(NP.min(num_backers_np))
            max_num_backer = float(NP.max(num_backers_np))
            avg_num_backer = float(NP.mean(num_backers_np))
            std_num_backer = float(NP.std(num_backers_np))
        else:
            total_num_backer = 0.0
            min_num_backer = 0.0
            max_num_backer = 0.0
            avg_num_backer = 0.0
            std_num_backer = 0.0
        return (variety_of_offer,
                avg_money,std_money,min_money,max_money,total_money,
                avg_num_backer,std_num_backer,min_num_backer,max_num_backer,total_num_backer)
    
    def run(self):
        inque = self.inque
        kpa = self.kpa
        url = ""
        while self.running:
            try:
                url = inque.get(block = True, timeout = 10)
                self.kpa.read(url)
                self.kpa.analyze()
                identifier = url.replace("https://www.kickstarter.com/projects/","").replace("?ref=discovery","")
                recording_date = time_stamp()[:10].replace("_","/")
                #database
                con = sqlite3.connect(self.sqlite_db)
                cur = con.cursor()
                if self.has_image:
                    sql = """INSERT INTO project (recording_date,
                            identifier,title,founder,url,condition_desc,full_description,
                            risks,video_fname,video_length,
                            number_of_backers,goal,percent_raised,amount_pledged,currency,duration,end_time,hours_remaining,facebook_count,minimum_pledge,
                            reward_variety_of_offer,reward_avg_money,reward_std_money,reward_min_money,reward_max_money,reward_total_money,
                            reward_avg_num_backer,reward_std_num_backer,reward_min_num_backer,reward_max_num_backer,reward_total_num_backer,
                            projects_reward_result,images,image_fnames,backers,
                            page_compressed
                            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?);
                        """
                else:
                    sql = """INSERT INTO project (recording_date,
                            identifier,title,founder,url,condition_desc,full_description,
                            risks,video_fname,video_length,
                            number_of_backers,goal,percent_raised,amount_pledged,currency,duration,end_time,hours_remaining,facebook_count,minimum_pledge,
                            reward_variety_of_offer,reward_avg_money,reward_std_money,reward_min_money,reward_max_money,reward_total_money,
                            reward_avg_num_backer,reward_std_num_backer,reward_min_num_backer,reward_max_num_backer,reward_total_num_backer,
                            projects_reward_result,image_fnames,backers,
                            page_compressed
                            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?);
                        """                    
                input_data = []
                stat_reward_results = self.stat_reward(kpa.projects_reward_result)
                #
                input_data.append(recording_date)
                input_data.append(identifier)
                input_data.append(kpa.title)
                input_data.append(kpa.founder)
                input_data.append(kpa.url)
                input_data.append(kpa.condition_desc)
                input_data.append(kpa.full_description)
                input_data.append(kpa.risks)
                input_data.append(kpa.video_fname)
                input_data.append(kpa.video_length)
                input_data.append(kpa.stat_result[0])
                input_data.append(kpa.stat_result[1])
                input_data.append(kpa.stat_result[2])
                input_data.append(kpa.stat_result[3])
                input_data.append(kpa.stat_result[4])
                input_data.append(kpa.stat_result[5])
                input_data.append(kpa.stat_result[6])
                input_data.append(kpa.stat_result[7])
                input_data.append(kpa.stat_result[8])
                input_data.append(kpa.stat_result[9])
                input_data.append(stat_reward_results[0])
                input_data.append(stat_reward_results[1])
                input_data.append(stat_reward_results[2])
                input_data.append(stat_reward_results[3])
                input_data.append(stat_reward_results[4])
                input_data.append(stat_reward_results[5])
                input_data.append(stat_reward_results[6])
                input_data.append(stat_reward_results[7])
                input_data.append(stat_reward_results[8])
                input_data.append(stat_reward_results[9])
                input_data.append(stat_reward_results[10])
                input_data.append(sqlite3.Binary(cPickle.dumps(kpa.projects_reward_result,cPickle.HIGHEST_PROTOCOL)))
                if self.has_image:
                    input_data.append(sqlite3.Binary(cPickle.dumps(kpa.images,cPickle.HIGHEST_PROTOCOL)))
                input_data.append(sqlite3.Binary(cPickle.dumps(kpa.image_fnames,cPickle.HIGHEST_PROTOCOL)))
                input_data.append(sqlite3.Binary(cPickle.dumps(kpa.backers,cPickle.HIGHEST_PROTOCOL)))
                input_data.append(sqlite3.Binary(cPickle.dumps(kpa.page_compressed,cPickle.HIGHEST_PROTOCOL)))
                cur.execute(sql,input_data)
                con.commit()
                cur.close()
                con.close()
                kpa.clear() #clear out buffer
                inque.task_done()
            except Queue.Empty:
                pass #waiting for the next queue
# PROGRAM END ===========