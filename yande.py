from datetime import datetime, timedelta
import asyncio
from lxml import etree
import os
import aiofiles
import aiohttp
from tqdm import tqdm


def println(text: str, color: int):
    print(f"\033[1;10;{color}m\r{text}\033[0m", end='')


def generate_url(model, start, end):
    try:
        start = datetime(*start).date()
        end = datetime(*end).date() if end else datetime.now().date()
    except ValueError:
        raise ValueError("输入日期错误")

    if end <= start:
        raise ValueError(f"开始日期大于结束日期")
    page = {}
    if model == "MONTH":
      #  path = f"\\{start.year}-{start.month}月~{end.year}-{end.month}月"
        while start <= end:
            page[
                f"{start.year}-{start.month}"] = f"https://yande.re/post/popular_by_month?month={start.month}&year={start.year}"
            if start.month == 12:
                start = start.replace(year=start.year + 1, month=1)
            else:
                start = start.replace(month=start.month + 1)

    elif model == "DAY":
       # path = f"\\{start}日~{end}日"
        while start <= end:
            page[
                f"{start.year}-{start.month}-{start.day}"] = f"https://yande.re/post/popular_by_day?day={start.day}&month={start.month}&year={start.year}"
            start += timedelta(days=1)

    elif model == "WEEK":
      #  path = f"\\{start}周~{end}周"
        start -= timedelta(days=start.weekday())
        while start <= end:
            page[f"{start.year}-{start.month}-{start.day}"] = \
                f"https://yande.re/post/popular_by_week?day={start.day}&month={start.month}&year={start.year}"
            start += timedelta(weeks=1)
    else:
        raise ValueError(f'model参数错误:{model}', "请输入:DAY,WEEK,MONTH")
    return  page


async def get_image_url(session, url, proxy, mark, semaphore):
    async with semaphore:
        async with session.get(url, proxy=proxy) as resp:
            try:
                html = etree.HTML(await resp.text())
                return True, mark, html.xpath('//*[@class="directlink largeimg"]/@href'),
            except:
                return False, mark, []


async def download_image(session, semaphore, url, mark, save_path, proxy):
    async with semaphore:
        async with session.get(url, proxy=proxy,timeout=300) as resp:
            content_type = resp.headers.get('Content-Type', '')
            if content_type == 'image/jpeg':
                pbar = tqdm(total=int(resp.headers.get('Content-Length', 0)), leave=False, desc=f'下载 {mark}.jpg',
                            unit_scale=True, unit_divisor=1024, unit='KB')
                async with aiofiles.open(f'{save_path}\\{mark}.jpg', 'wb') as file:
                    while True:
                        chunk = await resp.content.read(10240)
                        if not chunk:
                            break
                        await file.write(chunk)
                        pbar.update(10240)
                pbar.close()
                return True, mark, url
            else:
                return False, mark, url


async def main(save_path: str, start: tuple, end, model, tag, tag_mode: str, proxy: str, max_post: int):
    """

    :param save_path:  保存路径
    :param start: 开始日期
    :param end: 结束日期
    :param model: 模式
    :param tag: 标签列表
    :param tag_mode: 标签模式
    :param proxy: 代理
    :param max_post: 并发数
    :return:
    """
    tag = set(tag)
    semaphore = asyncio.Semaphore(max_post)
    image_url = {}
    urls = generate_url(model, start, end)

    if not os.path.exists(save_path):
        os.makedirs(save_path)
    println('开始获取图片URL', 31)
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(limit=0, ssl=False)) as session:
        while urls:
            for completed_task in asyncio.as_completed(
                    [get_image_url(session, v, proxy, k, semaphore) for k, v in urls.items()]):
                state, key, ls = await completed_task
                if state:
                    num = 0
                    for url in ls:
                        sp = url.split('%20')
                        name = sp[1]
                        sp = set(sp)
                        if (tag_mode == "OR" and sp & tag) or \
                                (tag_mode == "AND" and (sp & tag == tag)) or \
                                (tag_mode == "NOT" and not sp & tag):
                            image_url[name] = url
                            num += 1
                    println(f'{key},获取到:{num}张,总计{len(image_url)}张', 33)
                    del urls[key]
                else:
                    println(f'{key},获取失败 即将重试', 31)
        pbar = tqdm(leave=False, position=0, bar_format='{desc}', total=1, miniters=0)
        num, total = 0, len(image_url)
        println(f"状态:{num}/{total}                                                               ", 32)
        while image_url:
            for completed_task in asyncio.as_completed(
                    [download_image(session, semaphore, v, k, save_path, proxy) for k, v in image_url.items()]):
                state, mark, url = await completed_task
                if state:
                    num += 1
                    # pbar.set_description_str(f"{num}/{total}")
                    println(f"状态:{num}/{total}", 32)
                    del image_url[mark]
        pbar.close()
    println('下载完毕!', 31)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(
        save_path=r"F:\s",
        start=(2024, 1, 1),
        end=(),
        model='MONTH',
        tag={'pussy'},
        tag_mode='OR',
        proxy='http://127.0.0.1:10809',
        max_post=6,
    )
    )
