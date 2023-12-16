import asyncio
import random
import string
from datetime import datetime
import aiohttp
from tqdm import tqdm

from lxml import etree


def random_filename():
    characters = string.ascii_letters + string.digits  # 使用字母和数字
    random_string = ''.join(random.choice(characters) for i in range(10))
    return f'{datetime.now().strftime("%Y%m%d%H%M%S")}#{random_string}'


async def download_image(session, url, image_queue):
    try:
        #   pbar1.set_description_str(f'保存图片: {url}')
        async with session.get(url, proxy='http://127.0.0.1:10809') as resp:
            content_type = resp.headers.get('Content-Type', '')
            if content_type == 'image/jpeg':
                with open(fr"F:\image\{random_filename()}.jpg", "wb") as f:
                    f.write(await resp.read())
            else:
                await image_queue.put(url)
            image_queue.task_done()
    except:
        #  print("下载图片出错: ", url)
        await image_queue.put(url)


async def get_image(image_queue):
    tasks = []
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(limit=0, ssl=False)) as session:
        while url := await image_queue.get():
            tasks.append(asyncio.create_task(download_image(session, url, image_queue)))
        await asyncio.gather(*tasks)
    print('退出', 'get_image')


async def get_image_url(url_queue, image_queue):
    tasks = []
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(limit=0, ssl=False)) as session:
        while url := await url_queue.get():
            tasks.append(asyncio.create_task(download_image_url(session, url, url_queue, image_queue)))
        await asyncio.gather(*tasks)
    await image_queue.join()
    await image_queue.put(None)
    print('退出', 'get_image_url')


async def download_image_url(session, url, url_queue, image_queue):
    pbar2.set_description_str(f'处理图片url: {url}')
    try:
        async with session.get(url, proxy='http://127.0.0.1:10809') as resp:
            await image_queue.put(etree.HTML(await resp.text()).xpath('//*[@id="image"]/@src')[0])
            url_queue.task_done()
    except:
        #   print("获取图片地址出错: ", url)
        await url_queue.put(url)


async def download_page(session, url, page_queue, url_queue):
    #    pbar3.set_description_str(f'处理页面: {url}')
    try:
        async with session.get(url, proxy='http://127.0.0.1:10809') as resp:
            html = etree.HTML(await resp.text())
            pages = html.xpath('//*[@id="post-list-posts"]//li//div//a/@href')
            urls = [f"{URL}{right}" for right in pages]
            for _ in urls:
                await url_queue.put(_)
            page_queue.task_done()
    except:
        #  print("下载页面出错: ", url)
        await page_queue.put(url)


async def get_page(page_queue, url_queue):
    tasks = []
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(limit=0, ssl=False)) as session:
        while url := await page_queue.get():
            tasks.append(asyncio.create_task(download_page(session, url, page_queue, url_queue)))
        await asyncio.gather(*tasks)
    await url_queue.join()
    await url_queue.put(None)
    print('退出', 'page_queue')


async def put_page(page_queue, url_queue, sy, sm, ey, em):
    _ = asyncio.create_task(get_page(page_queue, url_queue))
    while (sy, sm) <= (ey, em):
        await page_queue.put(f"{URL}/post/popular_by_month?month={sm}&year={sy}")
        if sm == 12:
            sy += 1
            sm = 1
        else:
            sm += 1
    await page_queue.join()
    await page_queue.put(None)
    print('退出', 'put_page')


async def main():
    image_queue = asyncio.Queue(maxsize=5)
    page_queue = asyncio.Queue(maxsize=10)
    url_queue = asyncio.Queue(maxsize=20)

    page_task = asyncio.create_task(put_page(page_queue, url_queue, start_year, start_month, end_year, end_month))

    url_task = asyncio.create_task(get_image_url(url_queue, image_queue))
    image_task = asyncio.create_task(get_image(image_queue))

    await asyncio.gather(page_task, url_task, image_task)


if __name__ == '__main__':
    URL = "https://yande.re"

    pbar1 = tqdm(leave=False, position=3, bar_format='正在: {desc}', total=1, miniters=0)
    pbar2 = tqdm(leave=False, position=2, bar_format='正在: {desc}', total=1, miniters=0)
    pbar3 = tqdm(leave=False, position=1, bar_format='正在: {desc}', total=1, miniters=0)
    pbar4 = tqdm(leave=False, position=4, bar_format='正在: {desc}', total=1, miniters=0)

    start_year = 2020
    start_month = 1 # 包含开始月份

    end_year = 2023
    end_month = 10 # 包含结束月份

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
