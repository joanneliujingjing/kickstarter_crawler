'''
KICKSTARTER PAGE DATA COLLECTION
AUTHOR: DRTAGKIM
2014
'''
# SETTING =====
PORT = 1002
THREAD_POOL = 10
DBNAME = "test_page_out.db"
QUIETLY = False
HAS_IMAGE = False

# IMPORT MODULES =====
from web3 import PhantomBrowser as PB
from bs4 import BeautifulSoup as BS
from hsaudiotag import mp4 # $ pip install hsaudiotag
from StringIO import StringIO
from threading import Thread

import zlib, re, time, sys, Queue, sqlite3,cPickle
import socket, os
import requests # $ pip install requests
'''
HELPER FUNCTIONS
CONVERSION BETWEEN LIST AND QUEUE
'''

# HELPERS =====
def list_to_queue(list_data):
    queue = Queue.Queue()
    map(lambda x : queue.put(x), list_data)
    return queue

def queue_to_list(queue_data):
    list_data = []
    list_data_append = list_data.append
    while True:
        try:
            list_data_append(queue_data.get_nowait())
        except:
            break
    return list_data

# PROGRAM STARTS =====
class ImageDownloader(Thread):
    '''
|  IMAGE DOWNLOADER
|  GET IMAGES FROM WEBSITES AND MAKE THEM BINARY FILES
    '''
    
    def __init__(self, inque, outque, quietly = True, has_image = True):
        Thread.__init__(self)
        self.inque = inque
        self.outque = outque
        self.running = True
        self.quietly = quietly
        self.has_image = has_image

    def stop(self):
        self.running = False

    def run(self):
        # data referencce
        inque = self.inque
        outque = self.outque
        has_image = self.has_image
        # precondition
        assert inque is not None, ""
        assert outque is not None, ""
        assert isinstance(inque, Queue.Queue), ""
        assert isinstance(outque, Queue.Queue), ""
        # processing
        while self.running:
            try:
                src = inque.get(block = True, timeout = 1)
                if has_image:
                    r = requests.get(src)
                    if r.status_code == 200: # if everything is OK,
                        c = r.content
                        outque.put([c,src]) # return ([binary data, file url])
                    if not self.quietly: # reporting if needed
                        sys.stdout.write("i")
                        sys.stdout.flush()
                else:
                    outque.put(['',src])
                    if not self.quietly:
                        sys.stdout.write("o")
                        sys.stdout.flush()
                inque.task_done() # pass the finished token
            except Queue.Empty: # wait for 1 second for the next data
                pass

class KickstarterPageAnalyzer(Thread):
    """
|  Page analyzer
|  For example,
|  >>> kpa = KickstarterPageAnalyzer()
|  >>> ts_id = "2014/06/23"
|  >>> project_id = 000000001
|  >>> url = "https://www.kickstarter.com/projects/1311317428/a-limited-edition-cleverly-designed-leather-collec"
|  >>> kpa.read(ts_id,project_id,url)
|  >>> kpa.analyze()
|
|  # OPTIONS
|  >>> kap = KickstarterPageAnalyzer(quietly = False, has_image = True)

|  Backers
|  Condition
|  Full description
|    Images
|    Video
|  Facebook

    """

    def __init__(self, inque, dbname, quietly = True, has_image = False):
        """
|  quietly (True/False): display progress log
|  has_image (True/False): download image data during scrapping
        """
        Thread.__init__(self) # multithreading (be careful! do not over the number of processors)
        self.inque = inque # input queue
        self.dbname = dbname # sqlite3 database name (out data)
        self.pb = None # phantom browser
        self.quietly = quietly
        self.has_image = has_image
        #data clear
        self.clear()
        self.running = True # multithreading control

    def clear(self):
        self.ts_id = ""
        self.project_id = -1
        self.url = ""
        self.projects_reward_result = []
        self.images = []
        self.full_description = ""
        self.risks = ""
        self.backers = []
        self.image_fnames = []
        self.video_fname = ""
        self.video_has_high = 0
        self.video_has_base = 0
        self.video_length = 0
        self.video_has = False
        self.page_compressed = None
        self.facebook_like = 0

    def terminate(self):
        try:
            self.pb.close()
            self.pb == None
        except:
            pass
    def stop(self):
        self.running = False
        self.terminate()
        
    def run(self):
        """
        """
        inque = self.inque
        if not self.quietly:
            sys.stdout.write("Get set...")
            sys.stdout.flush()
        if self.pb == None: # if there is no browser, create new one
            self.pb = PB(noimage=True)        
        while self.running:
            try:
                self.ts_id, self.project_id, self.url = inque.get(block = True, timeout = 1)
                self.read(self.ts_id, self.project_id, self.url) # for clear representation
                self.analyze()
                self.prep_database()
                self.write_database()
                self.clear()
            except Queue.Empty:
                pass
    def read(self, ts_id, project_id, url):
        """
|  project page
        """
        self.pb.goto(url)
        if not self.quietly:
            sys.stdout.write("OK\n")
            sys.stdout.flush()

    def analyze(self):
        pb = self.pb
        page = pb.get_page_source()
        # preconditions
        assert page is not None and len(page) > 0, ""
        self.page_compressed = zlib.compress(page.encode('utf-8'))
        if not self.quietly:
            sys.stdout.write("Page data compressed: self.page_compressed..\n")
            sys.stdout.flush()
        soup = BS(page,'html.parser')
        # precondition
        assert soup != None, "No Page!"
        #main page
        if not self.quietly:
            sys.stdout.write("..Main..")
            sys.stdout.flush()
        #analyze main page ===========
        # reward
        frame = soup.select(".NS-projects-reward")
        proj_reward_append = self.projects_reward_result.append
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
                proj_reward_append([
                    money,
                    num_backers,
                    description,
                    delivery_estimated,
                    limited_num,
                ])
            #for
        # collect images
        frame = soup.select("img.fit")
        image_fnames_append = self.image_fnames.append
        images_append = self.images.append
        if len(frame) > 0:
            for imgf in frame:
                src = imgf['src']
                src = re.sub(r"\?.*$","",src)
                image_fnames_append(src)
                images_append("") #basically nothing is apppended
            if self.has_image:
                inque = list_to_queue(self.image_fnames)
                outque = Queue.Queue()
                tasks = []
                # parallel processing
                for i in range(inque.qsize()):
                    imageD = ImageDownloader(inque,outque,self.quietly,True)
                    imageD.setDaemon(True)
                    tasks.append(imageD)
                    imageD.start()
                inque.join() #wait till being finished
                for task in tasks:
                    task.stop()
                outlist = queue_to_list(outque)
                self.images = copy.deepcopy(outlist)
                # replace string list to binary data list
        # video (source file name, length)s
        frame = soup.select("video.has_webm")
        self.video_fname = "na"
        v_url = ""
        if len(frame) > 0:
            sources = frame[0].select("source")
            if len(sources) > 0:
                self.video_has = True
                for source in sources:
                    v_url = source['src']
                    if v_url.endswith(".mp4"):
                        if v_url.find('high') > 0:
                            self.video_has_high = 1
                            self.video_fname = v_url
                        else:
                            self.video_has_base = 1
                            self.video_fname = v_url # if base exists, replace by it.
                if self.video_has_high > 0 or self.video_has_base > 0:
                    url = self.video_fname
                    # video duration
                    r = requests.get(url,stream = True)
                    a = r.raw.read(2000) #2kb buffer
                    b = StringIO()
                    b.write(a)
                    c = mp4.File(b)
                    self.video_length = c.duration
                    b.close()
                    r.close()
        # collect full description
        frame = soup.select(".full-description")        
        rv = ""
        if len(frame) > 0:
            desc = frame[0].text
            rv = re.sub(r"\n\n\n+","\n",desc)
            try:
                rv = rv.strip()
            except:
                pass
        self.full_description = rv        
        # collect risk
        frame = soup.select("#risks")
        rv = ""
        if len(frame) > 0:
            desc = frame[0].text
            rv = re.sub(r"\n\n\n+","\n",desc)
            try:
                rv = rv.strip()
            except:
                pass
        self.risks = rv        
        # Facebook
        frame = soup.select("li.facebook.mr2 .count")
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
                    temp_soup_facebook = BS(pb.get_page_source(),'html.parser')
                    frame = temp_soup_facebook.select("li.facebook.mr2 .count")
            else:
                self.facebook_like = 0
                break
            if waiting >= 10:
                if not self.quietly:
                    sys.stdout.write(" [facebook error] ")
                    sys.stdout.flush()
                self.facebook_like = -1 #means, error
                break
        
        # ============================
        if not self.quietly:
            sys.stdout.write("OK\n")
            sys.stdout.flush()
        #backers =====================
        #btn = pb.css_selector_element("#backers_nav")
        soup = None
        if not self.quietly:
            sys.stdout.write("..Visiting backers data..")
            sys.stdout.flush()
        try:
            headers = { 'User-Agent' : 'Mozilla/5.0 (X11; U; Linux i686) Gecko/20071127 Firefox/2.0.0.11',
                     'connection' : 'close',
                     'charset' : 'utf-8'}
            params = {'format':'json'}            
            con = requests.get(self.url,headers=headers,params=params)
            j = con.json()
            board = j['running_board']
            s = BS(board,'html.parser')
            eles = s.select('a#backers_nav data')
            if len(eles) > 0:
                t = eles[0].text.replace(",","")
                n = int(t)
                pn = n/40 + 2
            else:
                n = 0
                pn = 0            
            self.pagination = pn
            
            backer_url = self.url+"/backers"
            pb.goto(backer_url)
            page = 1
            # measure current backers
            p = pb.get_page_source()
            s = BS(p,'html.parser')
            frame = s.select("div.NS_backers__backing_row .meta a")
            prevc = len(frame)
            # init
            nowc = 0
            # pagination
            while 1:
                pb.scroll_down()
                # measure current backers
                p = pb.get_page_source()
                s = BS(p,'html.parser')
                frame = s.select("div.NS_backers__backing_row .meta a")
                nowc = len(frame)
                if not self.quietly:
                    sys.stdout.write("b")
                    sys.stdout.flush()
                if nowc > prevc:
                    prevc = nowc
                else:
                    break
            self.get_backers(pb)
            #get backers
            p = pb.get_page_source()
            s = BS(p,'html.parser')
            frame = s.select("div.NS_backers__backing_row .meta a")
            backers_append = self.backers.append
            if len(frame) > 0:
                for backer in frame:
                    profile_url = "%s"%(backer['href'])
                    backer_name = backer.text
                    backers_append((profile_url,backer_name,))
    def prep_database(self):
        sql_create_table1 = """
            CREATE TABLE IF NOT EXISTS project_benchmark_sub (
                ts_id NUMBER,
                project_id NUMBER,
                project_reward_number NUMBER,
                project_reward_mim_money_list TEXT,
                project_reward_description_total_length NUMBER,
                project_reward_description_str TEXT,
                image_count NUMBER,
                image_fnames_list TEXT,
                description_length NUMBER,
                description_str TEXT,
                risks_length NUMBER,
                risks_str TEXT,
                video_has NUMBER,
                video_length NUMBER,
                video_fname TEXT,
                video_has_high NUMBER,
                video_has_base NUMBER,
                facebook_like NUMBER,
                html_compressed BLOB,
                CONSTRAINT update_rule UNIQUE (ts_id, project_id) ON CONFLICT REPLACE);
            )
        """
        sql_create_table2 = """
            CREATE TABLE IF NOT EXISTS int_project_backer (
                ts_id NUMBER,
                project_id NUMBER,
                profile_url TEXT,
                backer_slug TEXT,
                CONSTRAINT update_rule UNIQUE (ts_id, project_id, backer_slug) ON CONFLICT REPLACE);
        """
        self.sql_insert1 = """
            INSERT INTO project_benchmark_sub (
                ts_id, project_id, project_reward_number,
                project_reward_mim_money_list, project_reward_description_total_length,
                project_reward_description_str, image_count, image_fnames_list, description_length, description_str, risks_length, risks_str, video_has, 
                video_length, video_fname, video_has_high, video_has_base, facebook_like,
                html_compressed) VALUES (
                ?,?,?,?,?,?,?,?,?,??,?,?,?,?,?,?,?,?
            );
        """
        self.sql_insert2 = """
            INSERT INTO int_project_backer (
                ts_id, project_id, profile_url, backer_slug)
                VALUES (?,?,?,?);
        """
        con = sqlite3.connect(self.dbname)
        cur = con.cursor()
        cur.execute(sql_create_table1)
        con.commit()
        cur.execute(sql_create_table2)
        con.commit()
        cur.close()
        con.close()
    def write_database(self):
        project_reward_number = len(self.projects_reward_result)
        project_reward_mim_money_list = repr([item[0] for item in self.projects_reward_result])
        project_reward_description_total_length = 0
        project_reward_desc_temp = []
        for item in self.projects_reward_result:
            project_reward_description_total_length += len(item[2])
            project_reward_desc_temp.append(item[2])
        project_reward_description_str = " ".join(project_reward_desc_temp)
        image_count = len(self.image_fnames)
        image_fnames_list = repr(self.image_fnames)
        description_length = len(self.full_description)
        risks_length = len(self.risks)
        # insert first
        if not self.quietly:
            sys.stdout.write("...DATA BASE INIT...")
            sys.stdout.flush()
        con = sqlite3.connect(self.dbname)
        cur = con.cursor()
        cur.execute(self.sql_insert1,(
            self.ts_id,self.project_id,
            project_reward_number,project_reward_mim_money_list,
            project_reward_description_total_length,
            project_reward_description_str,
            image_count,image_fnames_list,
            description_length,self.full_description,
            risks_length,self.risks,
            self.video_has,self.video_length,self.video_fname,self.video_has_high,self.video_has_base,self.facebook_like,
            sqlite3.Binary(cPickle.dumps(self.page_compressed,cPickle.HIGHEST_PROTOCOL))
        ))
        con.commit()
        backer_input_list = []
        for backer in self.backers:
            backer_input_list.append((self.ts_id, self.project_id, backer[0], backer[1],))
        cur.executemany(self.sql_insert2,backer_input_list)
        con.commit()
        cur.close()
        con.close()
        if not self.quietly:
            sys.stdout.write("...DB OK...")
            sys.stdout.flush()
            
# SERVER

if __name__ == "__main__":
    inque = Queue.Queue()
    workers = []
    for i in range(THREAD_POOL):
        worker = KickstarterPageAnalyzer(inque,DBNAME,QUIETLY,HAS_IMAGE)
        worker.setDaemon(True)
        workers.append(worker)
    server = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    server.bind('',PORT)
    server.listen(1)
    sys.stdout.write("SERVER STARTS\n=============\n")
    sys.stdout.flush()
    while 1:
        try:
            conn, addr = server.accept()
            data = conn.recv(1000000)
            data = eval(data)
            inque.put(data)
            conn.close() # disconnect client
        except KeyboardInterrupt:
            sys.stdout.write("\n\nSERVER OUT.\nTHANK YOU.")
            sys.stdout.flush()
            break
        except socket.error, msg:
            sys.stdout.write(msg)
            sys.stdout.write("\n\nSocket Error.\n")
            sys.stdout.flush()
            break
    for worker in workers: # terminate threads
        worker.stop()
    server.close() # close server
# END OF PROGRAM ====================