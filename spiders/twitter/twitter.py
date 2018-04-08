from core import spider, config
import tweepy


class TwitterSpider(spider.Spider):
    def __init__(self):
        super(TwitterSpider, self).__init__()  # 仅修改类名，不要修改其他
        self.name = 'Twitter'  # 声明Spider名，要和类名里的一样

    def main(self):
        """主抓取逻辑，只修改内容，不修改函数名"""
        auth = tweepy.OAuthHandler(config.TWITTER_CONSUMER_KEY, config.TWITTER_CONSUMER_SECRET)
        auth.set_access_token(config.TWITTER_ACCESS_TOKEN, config.TWITTER_ACCESS_SECRET)

        api = tweepy.API(auth)
        # 将待监控的twitter id增加在下面
        self.process(api, "LoveLive_staff") #LL
        self.process(api, "wakeupgirls_PR") #wug
        self.process(api, 'akane_fujikawa') #藤川茜

    def process(self, api, name, count=5):
        status = api.user_timeline(name, count=count)
        events = []
        for tweet in status:
            id = tweet.id
            text = tweet.text
            user = tweet.author.screen_name
            name = tweet.author.name
            profile_image = tweet.author.profile_image_url_https
            media_type = ""
            media = ""
            if hasattr(tweet, 'extended_entities'):
                medias = tweet.extended_entities['media'][0]
                media = medias['media_url_https']
                media_type = medias['type']

            if media_type == "photo":
                text = text + ('<img src="%s">' % (media,))

            json_data = {
                "title" : "【%s】正在发推" % (name,),
                "content" : text,
                "link" : "https://twitter.com/%s/status/%s" % (user, id),
                "cover" : profile_image,
            }

            events.append(json_data)

        self.record_many(3, events) 



if __name__ == '__main__':
    pass
