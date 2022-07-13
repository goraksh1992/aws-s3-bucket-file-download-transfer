from urllib import request
from celery import shared_task
from celery_progress.backend import ProgressRecorder
from common.views import connection, target_db_connection
import datetime
import logging

# Get an instance of a logger
logger = logging.getLogger(__name__)


def insert_last_inserted_id(data, cursor, target_cursor):
    cursor.execute(f"SELECT id from {data['target_table_name']} ORDER BY id DESC LIMIT 1")
    lastInsertedId = cursor.fetchone()
    if lastInsertedId:
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


@shared_task(bind=True)
def get_records(self, data={}, flag=True, start=0, end=5, count=0):
    # progress_recorder = ProgressRecorder(self)
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

            # lastId = get_last_inserted_id(cursor2, target_cursor)

            # Get records
            # if not lastId:
            #     cursor.execute(f'''
            #         SELECT * FROM {data['table_name']} WHERE id > {lastId[0]} ORDER BY id DESC LIMIT {end} OFFSET {start}
            #     ''')    
            # else:
            #     cursor.execute(f'''
            #         SELECT * FROM {data['table_name']} ORDER BY id DESC LIMIT {end} OFFSET {start}
            #     ''')

            # cursor.execute(f'''
            #         SELECT * FROM {data['table_name']}
            #     ''')
            # all_records = cursor.fetchall()

            cursor.execute(f'''
                    SELECT * FROM {data['table_name']} ORDER BY id DESC LIMIT {end} OFFSET {start}
                ''')
            result = cursor.fetchall()

            args = ','.join(cursor.mogrify("(%s,%s,%s,%s,%s,%s,%s,%s)", get_record(data, i, cursor2)).decode('utf-8')
                        for i in result)
            
            print(f"Start: {start}, End: {end} ")
            
            if result:
                # sql = """
                #         INSERT INTO models 
                #             (id, user_id, upload_user_id, token, bucket, meta, created_at, updated_at) 
                #         VALUES 
                #             (%s,%s,%s,%s,%s,%s,%s,%s)
                #     """
                # for index, record in enumerate(result):

                #     # Check Record Exist 
                #     cursor2.execute(f'SELECT * FROM models where id = {record[0]}')
                #     recordFound = cursor2.fetchone()

                #     if not recordFound:
                #         cursor2.execute(sql, record)
                #         target_cursor.commit()
                    
                    
                #     count += 1
                    
                #     if index+1 == len(result):
                #         progress_recorder.set_progress(count, len(all_records))
                #         get_records(data=data, flag=True, start=start+end, end=5, count=count)

                cursor2.execute(f"INSERT INTO {data['target_table_name']} VALUES " + (args))
                target_cursor.commit()

                get_records(data=data, flag=True, start=start+end, end=5, count=count)

                # progress_recorder.set_progress(count, len(all_records))

            else:

                # insert_last_inserted_id(data, cursor2, target_cursor)
                print("closed====>")
                get_records(data, flag=False)

        return "Done"
    
    except Exception as e:
        print(e)
        # insert_last_inserted_id(data, cursor2, target_cursor)

        logger.warning('Error:'+str(datetime.datetime.now())+':'+str(e))
        return e
        
