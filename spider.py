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
    "cookie": "appmsglist_action_3927278544=card; RK=my+AktDQZ9; ptcz=02e0a91d63b0b3b80d20d77ba9d5a115396e405288336a8fd65c86ff113b0d84; pgv_pvid=5112798840; \
    o_cookie=1371738978; pac_uid=1_1371738978; eas_sid=x1G6e5g4s9r409R3Z8b2Y1C7b0; ua_id=ZnZexjXIpvjrO6FDAAAAAKWPoksVbeplHST5ihsYKBo=; wxuin=57093901569073; \
    mm_lang=zh_CN; _clck=1c3dtht|1|f2x|0; tvfe_boss_uuid=f37539dea40c434e; Qs_lvt_323937=1661926412,1661928399,1674526381; Qs_pv_323937=1496408176218038500,\
    3675276323908851700,4381077217831457300; ptui_loginuin=1336942450@qq.com; fqm_pvqid=3723974f-d66f-41f7-bd72-1eacbfddd8d8; pgv_info=ssid=s8678376860; \
    uuid=d046dd459a403be5ac0eb672cfad45d0; rand_info=CAESIEHtUO0TwAx/GqVl2zm4gp6Ja2AF8MqqZPe3/MMPLyOc; slave_bizuin=3927278544; data_bizuin=3927278544; \
    bizuin=3927278544; data_ticket=JQJaQKmTcFtFGt9c2MYNjiGsfEzo5oCWzkMBCXHPuVH8+As9SfudrdZP62/jWq0r; slave_sid=bnBOeUYwaDR6V1h6NUVGRG9KeTB3ZW42QUxxRmNvc0FCV2xqTVpyM0FKYlZacTNDbmM4TERhNFNYRlh5a3d1cDUwMjhGX2VPMGtTWjdrZ0lxOXNrZDMzQmRDSkthQU9ib0xrWmoyZ3JHQVoxcVo5cTNubGF2TXMxOXExWjVCQVJDdnZ3ekpOMkF1RHUxUnJy; \
    slave_user=gh_20cd46a1f992; xid=90d47b8c18b9902dc428448b9ebbf585; cert=GnyolHvmGZRqUe5xiwHwiQKwFVp5klOg; rewardsn=; wxtokenkey=777",
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
