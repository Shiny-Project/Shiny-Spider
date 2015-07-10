import config,meta
from log import Log 
import pymysql.cursors
import sys

def main():
    sys.path.append("spiders");
    Logger = Log(connection);
    if (len(sys.argv) == 1):
        #如果是命令行调用 走下面的流程
        print('''
            Usages:

            Main.py <command> [params]

            Command:

            renew <api_id> : renew the data of the API

            Others:

            --version : show version information
        ''');
        exit();
    elif (len(sys.argv) >= 2):
        command = sys.argv[1];
        if (command == 'renew'):
            if (len(sys.argv) >= 3):
                api_id = sys.argv[2];
                Logger.info(u'尝试刷新' + api_id);
                #未完成部分

        elif (command == '-version' or command == '--version' or command == 'version'):
            print(meta.project + ' ' + meta.version);
            exit();
    
    try:
        with connection.cursor() as cursor:
            sql = 'SELECT * FROM data'
            cursor.execute(sql)
            result = cursor.fetchall()
            print(result)

    except:
        print('ERROR')
if __name__ == "__main__":
    connection = pymysql.connect(host = 'localhost', user = config.DATABASE_USER, passwd = config.DATABASE_PASSWORD, db = config.DATABASE_NAME)
    main();

connection = pymysql.connect(host = 'localhost', user = config.DATABASE_USER, passwd = config.DATABASE_PASSWORD, db = config.DATABASE_NAME)




