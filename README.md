# Yande.re 爬虫
## 按照 月/周/日  爬取热门图片
|参数      | 示例     |类型    | 解释    |
|--------- | -------- |--------|--------|
| `model`  | `DAY`|  str      |                 参数有:DAY,WEEK,MONTH (日,星期,月)
| `start`  |`(2024, 2, 5)`|  tuple(int,int,int)  |             开始日期:(年,月,日)   包含开始日期
| `end`    | `()`|   同上        |                 结束日期:不填为获取当前日期 包含结束日期
| `save_path`| `F:\s`| str     |               保存位置 注意最后没有`\`
| `proxy`| `http://127.0.0.1:10809`|  str|   代理 
| `max_post`| `12`|   int           |       同时下载数, 越大出错概率越大,出错任务会自动重新下载
| `tag`| `{'white_hair'}`|   set           |    标签请自行查找
| `tag_mode`| `OR`|   str           |       参数有:OR(包含集合里任意一个标签的图片),AND(包含集合里全部标签的图片),NOT(不包含集合里任意一个标签的图片)

