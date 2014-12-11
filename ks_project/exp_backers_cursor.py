import requests,sys
from bs4 import BeautifulSoup as BS

from multiprocessing import Process
from multiprocessing.queues import SimpleQueue
import urllib2,copy

def read_page(url,outq,cursor=None):
    if cursor is not None:
        url1 = "%s?cursor=%s"%(url,cursor)
    else:
        url1 = url
    r = requests.get(url1)
    rv = r.text
    outq.put(rv[:100])
    #outq.put(u'hi')
def get_cursors(text):
    soup = BS(text,'html.parser')
    eles = soup.select("div.NS_backers__backing_row")
    data = [ele['data-cursor'] for ele in eles]
    return data
if __name__ == "__main__":
    #test_url = "https://www.kickstarter.com/projects/1935800597/wheely-a-wheelchair-accessible-guide/backers"
    url = "https://www.kickstarter.com/projects/502093706/unsounded-comic-volume-2/backers"
    print "start"
    assert url.endswith("backers"),""
    param = {}
    all_data = []
    #first page
    #c = requests.get(url)
    outq = SimpleQueue()
    p = Process(target=read_page,args=(url,outq,))
    p.start()
    p.join()
    sys.stdout.write(".")
    #cursors = get_cursors(outq.get())
    ##c.close()
    #all_data.extend(cursors)
    #print len(all_data)
    #while len(cursors) > 0:
        ##param['cursor'] = cursors[-1]
        #print cursors[-1]
        ##c = requests.get(url,params=param)
        #p = Process(target=read_page,args=(url,outq,cursors[-1]))
        #p.start()
        #p.join()
        #sys.stdout.write(",")
        #cursors = get_cursors(outq.get())
        ##c.close()
        #all_data.extend(cursors)
        #print len(all_data)
    print "end"