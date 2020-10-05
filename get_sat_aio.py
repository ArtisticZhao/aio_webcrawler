# coding: utf-8

import requests
import asyncio
import aiohttp
from bs4 import BeautifulSoup
import pickle
import csv
import traceback


START_YEAR = 1957
STOP_YEAR = 2020
ROOT = 'https://space.skyrocket.de'

total = 0
num = 0
errors = []
d = []


def get_index(url):
    kv = {'user-agent': 'Mozilla/5.0'}
    r = requests.get(url, headers=kv)
    r.encoding = 'utf-8'
    soup = BeautifulSoup(r.text, 'lxml')
    # tbody = soup.find('div', {'class': 'fd-list'})

    trs = soup.find_all('a')  # 获取全部超链接
    trs_l = list()
    is_header = False
    for each in trs:
        # 通过匹配地址中十分包含sdat来判断是否为卫星链接
        try:
            if each.attrs['href'].find('sdat') != -1:
                trs_l.append(each.attrs['href'])
        except:
            print('[Error] in {}'.format(url))
            print(each)
    return list(set(trs_l))


async def get_chapter(url):
    global errors
    try:
        kv = {'user-agent': 'Mozilla/5.0'}
        session = aiohttp.ClientSession()
        response = await session.get(url, headers=kv,)
        r = await response.text(errors='ignore')  # 忽略页面中的非法字符
        await session.close()
        global d
        global num

        num += 1
        print('[{0}/{1}]: {2}'.format(num, total, url))
        # r = requests.get(url, headers=kv)
        soup = BeautifulSoup(r, 'lxml')
        title = soup.find('h1', ).text
        # find table 1
        table = soup.find('table', {'id': 'satdata'})
        data = [title]
        for each in table.find_all('td', class_='rcont'):
            data.append(each.text.replace(u'\xa0', ' '))
        # find table 2
        table = soup.find('table', {'id': 'satlist'})
        tdata = table.find_all('tr')
        s = tdata[1].find_all('td')
        for each in s:
            data.append(each.text.replace(u'\xa0', ' '))
        # get pic
        p_div = soup.find('div', {'id': 'contimg'})
        if p_div is not None:
            ps = p_div.find_all('img')
            if len(ps)>0:
                p = ps[0].attrs['src']
            else:
                print("find mult pics")
                pic_table = soup.find('table', {'class': 'bx'})
                ps = pic_table.find_all('img')
                p = ps[0].attrs['src']
        else:
            p = ''
        data.append(p)
        data.append(url)
        d.append(data)
        await session.close()
    except Exception as e:
        print('[Error] in {}:\n{}'.format(url, str(e)))
        errors.append(url + '\n\r')
        traceback.print_exc()
        print('traceback.format_exc():\n{}'.format(traceback.format_exc()))



def test_get(url):
    kv = {'user-agent': 'Mozilla/5.0'}
    r = requests.get(url, headers=kv)
    r.encoding = 'utf-8'
    soup = BeautifulSoup(r.text, 'lxml')
    table = soup.find('div', {'id': 'contimg'})
    tdata = table.find_all('img')
    s = tdata[0].attrs['src']
    print(s)


# if __name__ == '__main__':
#     test_get('https://space.skyrocket.de/doc_sdat/starlink-v1-0.htm')
if __name__ == "__main__":
    IS_INDEX = False
    GET_ERROR = False
    if IS_INDEX:
        l = get_index('https://space.skyrocket.de/doc_chr/lau1957.htm')
        print(ROOT + l[0][2:])

        # 获取卫星列表
        satellites = []
        for year in range(START_YEAR, STOP_YEAR+1):
            index_url = "https://space.skyrocket.de/doc_chr/lau{0}.htm".format(year)
            print('Getting index in {}...'.format(year), end='')
            satellites.append(get_index(index_url))
            print(' OK')
        sum = 0
        for each in satellites:
            sum += len(each)
        print('find {0} satellites'.format(sum))
        f = open('satellites_url', 'wb')
        pickle.dump(satellites, f)
        f.close()
    elif not GET_ERROR:
        # 开始根据列表爬取数据
        f = open('satellites_url', 'rb')
        satellites = pickle.load(f)
        f.close()

        total = 0
        for each in satellites:
            total += len(each)
        print('find {0} satellites'.format(total))

        print('Starting...')
        i = START_YEAR
        for each in satellites:
            tasks = list()
            for sat in each:
                sat_url = ROOT + sat[2:]
                tasks.append(asyncio.ensure_future(get_chapter(sat_url)))
            print('{0}: {1} sats'.format(i, len(tasks)))
            loop = asyncio.get_event_loop()
            loop.run_until_complete(asyncio.wait(tasks))
            i += 1

        print('Saving...')
        f = open('sat.csv', 'a', encoding="utf-8", newline='')  # 解决文件换行问题
        w = csv.writer(f)

        for l in d:
            w.writerow(l)
        f.close()

        # save error url
        ef = open('err.txt', 'w', newline='')
        ef.writelines(errors)
        ef.close()
    else:
        # GET ERROR url
        f = open('err.txt')
        err_l = list()
        for each in f.readlines():
            if len(each) > 3:
                err_l.append(each[:-1])

        print("find {} errors, retrying...".format(len(err_l)))
        tasks = list()
        for each in err_l:
            tasks.append(asyncio.ensure_future(get_chapter(each)))
        loop = asyncio.get_event_loop()
        loop.run_until_complete(asyncio.wait(tasks))
