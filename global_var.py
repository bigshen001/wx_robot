from collections import OrderedDict
from datetime import timezone, timedelta
from platform import system

from redis import StrictRedis

msg_deque = OrderedDict()
tz_beijing = timezone(offset=timedelta(hours=8))
robot_name = '小薇'


def host():
    if system() == 'Linux':
        address = 'localhost'
    elif system() == 'Windows':
        address = '47.95.11.71'
    else:
        address = ''
    return address


host = host()
port = 6379
db = 2
r = StrictRedis(host=host, port=port, db=db)
