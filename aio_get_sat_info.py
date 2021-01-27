# coding: utf-8
'''
运行aio_get_sat_urls会将系列卫星url保存下来
当前程序就是从这些url中爬具体的数据
'''
import requests
import pickle
import aiohttp
import aiofiles
import asyncio
from aiocsv import AsyncWriter
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from bs4.element import NavigableString
from tqdm import tqdm


IS_SOLO = False  # 这个变量用于控制单星或者系列星的CSV存储模式 True时保存到同一个CSV文件中
Threads_N = 50  # 协程任务数

TABLE_HEADER = ['原名', '国籍', '任务类型', 'Operator', '研发机构',
                '载荷', '结构', '推进', '能源', '设计寿命', '质量', '轨道高度',
                'Satellite', '国际卫星标识符', '发射日期', '发射基地', '', '运载火箭', '备注',
                'pic_name']

TABLE_HEADER_NEW = ['中文名称', '英文名称', '别名', '系列名', '每颗名', '国籍', '任务类型', '研发机构',
                    '设计寿命', '质量',  '轨道类型', '轨道高度', '轨道倾角',
                    '国际卫星标识符', '发射日期', '发射基地', '', '运载火箭', '备注',
                    ]

errors = []


def fit_header(data_basic, data_more):
    '''
    To fix the TABLE_HEADER_NEW add or delete some columns
    '''
    csv_column = ['', '', '', data_basic[0], data_more[0], data_basic[1], data_basic[2], data_basic[4],
                  data_basic[9], data_basic[10], '', data_basic[11], '',
                  data_more[1], data_more[2], data_more[3], data_more[4], data_more[5], data_more[6]]
    return csv_column


async def get_info(url):
    '''
    Find the data info in the page.

    '''
    global errors
    global IS_SOLO
    try:
        # aio get the page
        kv = {'user-agent': 'Mozilla/5.0'}
        session = aiohttp.ClientSession()
        response = await session.get(url, headers=kv,)
        r = await response.text(errors='ignore', encoding="windows-1252")  # 忽略页面中的非法字符
        await session.close()

        # get info from downloaded page
        soup = BeautifulSoup(r, 'lxml')
        title = soup.find('h1', ).text

        # find table 1
        table = soup.find('table', {'id': 'satdata'})
        data_basic = [title]
        for each in table.find_all('td', class_='rcont'):
            data_basic.append(each.text.replace(u'\xa0', ' '))

        # find table 2
        table = soup.find('table', {'id': 'satlist'})
        tdata = table.find_all('tr')
        data_more = []
        for tdata_line in tdata:
            s = tdata_line.find_all('td')
            data = []
            for each in s:
                data.append(each.text.replace(u'\xa0', ' '))
            data_more.append(data)

        # get pic
        filename = data_basic[0].replace('/', '_')  # filename is the title of the page
        imgs = soup.find_all('img')
        img_count = 0
        img_name = []
        if imgs is not None:
            # get pic url
            for img in imgs:
                img_url = img.attrs['src']
                # 判断链接是否为词条图片链接
                if img_url.find('img_sat') != -1:
                    # aio save picture
                    pic_url = urljoin(url, img_url)
                    type_name = pic_url[pic_url.rfind('.'):]
                    session = aiohttp.ClientSession()
                    response = await session.get(pic_url, headers=kv, )
                    if response.status == 200:
                        if img_count == 0:
                            f = await aiofiles.open('img/{}'.format(filename + type_name), mode='wb')
                        else:
                            f = await aiofiles.open('img/{}-{}{}'.format(filename, img_count, type_name), mode='wb')
                        await f.write(await response.read())
                        await f.close()
                    await session.close()
                    img_count = img_count + 1

                    # get pic name
                    # 这里分两种情况， 一种是img下一个对象就是名字， 另一种是img父对象
                    imgs = soup.find_all('img')
                    first_img_flag = True
                    if imgs is not None:
                        # get pic url
                        for img in imgs:
                            img_url = img.attrs['src']
                            # 判断链接是否为词条图片链接
                            if img_url.find('img_sat') != -1:
                                # get img name
                                if (img.next_sibling is None):
                                    if first_img_flag:
                                        first_img_flag = False
                                        contimg = soup.find(None, {'id': 'contimg'})
                                        p = contimg.find_all('p')
                                        for i in range(len(p)):
                                            img_name.append(p[i].text + ';')
                                else:
                                    if isinstance(img.next_sibling, NavigableString):
                                        contimg = soup.find(None, {'id': 'contimg'})
                                        p = contimg.find_all('p')
                                        for i in range(len(p)):
                                            img_name.append(p[i].text + ';')

                                    else:
                                        img_name.append(img.next_sibling.text + ';')

        # aio save the csv file
        if IS_SOLO:
            f = await aiofiles.open('doc/sat_solo.csv', 'a', encoding="utf-8", newline='')  # 解决文件换行问题
            w = AsyncWriter(f)
        else:
            f = await aiofiles.open('doc/{}.csv'.format(filename), 'w', encoding="utf-8", newline='')  # 解决文件换行问题
            w = AsyncWriter(f)
            await w.writerow(TABLE_HEADER_NEW)

        for line in data_more:
            if len(line) == 0:
                continue
            await w.writerow(fit_header(data_basic, line))
        await f.close()
    except Exception as e:
        print('[Error] in {}:\n{}'.format(url, str(e)))
        errors.append(url)
        await session.close()

    global pbar
    pbar.update(1)


def test_find_img_name(url):
    kv = {'user-agent': 'Mozilla/5.0'}
    r = requests.get(url, headers=kv)
    r.encoding = 'utf-8'
    soup = BeautifulSoup(r.text, 'lxml')
    imgs = soup.find_all('img')
    first_img_flag = True
    if imgs is not None:
        # get pic url
        for img in imgs:
            img_url = img.attrs['src']
            # 判断链接是否为词条图片链接
            if img_url.find('img_sat') != -1:
                # get img name
                if (img.next_sibling is None):
                    if first_img_flag:
                        first_img_flag = False
                        contimg = soup.find(None, {'id': 'contimg'})
                        p = contimg.find_all('p')
                        for i in range(len(p)):
                            print(p[i].text)
                else:
                    print(img.next_sibling.text)


# test find img_name
#  if __name__ == "__main__":
#      test_find_img_name('https://space.skyrocket.de/doc_sdat/explorer_ad.htm')

if __name__ == "__main__":
    # open urls from all_satellites_urls pickle
    f = open("./all_satellites_urls", 'rb')
    all_satellites_urls = pickle.load(f)
    f.close()

    # open urls from errors.txt file
    #  all_satellites_urls = []
    #  f = open('./errors.txt', 'r')
    #  for line in f.readlines():
    #      all_satellites_urls.append(line[:-1])
    #  f.close()

    # initial tqdm
    total_count = len(all_satellites_urls)
    tasks_count = total_count // Threads_N + 1
    pbar = tqdm(total=total_count)

    #  # 测试
    #  data_basic, data_more, pic_name = get_info('https://space.skyrocket.de/doc_sdat/starlink-v1-0.htm')
    #  # save to csv file
    #  f = open('{}.csv'.format(data_basic[0]), 'w', encoding="utf-8", newline='')  # 解决文件换行问题
    #  w = csv.writer(f)
    #  w.writerow(TABLE_HEADER)
    #
    #  for line in data_more:
    #      if len(line) == 0:
    #          continue
    #      w.writerow(data_basic + line + [pic_name])
    #  f.close()

    # 一次取出一些url 异步爬取数据
    for i in range(tasks_count):
        if i == tasks_count-1:
            task_urls = all_satellites_urls[(i)*Threads_N:]
        else:
            task_urls = all_satellites_urls[i*Threads_N:(i+1)*Threads_N]
        # start the aio tasks
        tasks = []
        for each in task_urls:
            tasks.append(asyncio.ensure_future(get_info(each)))

        loop = asyncio.get_event_loop()
        loop.run_until_complete(asyncio.wait(tasks))

    pbar.close()
    # save errors to file
    ef = open('errors.txt', 'w', newline='\r\n')
    ef.writelines(errors)
    ef.close()
