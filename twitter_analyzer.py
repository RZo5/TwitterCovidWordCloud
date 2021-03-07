from tweepy import API 
from tweepy import Cursor
from tweepy.streaming import StreamListener
from tweepy import OAuthHandler
from tweepy import Stream
from wordcloud import WordCloud, STOPWORDS

import os.path
import tweepy
import time
import matplotlib.pyplot as plt  
import twitter_credentials
import numpy as np
import pandas as pd


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
        #today = 
        for tweet in Cursor(self.twitter_client.search, q = search_terms, lang = "en").items(num_tweets):
            #if tweet.created_at 
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
        stopwords = ["RT"] + list(STOPWORDS) 
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
    def tweet_word_cloud(count, keywords):
        # including other classes to be used later
        twitter_client = TwitterClient()
        tweet_analyzer = TweetAnalyzer()
        word_cloud = PlotWordCloud()
        api = twitter_client.get_twitter_client_api()

        # get tweets
        tweets = twitter_client.get_today_tweets(count, keywords)
        # store tweets into data frame
        df = tweet_analyzer.tweets_to_data_frame(tweets)

        # extracting only the contents of the tweet
        str = df.text.to_string()

        # make the word cloud and store it on computer
        # path = "C:\Users\richa\Desktop\Twitter\"
        wordcloud = word_cloud.make_word_cloud(str)
        wordcloud.to_file(os.path.join("./testing", "testcloud2.png"))
    
        # tweet the wordcloud that was made
        twitter_client.tweet("testwordcloud", "./testing/testcloud2.png")

if __name__ == '__main__':

    twitter_client = TwitterClient()
    tweet_analyzer = TweetAnalyzer()
    word_cloud = PlotWordCloud()
    api = twitter_client.get_twitter_client_api()

    keywords = "corona OR covid" # -filter:retweets"
    BotFunctions.tweet_word_cloud(100, keywords)

    #stream.filter(track = []) (filtering)
    
    #tweets = api.get_random_tweets()
    #print(twitter_client.get_random_tweets(1))

    #print(dir(tweets[0]))
    #print(tweets[0].retweet_count)
    #twitter_client.tweet("Hello World")

    #tweets = api.user_timeline(screen_name="JoeBiden", count=20)
    # keywords = "corona OR covid" # -filter:retweets"
    # tweets = twitter_client.get_today_tweets(100, keywords)
    # df = tweet_analyzer.tweets_to_data_frame(tweets)
    
    # print(df.head(10))

    # str = df.text.to_string()
    # wordcloud = word_cloud.make_word_cloud(str)

    #path = "C:\Users\richa\Desktop\Twitter\"
    # wordcloud.to_file(os.path.join("./testing", "testcloud2.png"))
    
    # tweet the wordcloud that was made
    # twitter_client.tweet("testwordcloud", "./testing/testcloud2.png")

    # this plots the word cloud so I can see it
    # word_cloud.plot_word_cloud(wordcloud)