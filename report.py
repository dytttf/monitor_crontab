#coding:utf8
try:
    from Api.DingTalkWarn import send
except:
    def send(data):
        print u"发送信息成功 %s"%data
        return

if __name__ == '__main__':
    send({})
