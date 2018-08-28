import scrapy
import re
import os
from scrapy import signals
from scrapy.exceptions import CloseSpider
from scrapy.loader import ItemLoader
from Spitz_Crawler.items import SpitzCrawlerItem
from datetime import datetime


class SpitzCrawlSpider(scrapy.Spider):
    name = 'spitz_crawler'
    custom_settings = {
        'ITEM_PIPELINES': {
            'Spitz_Crawler.pipelines.RQPipeline': 400
        }
    }
    allowed_domains = ['m.todayhumor.co.kr']

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(SpitzCrawlSpider, cls).from_crawler(crawler, *args, **kwargs)
        spider.started_on = datetime.now()
        spider.visited_links = set()
        spider.r = re.compile(r'(\d+)-(\d+)-(\d+) (\d+):(\d+)')
        spider.p = re.compile(r'view.php\?table=.*')
        spider.prefix = 'http://m.todayhumor.co.kr/'
        spider.postPage = 'http://m.todayhumor.co.kr/list.php?table=total&page={}'
        spider.i = 1
        if os.path.isfile('/var/log/{}.log'.format(cls.name)):
            with open('/var/log/{}.log'.format(cls.name), mode='rt', encoding='utf-8') as f:
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
        with open('/var/log/{}.log'.format(self.name), mode='wt', encoding='utf-8') as f:
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

    def parse(self, response):
        self.url_list = []
        flag = False
        for link in response.xpath('/html/body//a'):
            url = link.xpath('./@href').extract_first()
            if self.p.search(url):
                if len(self.furl) <= 5:
                    furl = self.prefix + url
                    furl = furl[:furl.find('&page')]
                    self.furl.append(furl)
                item = {'date': link.xpath('./div/div[2]/span[2]/text()').extract_first(),
                        'title': link.xpath('./div/div[3]/h2/text()').extract()}
                self.url_list.append({'url': self.prefix + url[:url.find('&page')],
                                      'item': item})
        while True:
            if not self.url_list:
                if flag:
                    self.i += 1
                    rq = scrapy.Request(self.postPage.format(self.i), dont_filter=True, callback=self.parse)
                    return rq
                else:
                    return
            tmp = self.url_list.pop(0)
            if tmp['url'] not in self.visited_links:
                next_url = tmp['url']
                break
            flag = True
        rq = scrapy.Request(url=next_url, callback=self.parse_post,
                            meta={'item': tmp['item']})
        return rq

    def parse_post(self, response):
        print('parsing post..', response.url)
        i = ItemLoader(item=SpitzCrawlerItem(), response=response)
        item = response.meta['item']
        i.add_value('title', item['title'])
        i.add_xpath('writer', '//*[@id="viewPageWriterNameSpan"]/@name')
        i.add_xpath('writer', '/html/body/div[@class="view_spec"]//span[@class="view_writer_span"]//text()')
        i.add_xpath('content', '/html/body//div[@class="viewContent"]//text()')
        i.add_value('date', item['date'])
        i.add_xpath('pic', '/html/body//div[@class="viewContent"]//img/@src')
        i.add_value('url', response.url)
        re_i = i.load_item()
        match = self.r.search(re_i['date'])
        if match:
            if self.is_okay(response, match):
                if self.url_list:
                    tmp = self.url_list.pop(0)
                    next_url = tmp['url']
                    rq = scrapy.Request(url=next_url, callback=self.parse_post,
                                        meta={'item': tmp['item']})
                    self.visited_links.add(next_url)
                    return re_i, rq
                else:
                    self.i += 1
                    rq = scrapy.Request(self.postPage.format(self.i), dont_filter=True, callback=self.parse)
                    return re_i, rq
            else:
                raise CloseSpider('termination condition met')
