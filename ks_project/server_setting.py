'''
KICKSTARTER SERVER SETTING
AUTHOR: DRTAGKIM
2014
'''
# GENERAL SETTING ===============================
HAS_IMAGE = False
QUIETLY = False
RECOVER_TRIAL = -1
# DATABASE SETTING ==============================
DATABASE_NAME = "sample.db" #SQLite3 database name (main)
CREATE_SCHEMA = False
SQLITE_MYSQL = "mysql" # (sqlite / mysql)
LOCK_TIMEOUT = 120 #seconds
# MYSQL SETTING =================================
HOST = "localhost"
DATABASE = "kickstarter_new" # database name
USER = "root"
PASSWORD = "900330"

# SCHEDULE ======================================
PROJECT_LOG_START_HOUR = '0' # project log starts at
PROJECT_LOG_START_MIN = '0' #0-59
PROJECT_LOG_START_SEC = '59' #0-59

PROJECT_PAGE_START_HOUR = '3'
PROJECT_PAGE_START_MIN = '0'
PROJECT_PAGE_START_SEC = '59'

RECOVER_ERROR_HOUR = '9'
RECOVER_ERROR_MIN = '0'
RECOVER_ERROR_SEC = '59'

VACUUM_DATABASE_HOUR = '15'
VACUUM_DATABASE_MIN = '0'
VACUUM_DATABASE_SEC = '59'


# PROJECT_LOG_SERVER SETTING ====================
# Data collection range. If True, full collection (from the beginning); othersie, False
SCRAP_FULL = True  
# Page call again if the server responses too late.
PAGE_REQUEST_TRIAL = 10 # how many calls if it fails?
PROJECT_LOG_PORT = 10001
PROJECT_LOG_SERVER_THREAD_POOL = 15 
CATEGORIES = ["1","2","3","4","5","6","7","8","9","10","11","12","13","14","15"]

# PROJECT_PAGE_SERVER SETTING ===================
PROJECT_PAGE_PORT = 10002
PROJECT_PAGE_SERVER_THREAD_POOL = 20
BACKER_CONNECTION_RECOVER = 10 # second
