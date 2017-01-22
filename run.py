# coding:utf8
import os
import time
import argparse
import threading
from multiprocessing import Process, Event

import db_sqlite
try:
    from Api import log
except:
    import log
import warn_file


# 获取当前文件路径
cur_path = os.path.dirname(__file__)

# 预警脚本存放路径
warn_dir = os.path.join(cur_path, 'warn_dir')
if not os.path.exists(warn_dir):
    os.mkdir(warn_dir)

# pid 文件
pid_file = os.path.join(cur_path, 'pid')

wait_join_timeout = 10


def check_warn_dir_changes():
    u'''
    监测思路：
        文件增减
        文件修改 os.stat.st_mtime
        '''
    old_files = []
    new_files = []
    delete_files = []
    all_files = []
    for root, dirs, files in os.walk(warn_dir):
        for filename in files:
            if filename.startswith('.'):
                continue
            abs_filename = os.path.join(root, filename)
            try:
                File = warn_file.WarnFile(abs_filename)
            except Exception as e:
                log.logger.exception(e)
                log.logger.error(u"初始化预警文件失败 file: %s error:%s" % (
                                                        abs_filename, e
                                    ))
                continue
            all_files.append(File)
            resp = db_sqlite.is_new_file(File)
            status = resp['status']
            if status:
                db_sqlite.upsert(resp, File)
                new_files.append(File)
            else:
                old_files.append(File)
    delete_files = db_sqlite.get_delete_files(all_files)
    return old_files, new_files, delete_files


def create_pid():
    u'''创建pid文件'''
    if os.path.exists(pid_file):
        return 0
    pid = os.getpid()
    try:
        with open(pid_file, 'w') as f:
            f.write(str(pid))
    except Exception as e:
        log.logger.exception(e)
        return 0
    return 1


def check_stop():
    u'''判断是否需要停止进程'''
    if not os.path.exists(pid_file):
        log.logger.error(u"pid文件不存在")
        return 1
    else:
        cur_pid = os.getpid()
        with open(pid_file) as f:
            pid = int(f.read())
        if cur_pid != pid:
            log.logger.error(u"pid 不一致")
            return 1
    return 0


def update_heart(p_name='main'):
    u'''更新心跳'''
    db_sqlite.update_heart(p_name)
    return 1


def check_heart_timeout(p_name="main"):
    u'''监测心跳是否超时'''
    last_time = db_sqlite.get_heart(p_name)
    if time.time() - last_time > 3 * 60:
        return 1
    return 0

def kill_all():
    pid = str(os.getpid())
    exists_python_process_pids = os.popen("ps -ef| grep python | awk '{print $2}' | xargs").read().split()
    for e_pid in exists_python_process_pids:
        if e_pid != pid:
            os.system("kill -9 %s"%e_pid)
    return 1


def work():
    u'''主进程执行函数'''
    if not create_pid():
        log.logger.error(u"pid 文件已存在或创建失败")
        return 0
    process_dict = {}
    while 1:
        if check_stop():
            for filename in process_dict:
                stopEvent = process_dict[filename]['event']
                process = process_dict[filename]['process']
                stopEvent.set()
                # 更新心跳
                update_heart()
                process.join(timeout=wait_join_timeout)
            log.logger.info(u"进程停止")
            return 1
        # 更新心跳
        update_heart()
        need_stop_process_list = []
        # 监测预警脚本变化
        old_files, new_files, delete_files = check_warn_dir_changes()
        # 处理已经存在的脚本 主要为了在重启的时候重启
        for File in old_files:
            if File.filename not in process_dict:
                new_files.append(File)

        # 处理删除脚本
        for filename in delete_files:
            # 更新心跳
            update_heart()
            log.logger.debug(u"delete %s" % filename)
            db_sqlite.delete(filename)
            if filename in process_dict:
                stopEvent = process_dict[filename]['event']
                process = process_dict[filename]['process']
                process_dict.pop(filename)
                stopEvent.set()
                need_stop_process_list.append((process, filename))

        # 处理超时脚本
        for filename in process_dict:
            File = process_dict[filename]['File']
            if File.is_timeout():
                log.logger.error(u"file: %s timeout!!!" % filename)
                new_files.append(File)

        # 处理有变化的脚本
        for File in new_files:
            # 更新心跳
            update_heart()
            filename = File.filename
            if filename in process_dict:
                log.logger.debug(u"change %s" % filename)
                stopEvent = process_dict[filename]['event']
                process = process_dict[filename]['process']
                process_dict.pop(filename)
                stopEvent.set()
                need_stop_process_list.append((process, filename))

        # 等待进程停止
        for process, filename in need_stop_process_list:
            process.join(timeout=wait_join_timeout)
            # 更新心跳
            update_heart()
            del process
            log.logger.debug(u"stop process: %s" % filename)

        # 处理新增脚本
        for File in new_files:
            filename = File.filename
            log.logger.debug(u'new %s' % filename)
            stopEvent = Event()
            process = Process(target=File.main, args=(stopEvent,))
            process.start()
            process_dict[filename] = {'event': stopEvent,
                                      'process': process,
                                      'File': File}
        time.sleep(10)
    return 1


def main():
    u'''主函数'''
    parser = argparse.ArgumentParser()
    parser.add_argument("--start",
                        action="store_true",
                        help="start process")
    parser.add_argument("--stop",
                        action="store_true",
                        help="stop process")
    parser.add_argument("--restart",
                        action="store_true",
                        help="restart process")
    options = parser.parse_args()
    if options.restart:
        try:
            os.remove(pid_file)
        except:
            pass
        kill_all()
        work()
    elif options.start:
        if check_heart_timeout():
            work()
        else:
            log.logger.debug(u"进程已启动")
    elif options.stop:
        try:
            os.remove(pid_file)
        except:
            pass
    else:
        parser.print_usage()
    return 1

if __name__ == '__main__':
    main()
    pass
