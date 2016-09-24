#coding=utf-8

import os
import sys
import logging
import logging.handlers


def get_current_file_path():
    '''
    获取当前文件所在路径
    '''
    path = os.path.dirname(os.path.abspath(sys.path[0]))
    if os.path.isdir(path):
        return path
    elif os.path.isfile(path):
        return os.path.dirname(path)

logger = logging.getLogger()

current_file_path = get_current_file_path()
log_path = current_file_path + "/log/"

if os.path.isdir(log_path) == False:
    os.makedirs(current_file_path +"/log/")

fp = logging.handlers.RotatingFileHandler(log_path+"debug.log", maxBytes=10*1024*1024,  mode='a', backupCount=100) 
logger.addHandler(fp)

std = logging.StreamHandler(sys.stderr)
logger.addHandler(std)

formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] [%(filename)s] [%(lineno)d] - %(message)s")
fp.setFormatter(formatter)
std.setFormatter(formatter)

logger.setLevel(logging.NOTSET)
