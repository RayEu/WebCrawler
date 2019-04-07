#coding:utf-8    
import urllib.request    
import http.cookiejar    
import urllib.error  
import urllib.parse
import re
import socket
import os
from concurrent.futures import ThreadPoolExecutor

class Xigua66Downloader:
    
    def __init__(self, url, target='.'):
        self.target = target
        self.url = url
        self.playlist_url = None
        self.max_num=250
        self.header={ "Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",    
          "Accept-Language":"zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3",    
          "User-Agent":"Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/38.0.2125.122 Safari/537.36 SE 2.X MetaSr 1.0",    
          "Connection": "keep-alive"   
          }
        self.cjar = http.cookiejar.CookieJar()
        self.cookie = urllib.request.HTTPCookieProcessor(self.cjar)  
        self.opener = urllib.request.build_opener(self.cookie)      
        urllib.request.install_opener(self.opener)

        self.pool = ThreadPoolExecutor(max_workers=10)

        #设置超时时间为20s
        #利用socket模块，使得每次重新下载的时间变短
        socket.setdefaulttimeout(20)
    
    def download_file(self, url, target):
        #解决下载不完全问题且避免陷入死循环
        try:
            urllib.request.urlretrieve(url,target)
        except socket.timeout:
            count = 1
            while count <= 5:
                try:
                    urllib.request.urlretrieve(url,target)                                                
                    break
                except socket.timeout:
                    err_info = url+' Reloading for %d time'%count if count == 1 else 'Reloading for %d times'%count
                    print(err_info)
                    count += 1
                except:
                    #解决远程主机关闭问题
                    self.download_file(url, target)
            if count > 5:
                print("downloading fialed!")
        except:
            #解决远程主机关闭问题
            self.download_file(url, target)
                
    def open_web(self, url):
        try:
            response = self.opener.open(url, timeout=3)    
        except urllib.error.URLError as e:
            print('open ' + url + ' error')
            if hasattr(e, 'code'):    
                print(e.code)    
            if hasattr(e, 'reason'):    
                print(e.reason)    
        else:            
            return response.read()

    '''第一步、获取真正的url地址'''
    def get_available_IP(self):
        print('开始获取真实的url')
        req = urllib.request.Request(url=self.url,headers=self.header)
        data = self.open_web(req).decode('gbk')
        target_js = re.findall('<ul id="playlist"><script type="text/javascript" src="(.*?)"></script>',data)[0]
        data = self.open_web("http://www.xigua66.com"+target_js).decode('gbk')
        data = urllib.parse.unquote(data)

        find_33uu = re.findall('33uu\$\$(.*)33uu\$\$', data)
        if len(find_33uu) == 0:
            find_zyp = re.findall('zyp\$\$(.*)zyp\$\$', data)
            if len(find_zyp) != 0:
                find = find_zyp[0]
                label = 'zyp'
        else:
            find = find_33uu[0]
            label = '33uu'
        tv_lists = re.findall('%u7B2C(.*?)%u96C6\$https://(.*?)\$', find)#[(集数,url)]
        return tv_lists, label

    '''第二步、获取各个ts文件数量与名称'''
    def get_playlist(self, tv_lists, label):
        num = int(re.findall('player-(.*?).html', self.url)[0].split('-')[-1])
        url = 'https://' + tv_lists[num][-1]
        print('开始下载第'+str(num+1)+'集：\n'+url)
        print('开始获取playlist_url')
        ts_data = self.open_web(url).decode('utf-8')

        if label == '33uu':
            self.palylist_url = re.findall("url: '(.*?\.m3u8)'", ts_data)[-1]
        else:#label='zyp'
            self.palylist_url = re.findall("url: '(.*?\.m3u8)'", ts_data)[-1]

        #url检查
        #/2019/04/03/dkqcLONDC9I26yyG/playlist.m3u8
        #https://www4.yuboyun.com/hls/2019/02/27/9eBF1A0o/playlist.m3u8
        if self.palylist_url.startswith('http'):
            pass
        else:
            self.palylist_url = re.findall('(http.*?\.com)', url)[0] + self.palylist_url
        print(self.palylist_url)
        print('开始获取playlist')
        palylist_data = self.open_web(self.palylist_url).decode('utf-8')
        print('已获得playlist列表')
        ts_list = re.findall('#EXTINF:(.*?),\n(.*?)\n', palylist_data)#[(时间长度，ts文件名)]
        return ts_list

    '''第三步、下载ts文件'''
    def download_with_single_process(self, ts_list):
        url_header = re.findall('(http.*/)', self.palylist_url)[0]
        print('开始单线程下载\n下载链接及情况：')
        for index, ts in enumerate(ts_list):
            if ts[-1].startswith('out'):
                ts_url = url_header + ts[-1]
                #下载
                self.download_file(ts_url, self.target+'/out'+str(index).zfill(4)+'.ts')
                print(ts_url+'--->Done')
            elif ts[-1].endswith('.ts'):
                ts_url = ts[-1]
                self.download_file(ts_url, self.target+'/out'+str(index).zfill(4)+'.ts')
                print(ts_url+'--->Done')
            else:
                print(ts[-1]+'无效')
        print('全部下载完成')

    def download_for_multi_process(self, ts):
        url_header = re.findall('(http.*/)', self.palylist_url)[0]
        if ts[-1].startswith('out'):
            ts_url = url_header + ts[-1]
            #下载
            index = re.findall('out(.*)\.ts',ts[-1])[0]
            self.download_file(ts_url, self.target+'/out'+index.zfill(4)+'.ts')
            print(ts_url+'--->Done')
        elif ts[-1].endswith('.ts'):
            ts_url = ts[-1]
            index = re.findall('out(.*)\.ts',ts[-1])[0]
            self.download_file(ts_url, self.target+'/out'+index.zfill(4)+'.ts')
            print(ts_url+'--->Done')
        else:
            print(ts[-1]+'无效')
    
    def download_with_multi_process(self, ts_list):
        print('开始多线程下载')
        print('下载链接及情况：')
        """<urlopen error [WinError 10054] 远程主机强迫关闭了一个现有的连接。>"""
        """建议优化代码"""
        """https://blog.csdn.net/qq_40910788/article/details/84844464"""
        task = self.pool.map(self.download_for_multi_process,ts_list)#此时非阻塞
        for t in task:#此时会变成阻塞
            pass
        '''
        from multiprocessing.dummy import Pool
        pool = Pool(10)
        pool.map(self.download_for_multi_process, ts_list)
        pool.close()
        pool.join()
        '''

    '''第四步、合并ts文件'''
    def merge_ts_file_with_os(self):
        print('开始合并')
        L=[]
        file_dir=self.target
        for root, dirs, files in os.walk(file_dir): 
            for file in files:  
                if os.path.splitext(file)[1] == '.ts':  
                    L.append(file)
        L.sort()
        blocks = [L[i:i+self.max_num] for i in range(0,len(L),self.max_num)]

        os.system('cd '+self.target)
        tmp=[]
        for index, block in enumerate(blocks):
            b='+'.join(block)
            new_name=' out_new_'+str(index).zfill(2)+'.ts'
            tmp.append(new_name)
            os.system('copy /b '+b+new_name)

        cmd='+'.join(tmp)
        num = int(re.findall('player-(.*?).html', self.url)[0].split('-')[-1])+1
        os.system('copy /b '+cmd+' E'+str(num).zfill(2)+'.mp4')
        os.system('del /Q out*.ts')
        print('合并完成')

    def merge_ts_file_with_ffmpeg():
        pass
    
    def main_process(self):
        available_IP = self.get_available_IP()
        ts_list = self.get_playlist(available_IP)
        self.download_with_multi_process(ts_list)
        self.merge_ts_file_with_os()
    
if __name__ == '__main__':
    web_url= "http://www.xigua66.com/mainland/yitiantulongji2019/player-0-36.html"
    down = Xigua66Downloader(web_url)
    available_IP, label = down.get_available_IP()
    ts_list = down.get_playlist(available_IP, label)
    down.download_with_multi_process(ts_list)
    down.merge_ts_file_with_os()
