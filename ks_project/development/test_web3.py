'''
WEB3 TEST
'''
from web3 import PhantomBrowser as PB
from bs4 import BeautifulSoup as BS

cnt_projects = 0
breaker = False

def facebook_filter(pb):
   rv = False
   page = pb.get_page_source()
   soup = BS(page,'html.parser')
   eles = soup.select("li.facebook.mr2 .count")
   if len(eles) > 0:
      rv = len(eles[0].text.strip()) > 0
   return rv   
def filter_down(pb):
   global cnt_projects
   rv = False
   page = pb.get_page_source()
   soup = BS(page,'html.parser')
   eles = soup.select("div.NS_backers__backing_row")
   new_size = len(eles)
   if cnt_projects < new_size:
      cnt_projects = new_size
      rv = True
   return rv
if __name__ == "__main__":
   url= "https://www.kickstarter.com/projects/1900602681/fireball-newsflash-crosswords/backers"
   pb = PB()
   #pb.goto(url,facebook_filter)
   pb.goto(url)
   pb.capture('sample1.png')
   old = 0
   while 1: 
      pb.scroll_down(filter_func=filter_down)
      p = pb.get_page_source()
      s = BS(p,'html.parser')
      f = s.select("div.NS_backers__backing_row .meta a")
      new_ = len(f)
      print new_
      if (new_ % 50) != 0 or new_ == 0:
         break
   pb.capture('sample2.png')
   del pb
   print "done"
    