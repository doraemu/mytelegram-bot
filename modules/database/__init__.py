import time
import json
import os

PATH = os.path.dirname(os.path.realpath(__file__)) + '/'

DB_LOCK = []

def save(dbname, data, lock=False):
    if lock:
        global DB_LOCK        
        while DB_LOCK[dbname]: time.sleep(0.05)
        DB_LOCK[dbname] = True
    f = open(PATH + dbname + '.json', 'w', encoding='utf-8')
    f.write(json.dumps(data, ensure_ascii=False))
    f.close()
    if lock: DB_LOCK[dbname] = False
    
def read(dbname):
    data = json.loads(open(PATH + dbname + '.json', 'r').read())
    return data