#coding:utf8
import os
import sqlite3

cur_path = os.path.dirname(__file__)
_db_file = os.path.join(cur_path, 'data.db')

sqlite_conn = sqlite3.connect(_db_file)
sqlite_cursor = sqlite_conn.cursor()

def close():
    u'''关闭数据库'''
    sqlite_cursor.close()
    sqlite_conn.close()
    return

def create_table():
    u'''创建表'''
    sql = '''create table `FILE_STATUS` (
              `filename` varchar(255) primary key,
              `st_mtime` int(11),
              `last_warning` int(11)
            )'''
    sqlite_cursor.execute(sql)
    return 1

def auto_commit(func):
    u'''commit 装饰器'''
    def wrap(*args, **kwargs):
        result = func(*args, **kwargs)
        sqlite_conn.commit()
        return result
    return wrap

@auto_commit
def upsert(data, File):
    u'''更新或者添加一个预警文件'''
    if data['update'] == 0:
        sql = '''insert into `FILE_STATUS` (filename, st_mtime, last_warning)
                 values ("%s", %d, %d)'''%(
                 File.filename, data['st_mtime'], data['last_warning']
                 )
        sqlite_cursor.execute(sql)
    else:
        sql = '''update `FILE_STATUS` set st_mtime=%d, last_warning=%d where
                 filename="%s";'''%(
                 data['st_mtime'], data['last_warning'],File.filename
                )
        sqlite_cursor.execute(sql)
    return 1

@auto_commit
def delete(File):
    u'''删除预警文件'''
    sql = '''delete from `FILE_STATUS` where filename="%s"'''%File.filename
    sqlite_cursor.execute(sql)
    return 1

def get_delete_files(Files):
    u'''获取应该被删除的文件'''
    files = [File.filename for File in Files]
    sql = '''select filename from `FILE_STATUS`'''
    sqlite_cursor.execute(sql)
    infos = sqlite_cursor.fetchall()
    old_files = [info[0] for info in infos]
    delete_files = set(old_files) - set(files)
    delete_files = [File for File in Files if File.filename in delete_files]
    return list(delete_files)

def is_new_file(File):
    u'''判断是否为新文件'''
    st_mtime = File.st_mtime
    sql = 'select st_mtime, last_warning from FILE_STATUS \
            where filename="%s";'%File.filename
    sqlite_cursor.execute(sql)
    info = sqlite_cursor.fetchall()

    result = {
            'status':1,
            'st_mtime':st_mtime,
            'last_warning':File.last_warning,
            'update':0,
            }
    if info:
        if info[0][0] < st_mtime:
            result.update({'update':1})
        else:
            result.update({'status':0})
    return result



if __name__ == '__main__':
    #create_table()
    pass

