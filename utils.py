import time

import itchat


def send_new_year():
    msg = '新年快乐呀！'
    friends = itchat.get_friends()
    for f in friends:
        time.sleep(1)
        print(f"send to {f['RemarkName']}/{f['NickName']}")
        itchat.send(msg, f['UserName'])
