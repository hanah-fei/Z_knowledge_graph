#!/usr/bin/env python
# coding=utf-8

from __future__ import absolute_import
from __future__ import division     
from __future__ import print_function


from baidu_baike.items import BaiduBaikeItem
import scrapy
from scrapy.http import Request
from bs4 import BeautifulSoup
import re
import urlparse
import json

class BaiduBaikeSpider(scrapy.Spider, object):
    name = 'baidu'
    allowed_domains = ["baike.baidu.com"]
    start_urls = ['https://baike.baidu.com/item/%E5%91%A8%E6%98%9F%E9%A9%B0/169917?fr=aladdin']
#    start_urls = ['https://baike.baidu.com/item/%E4%B8%8A%E6%B5%B7/114606'] # 上海
#    start_urls = ['https://baike.baidu.com/item/%E4%B8%83%E5%B0%8F%E7%A6%8F']
    
    def _get_from_findall(self, tag_list):
        result = []        
        for slist in tag_list:
            tmp = slist.get_text()
            result.append(tmp)
        return result

    def parse(self, response):
        # tooooo ugly,,,, but can not use defaultdict
        item = BaiduBaikeItem()
        for sub_item in [ 'title', 'title_id', 'abstract', 'infobox', 'subject', 'disambi', 'interPic', 'interLink', 'exterLink', 'relateLemma']:
            item[sub_item] = None

        mainTitle = response.xpath("//dd[@class='lemmaWgt-lemmaTitle-title']/h1/text()").extract()
        subTitle = response.xpath("//dd[@class='lemmaWgt-lemmaTitle-title']/h2/text()").extract()
        item['title'] = ' '.join(mainTitle)
        item['disambi'] = ' '.join(mainTitle + subTitle)

        soup = BeautifulSoup(response.text, 'lxml')
        summary_node = soup.find("div", class_ = "lemma-summary")
        item['abstract'] = summary_node.get_text().replace("\n"," ")

        page_category = response.xpath("//dd[@id='open-tag-item']/span[@class='taglist']/text()").extract()
        page_category = [l.strip() for l in page_category]
        item['subject'] = ','.join(page_category)

        # Get infobox
        all_basicInfo_Item = soup.find_all("dt", class_="basicInfo-item name")
        basic_item = self._get_from_findall(all_basicInfo_Item)
        basic_item = [s.strip().replace('\n', ' ') for s in basic_item]
        all_basicInfo_value = soup.find_all("dd", class_ = "basicInfo-item value" )
        basic_value = self._get_from_findall(all_basicInfo_value)
        basic_value = [s.strip().replace(u'收起', '') for s in basic_value]
        info_dict = {}
        for i, info in enumerate(basic_item):
            info_dict[info] = basic_value[i]
        item['infobox'] = json.dumps(info_dict)
       
        # Get inter picture
        selector = scrapy.Selector(response)
        img_path = selector.xpath("//img[@class='picture']/@src").extract()
        item['interPic'] = ','.join(img_path)

        inter_links_dict = {}
        soup = BeautifulSoup(response.text, 'lxml')
        inter_links = soup.find_all('a', href=re.compile(r"/item/"))
        for link in inter_links:
            new_url = link["href"]
            url_name = link.get_text()
            new_full_url = urlparse.urljoin('https://baike.baidu.com/', new_url)
            inter_links_dict[url_name] = new_full_url
        item['interLink'] = json.dumps(inter_links_dict)
        
        exter_links_dict = {}
        soup = BeautifulSoup(response.text, 'lxml')
        exterLink_links = soup.find_all('a', href=re.compile(r"/redirect/"))
        for link in exterLink_links:
            new_url = link["href"]
            url_name = link.get_text()
            new_full_url = urlparse.urljoin('https://baike.baidu.com/', new_url)
            exter_links_dict[url_name] = new_full_url
        item['exterLink'] = json.dumps(exter_links_dict)

        yield item

        soup = BeautifulSoup(response.text, 'lxml')
        links = soup.find_all('a', href=re.compile(r"/item/"))
        for link in links:
            new_url = link["href"]
            new_full_url = urlparse.urljoin('https://baike.baidu.com/', new_url)
            yield scrapy.Request(new_full_url, callback=self.parse)