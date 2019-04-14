import requests
import json
import pandas as pd
import os
import re
import time
import random
from concurrent.futures import ThreadPoolExecutor

class TXdanmuDownloader:

    def __init__(self, url, target='.'):
        self.target = target
        self.url = url
        self.name = ''
        self.headers={ "Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",    
          "Accept-Language":"zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3",    
          "User-Agent":"Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/38.0.2125.122 Safari/537.36 SE 2.X MetaSr 1.0",    
          "Connection": "keep-alive"   
          }
        self.pool = ThreadPoolExecutor(max_workers=10)

    #页面基本信息解析，获取构成弹幕网址所需的后缀ID、播放量、集数等信息。
    def parse_base_info(self, url):
        df = pd.DataFrame()
        html = requests.get(url, headers=self.headers)
        bs = json.loads(html.text[html.text.find('{'):-1])
        for i in bs['results']:
            v_id = i['id']
            title = i['fields']['title']
            view_count = i['fields']['view_all_count']
            episode = int(i['fields']['episode'])
            if episode == 0:
                pass
            else:
                cache = pd.DataFrame({'id':[v_id],'title':[title],'播放量':[view_count],'第几集':[episode]})
                df = pd.concat([df,cache])
        return df

    #传入后缀ID，获取该集的target_id并返回
    def get_episode_danmu(self, v_id):
        base_url = 'https://access.video.qq.com/danmu_manage/regist?vappid=97767206&vsecret=c0bdcbae120669fff425d0ef853674614aa659c605a613a4&raw=1'

        pay = {"wRegistType":2,"vecIdList":[v_id],
               "wSpeSource":0,"bIsGetUserCfg":1,
               "mapExtData":{v_id:{"strCid":"wu1e7mrffzvibjy","strLid":""}}}
        html = requests.post(base_url, data=json.dumps(pay), headers=self.headers)
        bs = json.loads(html.text)
        danmu_key = bs['data']['stMap'][v_id]['strDanMuKey']
        target_id = danmu_key[danmu_key.find('targetid') + 9 : danmu_key.find('vid') - 1]
        return [v_id,target_id]

    #解析单个弹幕页面，需传入target_id，v_id(后缀ID)和集数（方便匹配），返回具体的弹幕信息
    def parse_danmu(self, url, target_id, v_id, period):
        html = requests.get(url,headers = self.headers)
        bs = json.loads(html.text,strict = False)
        df = pd.DataFrame()
        for i in bs['comments']:
            content = i['content']
            name = i['opername']
            upcount = i['upcount']
            user_degree =i['uservip_degree']
            timepoint = i['timepoint']
            comment_id = i['commentid']
            cache = pd.DataFrame({'用户名':[name],'内容':[content],'会员等级':[user_degree],
                              '弹幕时间点':[timepoint],'弹幕点赞':[upcount],'弹幕id':[comment_id],'集数':[period]})
            df = pd.concat([df,cache])
        return df

    #构造单集弹幕的循环网页，传入target_id和后缀ID（v_id），通过设置爬取页数来改变timestamp的值完成翻页操作
    def format_url(self, target_id, v_id, end = 85):
        urls = []
        base_url = 'https://mfm.video.qq.com/danmu?otype=json&timestamp={}&target_id={}%26vid%3D{}&count=80&second_count=5'
        for num in range(15,end * 30 + 15,30):
            url = base_url.format(num,target_id,v_id)
            urls.append(url)
        return urls

    """第一步、获得v_id"""
    def get_target_ids(self):
        html = requests.get(self.url, headers=self.headers).text
        res = re.findall('"nomal_ids":\[(.*?)\]', html)
        v_ids = re.findall('{"F":[0-9],"V":"(.*?)","E":', res[0])
        pir = 'https://union.video.qq.com/fcgi-bin/data?otype=json&tid=682&appid=20001238&appkey=6c03bbe9658448a4&idlist='
        last = '&callback=jQuery19107048738290725545_1554987778515&_=1554987778523'
        url_list = [pir+','.join(v_ids[i:i+30])+last for i in range(0,len(v_ids),30)]
        return url_list

    """第二步、获得target_id"""
    def get_all_ids(self, part_url):
        #分别获取1-30，31-60的所有后缀ID（v_id）
        tmp = []
        for p in part_url:
            res = self.parse_base_info(p)
            tmp.append(res)
        df = pd.concat(tmp)
        df.sort_values('第几集',ascending = True,inplace = True)
        #去重
        df = df.loc[df.duplicated('id') == False,:]
        #去预告片
        df = df[~df['title'].str.contains('预告片')]
        self.name = list(df['title'])[0].split('_')[0]
        print('正在获取《'+self.name+'》的target_id')
        count = 1
        #创建一个列表存储target_id
        info_lst = []
        for i in df['id']:
            info = self.get_episode_danmu(i)#['a0029vjyzhl', '3748894704']
            info_lst.append(info)
            count += 1
            time.sleep(0.5 + random.random())
        print('以获得《'+self.name+'》全部 '+str(count)+' 个target_id')
        #根据后缀ID，将target_id和后缀ID所在的表合并
        info_lst = pd.DataFrame(info_lst)
        info_lst.columns = ['v_id','target_id']
        combine = pd.merge(df,info_lst,left_on = 'id',right_on = 'v_id',how = 'inner')
        return combine

    """第三步、爬取弹幕"""
    #输入包含v_id,target_id的表，并传入想要爬取多少集
    def crawl_all(self, combine, num, page):
        c = 1
        final_result = pd.DataFrame()
        #print('Bro,马上要开始循环爬取每一集的弹幕了')
        for v_id,target_id in zip(combine['v_id'][:num],combine['target_id'][:num]):
            count = 1
            urls = self.format_url(target_id,v_id,page)
            for url in urls:
                result = self.parse_danmu(url,target_id,v_id, c)
                final_result = pd.concat([final_result,result])
                #time.sleep(2+ random.random())
                print('这是 %d 集的第 %d 页爬取..' % (c,count))
                count += 1
            print('-------------------------------------')
            c += 1
        return final_result

    #输入包含v_id,target_id的表，并传入想要爬取哪一集
    def crawl_single(self, combine, num, page):
        final_result = pd.DataFrame()
        v_id = combine['v_id'][num-1]
        target_id = combine['target_id'][num-1]
        urls = self.format_url(target_id,v_id,page)
        print('正在获得《'+self.name+'》第 '+str(num-1)+' 集的指定 '+str(page)+' 页弹幕')
        count = 1
        for url in urls:
            result = self.parse_danmu(url,target_id,v_id,num-1)
            final_result = pd.concat([final_result,result])
            count += 1
        print('已获得《'+self.name+'》第 '+str(num-1)+' 集的指定 '+str(page)+' 页弹幕')
        return final_result

    def main(self):
        part_url = self.get_target_ids()
        #得到所有的后缀ID，基于后缀ID爬取target_id
        combine = self.get_all_ids(part_url)
    
        #设置要爬取多少集（num参数），每一集爬取多少页弹幕（1-85页，page参数），
        #这里默认是爬取第一集的5页弹幕
        #比如想要爬取30集，每一集85页，num = 30,page = 85
        final_result = self.crawl_single(combine,num = 46,page = 50)
        final_result.to_excel(self.target+'/'+self.name+'弹幕.xlsx', engine="xlsxwriter") #可以输出成EXCEL格式的文件

if __name__ =="__main__":
    #https://blog.csdn.net/csdnsevenn/article/details/89089480
    url = 'https://v.qq.com/x/cover/ha7r9z89i9d234y/b00296wioni.html'
    down = TXdanmuDownloader(url)
    down.main()
