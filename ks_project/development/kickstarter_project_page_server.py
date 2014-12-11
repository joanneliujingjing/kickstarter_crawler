'''
Author: DrTagKim
'''
import kickstarter_project_analysis_server as KPAS
import kickstarter
import sys,os,Queue,time,glob,csv
import shutil,sqlite3

# =================================================== #
DATABASE_DIR = "current_project_page_sqlite3"
DATABASE_NAME = "kickstarter_project_sqlite3.db"
NUMBER_OF_WORKERS = 10
INSPECTION_INTERVAL = 10 #seconds
QUIETLY = True
IMAGE = False
# =================================================== #
def create_db():
    db_name = "%s/%s" % (DATABASE_DIR,DATABASE_NAME,)
    con = sqlite3.connect(db_name)
    sql = """ CREATE TABLE IF NOT EXISTS project (
                recording_date TEXT,
                identifier TEXT,
                title TEXT,
                founder TEXT,
                url TEXT,
                condition_desc TEXT,
                full_description TEXT,
                risks TEXT,
                video_fname TEXT,
                video_length NUMBER,
                number_of_backers NUMBER,
                goal NUMBER,
                percent_raised NUMBER,
                amount_pledged NUMBER,
                currency TEXT,
                duration NUMBER,
                end_time TEXT,
                hours_remaining NUMBER,
                facebook_count NUMBER,
                minimum_pledge TEXT,
                reward_variety_of_offer NUMBER,
                reward_avg_money NUMBER,
                reward_std_money NUMBER,
                reward_min_money NUMBER,
                reward_max_money NUMBER,
                reward_total_money NUMBER,
                reward_avg_num_backer NUMBER,
                reward_std_num_backer NUMBER,
                reward_min_num_backer NUMBER,
                reward_max_num_backer NUMBER,
                reward_total_num_backer NUMBER,
                projects_reward_result BLOB,
                images BLOB,
                image_fnames BLOB,
                backers BLOB,
                page_compressed BLOB,
                CONSTRAINT update_rule UNIQUE (recording_date,identifier) ON CONFLICT REPLACE);
          """
    cur = con.cursor()
    cur.execute(sql)
    con.commit()
    con.close()
def main():
    if not os.path.exists(DATABASE_DIR):
        os.mkdir(DATABASE_DIR)
    create_db()
    inque = Queue.Queue()
    workers = []
    db_name = "%s/%s" % (DATABASE_DIR,DATABASE_NAME,)
    for i in range(NUMBER_OF_WORKERS):
        worker = kickstarter.KsPageAnalyzerWrapper(inque,db_name,quietly=QUIETLY,has_image=IMAGE)
        worker.setDaemon(True)
        workers.append(worker)
        worker.start()
    sys.stdout.write("KICKSTARTER PAGE DATA COLLECTOR IS READY...\n")
    sys.stdout.write("NUMBER OF AGENTS = %d\n" % NUMBER_OF_WORKERS)
    sys.stdout.flush()
    while 1:
        try:
            input_files = glob.glob("%s/*.inv"%(KPAS.ONGOING_DIR,)) #get inventory
            all_input = []
            for input_file in input_files:
                with open(input_file) as f:
                    reader = csv.reader(f,delimiter='\t',lineterminator='\n')
                    for row in reader:
                        all_input.append(row[0])
                os.remove(input_file)
            for inp in all_input:
                inque.put(inp)
            time.sleep(INSPECTION_INTERVAL)
            sys.stdout.write("\rDATA IN QUEUE: %d" % inque.qsize())
            sys.stdout.flush()
        except KeyboardInterrupt:
            break
    for worker in workers:
        worker.stop()
        worker.kpa.terminate()
    inque.join()
    sys.stdout.write("\nGOOD BYE\n")
    sys.stdout.flush()
if __name__ == "__main__":
    main()