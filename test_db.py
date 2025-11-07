import MySQLdb

try:
    conn = MySQLdb.connect(
        host='localhost',
        user='root',
        password='sagar123',
        database='ngo_management_system'
    )
    print('MySQL connection established successfully')
    cur = conn.cursor()
    cur.execute("SELECT 1")
    result = cur.fetchone()
    print(f"Test query result: {result}")
    cur.close()
    conn.close()
except Exception as e:
    print(f"Error: {e}")
