import re
from pathlib import Path
from platform import system

import itchat
from itchat.content import TEXT, RECORDING, ATTACHMENT, PICTURE, VIDEO, SHARING, NOTE

from global_var import msg_deque
from handler import MsgHandler, HereScheduler

if not Path('backup').exists():
    Path('backup').mkdir()


@itchat.msg_register([TEXT, SHARING, PICTURE,
                      RECORDING, ATTACHMENT, VIDEO])
def auto_handler(msg):
    msg_handler = MsgHandler(msg)
    if msg_handler.is_me():
        pass
    else:
        # auto reply msg when sleeping
        msg_handler.sleep_auto_reply()
        # save msg for backup
        msg_handler.save_msg()
        # robot
    msg_handler.start_robot()


@itchat.msg_register([NOTE])
def backup_revoke(msg):
    """backup the revoke message"""
    msg_handler = MsgHandler(msg)
    text = msg['Text']
    if text.endswith('撤回了一条消息') and text != '你撤回了一条消息':
        res = re.search(r'<msgid>([0-9]+)</msgid>', msg['Content'])
        # get revoke msg id
        msgid = res.group(1)
        try:
            # get message from msg_deque,then send to filehelper
            rm = revoke_message = msg_deque.pop(msgid)
            notice_message = f"{rm['time']}\n{rm['from']}:\n{rm['content']}"
            msg_handler.notice_to_me(notice_message)
            if revoke_message['type'] != 'Text':
                # not text, send and delete stored file.
                msg_handler.notice_to_me(f"@fil@backup/{revoke_message['content']}", is_text=False)
                Path('backup', f"{revoke_message['content']}").unlink()
        except KeyError:
            msg_handler.notice_to_me('get revoke failed')


def login_start():
    itchat.send('小薇：开始工作啦！', 'filehelper')


def logout():
    itchat.send('自动回复终止', 'filehelper')


if __name__ == '__main__':
    if system() == 'Windows':
        itchat.auto_login(hotReload=True,
                          loginCallback=login_start, exitCallback=logout)
    elif system() == 'Linux':
        itchat.auto_login(hotReload=True, enableCmdQR=2, loginCallback=login_start, exitCallback=logout)

    # itchat.run()
    itchat.run(blockThread=False)
    here_scheduler = HereScheduler()
    here_scheduler.run_scheduler()
