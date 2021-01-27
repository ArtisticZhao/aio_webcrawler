# 异步卫星信息爬虫
## Introduction
From the [Gunter's Space Page](https://space.skyrocket.de/)
The webcrawler use the asyncio to speed up the download process.

## Requirements
BeautifulSoup
aiocsv
aiofiles
aiohttps

## Usage
0. make the directories.
```shell
mkdir img
mkdir doc
```

1. get the satellites indexes
```shell
python3 ./aio_get_sat_urls.py
```

2. get the satellites informations from the indexes
```shell
python3 ./aio_get_sat_info.py
```

**NOTE:** To modify the webcrawler saved files' contexts, please read the comments in the code.
