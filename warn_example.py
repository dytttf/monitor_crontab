#coding:utf8
import datetime

#必须参数 定时计划
crontab = "*/10 * * * *"

#必须函数
def execute():
    u'''
    返回一个字典 
        status 字段为0, 表示不需要预警
        不为0 则调用 report.py 中 send 函数发送预警信息
    '''
    data = {'status':0}
    now = datetime.datetime.now()
    if now.hour == 10:
        data.update({
            "status":1,
            "content":"该起床了"
            })
    else:
        pass
    return data


if __name__ == "__main__":
    print execute()
