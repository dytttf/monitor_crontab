#coding:utf8
import os
import time
import sqlite3

try:
    from Api import log
except:
    import log

cur_path = os.path.dirname(__file__)
_db_file = os.path.join(cur_path, 'data.db')

sqlite_conn = sqlite3.connect(_db_file)
sqlite_cursor = sqlite_conn.cursor()

def auto_commit(func):
    u'''commit 装饰器'''
    def wrap(*args, **kwargs):
        result = func(*args, **kwargs)
        sqlite_conn.commit()
        return result
    return wrap

def close():
    u'''关闭数据库'''
    sqlite_cursor.close()
    sqlite_conn.close()
    return

@auto_commit
def create_table():
    u'''创建表 保存预警文件信息'''
    sql = '''create table `FILE_STATUS` (
              `filename` varchar(255) primary key,
              `st_mtime` int(11),
              `last_warning` int(11)
            )'''
    try:
        sqlite_cursor.execute(sql)
    except Exception as e:
        if 'already exists' in str(e):
            pass
        else:
            log.logger.debug(e)
    return 1

@auto_commit
def create_table_process_info():
    u'''创建表用来保存进程信息  主要用来监测心跳'''
    sql = '''create table `PROCESS` (
                `p_name` varchar(255) primary key,
                `alive_time` int(11)
            )'''
    try:
        sqlite_cursor.execute(sql)
    except Exception as e:
        if 'already exists' in str(e):
            pass
        else:
            log.logger.debug(e)
    return 1

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
def delete(filename):
    u'''删除预警文件'''
    sql = '''delete from `FILE_STATUS` where filename="%s"'''%filename
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

def get_heart(p_name):
    u'''获取心跳时间'''
    sql = '''select `alive_time` from `PROCESS` where `p_name`="%s"'''%p_name
    sqlite_cursor.execute(sql)
    info = sqlite_cursor.fetchall()
    return info[0][0] if info else 0

@auto_commit
def update_heart(p_name):
    u'''更新心跳时间'''
    insert_sql = '''insert into `PROCESS` (`p_name`, `alive_time`) values
                        ("%s", %d)'''%(
                        p_name, time.time()
                        )
    update_sql = '''update `PROCESS` set `alive_time`=%d
                    where `p_name`="%s"'''%(
                    time.time(), p_name
                    )
    try:
        sqlite_cursor.execute(update_sql)
        resp = sqlite_cursor.rowcount
        if resp < 1:
            sqlite_cursor.execute(insert_sql)
    except:
        pass
    return 1

create_table()
create_table_process_info()

if __name__ == '__main__':
    #create_table()
    #update_heart("main")
    #print get_heart("main")
    pass

