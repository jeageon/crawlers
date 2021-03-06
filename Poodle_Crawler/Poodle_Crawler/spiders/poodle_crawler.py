import scrapy
import re
import os
import time

from scrapy import signals
from scrapy.exceptions import CloseSpider
from scrapy.loader import ItemLoader
from Poodle_Crawler.items import PoodleCrawlerItem
from datetime import datetime

'''
gall_list = [
    'hit',  # 히트갤러리
    'superidea',  # 초개념
    'accident_new',  # 막장
    'fashion_new1',  # 상의
    'pants',  # 하의
    'alcohol',  # 주류
    'car_new1',  # 자동차
    'online',  # 온라인게임
    'game1'  # 게임
]
'''


class PoodleCrawlSpider(scrapy.Spider):
    name = 'poodle_crawler'
    custom_settings = {
        'ITEM_PIPELINES': {
            'Poodle_Crawler.pipelines.RQPipeline': 400
        }
    }
    allowed_domains = ['gall.dcinside.com']

    @classmethod
    def from_crawler(cls, crawler, gall_id='', **kwargs):
        spider = super(PoodleCrawlSpider, cls).from_crawler(crawler, **kwargs)
        spider.gall_id = gall_id
        spider.started_on = datetime.now()
        spider.visited_links = set()
        spider.r = re.compile(r'(\d+)-(\d+)-(\d+) (\d+):(\d+):(\d+)')
        spider.p = re.compile(r'/board/view/\?id={}&no=.*'.format(gall_id))
        spider.prefix = 'http://gall.dcinside.com'
        spider.postPage = 'http://gall.dcinside.com/board/lists/?id=%s&page={}' % gall_id
        spider.i = 1
        spider.url_list = []
        if os.path.isfile('/var/log/{}.log'.format(cls.name + '_' + spider.gall_id)):
            with open('/var/log/{}.log'.format(cls.name + '_' + spider.gall_id), mode='rt', encoding='utf-8') as f:
                s = f.read()
                if s:
                    spider.mode = True
                    spider.url = s.split()
                    spider.furl = []
                else:
                    spider.mode = False
                    spider.url = []
                    spider.furl = []
        else:
            spider.mode = False
            spider.url = []
            spider.furl = []
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    def spider_closed(self, spider):
        with open('/var/log/{}.log'.format(self.name + '_' + self.gall_id), mode='wt', encoding='utf-8') as f:
            f.write(' '.join(spider.furl))
        print('Work time:', datetime.now() - spider.started_on)

    def start_requests(self):
        url = self.postPage.format(self.i)
        rq = scrapy.Request(url, callback=self.parse)
        yield rq

    def is_okay(self, response, match):
        if self.mode:
            for t_url in self.url:
                if t_url in response.url:
                    return False
            return True
        else:
            hr = (self.started_on - datetime(int(match.group(1)), int(match.group(2)), int(match.group(3)),
                                             int(match.group(4)), int(match.group(5))))
            if hr.days < 1:
                if (hr.seconds // 3600) > 6:
                    return False
                else:
                    return True
            else:
                return False

    def get_filtered_request(self, is_parse=False):
        if is_parse and not self.url_list:
            print('parsing page error!')
            return None
        while True:
            if not self.url_list:
                self.i += 1
                rq = scrapy.Request(self.postPage.format(self.i), callback=self.parse)
                return rq
            tmp = self.url_list.pop(0)
            if tmp['url'] not in self.visited_links:
                next_url = tmp['url']
                break
        rq = scrapy.Request(url=next_url, callback=self.parse_post,
                            meta={'item': tmp['item']})
        self.visited_links.add(next_url)
        return rq

    def parse(self, response):
        self.url_list.clear()
        for link in response.xpath('//*[@id="container"]//table[@class="gall_list"]/tbody//tr'):
            if link.xpath('./@data-no').extract_first() == '1':
                continue
            url = link.xpath('./td[@class="gall_tit ub-word"]/a[1]/@href').extract_first()
            if self.p.search(url):
                if len(self.furl) <= 5:
                    furl = self.prefix + url
                    furl = furl[:furl.find('&page')]
                    self.furl.append(furl)
                item = {'writer': link.xpath('./td[@class="gall_writer ub-writer"]/@data-nick').extract(),
                        'title': link.xpath('./td[@class="gall_tit ub-word"]/a[1]/text()').extract()}
                self.url_list.append({'url': self.prefix + url[:url.find('&page')],
                                      'item': item})
        rq = self.get_filtered_request(is_parse=True)
        if not rq:
            time.sleep(3)
            return scrapy.Request(url=response.url, callback=self.parse)
        return rq

    def parse_post(self, response):
        print('parsing post..', response.url)
        i = ItemLoader(item=PoodleCrawlerItem(), response=response)
        item = response.meta['item']
        i.add_value('title', item['title'])
        i.add_value('writer', item['writer'])
        i.add_value('category', self.gall_id)
        i.add_xpath('content', '//div[@class="writing_view_box"]/div[@style="overflow:hidden;"]//text()')
        i.add_xpath('date', '//span[@class="gall_date"]/@title')
        i.add_xpath('pic', '//div[@class="writing_view_box"]/div[@style="overflow:hidden;"]//img/@src')
        i.add_value('url', response.url)
        re_i = i.load_item()
        if 'date' not in re_i:
            time.sleep(3)
            return scrapy.Request(url=response.url, callback=self.parse_post, meta={'item': item})
        match = self.r.search(re_i['date'])
        if match:
            if self.is_okay(response, match):
                rq = self.get_filtered_request()
                return re_i, rq
            else:
                print('termination condition met')
                raise CloseSpider('termination condition met')
