import asyncio
from datetime import datetime, timedelta
from lxml import etree
import os
import aiohttp
import aiofiles


def println(text, color):
    print(f"\033[1;10;{color}m\r{text}\033[0m")


def generate_url(model, start, end):
    global save_path
    try:
        start = datetime(*start).date()
        end = datetime(*end).date() if end else datetime.now().date()
    except ValueError:
        raise ValueError("输入日期错误")

    if end <= start:
        raise ValueError(f"开始日期大于结束日期")
    #

    page_ls = []
    if model == "MONTH":
        save_path = f"{save_path}\\{start.year}-{start.month}月~{end.year}-{end.month}月"
        while start <= end:
            page_ls.append(
                (
                    f"https://yande.re/post/popular_by_month?month={start.month}&year={start.year}",
                    f"{start.year}-{start.month}"
                )
            )
            if start.month == 12:
                start = start.replace(year=start.year + 1, month=1)
            else:
                start = start.replace(month=start.month + 1)

    elif model == "DAY":
        save_path = f"{save_path}\\{start}日~{end}日"
        while start <= end:
            page_ls.append(
                (
                    f"https://yande.re/post/popular_by_day?day={start.day}&month={start.month}&year={start.year}",
                    f"{start.year}-{start.month}-{start.day}"
                )
            )
            start += timedelta(days=1)

    elif model == "WEEK":
        save_path = f"{save_path}\\{start}周~{end}周"
        start -= timedelta(days=start.weekday())
        while start <= end:
            page_ls.append(
                (
                    f"https://yande.re/post/popular_by_week?day={start.day}&month={start.month}&year={start.year}",
                    f"{start.year}-{start.month}-{start.day}"
                )
            )
            start += timedelta(weeks=1)
    else:
        raise ValueError(f'model参数错误:{model}', "请输入:DAY,WEEK,MONTH")
    return page_ls


async def download(session, info):
    url = info[0]

    try:
        async with session.get(url, proxy=proxy) as resp:
            content_type = resp.headers.get('Content-Type', '')
            if content_type == 'image/jpeg':
                async with aiofiles.open(info[1], 'wb') as file:
                    await file.write(await resp.read())
                    download_image.task_done()
            else:
                except_queue.put_nowait(info)

    except:
        except_queue.put_nowait(info)


async def download_image_control(session):
    global done_count

    running = []

    while True:
        await asyncio.sleep(0)
        if len(running) < max_running:
            info = await download_image.get()
            if info is None:
                break
            running.append(asyncio.create_task(download(session, info)))

        _ = []
        for task in running:
            if task.done():
                done_count += 1
            else:
                _.append(task)
        running = _
        print(f"\033[1;10;32m\r已完成任务:{done_count}\{total + errors}(当前以获取:{total}张+任务错误数:{errors}) 下载中的任务数:{len(running)}\033[0m", end='')
    await asyncio.gather(*running)
    for task in running:
        if task.done():
            done_count += 1
    print(f"\033[1;10;35m\r下载已完成:{done_count}\{total + errors}(当前以获取:{total}张+任务错误数:{errors})\033[0m", end='')


async def except_while():
    global errors
    while True:
        info = await except_queue.get()
        await download_image.put(info)
        errors += 1
        download_image.task_done()


async def main(url_ls):
    global total
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(limit=0, ssl=False)) as session:
        dic = asyncio.create_task(download_image_control(session))
        _ = asyncio.create_task(except_while())
        while url_ls:

            info = url_ls.pop(0)
            url = info[0]
            folder = f"{save_path}\\{info[1]}" if save_sort else save_path
            if not os.path.exists(folder):
                os.makedirs(folder)

            try:
                async with session.get(url, proxy=proxy) as resp:
                    html = etree.HTML(await resp.text())
                    urls = html.xpath('//*[@class="directlink largeimg"]/@href')
                    println(f'{info[1]} 获取到:{len(urls)}张', 33)
                    total += len(urls)
                    for url in urls:
                        sp = url.split('%20')
                        file_name = fr"{folder}\{sp[1]}.jpg"
                        await download_image.put((url, file_name))


            except Exception as e:
                println(f"page错误,重新加入列表:{url}", 31)
                url_ls.append(info)

        await download_image.join()
        _.cancel()
        await download_image.put(None)
        await dic


if __name__ == '__main__':
    parameter = {
        "model": "DAY",  # 获取排名模式按(日 星期 月),参数为:DAY,WEEK,MONTH
        "start": (2024, 2, 5),  # 开始日期：年,月,日 必填 包含开始日,月,星期
        "end": (),  # 结束日期 不填为获取当前日期,包含结束日,月,星期
        "save_path": r"F:\s",  # 保存位置 注意最后没有”\“
        "save_sort": False,  # 是否按照日期创建文件夹,否则全部图片存储在一个文件夹内
        "proxy": 'http://127.0.0.1:10809',  # 代理
        "max_post": 12,  # 同时下载数, 越大出错概率越大,出错任务会自动重新下载
        'dynamic_loading': True  # 是否根据下载数,动态获取下载图片,为否则一次获取所有可下载图片
    }
    ###############################################################
    total, errors, done_count = 0, 0, 0
    max_running = parameter["max_post"]
    download_image = asyncio.Queue(maxsize=parameter['max_post'] if parameter['dynamic_loading'] else 0)
    except_queue = asyncio.Queue(maxsize=0)
    proxy = parameter['proxy']
    save_path = parameter['save_path']
    save_sort = parameter['save_sort']
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(generate_url(parameter['model'], parameter['start'], parameter['end'])))
