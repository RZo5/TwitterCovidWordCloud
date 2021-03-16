from apscheduler.schedulers.blocking import BlockingScheduler
from twitter_analyzer import __all__

sched = BlockingScheduler()

@sched.scheduled_job('cron', hour = 23, minute = 59, second = 59, timezone = utc) # 23:59:59 UTC
def scheduled_job():
    twitter_client = TwitterClient()
    tweet_analyzer = TweetAnalyzer()
    word_cloud = PlotWordCloud()
    api = twitter_client.get_twitter_client_api()

    keywords = "corona OR covid" # -filter:retweets"

    # get tweets, uses UTC timezone
    tweets = twitter_client.get_today_tweets(1000, keywords)
    # store tweets into data frame
    df = tweet_analyzer.tweets_to_data_frame(tweets)

    # extracting only the contents of the tweet
    str = df.text.to_string()
    # remove twitter handles (starting with @), replaces it with empty string
    # removing RT in stopwords (see make_word_cloud function)
    str = re.sub("@\w[\w']+", "", str)
    str = re.sub("\s\w\s", "", str) # remove single letters
    # print(str)

    BotFunctions.tweet_word_cloud(str)

sched.start()