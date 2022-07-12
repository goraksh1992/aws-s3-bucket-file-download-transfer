from urllib import request
from celery import shared_task
from common.views import connection, target_db_connection
import datetime
import logging

# Get an instance of a logger
logger = logging.getLogger(__name__)


def insert_last_inserted_id(data, cursor, target_cursor):
    cursor.execute(f"SELECT id from {data['target_table_name']} ORDER BY id DESC LIMIT 1")
    lastInsertedId = cursor.fetchone()
    cursor.execute("INSERT INTO last_inserted_id (id) VALUES (%s)", (lastInsertedId[0], ))
    target_cursor.commit()

def get_last_inserted_id(cursor, target_cursor):
    cursor.execute("SELECT id from last_inserted_id ORDER BY id DESC LIMIT 1")
    lastInsertedId = cursor.fetchone()
    if lastInsertedId:
        return lastInsertedId
    return None

def get_record(data, arg, cursor2):
    cursor2.execute(f'SELECT * FROM {data["target_table_name"]} where id = {arg[0]}')
    recordFound = cursor2.fetchone()
    if not recordFound:
        return arg


@shared_task
def get_records(data, flag=True, start=0, end=1000):
    print(data['database_name'])
    try:
        if flag:

            # db connection
            transfer_cursor = connection(
                data['database_name'],
                data['username'],
                data['password'],
                data['host'],
                data['port']
            )

            # Target DB
            target_cursor = target_db_connection(
                data['target_database_name'],
                data['target_username'],
                data['target_password'],
                data['target_host'],
                data['target_port']
            )

            # Create cursor
            cursor = transfer_cursor.cursor()
            cursor2 = target_cursor.cursor()

            lastId = get_last_inserted_id(cursor2, target_cursor)

            # Get records
            if lastId:
                cursor.execute(f'''
                    SELECT * FROM {data['table_name']} WHERE upload_user_id='33' AND id > {lastId[0]} ORDER BY id DESC LIMIT {end} OFFSET {start}
                ''')
            else:
                cursor.execute(f'''
                    SELECT * FROM {data['table_name']} WHERE upload_user_id='33' ORDER BY id DESC LIMIT {end} OFFSET {start}
                ''')

            result = cursor.fetchall()
            args = ','.join(cursor.mogrify("(%s,%s,%s,%s,%s,%s,%s,%s)", get_record(data, i, cursor2)).decode('utf-8')
                        for i in result)

            if result:

                cursor2.execute(f"INSERT INTO {data['target_table_name']} VALUES " + (args))
                target_cursor.commit()

                get_records(data, flag=True, start=start+end, end=5)

            else:
                
                insert_last_inserted_id(data, cursor2, target_cursor)
                get_records(data, flag=False)

        return "Done"
    
    except Exception as e:
        print(e)
        insert_last_inserted_id(data, cursor2, target_cursor)

        logger.warning('Error:'+str(datetime.datetime.now())+':'+str(e))
        return e
        
