'''
Author: DrTagKim
'''
import sys,os
import kickstarter
import kickstarter_server_port as KSP
import kickstarter_project_probe_server as KPAS
LISTENER_DIR = KPAS.REPOSITORY_NAME
SPEAKER_DIR = "result_project_analysis"
RESERVER_DIR = "warehouse_project"
ONGOING_DIR = "current_project"
def main():
    analyzer = kickstarter.ksProjectPageAnalyzer(ongoing_dir = ONGOING_DIR,
                                                 listener_dir = LISTENER_DIR,
                                                 speaker_dir = SPEAKER_DIR,
                                                 reserver_dir = RESERVER_DIR,
                                                 listen_duration = 5) #seconds
    analyzer.setDaemon(True)
    analyzer.start()
    analyzer.join()
if __name__ == "__main__":
    main()