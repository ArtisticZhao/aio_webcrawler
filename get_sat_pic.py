# coding: utf-8
import csv
import re
import asyncio
import aiohttp
import aiofiles
import traceback


MAX_TASKS = 100
ROOT = 'https://space.skyrocket.de'

total = 0
download_count = 0
errors = []


async def aio_get_pic(name, url):
    global download_count
    global total
    global errors

    download_count = download_count + 1
    type_name = url[url.rfind('.'):]
    print("[{}/{}]: {}".format(download_count, total, url))
    try:
        kv = {'user-agent': 'Mozilla/5.0'}
        session = aiohttp.ClientSession()
        response = await session.get(url, headers=kv, )
        if response.status == 200:
            f = await aiofiles.open('img/{}'.format(name + type_name), mode='wb')
            await f.write(await response.read())
            await f.close()
        await session.close()
    except Exception as e:
        print('[Error] in {}:\n{}'.format(url, str(e)))
        errors.append(url)
        await session.close()
        # traceback.print_exc()
        # print('traceback.format_exc():\n{}'.format(traceback.format_exc()))


def get_pic_url_from_csv(csv_file):
    with open(csv_file) as f:
        reader = csv.reader(f)
        result = {}
        for item in reader:
            # 忽略第一行
            if reader.line_num == 1:
                print(item[12], item[19])
                continue
            if len(item[19]) > 3:
                result[item[12]] = item[19]
        return result


def check_filename(name):
    rstr = r"[\/\\\:\*\?\"\<\>\|]"  # '/ \ : * ? " < > |'
    new_title = re.sub(rstr, "_", name)  # 替换为下划线
    return new_title


if __name__ == '__main__':
    pic_urls = get_pic_url_from_csv('sat.csv')
    total = len(pic_urls)
    index = 0
    pic_name = list(pic_urls.keys())
    while index < total:
        if total - index < MAX_TASKS:
            pn = pic_name[index:]
        else:
            pn = pic_name[index: index+MAX_TASKS]
        index = index + len(pn)
        tasks = list()
        for sat_name in pn:
            tasks.append(asyncio.ensure_future(aio_get_pic(check_filename(sat_name), ROOT + pic_urls[sat_name][2:])))

        loop = asyncio.get_event_loop()
        loop.run_until_complete(asyncio.wait(tasks))
    print(errors)