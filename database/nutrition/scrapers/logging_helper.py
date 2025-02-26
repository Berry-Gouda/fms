import pandas as pd
from datetime import datetime

logging_DF = pd.DataFrame(columns=['Error Message', 'Line Number', 'URL Causing Error', 'time'])
LOGGING_PATH = '/home/bg-labs/bg_labs/fms/database/nutrition/scrapers/logs/log_'

def add_to_log(mssg: str, url: str, line: str):
    global logging_DF
    
    new_row = {'Error Message': mssg, 'Line Number': line, 'URL Causing Error': url,  'time': datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    logging_DF.loc[len(logging_DF)] = new_row

def write_to_file():
    global LOGGING_PATH, logging_DF

    path = LOGGING_PATH + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + '.csv'
    logging_DF.to_csv(path)
