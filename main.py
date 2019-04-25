"""
从 Bing 抓取每天最新的壁纸, 然后通过系统 API 切换桌面壁纸
"""

import os
import re
import subprocess
import sys
import time
from typing import Dict
from urllib.parse import urljoin, urlencode

import requests

BASE_URL = 'https://cn.bing.com/'

# 壁纸信息 URL 模板
IMAGE_INFO_URL: str = urljoin(BASE_URL, 'HPImageArchive.aspx')


def get_pictures_path() -> str:
    """
    获取图片文件夹路径
    :return: 图片文件夹路径
    """
    s = subprocess.Popen('echo $HOME', shell=True, stdout=subprocess.PIPE)
    s.wait()
    path = s.stdout.read().decode().strip()
    path = os.path.join(path, 'Pictures')
    return path


def get_headers() -> Dict[str, str]:
    """
    获取 headers
    :return: headers
    """
    headers = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,'
                  '*/*;q=0.8,application/signed-exchange;v=b3',
        'accept-language': 'zh-CN,zh;q=0.9',
        'accept-encoding': 'gzip, deflate, br',
        'cache-control': 'max-age=0',
        'dnt': '1',
        'cookie': 'ENSEARCH=BENVER=1;',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_4) AppleWebKit/537.36 '
                      '(KHTML, like Gecko) Chrome/74.0.3729.108 Safari/537.36',
    }
    return headers


def get_newest_image_info() -> Dict[str, str]:
    """
    获取最新的图片信息
    :return: image info
    """
    info = {}
    timestamp = int(time.time() * 1000)
    params = {
        'format': 'hp',
        'idx': '0',
        'n': '1',
        'nc': str(timestamp),
        'pid': 'hp',
        'mkt': 'zh-CN',
        'quiz': '1',
        'og': '1',
    }
    info_url = IMAGE_INFO_URL + '?' + urlencode(params)
    try:
        r = requests.get(info_url, headers=get_headers())
    except requests.RequestException as e:
        print('获取图像信息失败, err:', e)
        return info
    if r.headers.get('content-encoding') == 'br':
        import brotli
        data = brotli.decompress(r.content)
        text = data.decode()
    else:
        text = r.text
    uri = re.search(r'"url":"(/th\?.*?pid=hp)"', text)
    if uri:
        uri = uri.group(1)
    else:
        uri = ''
    info['image_uri'] = uri
    title = re.search('"title":"(.*?)"', text)
    if title:
        title = title.group(1)
    else:
        title = ''
    info['image_title'] = title
    return info


def catch_image(url: str) -> bytes:
    """
    抓取图像
    :param url: image url
    :return: image bytes
    """
    try:
        r = requests.get(url)
    except requests.RequestException as e:
        print('抓取失败, err:', e)
        return b''
    return r.content


def save_image(image: bytes, path: str) -> bool:
    """
    保存图像
    :param image: 图像, bytes形式
    :param path: 保存路径
    :return: 保存成功返回 True, 否则返回 False
    """
    try:
        with open(path, mode='wb') as f:
            f.write(image)
    except os.error as e:
        print('保存文件失败, err:', e)
        return False
    else:
        print('保存成功!')
    return True


def change_wallpaper(path: str) -> None:
    """
    更换壁纸
    :param path: 图像路径
    """
    cmd = r'osascript -e "tell application \"Finder\" to set desktop picture to POSIX file \"{}\""'
    cmd = cmd.format(path)
    res = os.system(cmd)
    if res == 0:
        print('更换壁纸成功')
    else:
        print('更换壁纸失败')


if __name__ == '__main__':
    image_info = get_newest_image_info()
    image_title = image_info.get('image_title')
    image_uri = image_info.get('image_uri')
    if image_uri == '':
        print('找不到 image_uri!')
    image_url = urljoin(BASE_URL, image_uri)
    content = catch_image(image_url)
    save_path = os.path.join(get_pictures_path(), 'Bing')
    if not os.path.exists(save_path):
        os.makedirs(save_path)
    filename = os.path.join(save_path, image_title) + '.jpeg'
    if os.path.exists(filename):
        print('已存在该文件,', filename)
    else:
        if not save_image(content, path=filename):
            sys.exit(1)
    change_wallpaper(filename)
