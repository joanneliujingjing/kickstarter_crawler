import socket,sys,os
import kickstarter
import kickstarter_server_port as KSP
import Queue
from threading import active_count
from colorconsole import terminal
'''
pip install colorconsole
'''

REPOSITORY_NAME = 'repo_project'
CONTINUE_ = False # if True, only collect in-progress projects

screen = terminal.get_terminal() #get the currrent screen
screen.clear()
sys.stdout.flush()
def create_repository():
    if not os.path.exists(REPOSITORY_NAME):
        os.mkdir(REPOSITORY_NAME)
def display_hello():
    
    screen.gotoXY(0,1)
    screen.cprint(15,0,"= = = = = = = = = = = = = = = = = = = = = = = = = ")
    sys.stdout.flush()
    screen.gotoXY(0,2)
    screen.cprint(10,0,"         KICKSTARTER PROJECT PAGE COLLECTOR")
    sys.stdout.flush()
    screen.gotoXY(0,3)
    screen.cprint(15,0,"= = = = = = = = = = = = = = = = = = = = = = = = = ")
    sys.stdout.flush()
    screen.gotoXY(0,4)
    screen.cprint(3,0,"Server Starts")
    sys.stdout.flush()
if __name__ == "__main__":
    display_hello()
    create_repository()
    probes = []
    inque = Queue.Queue()
    # make four...
    for i in range(4):
        probe = kickstarter.KsProjectProbe(inque,screen,loc_id = (i+5),continue_=CONTINUE_)
        probe.repository = "%s/"%(REPOSITORY_NAME,)
        probe.setDaemon(True)
        probes.append(probe)
        probe.start() 
    server = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    server.bind(('',KSP.PROJECT_PROBE_PORT))
    server.listen(1) #only one
    while 1:
        try:
            conn, addr = server.accept()
            data = conn.recv(1024*1024) # 1mb data
            #probe.add(data)
            data = eval(data)
            inque.put(data)
        except KeyboardInterrupt:
            screen.gotoXY(0,20)
            screen.cprint(12,0,"Server Stops")
            sys.stdout.flush()
            break
        except socket.error, msg:
            print msg
            screen.gotoXY(0,20)
            screen.cprint(12,0,"Socket error")
            sys.stdout.flush()
            break
    #inque.join() #no more data
    for probe in probes: #terminate threads
        probe.stop()
        probe.join()
    screen.gotoXY(10,22)
    screen.cprint(15,0,"Bye")
    sys.stdout.flush()
    screen.reset()