from collections import OrderedDict
from datetime import timezone, timedelta

msg_deque = OrderedDict()
tz_beijing = timezone(offset=timedelta(hours=8))
