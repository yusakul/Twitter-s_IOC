import re
import time
import maya
from selenium import webdriver
from bs4 import BeautifulSoup
import sqlite3 as sq
import iocextract

start_time = time.time()

def links():
    account = ["360CoreSec", "RedDrip7", "Timele9527","clearskysec", "blackorbird"] # , "kyleehmke", "malwrhunterteam"
    for i in range(len(account)):
        account[i] = ("https://twitter.com/" + account[i])
    return (account)

def CreateDataBase():
    con = sq.connect("Twitter.db")
    con.execute("""CREATE TABLE IF NOT EXISTS TwittersIoC (
        Account TEXT,
        LinkToTweet TEXT,
        DateTime TEXT,
        Hashtag TEXT,
        TypeIoC TEXT,
        IoC TEXT
    )""")
    con.execute("""DELETE FROM TwittersIoC""")
    con.commit()
    return (con)

def Insert(con,name,linkTweet, DTime, Hashtag, Type,IoC):
    list = [(str(name), str (linkTweet), str(DTime), str(Hashtag), str(Type), str(IoC))]
    cur = con.cursor()
    if IoC:
        cur.execute("select * from TwittersIoC where  IoC=?", [str(IoC)])
        if cur.fetchone() is None:
            con.executemany("""INSERT INTO TwittersIoC VALUES (?, ?, ?, ?, ?, ?)""", list)
            con.commit()

def parsing(driver,con):
    SCROLL_HEIGHT = 1080
    SCROLL_PAUSE_TIME = 0.5
    dt_new = []
    dt_last = []
    time.sleep(5)
    while True:
        url = driver.page_source
        soup = BeautifulSoup(url, 'html.parser')

        #Find the area of the tweet that contains all the data
        tweets_area = soup.findAll('div', {'class': ['css-1dbjc4n r-1iusvr4 r-16y2uox r-1777fci r-kzbkwu']})

        #Finding the time of the tweet
        for i in range (len(tweets_area)):
            dt = tweets_area[i].find('time')
            dt_new.append(maya.parse(dt.get('datetime')).datetime().date())

        if (len(dt_new) > len(dt_last)) and (not not dt_last):
            l = len(dt_new) - len(dt_last)
            for i in range (l) : dt_last.append(dt_last[0])

        # 我们取最后一个已知月份
        k = len(dt_new) - 1
        # 如果日期不早于二月
        try:
            if dt_new[k].month >= 1 and dt_new[k].year == 2021:
                for i in range(len(tweets_area)):
                    # 如果列表为空
                    if (not dt_last) or (dt_last[i] != dt_new[i]):
                        name = tweets_area[i].find('span',
                                                   {'class': [
                                                       'css-901oao css-16my406 r-poiln3 r-bcqeeo r-qvutc0']}).get_text(
                            strip=True)

                        linkTweet = tweets_area[i].find('a', {'class':
                            ['css-4rbku5 css-18t94o4 css-901oao r-9ilb82 r-1loqt21 r-1q142lx r-37j5jr r-a023e6 r-16dba41 r-rjixqe r-bcqeeo r-3s2u2q r-qvutc0']}).get('href')
                        linkTweet = ('https://twitter.com' + linkTweet)
                        need_value = tweets_area[i].find('div', {'class': [
                            'css-901oao r-1fmj7o5 r-37j5jr r-a023e6 r-16dba41 r-rjixqe r-bcqeeo r-bnwqim r-qvutc0']})
                        try:
                            content = need_value.text
                            if content == None:
                                continue

                            url = re.findall(r'http[s:]?\/{0,2}\w+\[.][^ \n]+', content)
                            hashtag = re.findall(r'#\w+', content)
                            mail = re.findall(r'\w+@\w+\[.]\w+', content)
                            sha256 = re.findall(r'\b[a-zA-Z0-9]{64}\b', content)
                            sha1 = re.findall(r'\b[a-zA-Z0-9]{40}\b', content)
                            md5 = re.findall(r'\b[a-zA-Z0-9]{32}\b', content)
                            domain = re.findall(r'\b[A-Za-z][^ @\n]+\[.][space|com|li|org|biz|site|life|cn]+\b', content)


                            # Get some valid obfuscated ip addresses.
                            IPV4_RE = re.compile(r"""
                                    (?:^|
                                        (?![^\d\.])
                                    )
                                    (?:
                                        (?:[1-9]?\d|1\d\d|2[0-4]\d|25[0-5])
                                        [\[\(\\]*?\.[\]\)]*?
                                    ){3}
                                    (?:[1-9]?\d|1\d\d|2[0-4]\d|25[0-5])
                                    (?:(?=[^\d\.])|$)
                                """, re.VERBOSE)
                            ipv4=""
                            for ip_address in IPV4_RE.finditer(content):
                                ipv4 = ip_address.group(0)
                                Insert(con, name, linkTweet, dt_new[i], hashtag, 'ip', ipv4)

                            Insert(con, name, linkTweet, dt_new[i],hashtag, 'Url', url)
                            Insert(con, name, linkTweet, dt_new[i],hashtag, 'Mail', mail)
                            Insert(con, name, linkTweet, dt_new[i],hashtag, 'Domain', domain)
                            Insert(con, name, linkTweet, dt_new[i],hashtag, 'Md5', md5)
                            Insert(con, name, linkTweet, dt_new[i],hashtag, 'sha256', sha256)
                            Insert(con, name, linkTweet, dt_new[i],hashtag, 'sha1', sha1)
                            Insert(con, name, linkTweet, dt_new[i], hashtag, 'ip', ipv4)
                        except Exception as err:
                            print(err)
                            continue

            else: break
            dt_last.clear()
            for i in range (len(dt_new)):
                dt_last.append(dt_new[i])
            dt_new.clear()
            driver.execute_script("window.scrollTo(0, arguments[0])", SCROLL_HEIGHT)
            # 1080 - height on the monitor
            SCROLL_HEIGHT = SCROLL_HEIGHT + 1080
            time.sleep(SCROLL_PAUSE_TIME)

        except Exception as err:
            print(err)
            #continue



if __name__ == '__main__':
    feedlist = links()
    db_con = CreateDataBase()
    driver = webdriver.Chrome()
    for i in range(len(feedlist)):
        driver.get(feedlist[i])
        parsing(driver,db_con)
    driver.close()
    driver.quit()
