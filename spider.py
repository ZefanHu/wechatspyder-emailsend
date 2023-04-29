# -*- coding: utf-8 -*-
import os
import time
import requests
import logging
import yagmail
from configparser import ConfigParser

# Read config
config = ConfigParser()
config.read('config.ini')
fad = config.get('rss', 'fad')  # 爬不同公众号只需要更改 fakeid
check_interval = config.getint('rss', 'check_interval')
email = config.get('email', 'email')
password = config.get('email', 'password')
recipient_email = config.get('email', 'recipient_email')
ehost = config.get('email', 'ehost')
eport = config.get('email', 'eport')
# Set up logging
logging.basicConfig(filename='rss_notifier.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s',
                    encoding='utf-8')


# 发送邮件通知
def send_email(subject, body, to_email):
    try:
        yag = yagmail.SMTP(user=email, password=password, host=ehost, port=eport)
        yag.send(to=to_email, subject=subject, contents=body)
        return True
    except Exception as e:
        logging.error(f'Error sending email: {e}')
        return False


headers = {
  #/cgi-bin/appmsg的request header里面的cookie
    "cookie": "",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36"
}
url = 'https://mp.weixin.qq.com/cgi-bin/appmsg'


def page(num=1):  # 要请求的文章页数
    title = []
    link = []
    for i in range(num):
        data = {
            'action': 'list_ex',
            # 'begin': i * 5,  # 页数
            'count': '1',
            'fakeid': fad,
            'type': '9',
            'query': '',
            'token': '1182507961',
            'lang': 'zh_CN',
            'f': 'json',
            'ajax': '1',
        }
        r = requests.get(url, headers=headers, params=data)
        dic = r.json()
        for i in dic['app_msg_list']:  # 遍历dic['app_msg_list']中所有内容
            title.append(i['title'])  # 取 key键 为‘title’的 value值
            link.append(i['link'])  # 去 key键 为‘link’的 value值
    return title, link


#
def check_link(last_link):
    try:
        (title, link) = page()
    except Exception as e:
        logging.error(f'Error fetching RSS feed: {e}')
        return None, last_link
    new_entry = None

    if link[0] != last_link:
        new_entry = (title, link)
    return new_entry


# 检查微信公众号是否更新，更新则发邮件提醒
def main():
    # Load last_entry_id from file
    if os.path.exists('last_link.txt'):
        with open('last_link.txt', 'r') as f:
            last_link = f.read().strip()
    else:
        last_link = None

    while True:
        new_entry = check_link(last_link)
        if new_entry:
            title = new_entry[0]
            link = new_entry[1]
            print(title)
            logging.info(f'New entry found: {title[0]}')
            success = send_email(f'New RSS Update: {title[0]}', link[0], recipient_email)

            # Update last_entry_id only if the email was sent successfully
            if success:
                last_link = link
                with open('last_link.txt', 'w') as f:
                    f.write(last_link[0])

        time.sleep(check_interval)


if __name__ == '__main__':
    main()
