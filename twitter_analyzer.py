from tweepy import API 
from tweepy import Cursor
from tweepy.streaming import StreamListener
from tweepy import OAuthHandler
from tweepy import Stream
from wordcloud import WordCloud, STOPWORDS
from datetime import datetime, timedelta

import os.path
import tweepy
import time
import matplotlib.pyplot as plt  
import twitter_credentials
import numpy as np
import pandas as pd
import re

# # # # TWITTER CLIENT # # # #
class TwitterClient():
    def __init__(self, twitter_user=None):
        self.auth = TwitterAuthenticator().authenticate_twitter_app()
        self.twitter_client = API(self.auth)

        self.twitter_user = twitter_user

    def get_twitter_client_api(self):
        return self.twitter_client

    def get_user_timeline_tweets(self, num_tweets):
        tweets = []
        for tweet in Cursor(self.twitter_client.user_timeline, id=self.twitter_user).items(num_tweets):
            tweets.append(tweet)
        return tweets

    def get_friend_list(self, num_friends):
        friend_list = []
        for friend in Cursor(self.twitter_client.friends, id=self.twitter_user).items(num_friends):
            friend_list.append(friend)
        return friend_list

    def get_home_timeline_tweets(self, num_tweets):
        home_timeline_tweets = []
        for tweet in Cursor(self.twitter_client.home_timeline, id=self.twitter_user).items(num_tweets):
            home_timeline_tweets.append(tweet)
        return home_timeline_tweets

    def get_random_tweets(self, num_tweets, search_terms):
        tweets = []
        for tweet in Cursor(self.twitter_client.search, q = search_terms).items(num_tweets):
            tweets.append(tweet)
        return tweets

    def get_today_tweets(self, num_tweets, search_terms):
        tweets = []
        start_date = datetime.now() #- timedelta(days=1)
        # start_time = start_date.strftime("%Y-%m-%dT%H:%M:%SZ")
        today = start_date.strftime("%Y-%m-%d") # only give tweets posted from today
        
        # we get a mix of popular tweets and recent (realtime) tweets
        for tweet in Cursor(self.twitter_client.search, q = search_terms + " since:" + today,
         lang = "en", result_type = "popular").items(num_tweets): 
            tweets.append(tweet)
        return tweets

    def tweet(self, text, img=None):
        if (img == None):
            self.twitter_client.update_status(text)
        else:
            media = self.twitter_client.media_upload(img)
            self.twitter_client.update_status(text, media_ids = [media.media_id])

# # # # TWITTER AUTHENTICATER # # # #
class TwitterAuthenticator():

    def authenticate_twitter_app(self):
        auth = OAuthHandler(twitter_credentials.CONSUMER_KEY, twitter_credentials.CONSUMER_SECRET)
        auth.set_access_token(twitter_credentials.ACCESS_TOKEN, twitter_credentials.ACCESS_TOKEN_SECRET)
        return auth

# # # # TWITTER STREAMER # # # #
class TwitterStreamer():
    """
    Class for streaming and processing live tweets.
    """
    def __init__(self):
        self.twitter_autenticator = TwitterAuthenticator()    

    def stream_tweets(self, fetched_tweets_filename, hash_tag_list):
        # This handles Twitter authetification and the connection to Twitter Streaming API
        listener = TwitterListener(fetched_tweets_filename)
        auth = self.twitter_autenticator.authenticate_twitter_app() 
        stream = Stream(auth, listener)

        # This line filter Twitter Streams to capture data by the keywords: 
        stream.filter(track=hash_tag_list)

# # # # TWITTER STREAM LISTENER # # # #
class TwitterListener(StreamListener):
    """
    This is a basic listener that just prints received tweets to stdout.
    """
    def __init__(self, fetched_tweets_filename):
        self.fetched_tweets_filename = fetched_tweets_filename

    def on_data(self, data):
        try:
            print(data)
            with open(self.fetched_tweets_filename, 'a') as tf:
                tf.write(data)
            return True
        except BaseException as e:
            print("Error on_data %s" % str(e))
        return True
          
    def on_error(self, status):
        if status == 420:
            # Returning False on_data method in case rate limit occurs.
            return False
        print(status)

# # # # TWITTER ANALYZER (DATAFRAME) # # # #
class TweetAnalyzer():
    """
    Functionality for analyzing and categorizing content from tweets.
    """
    def tweets_to_data_frame(self, tweets):
        df = pd.DataFrame(data=[tweet.text for tweet in tweets], columns=['text'])

        df['id'] = np.array([tweet.id for tweet in tweets])
        df['len'] = np.array([len(tweet.text) for tweet in tweets])
        df['date'] = np.array([tweet.created_at for tweet in tweets])
        df['source'] = np.array([tweet.source for tweet in tweets])
        df['likes'] = np.array([tweet.favorite_count for tweet in tweets])
        df['retweets'] = np.array([tweet.retweet_count for tweet in tweets])

        return df

# # # # WORD CLOUD FUNCTION # # # #
class PlotWordCloud():
    # create and plots word cloud from passed str
    def make_word_cloud(self, str):
        stopwords = ["RT", "https", "http", "t", "u", "l", "n", "b", "s"] + list(STOPWORDS) 
        wordcloud = WordCloud(width = 800, height = 800, 
                    background_color ='white', 
                    stopwords = stopwords, 
                    min_font_size = 10).generate(str)
        return wordcloud

    def plot_word_cloud(self, wordcloud):    
        # plot the WordCloud image                        
        plt.figure(figsize = (8, 8), facecolor = None) 
        plt.imshow(wordcloud) 
        plt.axis("off") 
        plt.tight_layout(pad = 0) 
  
        plt.show()

# Stuff the bot should be able to do
class BotFunctions():
    # makes a tweets a daily wordcloud
    # gets count number of tweets and filters by keywords
    def tweet_word_cloud(self, str):
        # including other classes to be used later
        twitter_client = TwitterClient()
        word_cloud = PlotWordCloud()

        # get today's date (for naming the wordcloud)
        today = datetime.today()
        today_str = today.strftime("%m-%d-%Y")
        # gives the exact time, used to make wordclouds while testing unique
        # now = datetime.now()
        # now = now.strftime("%H.%M.%S")

        cloud_name = "wordcloud" + today_str + ".png"

        # make the word cloud and store it on computer
        # path = "C:\Users\richa\Desktop\Twitter\"
        wordcloud = word_cloud.make_word_cloud(str)
        wordcloud.to_file(os.path.join("./dailyclouds", cloud_name))
    
        # tweet the wordcloud that was made
        twitter_client.tweet("Today's Covid Wordcloud: " + today_str, "./dailyclouds/" + cloud_name)

    def fix_str(self, str):
        str = re.sub("@\w[\w']+", "", str)
        str = re.sub("\s\w\s", "", str)
        return str

    def post_once_a_day(self):
        twitter_client = TwitterClient()
        tweet_analyzer = TweetAnalyzer()

        keywords = "corona OR covid"

        # get tweets, uses UTC timezone
        tweets = twitter_client.get_today_tweets(1000, keywords)
        # store tweets into data frame
        df = tweet_analyzer.tweets_to_data_frame(tweets)

        # extracting only the contents of the tweet
        str = df.text.to_string()
        # remove twitter handles (starting with @), replaces it with empty string
        # removing RT in stopwords (see make_word_cloud function)
        str = BotFunctions().fix_str(str)

        BotFunctions().tweet_word_cloud(str)

    #def respond_to_tweets():

if __name__ == '__main__':
    BotFunctions().post_once_a_day()