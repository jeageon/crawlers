from scrapy import signals, Request
from selenium import webdriver
from scrapy.http import HtmlResponse
from selenium.webdriver.common.keys import Keys
from scrapy.exceptions import CloseSpider

import time


class JavaScriptMiddleware(object):
    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        s.retry = 0

        s.usr_id = "newsdog620"
        s.pw = "shiba620"
        s.driver = webdriver.PhantomJS()

        s.driver.get("https://nid.naver.com/nidlogin.login")
        elem = s.driver.find_element_by_id("id")
        elem.send_keys(s.usr_id)
        elem = s.driver.find_element_by_id("pw")
        elem.send_keys(s.pw)
        elem.send_keys(Keys.RETURN)
        time.sleep(1)
        print('login okay')

        crawler.signals.connect(s.spider_closed, signal=signals.spider_closed)
        return s

    def process_request(self, request, spider):
        if request.meta['reconnect']:
            self.driver.get("https://nid.naver.com/nidlogin.login")
            elem = self.driver.find_element_by_id("id")
            elem.send_keys(self.usr_id)
            elem = self.driver.find_element_by_id("pw")
            elem.send_keys(self.pw)
            elem.send_keys(Keys.RETURN)
            time.sleep(1)
            print('reconnect okay')
        print("rendering...")
        self.driver.get(request.url)
        time.sleep(1)
        body = self.driver.page_source.encode('utf-8')
        print("parsing... " + request.url)
        self.retry = 0
        return HtmlResponse(self.driver.current_url, body=body, encoding='utf-8', request=request)

    def process_response(self, request, response, spider):
        return response

    def process_exception(self, request, exception, spider):
        print("rendering error occurred!")
        print(str(exception))
        self.retry += 1
        if self.retry > 10:
            raise CloseSpider('max retries exceeded!')
        print("move to next url")
        if spider.url_list:
            tmp = spider.url_list.pop(0)
            next_url = tmp['url']
            rq = spider.Request(url=next_url, callback=spider.parse_post,
                                meta={'item': tmp['item'], 'reconnect': False})
            spider.visited_links.add(next_url)
            return rq
        else:
            spider.i += 1
            rq = spider.Request(spider.postPage.format(spider.i), dont_filter=True, callback=spider.parse)
            rq.meta['reconnect'] = False
            return rq

    def spider_closed(self, spider):
        self.driver.quit()
        print("driver closed!")
