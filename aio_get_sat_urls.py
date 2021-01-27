# coding: utf-8
'''
This is an web crawler which get the satellites information from Gunter's Space Page.
The satellites list divide by year.
'''
import pickle
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from collections import Counter
import aiohttp
import asyncio


page_counter = 0


async def get_index(url, all_satellites):
    '''
    @ input: url, the url of year page.
    @ output: list of all satellites link in the page.
    '''
    global page_counter
    kv = {'user-agent': 'Mozilla/5.0'}
    session = aiohttp.ClientSession()
    response = await session.get(url, headers=kv,)
    r = await response.text(errors='ignore')  # 忽略页面中的非法字符
    await session.close()

    print("page_counter: {}".format(page_counter))
    page_counter = page_counter + 1

    soup = BeautifulSoup(r, 'lxml')
    # tbody = soup.find('div', {'class': 'fd-list'})

    trs = soup.find_all('a')  # 获取全部超链接
    for each in trs:
        # 通过匹配地址中十分包含sdat来判断是否为卫星链接
        try:
            if each.attrs['href'].find('sdat') != -1:
                # 使用urljoin把相对路径转换为绝对URL路径
                all_satellites.append(urljoin(url, each.attrs['href']))
        except Exception as e:
            print(e)
            print('[Error] in {}'.format(url))
            print(each)
    print("ok")
    await session.close()


def get_all_sat_url():
    '''
    这个函数会调用get_index，来获取全部的卫星链接；
    在这个过程中进行去这个函数会调用get_index，来获取全部的卫星链接，在这个过程中进行去重
    '''
    START_YEAR = 1957
    STOP_YEAR = 2021
    all_satellites_urls = []
    index_tasks = []
    for year in range(START_YEAR, STOP_YEAR+1):
        index_url = "https://space.skyrocket.de/doc_chr/lau{0}.htm".format(year)
        index_tasks.append(asyncio.ensure_future(get_index(index_url, all_satellites_urls)))
    print('find index in {0} pages'.format(len(index_tasks)))
    loop = asyncio.get_event_loop()
    loop.run_until_complete(asyncio.wait(index_tasks))

    # 进行重复计数
    counter = Counter(all_satellites_urls)
    # 只筛选出重复的内容， 并返回
    mult = [key for key, value in counter.items()if value == 1]
    return mult


if __name__ == "__main__":
    all_satellites_urls = get_all_sat_url()
    print("len: {0}, {1}".format(len(all_satellites_urls), all_satellites_urls[0]))
    f = open('all_satellites_urls', 'wb')
    pickle.dump(all_satellites_urls, f)
    f.close()
