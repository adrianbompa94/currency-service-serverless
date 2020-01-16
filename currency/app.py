import json
import requests
import pymysql.cursors
import time

import os

env_var = os.environ


def lambda_handler(event, context):
    connection = get_database_connection()
    if not connection:
        raise Exception('Database Connection Error', 'No connection available to the database')

    # we get new currency rates first, if there are any issues with API, we will not update end_time for current rates
    currency_rates = get_currency_rates()
    if not currency_rates:
        raise Exception('Unable to get currency rates')
    
    cursor = connection.cursor()

    print('Update end_date for current currenvies...')
    sql_update_query = """update currency set end_time = %s where end_time is NULL """
    sql_update_data = (time.strftime('%Y-%m-%d %H:%M:%S'))
    
    try:
        cursor.execute(sql_update_query, sql_update_data)
        connection.commit()
    except Exception as e: 
        print('Error occured when updating currency end_time: ' + str(e))
        raise e
    else: 
        print('Current currency values updated succesfully')

    print('Inserting new currency values...')

    try:
        for currency_code, currency_value in currency_rates['rates'].items():
            formatted_value = format(currency_value, '.2f')

            sql_insert_query = """insert into currency (code, value, start_time, created) VALUES (%s,%s,%s,%s)"""
            sql_insert_data = (currency_code, formatted_value, time.strftime('%Y-%m-%d %H:%M:%S'),time.strftime('%Y-%m-%d %H:%M:%S'))

            cursor.execute(sql_insert_query, sql_insert_data)
            connection.commit()
    except Exception as e:
        print('Error occured when inserting new currency rates: ' + str(e))
    finally:
        if (connection):
            cursor.close()
            connection.close()
            print('Mysql Connection closed!')

    return {
        "statusCode": 200
    }

def get_database_connection():
    try:
        connection = pymysql.connect(host=env_var['org_db_host_name'],
                                     user=env_var['org_db_username'],
                                     password=env_var['org_db_password'],
                                     database='organisation',
                                     cursorclass=pymysql.cursors.DictCursor)

    except Exception as e: 
        print('Unable to connect to mysql database :' + str(e) )
    else:
        return connection


def get_currency_rates():
    try:
        exchange_rates = requests.get("https://api.exchangeratesapi.io/latest?base=GBP")
    except requests.RequestException as e:
        print('Error occured when requesting currency rates from API: ' + e)

        raise e
    else:
        print('Currency rates returned successfully')
    
    return json.loads(exchange_rates.content)