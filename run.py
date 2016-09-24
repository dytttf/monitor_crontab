#coding:utf8
import os
import time
import threading
from  multiprocessing import Process, Event

import db_sqlite
try:
    from Api import log
except:
    import log
import warn_file


#获取当前文件路径
cur_path = os.path.dirname(__file__)

#预警脚本存放路径
warn_dir = os.path.join(cur_path, 'warn_dir')
if not os.path.exists(warn_dir):
    os.mkdir(warn_dir)

wait_join_timeout = 30


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
                log.logger.error(u"初始化预警文件失败 file: %s error:%s"%(
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

def main():
    u'''主函数'''
    process_dict = {}
    while 1:
        need_stop_process_list = []
        # 监测预警脚本变化
        old_files, new_files, delete_files = check_warn_dir_changes()
        # 处理已经存在的脚本
        for File in old_files:
            if File.filename not in process_dict:
                new_files.append(File)

        # 处理删除脚本
        for File in delete_files:
            log.logger.debug(u"delete %s"%File.filename)
            db_sqlite.delete(File)

        # 处理有变化的脚本
        for File in new_files:
            filename = File.filename
            if filename in process_dict:
                log.logger.debug(u"change %s"%filename)
                stopEvent = process_dict[filename]['event']
                process = process_dict[filename]['process']
                process_dict.pop(filename)
                stopEvent.set()
                need_stop_process_list.append(process)

        # 等待进程停止
        for process in need_stop_process_list:
            process.join(timeout=wait_join_timeout)
            del process

        # 处理新增脚本
        for File in new_files:
            filename = File.filename
            log.logger.debug(u'new %s'%filename)
            stopEvent = Event()
            process = Process(target=File.main, args=(stopEvent,))
            process.start()
            process_dict[filename] = {'event':stopEvent, 'process':process}
        time.sleep(10)

    return


if __name__ == '__main__':
    main()
    pass
