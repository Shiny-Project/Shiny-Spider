# Shiny 数据分析模块
import requests, json, datetime
from core import database,config
from core.log import Log
Logger = Log()

def extract_keywords(text):
    url = 'https://jlp.yahooapis.jp/KeyphraseService/V1/extract'
    data = {
        "output": "json",
        "appid": config.YAHOO_API_KEY,
        "sentence": text
    }
    headers = {
        'User-Agent': 'Shiny/0.1 (https://github.com/Shiny-Project/Shiny-README)'
    }

    response = requests.get(url, params=data, headers=headers).json()

    return response

def get_unanalysed_events(timestamp):
    return database.get_unanalysed_events(timestamp)

def analyze_events(event_list = []):
    for event in event_list:
        data = json.loads(event.data)
        text = data["content"]

        if text == "":
            database.mark_as_analysed(event.id)
            continue

        Logger.debug('尝试获得 Event ID = [' + str(event.id) + '] 的关键词')
        keywords = extract_keywords(text)
        
        try:
            if keywords == []:
                Logger.debug('Event ID = [' + str(event.id) + '] 关键词列表为空')
            else:
                for key in keywords.keys():
                    res = database.find_keyword(key)
                    if (len(res) == 0):
                        # 一个新的Keyword出现了!
                        Logger.debug('新 Keyword: [' + key + '] 发现 尝试记录')
                        database.create_keyword(key)
                    
                    Logger.debug('写入新的 Keyword - Score 数据')
                    database.create_keywordscore(key, keywords[key], event.id)
            
            # 标记已分析
            database.mark_as_analysed(event.id)
        except Exception as e:
            Logger.error('分析 Event ID = [' + str(event.id) + '] 时出现错误:' + str(e))

def analyze_all_events():
    analyze_events(get_unanalysed_events(str(datetime.datetime(2016,1,1))))

if __name__ == '__main__':
    pass