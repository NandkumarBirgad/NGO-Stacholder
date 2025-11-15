import MySQLdb

conn = MySQLdb.connect(host='localhost', user='root', password='sagar123', database='ngo_management_system')
cur = conn.cursor()
cur.execute('ALTER TABLE event ADD COLUMN status ENUM("Planning", "Active", "Completed", "On Hold") DEFAULT "Planning"')
conn.commit()
cur.close()
conn.close()
print('Status column added')
