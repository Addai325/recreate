import MySQLdb

try:
    connection = MySQLdb.connect(
        host="Addai325.mysql.pythonanywhere-services.com",
        user="Addai325",
        passwd="Extra111??!!",
        db="Addai325$omniblogs"
    )
    print("Connection successful!")
except MySQLdb.OperationalError as e:
    print(f"Error: {e}")
