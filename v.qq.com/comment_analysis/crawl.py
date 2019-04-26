# coding:utf-8
import sys
sys.path.append("..")
from TXZYdanmuDownloader import TXZYdanmuDownloader
import time

import urllib.request      
import urllib.error
from lxml import etree

header = { "Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",    
          "Accept-Language":"zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3",    
          "User-Agent":"Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/38.0.2125.122 Safari/537.36 SE 2.X MetaSr 1.0",    
          "Connection": "keep-alive",
         "content-type":"text/plain"
          }
opener = urllib.request.build_opener() 
urllib.request.install_opener(opener)

def open_web(url):
    try:
        response = opener.open(url, timeout=5)    
    except urllib.error.URLError as e:
        print('open ' + str(url) + ' error')
        if hasattr(e, 'code'):    
            print(e.code)    
        if hasattr(e, 'reason'):    
            print(e.reason)    
    else:            
        return response.read()

url = 'https://v.qq.com/x/cover/bowtx67rdcy378n.html'
data = open_web(url).decode('utf-8')
content = etree.HTML(data)
link_list = content.xpath("//a[@class='figure_detail']/@href")
url_list = ['https://v.qq.com'+i for i in link_list if i.startswith('/x/cover')]
print('共有'+str(len(url_list))+'集的弹幕需要下载。分别是：')
print(url_list)

for url in url_list:
    start = time.time()
    down = TXZYdanmuDownloader(url)
    down.main()
    end = time.time()
    print(end-start)
