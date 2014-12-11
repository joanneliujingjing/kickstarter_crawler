#backer test

from web3 import PhantomBrowser as PB
from bs4 import BeautifulSoup as BS
import re,time,sys


def backer_scroll_expected_condition(pb):
    rv = False #continue
    script = "window.scrollTo(0, document.body.scrollHeight);"
    page = pb.get_page_source()
    soup = BS(page,'html.parser')
    eles = soup.select("div.NS_backers__backing_row")
    new_size = len(eles)
    if pb.temp_backer_number < new_size: #something incresed
        pb.temp_backer_number = new_size
        rv = True #stop
    print "condition : %d %s" % (new_size, rv)
    return rv
def backer_exist_expected_condition(pb):
    rv = False
    page = pb.get_page_source()
    soup = BS(page,'html.parser')
    frame = soup.select("div.NS_backers__backing_row .meta a")
    rv = len(frame) > 0
    return rv

def test(url):
    pb = PB()
    backer_url = url+"/backers"
    pb.goto(backer_url,filter_func = backer_exist_expected_condition)
    p = pb.get_page_source()
    s = BS(p,'html.parser')
    backer_count_eles  = s.select("div#backers_count")
    if len(backer_count_eles) > 0:
        backer_count = int(backer_count_eles[0]['data-backers-count'])
    else:
        print 'hi'
    print "Backer count = %d" % backer_count
    frame = s.select("div.NS_backers__backing_row .meta a")
    pb.temp_backer_number = len(frame) # temp variable
    print "init = %d" % pb.temp_backer_number
    if len(frame) >= 50: # has pagination
        while 1: # pagination control
            if abs(backer_count - pb.temp_backer_number) < 10:
                break
            pb.scroll_down(filter_func = backer_scroll_expected_condition, 
                           filter_time_out = 10) # wait for three minutes
            p = pb.get_page_source()
            s = BS(p,'html.parser')
            frame = s.select("div.NS_backers__backing_row .meta a")
            nowc = len(frame) # get current number
            print ".[backer_page = %04d]."%(nowc)
            if nowc == 0 or (nowc % 50) != 0: #precondition, check end (from 51)
                break # the final page does not contain 50 projects (less than that)
    #get backers
    s = BS(p,'html.parser')
    frame = s.select("div.NS_backers__backing_row")
    backers = []
    backers_append = backers.append
    if len(frame) > 0:
        for backer in frame:
            anchors = backer.select(".meta a")
            if len(anchors) > 0:
                profile_url = "%s"%(anchors[0]['href'])
                backer_name = anchors[0].text
            else:
                profile_url = 'na'
                backer_name = 'na'
            history = backer.select(".backings")
            if len(history) > 0:
                backing_hist_eles = re.findall(r"[0-9,]+",history[0].text)
                if len(backing_hist_eles) > 0:
                    backing_hist = int(backing_hist_eles[0].replace(",","").strip())
                else:
                    backing_hist = 0
            else:
                backing_hist = 0
            backers_append((profile_url,backer_name,backing_hist))
    return backers
if __name__ =="__main__":
    #url = "https://www.kickstarter.com/projects/evanyoung/the-last-west-volume-two"
    #url = "https://www.kickstarter.com/projects/1112709940/all-i-didnt-say"
    #url = "https://www.kickstarter.com/projects/851629756/pick-a-card-a-burlesque-exploration-of-tarot"
    #url = "https://www.kickstarter.com/projects/1440827629/liz-imperios-breaking-barriers"
    #url = "https://www.kickstarter.com/projects/evanyoung/the-last-west-volume-two"
    #url = "https://www.kickstarter.com/projects/1721875190/kiss-comics"
    #url = "https://www.kickstarter.com/projects/synaid/peeved"
    #url = "https://www.kickstarter.com/projects/1350078939/da-bishops-stranger-zombie-comic-collection"
    #url = "https://www.kickstarter.com/projects/1835178575/the-will-of-captain-crown-book-two-gold-of-the-dam"
    #url = "https://www.kickstarter.com/projects/502093706/unsounded-comic-volume-2"
    #url = "https://www.kickstarter.com/projects/1576907254/little-nemo-dream-another-dream"
    #url ="https://www.kickstarter.com/projects/76843433/dance-dsm-bringing-competitive-swing-to-a-city-wit"
    #url = "https://www.kickstarter.com/projects/938861325/sherman-dances-a-childrens-book"
    #url = "https://www.kickstarter.com/projects/evanyoung/the-last-west-volume-two"
    url = "https://www.kickstarter.com/projects/laboratory/shadows-of-arkham"
    backers = test(url)
    print "Num = %d" % len(backers)