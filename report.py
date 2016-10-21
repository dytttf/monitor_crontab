# coding:utf8
try:
    from Api import log
except:
    import log
try:
    from Api.DingTalkWarn import send
except:
    def send(data):
        log.logger.debug(u"发送信息成功 %s" % data)
        return

if __name__ == '__main__':
    send({})
