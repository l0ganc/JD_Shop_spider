import json
import scrapy
import simplejson
from django.core import serializers
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
import requests
from requests import Response

from bs4 import BeautifulSoup


def ajax_submit(request):
    item_array = []
    first_url = request.GET.get("url")
    print(first_url)
    response = requests.get(first_url)
    sel = scrapy.Selector(response)

    first_temp = sel.xpath('//div[@class="g-pager"]')
    pages = first_temp.xpath('./span/i/text()').extract_first()  # 该商铺一共有多少页商品
    second_temp = sel.xpath('//div[@class="f-result-sum"]')
    goods_num = second_temp.xpath('./span/text()').extract_first()  # 该商铺一共有多少个商品

    appId = sel.xpath('//input[@id="pageInstance_appId"]/@value')[0].extract()  # appId用于之后的分页
    pageInstanceId = sel.xpath('//input[@id="pageInstance_id"]/@value')[0].extract()  # pageInstanceId用于之后的分页
    print("appId: " + appId)
    print("pageInstanceId: " + pageInstanceId)
    print("pageNum: " + pages)
    print("goods_num: " + goods_num)

    goods = sel.xpath('//li[@class="jSubObject gl-item"]')
    # print(goods)    # 这里可以取到goods的值

    for good in goods:
        item1 = {}
        item1['ID'] = \
            good.xpath('./div/div[@class="jScroll"]/div[@class="jScrollWrap"]/ul/li[1]/@sid').extract()[0]
        # print(type(item1['ID']))
        # print(item1['ID'])
        # q = good.xpath('./div/div[@class="jGoodsInfo"]/div[@class="jDesc"]/a/@title').extract()
        # s = str(q).replace('u\'', '\'')
        # s = s.decode("unicode-escape")

        item1['good_name'] = good.xpath('./div/div[@class="jGoodsInfo"]/div[@class="jDesc"]/a/@title').extract()[0]
        item1['good_link'] = good.xpath('./div/div[@class="jPic"]/a/@href').extract()[0]
        item1['first_photo_link'] = \
            good.xpath('./div/div[@class="jScroll"]/div[@class="jScrollWrap"]/ul/li[1]/@data-src').extract()[0]
        # item1['total_pages'] = good.xpath('../ul/..div/')
        item1['total_pages'] = pages
        item1['total_goods_num'] = goods_num
        item1['appId'] = appId
        item1['pageInstanceId'] = pageInstanceId

        url_for_goods_comment = "https://club.jd.com/comment/productCommentSummaries.action?referenceIds=" \
                                + str(item1['ID'])
        # print(url_for_goods_comment)
        url_for_goods_price = "http://c0.3.cn/stock?skuId=" + str(item1['ID']) \
                              + "&area=1_72_2799_0&cat=855,9858,9991&extraParam=" + "{}"
        # print(url_for_goods_price)

        response_for_comment = requests.get(url_for_goods_comment)
        js_comment = json.loads(response_for_comment.text)
        item1['comment_num'] = js_comment['CommentsCount'][0]['CommentCount']  # 商品评论数搞定

        response_for_price = requests.get(url_for_goods_price)

        js_price = json.loads(response_for_price.text)

        if 'p' in js_price['stock']['jdPrice']:
            item1['price'] = js_price['stock']['jdPrice']['p']  # 商品价格搞定
        else:
            item1['price'] = item1['price'] = js_price['stock']['jdPrice']['op']  # 商品价格搞定

        item_array.append(item1)
        # print(type(item1))       # 把item存入item_array中

        # 以上是第一页商品的爬取

    # 下面开始爬取分页的数据
    for pageNum in range(2, int(pages)):
        print(pageNum)
        url_next = "https://module-jshop.jd.com/module/allGoods/goods.html?callback=jQuery&sortType=0&appId=" + \
                   appId + "&pageInstanceId=" + pageInstanceId + "&searchWord=&pageNo=" + str(pageNum) + \
                   "&direction=1&instanceId=101463647&modulePrototypeId=55555&moduleTemplateId=905542"
        # print(url_next)
        response_next = requests.get(url_next)

        # print(response_next.content)
        test = response_next.content
        if test.startswith(b'jQuery'):
            test = test[7:-1]
        else:
            continue
        # print(test)
        # print(type(test))
        final_next_response_json_dict = json.loads(test)
        sel_next = final_next_response_json_dict["HTML_CONTENT_KEY"]  # 这里就是那堆半html数据
        # print(type(sel_next))
        # print(sel_next)
        soup = BeautifulSoup(sel_next, "html.parser")
        # print(type(soup))
        # print(soup)
        goods_next_page = soup.find_all('li', attrs={'class': 'jSubObject gl-item'})
        # print(goods_next_page)
        for good_next in goods_next_page:
            item2 = {}
            item2['ID'] = good_next.find_all('span', attrs={'class': 'jdNum'})[0]['jdprice']  # ID get，会有点小问题
            print(item2['ID'])
            item2['good_name'] = good_next.find_all('div', attrs={'class': 'jDesc'})[0].find_all('a')[0].string
            item2['good_link'] = good_next.find_all('div', attrs={'class': 'jPic'})[0].find_all('a')[0]['href']
            item2['first_photo_link'] = good_next.find_all('li')[0]['data-src']
            # print(item2)
            item2['total_pages'] = pages
            item2['total_goods_num'] = goods_num
            item2['appId'] = appId
            item2['pageInstanceId'] = pageInstanceId

            url_for_goods_comment_next = "https://club.jd.com/comment/productCommentSummaries.action?referenceIds=" \
                                         + str(item2['ID'][0])
            print(url_for_goods_comment_next)
            url_for_goods_price_next = "http://c0.3.cn/stock?skuId=" + item2['ID'] + \
                                       "&area=1_72_2799_0&cat=855,9858,9991&extraParam=" + "{}"

            response_for_comment_next = requests.get(url_for_goods_comment_next)
            js_comment_next = json.loads(response_for_comment_next.text)
            item2['comment_num'] = js_comment_next['CommentsCount'][0]['CommentCount']  # 商品评论数搞定

            # print(url_for_goods_price_next)
            response_for_price_next = requests.get(url_for_goods_price_next)
            js_price_next = json.loads(response_for_price_next.text)

            if js_price_next['stock']['jdPrice']['op'] is None:
                item2['price'] = js_price_next['stock']['jdPrice']['p']  # 商品价格搞定
                print("op is null")
                print(item2['price'])
            else:
                item2['price'] = item2['price'] = js_price_next['stock']['jdPrice']['op']  # 商品价格搞定
                print("p is null")
                print(item2['price'])


            # print(item2)
            item_array.append(item2)

    print("**********************************************************************")
    print("**********************************************************************")
    print("**********************************************************************")

    # print(item_array)
    # print(len(item_array))
    # print(type(item_array))

    data = json.dumps(item_array)
    print(data)

    return HttpResponse(data)


def spider(request1):
    return render(request1, "spider.html")
