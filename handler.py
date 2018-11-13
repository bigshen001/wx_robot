from datetime import timedelta, datetime, date
from pathlib import Path
from sched import scheduler
from time import mktime, sleep

import itchat
import schedule

from global_var import msg_deque, tz_beijing, r, robot_name


class BaseMsgHandler:
    def __init__(self, msg):
        from_user_username = msg['FromUserName']
        from_user = itchat.search_friends(userName=from_user_username)
        to_user_name = msg['ToUserName']
        to_user = itchat.search_friends(userName=to_user_name)
        msg_type = msg['MsgType']

        now = datetime.now(tz=tz_beijing)

        self.msg = msg
        self.from_user = from_user
        self.to_user = to_user
        self.msg_type = msg_type
        self.msg_content = msg['Content']
        self.msg_id = msg['MsgId']

        self.tz = tz_beijing
        self.msg_time = now

    def reply_from_user(self, message: str = '您好，我现在不在'):
        """if from user is not self, use message to reply."""
        itchat.send(message, self.from_user['UserName'])

    def notice_to_me(self, message: str = '', is_text=True):
        """send message to filehelper"""
        from_user_remark = self.from_user['RemarkName']
        if from_user_remark == '':
            from_user_remark = self.from_user['NickName']
        if is_text:
            if message == '':
                if self.msg['MsgType'] == 1:
                    message = f"{from_user_remark}于{self.msg_time:%H:%M:%S}：\n{self.msg.text}"
                else:
                    message = f"{from_user_remark}于{self.msg_time:%H:%M:%S}：\n非文本消息"
        itchat.send(message, toUserName='filehelper')

    def is_me(self):
        if self.from_user['NickName'] == '清蓝君' or self.from_user['UserName'] == 'filehelper':
            return True

    def is_night(self):
        """if time is in 23:00 to 7:00"""

        if self.msg_time.hour >= 23:
            # 凌晨之前
            td = date.today()
        else:
            # 凌晨之后
            td = date.today() - timedelta(days=1)
        today23 = datetime(td.year, td.month, td.day, 22, 0, 0, tzinfo=self.tz)
        tomorrow7 = today23 + timedelta(hours=8)
        if today23 < self.msg_time < tomorrow7:
            return True


class MsgHandler(BaseMsgHandler):
    def sleep_auto_reply(self):
        """auto reply at night"""
        if self.is_night():
            # get from user info
            from_user_nickname = self.from_user['NickName']

            reply = f"自动回复：\n{from_user_nickname}您好，消息收到。\n当前为睡眠时间，将于明早答复。\n当前时间：{self.msg_time:%H:%M:%S}"

            self.reply_from_user(reply)
            self.notice_to_me()

    def start_robot(self):
        """
        Identify and reply to certain text
        1.在吗，在不在，zaima,在ma zai吗，在么

        """
        self.is_online()
        self.is_alive()
        self.query_word()

    def save_msg(self):
        """save msg to  message_deque,if not text，and save file to backup/"""
        msg_type = self.msg['Type']
        remark_name = self.from_user['RemarkName']
        if remark_name == '':
            remark_name = self.from_user['NickName']
        if msg_type == 'Text':
            content = self.msg.text
        elif msg_type in ['Attachment', 'Video', 'Picture', 'Recording']:
            content = self.msg['FileName']
            # download file
            self.msg['Text'](f"backup/{content}")
        else:
            content = ''
        message = {self.msg_id: {'from': remark_name,
                                 'time': f"{self.msg_time:%y/%m/%d %H:%M:%S}",
                                 'content': content,
                                 'type': msg_type}}
        msg_deque.update(message)
        if len(msg_deque) >= 20:
            m0 = msg_deque.popitem(last=False)
            if m0[1]['type'] == 'Text':
                # nothing to do
                pass
            else:
                # rm backup file
                file = m0[1]['content']
                Path('backup', file).unlink()

    def is_online(self):
        if self.msg['Type'] == 'Text':
            message = self.msg.text
            # reply is online?
            certain_text = ['在吗', '在不在', 'zaima', '在ma', 'zai吗', '在么']
            if any([i in message for i in certain_text]):
                reply = f"消息助手：\n此消息已拦截。\n有事请直言，不要问在不在。"
                self.reply_from_user(reply)

    def is_alive(self):
        if self.msg['Type'] == 'Text':
            message = self.msg.text
            if self.is_me() and any([i == message for i in ['?', '？']]):
                # is alive?
                self.notice_to_me(f'{robot_name}：正在工作!')

    def query_word(self):
        """query word in redis by ?"""
        if self.msg['Type'] == 'Text':
            text = self.msg.text
            if text.startswith('?') or text.startswith('？'):
                word = text[1:]
                res = r.hgetall(word)
                if len(res) == 0:
                    # word not in redis
                    message = f'报告：{robot_name}的字典里没有这个东西！'
                else:
                    res_type = res[b'type']
                    # char,word,idiom,xhy
                    if res_type == b'char':
                        explain = res[b'explain'].decode('utf8')
                        pinyin = res[b'pinyin'].decode('utf8')
                        message = f"{word}:\n" \
                                  f"拼音：{pinyin}\n" \
                                  f"解释：{explain}"
                    elif res_type == b'word':
                        explain = res[b'explain'].decode('utf8')
                        message = f"{word}:\n" \
                                  f"解释：{explain}"
                    elif res_type == b'idiom':
                        explain = res[b'explain'].decode('utf8')
                        pinyin = res[b'pinyin'].decode('utf8')
                        eg = res[b'e.g'].decode('utf8')
                        from0 = res[b'from'].decode('utf8')
                        message = f"{word}:\n" \
                                  f"拼音：{pinyin}\n" \
                                  f"解释：{explain}\n" \
                                  f"例：{eg}\n" \
                                  f"出处：{from0}"
                    elif res_type == b'xhy':
                        explain = res[b'explain'].decode('utf8')
                        message = f"{word}:\n" \
                                  f"解释：{explain}"
                    else:
                        message = ''
                if self.is_me():
                    self.notice_to_me(message)
                else:
                    self.reply_from_user(message)


class Wechat:
    @classmethod
    def send_to_friend(cls, msg: str = '', remark_name: str = '', nick_name: str = '', alive=False):
        """send msg to friend"""
        if alive:
            itchat.send(msg, toUserName='filehelper')
        else:
            if remark_name == '':
                remark_name = nick_name
            to = itchat.search_friends(name=remark_name)[0]
            itchat.send(msg, toUserName=to['UserName'])

    @classmethod
    def send_to_chatroom(cls, msg: str = '', remark_name: str = '', nick_name: str = ''):
        if remark_name == '':
            remark_name = nick_name
        to = itchat.search_chatrooms(name=remark_name)[0]
        itchat.send(msg, toUserName=to['UserName'])

    @classmethod
    def send_alive_msg(cls):
        """send alive msg to filehelper"""
        now = datetime.now(tz=tz_beijing)
        message = f"{now:%H:%M:%S:%f}:alive!"
        cls.send_to_friend(message, alive=True)


class HereScheduler:
    def __init__(self):
        self.scheduler = scheduler(self.__class__.get_now)

    @classmethod
    def get_now(cls):
        current = datetime.now(tz=tz_beijing)
        return mktime(current.timetuple())

    @classmethod
    def period_hour_run(cls, func=Wechat.send_alive_msg):
        """receive a func,run it every hour."""
        # schedule.every().second.do(func)
        schedule.every().hour.do(func)
        while True:
            schedule.run_pending()
            sleep(0.01)

    def run_scheduler(self):
        """run every hour alive"""
        now = datetime.now(tz=tz_beijing)
        run_time = now + timedelta(hours=1) \
                   - timedelta(minutes=now.minute) \
                   - timedelta(seconds=now.second) \
                   - timedelta(microseconds=now.microsecond)
        # run_time = now + timedelta(seconds=5)
        run_time = mktime(run_time.timetuple())
        self.scheduler.enterabs(run_time, 1, self.__class__.period_hour_run)
        self.scheduler.run()
