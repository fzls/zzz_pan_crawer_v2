import logging
import os
import re
import string
import sys
import time
from queue import PriorityQueue
from random import randint

import pymysql
import pymysql.cursors
import requests

logging.addLevelName(level=25, levelName='MyINFO')
MyINFO = 25

logging.basicConfig(level=MyINFO,
                    format='%(asctime)s [line:%(lineno)d] %(levelname)s: %(message)s',
                    datefmt='%H:%M:%S')

CODE_LENGTH = 7
BASE_URL = "http://zzzpan.com/"
PARAMs = "?/file/view-"
SUFFIX = ".html"
ALPHABETS = string.ascii_uppercase[:] + string.digits
VISITED = set()
cnt = 0
url_cnt = 0
FAIL = 0
BANNED = 0

KB = 1024
MB = 1024 * KB
GB = 1024 * MB
SECOND = 1
MINUTE = 60 * SECOND
HOUR = 50 * MINUTE
DAY = 24 * HOUR

# enumerate for url info
DOWNLOAD_TIMES = 0
URL = 1
FILE_NAME = 2
FILE_SIZE = 3
DOWNLOAD_LINK = 4
URLS = 5

initial_urls = ["http://zzzpan.com/?/file/view-KN80TPI.html",
                "http://zzzpan.com/?/file/view-PNCCAVV.html",
                "http://zzzpan.com/?/file/view-QN4OH2T.html",
                "http://zzzpan.com/?/file/view-NN4KPVD.html",
                "http://zzzpan.com/?/file/view-FN5I2QS.html",
                "http://zzzpan.com/?/file/view-JNNI9HK.html",
                "http://zzzpan.com/?/file/view-DNPRTHB.html",
                "http://zzzpan.com/?/file/view-EN4H384.html",
                "http://zzzpan.com/?/file/view-BNVFFO1.html",
                "http://zzzpan.com/?/file/view-QN8VWS5.html",
                "http://zzzpan.com/?/file/view-UN8VWRE.html",
                "http://zzzpan.com/?/file/view-DO502Y2.html",
                "http://zzzpan.com/?/file/view-UNJLA75.html",
                "http://zzzpan.com/?/file/view-HN7O7BJ.html",
                "http://zzzpan.com/?/file/view-SNQP3JG.html",
                "http://zzzpan.com/?/file/view-ANO6QMZ.html",
                "http://zzzpan.com/?/file/view-HN4IXT5.html",
                "http://zzzpan.com/?/file/view-VN4IXSY.html",
                "http://zzzpan.com/?/file/view-KN7IL81.html",
                "http://zzzpan.com/?/file/view-MNQP3YA.html",
                ]


# class UrlInfo(object):
#     def __init__(self, download_times, url, file_name, file_size, download_link, urls):
#         self.download_times = download_times
#         self.url = url
#         self.file_name = file_name
#         self.file_size = file_size
#         self.download_link = download_link
#         self.urls = urls
#
#     def __str__(self):
#         return str(
#             self.download_times) + ", " + self.url + ", " + self.file_name + ", " + self.file_size + ", " + self.download_link + ", " + str(
#             self.urls)


# def print_size(size):
#     if size < KB:
#         print("file size is %.2f B" % (size))
#     elif size < MB:
#         print("file size is %.2f KB" % (size / KB))
#     elif size < GB:
#         print("file size is %.2f MB" % (size / MB))
#     else:
#         print("file size is %.2f GB" % (size / GB))


def get_readable_time(_t):
    t = int(_t)
    day = int(t / DAY)
    hour = int(t % DAY / HOUR)
    min_ = int(t % HOUR / MINUTE)
    sec = int(t % MINUTE / SECOND)
    sec += _t - t
    sec = int(sec*1000)/1000.0
    result = ''
    if day > 0:
        result = str(day) + " d " + str(hour) + " h " + str(min_) + " m " + str(sec) + " s"
    elif hour > 0:
        result = str(hour) + " h " + str(min_) + " m " + str(sec) + " s"
    elif min_ > 0:
        result = str(min_) + " m " + str(sec) + " s"
    else:
        result = str(sec) + " s"
    return result
    pass


def my_timer(total):
    DELAY = int(total)
    for t in range(DELAY):
        time.sleep(1)
        sys.stdout.write("\rTime elapsed : [ %s ]     ||||   remaining : [ %s ] " % (
            get_readable_time(t + 1), get_readable_time(DELAY - t - 1)))
    # the .x time like .6 in 10.6s
    time.sleep(total - DELAY)
    sys.stdout.write("\n")


def fetch_file_info(url, q):
    # -------download this url

    # 伪装浏览器
    headers = {
        'Connection': 'keep-alive',
        'Cache-Control': 'max-age=0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Upgrade-Insecure-Requests': '1',
        'Save-Data': 'on',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/49.0.2623.110 Safari/537.36',
        'DNT': '1',
        'Accept-Encoding': 'gzip, deflate, sdch',
        'Accept-Language': 'en,zh-CN;q=0.8,zh;q=0.6,zh-TW;q=0.4,en-GB;q=0.2'
    }

    try:
        html = requests.post(url, headers=headers)
    except requests.RequestException as e:
        logging.exception('except: %s' % e)
        sleep_after_banned("fetch file info")
        # fetch_file_info(url, q)
        return

    # if not found such file, add cnt for fail and exit
    if html.status_code != 200:
        global FAIL
        FAIL += 1
        logging.warning("%s is invalid, error code: %d" % (url, html.status_code))
        return

    # set encoding
    html.encoding = "utf-8"

    # find link
    download_link = re.search(r'href="(.+?)" title="本站下载"', html.text).group(1)

    # find name and format
    file_prefix = re.search(r'<p>文件名称：(.+?)</p>', html.text).group(1)
    file_suffix = re.search(r'<p>文件类型：(.+?)</p>', html.text).group(1)
    file_name = file_prefix + "." + file_suffix

    # find size
    file_size = re.search(r'<p>文件大小：(.+)</p>', html.text).group(1)

    # download times
    download_times = int(re.search(r'<p>下载次数：(\d+)次</p>', html.text).group(1))

    # upload time
    upload_time = re.search(r'<p>上传时间：(.+)</p>', html.text).group(1)

    # find new urls
    urls = re.findall(r'<li><a href="(.+?)">', html.text)
    # add base url
    for i in range(urls.__len__()):
        urls[i] = BASE_URL + urls[i]

    # put into priority queue
    q.put((-1 * download_times, url, file_name, file_size, download_link, urls))

    # mark visited
    VISITED.add(url)

    # save to database
    global config
    connection = pymysql.connect(**config)
    try:
        with connection.cursor() as cursor:
            # Read a single record
            sql = "INSERT INTO anime(download_times, url, file_name, file_size, download_link,upload_time, url_1, url_2, url_3) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)"
            cursor.execute(sql, (
                download_times, url, file_name, file_size, download_link, upload_time, urls[0], urls[1], urls[2]))
    finally:
        connection.close()
    logging.log(MyINFO, "[ " + str(download_times) + " : " + file_name + " ] <-----> SAVE TO DB")

    # sleep for a while to prevent from being banned
    sleep_after_visit(file_name)
    reconnect_and_sleep_after_fetched_max_files()


def reconnect_and_sleep_after_fetched_max_files():
    global url_cnt
    url_cnt += 1
    if url_cnt % MAX_PER_IP == 0:
        logging.log(MyINFO, "fetched %d files, reconnect network and sleep to prevent from being banned" % url_cnt)
        reconnect_net()
        t = SLEEP_AFTER_DOWNLOAD_MAX_FILE + randint(0, 10 * 1000) / 1000  # 0.0s ~ 10.0s
        logging.log(MyINFO, 'sleep for %s' % get_readable_time(t))
        my_timer(t)


def sleep_after_visit(file_name):
    from random import randint
    global SLEEP_L, SLEEP_H, MAX_PER_IP
    sleep_time = randint(SLEEP_L * 1000, SLEEP_H * 1000) / 1000
    logging.log(MyINFO, "sleep for %s when fetching file info [ %s ]" % (get_readable_time(sleep_time), file_name))
    my_timer(sleep_time)


def sleep_after_banned(message):
    global BANNED, SLEEP_AFTER_BANNED
    BANNED += 1
    reconnect_net()
    _SLEEP_AFTER_BANNED = SLEEP_AFTER_BANNED + randint(0, 60 * 1000) / 1000  # 0.0s ~ 60.0s
    logging.log(MyINFO,
                '%d th benned when %s, sleep for %s' % (BANNED, message, get_readable_time(_SLEEP_AFTER_BANNED)))
    my_timer(_SLEEP_AFTER_BANNED)


def get_size_in_Byte(file_size):
    size = re.search(r'(\d+(\.\d+)?)\s*(KB|MB)', file_size)
    number = float(size.group(1))
    suffix = size.group(3)
    if suffix == "KB":
        return number * KB
    elif suffix == "MB":
        return number * MB
    else:
        return -1
    pass


#  test data
# file_sizes = ["1.55 MB",
#               "1.69 MB",
#               "1.86 MB",
#               "1.92 MB",
#               "1.97 MB",
#               "10.1 MB",
#               "10.13 MB",
#               "1016.55 KB",
#               "103.99 KB",
#               "11.05 KB",
#               "11.72 KB",
#               "112.21 KB",
#               "113.06 KB",
#               "115.58 KB",
#               "128.95 KB",
#               "13.45 KB",
#               "13.84 KB",
#               "134.73 KB",
#               "135.47 KB",
#               "135.78 KB",
#               "14.77 KB",
#               "142.59 KB"
#               ]
# for file_size in file_sizes:
#     size = re.search(r'(\d+(\.\d+)?)\s*(KB|MB)',file_size)
#     print(size)
#     print(size.group(1))
#     print(size.group(3))


def download_file(urlInfo, q):
    global cnt, NEED_DOWNLOAD
    download_link = urlInfo[DOWNLOAD_LINK]
    file_name = urlInfo[FILE_NAME]
    logging.log(MyINFO, "\n------------------------------------------------------------------")
    logging.log(MyINFO, "downloaded times : %d" % urlInfo[DOWNLOAD_TIMES])
    if NEED_DOWNLOAD:
        # if file not exist, download it
        if not os.path.exists(os.getcwd() + '\\' + file_name):
            # print banner
            cnt += 1
            logging.log(MyINFO, "\n----------------------------the %d th----------------------------" % cnt)
            logging.log(MyINFO, "current url: %s" % urlInfo[URL])

            start = time.clock()
            logging.log(MyINFO, "%s is downloading" % file_name)
            logging.log(MyINFO, "file link is %s" % download_link)

            # download file
            try:
                downloaded_file = requests.get(download_link, stream=True)
                # find size
                start_time = time.time()
                file_size = urlInfo[FILE_SIZE]
                logging.log(MyINFO, "file size is %s" % file_size)

                # write into local
                logging.log(MyINFO, "%s is saving to local" % file_name)
                with open(file_name, "wb") as file:
                    count = 1
                    block_size = 512
                    total_size = get_size_in_Byte(file_size)
                    for chunk in downloaded_file.iter_content(chunk_size=block_size):
                        if chunk:  # filter out keep-alive new chunks
                            duration = time.time() - start_time
                            progress_size = int(count * block_size)
                            if (duration == 0):
                                duration = 0.1
                            speed = int(progress_size / (KB * duration))
                            percent = int(count * block_size * 100 / total_size)
                            remain_time = (total_size - progress_size) * duration / progress_size
                            sys.stdout.write(
                                "\r.......%d%%, %d KB, %d KB/s, [ %s passed | about %s remain ]" %
                                (percent, progress_size / KB, speed, get_readable_time(duration),
                                 get_readable_time(remain_time)))
                            file.write(chunk)
                            file.flush()
                            os.fsync(file.fileno())
                            count += 1
                    sys.stdout.write("\n")
                end = time.clock()
                logging.log(MyINFO, "file download and saved using %s" % get_readable_time(end - start))
            except requests.RequestException as e:
                logging.exception('except: %s' % e)
                sleep_after_banned("downloading " + file_name)
                # download_file(urlInfo, q)
                return
        else:
            logging.log(MyINFO, "%s already downloaded" % file_name)

    # add new unvisited urls into q
    urls = urlInfo[URLS]
    for url in urls:
        if url not in VISITED:
            fetch_file_info(url, q)

    logging.log(MyINFO, "remaining urls : %d  |||-----|||  newly fetched urls : %d" % (q.qsize(), url_cnt))


# def generate_next_random_url():
#     code = ''
#     for i in range(CODE_LENGTH):
#         code += choice(ALPHABETS)
#     return BASE_URL + PARAMs + code + SUFFIX


# def download_file_from_n_random_file(n):
#     for i in range(n):
#         url = ''
#         while True:
#             url = generate_next_random_url()
#             if url not in VISITED:
#                 VISITED.add(url)
#                 break
#         download_file(url)


def reconnect_net():
    os.system("rasdial /disconnect")
    os.system("rasdial MyVPN 3130101213 y19950425")
    # os.system("rasdial MyVPN 3130104501 300014")
    # print new ip
    import subprocess, locale
    p = subprocess.Popen("ipconfig", stdin=subprocess.PIPE, stdout=subprocess.PIPE, shell=True).communicate()[0]
    s = p.decode(locale.getpreferredencoding(False))
    ip = re.search(
        r'IPv4 Address. . . . . . . . . . . : (.+)\r\n   Subnet Mask . . . . . . . . . . . : 255.255.255.255\r\n',
        s).group(1)
    logging.log(MyINFO, "current ip is %s" % ip)


# def getTopDownloadedFiles(initial_urls, max_time):
#     global cnt, file_top_download
#     # reconnect net
#     reconnect_net()
#     q = PriorityQueue()
#     records = PriorityQueue()
#     # 加入初始urls
#     for url in initial_urls:
#         fetch_file_info(url, q)
#     # 开始广度优先遍历
#     while True:
#         urlInfo = q.get()
#         url = urlInfo[URL]
#         if url is None:
#             break
#         VISITED.add(url)
#         records.put(urlInfo)
#         # add new unvisited urls into q
#         urls = urlInfo[URLS]
#         for url in urls:
#             if BASE_URL + url not in VISITED:
#                 fetch_file_info(BASE_URL + url, q)
#         logging.log(MyINFO, "remaining urls : %d" % q.qsize())
#         if cnt >= max_time:
#             return
#     total = records._qsize()
#     for i in range(total):
#         anime = records.get()
#         file_top_download.write(anime[DOWNLOAD_TIMES] + " : " + anime[FILE_NAME])


def fetch_initial_file_info_from_db(q):
    global NEED_UPDATE
    if NEED_UPDATE:
        update_urls_in_each_row()
    # fetch urls
    global config
    connection = pymysql.connect(**config)
    try:
        with connection.cursor() as cursor:
            cursor.execute("select download_times,url,file_name,file_size,download_link,url_1,url_2,url_3 from anime")
            result = cursor.fetchall()
            logging.log(MyINFO, "fetch %d urlInfo from database" % cursor.rowcount)
            for r in result:
                q.put((-1 * r['download_times'], r['url'], r['file_name'], r['file_size'], r['download_link'],
                       [r['url_1'], r['url_2'], r['url_3']]))
                VISITED.add(r['url'])
    finally:
        connection.close()


def download_file_by_bfs(initial_urls, max_time):
    global cnt
    # reconnect net
    reconnect_net()
    q = PriorityQueue()
    fetch_initial_file_info_from_db(q)
    # 开始广度优先遍历
    while True:
        urlInfo = q.get()
        url = urlInfo[URL]
        if url is None:
            break
        download_file(urlInfo, q)
        if cnt >= max_time:
            return


def update_url(url, _urls):
    # if three urls are all not in database, stop here
    stop = True
    for _url in _urls:
        if _url in VISITED:
            stop = False
            break
    if stop:
        return;
    # 伪装浏览器
    headers = {
        'Connection': 'keep-alive',
        'Cache-Control': 'max-age=0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Upgrade-Insecure-Requests': '1',
        'Save-Data': 'on',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/49.0.2623.110 Safari/537.36',
        'DNT': '1',
        'Accept-Encoding': 'gzip, deflate, sdch',
        'Accept-Language': 'en,zh-CN;q=0.8,zh;q=0.6,zh-TW;q=0.4,en-GB;q=0.2'
    }

    try:
        html = requests.post(url, headers=headers)
    except requests.RequestException as e:
        logging.exception('except: %s' % e)
        sleep_after_banned("update info for " + url)
        # update_url(url)
        return

    # if not found such file, add cnt for fail and exit
    if html.status_code != 200:
        global FAIL
        FAIL += 1
        logging.warning("%s is invalid, error code: %d" % (url, html.status_code))
        return

    # set encoding
    html.encoding = "utf-8"

    # find new urls
    urls = re.findall(r'<li><a href="(.+?)">', html.text)
    # add base url
    for i in range(urls.__len__()):
        urls[i] = BASE_URL + urls[i]

    # update urls
    global config
    connection = pymysql.connect(**config)
    try:
        with connection.cursor() as cursor:
            update_sql = "UPDATE anime set url_1= %s,url_2=%s,url_3=%s WHERE url=%s"
            cursor.execute(update_sql, (urls[0], urls[1], urls[2], url))
    finally:
        connection.close()


def init_url_into_db(initial_urls):
    reconnect_net()
    # drop old dates
    global config
    connection = pymysql.connect(**config)
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "delete from anime")
    finally:
        connection.close()
    logging.log(MyINFO, "anime all clear")
    # add init url
    dump = PriorityQueue()
    for url in initial_urls:
        fetch_file_info(url, dump)
    print("initialize finished")


def update_urls_in_each_row():
    global config
    connection = pymysql.connect(**config)
    r_cnt = 0
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "select url,url_1,url_2,url_3 from anime")
            result = cursor.fetchall()
            r_cnt = cursor.rowcount
            logging.log(MyINFO, "fetch %d urlInfo from database to ---UPDATE---" % r_cnt)
            cnt_update = 0
            start_time = time.time()
            # preprocess visited
            global VISITED
            for r in result:
                VISITED.add(r['url'])
            for r in result:
                update_url(r['url'], [r['url_1'], r['url_2'], r['url_3']])
                cnt_update += 1
                duration = time.time() - start_time
                percent = 100 * cnt_update / r_cnt
                speed = cnt_update / duration
                sys.stdout.write("\r.......%.2f%%, %d urlInfo , %.2f p/s, %s passed" %
                                 (percent, cnt_update, speed, get_readable_time(duration)))
            sys.stdout.write("\n")
    finally:
        connection.close()
    logging.log(MyINFO, "UPDATED %d urlInfos in database" % r_cnt)
    pass


#########################################-----MAIN-----########################################
# data base config
config = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': 'y19950425',
    'db': 'zzz',
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor,
    'autocommit': True,
}

## configs
SAVE_DIR = "downloaded_files"
SAVE_DIR_top = "top_downloaded_files"

# check if need mkdir :working dir
if SAVE_DIR not in os.listdir(os.getcwd()):
    os.mkdir(os.getcwd() + "/" + SAVE_DIR)
os.chdir(os.getcwd() + "/" + SAVE_DIR)

# defined intervals
SLEEP_L = 0.1  # s
SLEEP_H = 0.2  # s
MAX_PER_IP = 500  # times
SLEEP_AFTER_BANNED = 90.0  # s
SLEEP_AFTER_DOWNLOAD_MAX_FILE = 15.0  # s
####
TOTAL = 10000
NEED_UPDATE = False
NEED_DOWNLOAD = True

## only need to run the first time
# init_url_into_db(initial_urls)
#
# delay for a piece of time at the start
DELAY = 0 * MINUTE + 30 * SECOND
logging.log(MyINFO, "delay for %s at the start" % get_readable_time(DELAY))
my_timer(DELAY)
# doing work
download_file_by_bfs(initial_urls, TOTAL)

# print result
total_downloaded = len([name for name in os.listdir('.') if os.path.isfile(name)])
print("-------------------------final result-------------------------")
print("Files downloaded so far: ", total_downloaded)
print("FAIL : ", FAIL)
