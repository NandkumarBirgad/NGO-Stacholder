import pymysql

try:
    conn = pymysql.connect(
        host="gateway01.ap-southeast-1.prod.aws.tidbcloud.com",
        port=4000,
        user="4MtRB8TtYgRCw9d.root",
        password="zjhDXJr1dnTNH0F7",
        database="test",
        ssl={"fake_flag_to_enable_tls": True},
        ssl_verify_cert=False
    )
    print("Connected!")
except Exception as e:
    print("Error:", e)
