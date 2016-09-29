#coding:utf8
'''
预警脚本管理文件
'''
import os
import imp
import time

from crontab import CronTab

try:
    from Api import log
except:
    import log
import report
import db_sqlite


class WarnFile(object):
    def __init__(self, filename, *args, **kwargs):
        u'''初始化'''
        self.filename = filename
        self.warn_module = None

        self.st_mtime = 0
        self.last_warning = 0

        self.args = args
        self.kwargs = kwargs

        self.init_file_info()

    def __str__(self):
        return self.filename

    def init_file_info(self):
        u'''获取文件属性'''
        stat = os.stat(self.filename)
        self.st_mtime = int(stat.st_mtime)
        return 1

    def init_warn_file(self):
        u'''初始化预警脚本 加载代码'''
        with open(self.filename) as f:
            code = f.read()
        module = imp.new_module('warn')
        try:
            code = compile(code, '', 'exec')
        except Exception as e:
            log.logger.exception(e)
            log.logger.error(u"compile file: %s error:%s"%(self.filename, e))
            return 0
        try:
            exec code in  module.__dict__
        except Exception as e:
            log.logger.exception(e)
            log.logger.error(u"exec code file: %s error: %s"%(self.filename, e))
            return 0
        self.warn_module = module
        return 1

    def update_heart(self):
        u"""更新心跳时间"""
        db_sqlite.update_heart(self.filename)
        return 1

    def is_timeout(self, timeout=10*60):
        u"""判断心跳是否超时"""
        last_time = db_sqlite.get_heart(self.filename)
        if time.time() - last_time > timeout:
            return 1
        return 0

    def _main(self, stopEvent):
        log.logger.info(u"子进程启动: %s"%self.filename)
        self.init_warn_file()

        cron = CronTab(self.warn_module.crontab)
        while 1:
            if stopEvent.is_set():
                log.logger.info(u"收到停止信号 %s"%self.filename)
                break
            try:
                self.update_heart()
            except Exception as e:
                log.logger.error(u"更新心跳失败 %s"%e)
            if cron.next() < 1:
                warn_info = self.warn_module.execute()
                if warn_info['status'] != 0:
                    warn_info.update({'filename':self.filename})
                    resp = report.send(warn_info)
                    self.last_warning = time.time()
                    data = {
                        'st_mtime':self.st_mtime,
                        'last_warning':self.last_warning,
                        'update':1,
                        }
                    db_sqlite.upsert(data, self)
                time.sleep(1)
            else:
                time.sleep(.5)
        return 1

    def main(self, stopEvent):
        resp = 1
        while 1:
            if stopEvent.is_set():
                break
            try:
                resp = self._main(stopEvent)
                break
            except Exception as e:
                log.logger.exception(e)
                time.sleep(60)
        return resp



if __name__ == '__main__':
    pass
