from apscheduler.schedulers.blocking import BlockingScheduler
from pytz import utc
from twitter_analyzer import BotFunctions

sched = BlockingScheduler()

@sched.scheduled_job('cron', hour = 23, minute = 50, timezone = utc) # 23:59:59 UTC
def scheduled_job():
    BotFunctions().post_once_a_day()

since_id = 1
@sched.reply('interval', minutes=1)
def reply():
    since_id = BotFunctions().check_mentions(since_id)

sched.start()