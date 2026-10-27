"""JMA 爬虫共用的 XML 下载缓存。"""

from collections import OrderedDict
from concurrent.futures import Future
from threading import Lock
from time import monotonic
import xml.etree.ElementTree as ET


FEED_URL = 'https://www.data.jma.go.jp/developer/xml/feed/extra.xml'
EQVOL_FEED_URL = 'https://www.data.jma.go.jp/developer/xml/feed/eqvol.xml'
_cache = OrderedDict()
_downloads = {}
_lock = Lock()


def fetch_xml(url, fetch):
    # Feed 每分钟更新；带唯一文件名的电文在 feed 存续期间无需重复下载。
    ttl = 40 if url in (FEED_URL, EQVOL_FEED_URL) else 3600
    with _lock:
        cached = _cache.get(url)
        if cached is not None and cached[0] > monotonic():
            _cache.move_to_end(url)
            return cached[1]

        download = _downloads.get(url)
        owner = download is None
        if owner:
            download = Future()
            _downloads[url] = download

    # 相同 URL 共用下载结果；不同 URL 的网络请求不持有全局缓存锁。
    if not owner:
        return download.result()

    try:
        data = fetch(url)
        ET.fromstring(data)  # 不缓存下载成功但内容损坏的响应。
        with _lock:
            _cache[url] = (monotonic() + ttl, data)
            _cache.move_to_end(url)
            while len(_cache) > 512:
                _cache.popitem(last=False)
            del _downloads[url]
    except BaseException as error:
        with _lock:
            del _downloads[url]
        download.set_exception(error)
        raise
    else:
        download.set_result(data)
        return data
