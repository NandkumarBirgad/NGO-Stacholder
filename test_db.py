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

    # Check if uri column exists in volunteer table
    cur.execute("DESCRIBE volunteer")
    columns = cur.fetchall()
    column_names = [col[0] for col in columns]
    if 'uri' not in column_names:
        print("Adding uri column to volunteer table...")
        cur.execute("ALTER TABLE volunteer ADD COLUMN uri VARCHAR(255)")
        print("uri column added to volunteer table")
    else:
        print("uri column already exists in volunteer table")

    # Check if uri column exists in donor table
    cur.execute("DESCRIBE donor")
    columns = cur.fetchall()
    column_names = [col[0] for col in columns]
    if 'uri' not in column_names:
        print("Adding uri column to donor table...")
        cur.execute("ALTER TABLE donor ADD COLUMN uri VARCHAR(255)")
        print("uri column added to donor table")
    else:
        print("uri column already exists in donor table")

    # Check if uri column exists in beneficiary table
    cur.execute("DESCRIBE beneficiary")
    columns = cur.fetchall()
    column_names = [col[0] for col in columns]
    if 'uri' not in column_names:
        print("Adding uri column to beneficiary table...")
        cur.execute("ALTER TABLE beneficiary ADD COLUMN uri VARCHAR(255)")
        print("uri column added to beneficiary table")
    else:
        print("uri column already exists in beneficiary table")

    cur.execute("SELECT 1")
    result = cur.fetchone()
    print(f"Test query result: {result}")
    cur.close()
    conn.close()
except Exception as e:
    print(f"Error: {e}")
