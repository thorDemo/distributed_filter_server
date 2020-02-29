import re
import os
from threadpool import ThreadPool, makeRequests


def file_list_func(path):
    file_list = []
    for filePath in path:
        for top, dirs, non_dirs in os.walk(filePath):
            for item in non_dirs:
                file_list.append(os.path.join(top, item))
    return file_list


args = []
mission = file_list_func(['F:/email/赠送数据库/3500万QQ群精准客户名单数据库（分类完整）/'])
for line in mission:
    if '解压' not in line and 'txt' in line:
        args.append(line)


def filter_email(path):
    file = open(path, 'r', encoding='utf-8')
    target = open('source/3500w.txt', 'a+', encoding='utf-8')
    for qq in file:
        temp = re.sub(r'\D', "", qq)
        if len(temp) < 5:
            continue
        target.write(temp + 'qq.com\n')
        print(temp + 'qq.com')

    file.close()
    target.close()


pool = ThreadPool(50)
request = makeRequests(filter_email, args)
[pool.putRequest(req) for req in request]
pool.wait()
