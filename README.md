# crawlers

## depndency
1. scrapy
2. selenium (phantom.js)

## log
* unix계열 /var/log/ 아래에 생성 **로그정보가 없을시 6시간정도의 데이터를 크롤링**

## Spitz_Crawler
### spider
* **spitz_crawler** : 오늘의 유머 크롤링
### how to use
* $ scrapy crawl spitz_crawler

## Beagle_Crawler
### spider
* **beagle_crawler_bbs** : 뽐뿌 자유게시판 크롤링
* **beagle_crawler_etc_info** : 뽐뿌 생활정보 게시판 크롤링
* **beagle_crawler_app_info** : 뽐뿌 앱정보 게시판 크롤링
* **beagle_crawler_ppomppu** : 뽐뿌 뽐뿌게시판 크롤링
### how to use
* $ scrapy crawl beagle_crawler_bbs
* $ scrapy crawl beagle_crawler_etc_info
* $ scrapy crawl beagle_crawler_app_info
* $ scrapy crawl beagle_crawler_ppomppu

## Poodle_Crawler
### spider
* **poodle_crawler** : dcinside 크롤링
### how to use
* $ scrapy crawl poodle_crawler -a gall_id=<갤러리 id>

## Dachshund_Crawler
### spider
* **dachshund_crawler** : 네이버카페 레몬테라스 크롤링
### how to use
* $ scrapy crawl dachshund_crawler
