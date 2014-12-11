import sqlite3,sys

class KickstarterDbConnector:
    def __init__(self,out_db_name):
        self.out_db_name = out_db_name
        self.sql_create_staic = """
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
                CONSTRAINT update_rule UNIQUE(project_id) ON CONFLICT IGNORE);
        """
        self.sql_create_dynamic = """
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
        self.sql_insert_static = """
            INSERT INTO project_benchmark (
            project_id,project_name,project_slug,country,created_at_unix,created_at_str,
                        project_url,desc,photo,category_parent,category_name,category_id,launched_at_unix,launched_at_str,
                        goal,currency,backers,pledged,state,currently,state_changed_unix,
                        state_changed_str,deadline_unix,deadline_str,creator_id,creator_url_slug,
                        creator_name,creator_url_api,creator_url_web,location_country,
                        location_name,location_slug,location_nearby_api,location_nearby_web1,location_nearby_web2
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?);
        """
        self.sql_insert_dynamic = """
            INSERT INTO project_history (
                ts_id,project_id,backers,pledged,state,currently,
                state_changed_unix,state_changed_str,deadline_unix,deadline_str
            ) VALUES (?,?,?,?,?,?,?,?,?,?);
        """
        self.sql_read_create_staic = """
            SELECT * FROM project_benchmark;
        """
        self.sql_read_dynamic = """
            SELECT * FROM project_history;
        """
        self.create()
    def create(self):
        con = sqlite3.connect(self.out_db_name)
        #create schema
        cur = con.cursor()
        cur.execute(self.sql_create_staic)
        con.commit()
        cur.execute(self.sql_create_dynamic)
        con.commit()
        con.close()
    def trans(self,from_db_name):
        sys.stdout.write("T...")
        sys.stdout.flush()
        con = sqlite3.connect(from_db_name)
        con_out = sqlite3.connect(self.out_db_name)
        cur = con.cursor()
        cur_out = con_out.cursor()
        cur.execute(self.sql_read_create_staic)
        data = cur.fetchall()
        cur_out.executemany(self.sql_insert_static,data)
        con_out.commit()
        cur.execute(self.sql_read_dynamic)
        data = cur.fetchall()
        cur_out.executemany(self.sql_insert_dynamic,data)
        con_out.commit()
        cur_out.close()
        cur.close()
        con_out.close()
        con.close()
        sys.stdout.write("OK\n")
        sys.stdout.flush()