import requests
import sqlite3
import sys
import re
from sqlite3 import Error



# args
PET_API = 'https://petition.president.gov.ua/petition/{}/votes/{}/json'

print 'Usage: python participants.py pet_id [out_html [out_db]]'

argc = len(sys.argv)
if argc == 1:
    sys.exit()

print 'Number of arguments:', argc, 'arguments.'
print 'Argument List:', str(sys.argv)

pet_id = sys.argv[1]
out_html = "output.html"
out_db = "output.db"

if argc > 2:
    out_html = sys.argv[2]
    if argc > 3:
        out_db = sys.argv[3]



# classes
class Participant:
    def __init__(self, number, name, date):
        self.number = number
        self.name = name
        self.date = date



# download
page_list = []
page = 0
while True:
    url = PET_API.format(pet_id, page)
    sys.stdout.write("\r%d" % page)
    sys.stdout.flush()
    r = requests.get(url)
    if r.status_code != 200:
        break
    try:
        page_list.append(r.json())
    except:
        break
    page += 1

print('\n--\n{} pages'.format(len(page_list)))

# parse
part_list = []
for page in page_list:
    s = page["table_html"]
    rows = s.split("<div class=\"table_row\">")
    for row in rows:
        r1 = re.findall(r"<div class=\"table_cell number\">(.*)<\/div>", row)
        r2 = re.findall(r"<div class=\"table_cell name\">(.*)<\/div>", row)
        r3 = re.findall(r"<div class=\"table_cell date\">(.*)<\/div>", row)
        if len(r1) == 1 and len(r2) == 1 and len(r3) == 1:
            part_list.append(Participant(r1[0], r2[0], r3[0]))

print('--\n{} participants'.format(len(part_list)))



# make html
html = "<!DOCTYPE html><html><head><style>" \
       ".table { display: table; width: auto; }"\
       ".table_row { display: table-row; width: auto; clear: both; }"\
       ".table_cell { float: left; display: table-column; width: 200px; }"\
       "</style></head><body><div class=\"table\">"

for p in part_list:
    html += \
        "<div class=\"table_row\">"\
            "<div class=\"table_cell\">" + p.number + "</div>"\
            "<div class=\"table_cell\">" + p.name + "</div>"\
            "<div class=\"table_cell\">" + p.date + "</div>"\
        "</div>"

html += "</div></body></html>"

# write html
print('writing {}'.format(out_html))

with open(out_html, "w") as text_file:
    text_file.write(html.encode('utf-8'))



# sqlite utils
def create_connection(db_file):
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        print 'sqlite3', sqlite3.version
    except Error as e:
        print(e)
    return conn

def create_table(conn, create_table_sql):
    try:
        c = conn.cursor()
        c.execute(create_table_sql)
    except Error as e:
        print(e)

def create_participant(conn, participant):
    sql = ''' INSERT INTO participants(number,name,date)
              VALUES(?,?,?) '''
    cur = conn.cursor()
    cur.execute(sql, participant)
    return cur.lastrowid

# write db
print('writing {}'.format(out_db))

conn = create_connection(out_db)
if conn is not None:
    create_table(conn, """ CREATE TABLE IF NOT EXISTS participants (
                                        id integer PRIMARY KEY,
                                        number text NOT NULL,
                                        name text NOT NULL,
                                        date text NOT NULL
                                    ); """)
    with conn:
        for p in part_list:
            create_participant(conn, (p.number, p.name, p.date))
else:
    print("Error! cannot create the database connection.")
