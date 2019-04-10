from core import spider, config
import tweepy


class TwitterSpider(spider.Spider):
    def __init__(self, info={}):
        super(TwitterSpider, self).__init__(info)  # 仅修改类名，不要修改其他
        self.name = 'Twitter'  # 声明Spider名，要和类名里的一样

    def main(self):
        """主抓取逻辑，只修改内容，不修改函数名"""
        if 'CONSUMER_KEY' in self.identity:
            self.CONSUMER_KEY = self.identity['CONSUMER_KEY']
        else:
            raise Exception('CONSUMER_KEY 未指定.')
        if 'CONSUMER_SECRET' in self.identity:
            self.CONSUMER_SECRET = self.identity['CONSUMER_SECRET']
        else:
            raise Exception('CONSUMER_SECRET 未指定.')
        if 'ACCESS_TOKEN' in self.identity:
            self.ACCESS_TOKEN = self.identity['ACCESS_TOKEN']
        else:
            raise Exception('ACCESS_TOKEN 未指定.')
        if 'ACCESS_SECRET' in self.identity:
            self.ACCESS_SECRET = self.identity['ACCESS_SECRET']
        else:
            raise Exception('ACCESS_SECRET 未指定.')
        
        auth = tweepy.OAuthHandler(self.CONSUMER_KEY, self.CONSUMER_SECRET)
        auth.set_access_token(self.ACCESS_TOKEN, self.ACCESS_SECRET)

        api = tweepy.API(auth)
        # 将待监控的twitter id增加在下面
        self.process(api, "LoveLive_staff") #LL
        # self.process(api, "wakeupgirls_PR") #wug
        self.process(api, "minazou_373")

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
                "channel": name,
                "link" : "https://twitter.com/%s/status/%s" % (user, id),
                "cover" : profile_image,
            }

            events.append(json_data)

        self.record_many(3, events) 



if __name__ == '__main__':
    pass
