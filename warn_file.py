#coding:utf8
'''
预警脚本管理文件
'''
import os
import imp
import time

from crontab import CronTab

import log
import report


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
        self.st_mtime = stat.st_mtime
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

    def main(self, stopEvent):
        self.init_warn_file()

        cron = CronTab(self.warn_module.crontab)
        while 1:
            if stopEvent.is_set():
                break
            if cron.next() < 1:
                warn_info = self.warn_module.execute()
                if warn_info['status'] != 0:
                    warn_info.update({'filename':self.filename})
                    report.send(warn_info)
                time.sleep(1)
            else:
                time.sleep(.5)
        return 1


if __name__ == '__main__':
    pass