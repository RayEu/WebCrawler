import urllib.request      
import urllib.error  
import pandas as pd
import re
import json

class TXZYdanmuDownloader:

    def __init__(self, url, target='.'):
        self.header = { "Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",    
          "Accept-Language":"zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3",    
          "User-Agent":"Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/38.0.2125.122 Safari/537.36 SE 2.X MetaSr 1.0",    
          "Connection": "keep-alive",
         "content-type":"text/plain"
          }
        self.url = url
        self.target = target
        self.name = ''
        self.period = ''
        self.opener = urllib.request.build_opener() 
        urllib.request.install_opener(self.opener)

    def open_web(self, url):
        try:
            response = self.opener.open(url, timeout=5)    
        except urllib.error.URLError as e:
            print('open ' + str(url) + ' error')
            if hasattr(e, 'code'):    
                print(e.code)    
            if hasattr(e, 'reason'):    
                print(e.reason)    
        else:            
            return response.read()

    #解析单个弹幕页面，需传入target_id，v_id(后缀ID)，返回具体的弹幕信息
    def parse_danmu(self, url):
        html = self.open_web(url).decode('utf-8')
        bs = json.loads(html, strict = False)
        df = pd.DataFrame()
        for i in bs['comments']:
            content = i['content']
            name = i['opername']
            upcount = i['upcount']
            user_degree =i['uservip_degree']
            timepoint = i['timepoint']
            comment_id = i['commentid']
            cache = pd.DataFrame({'用户名':[name],'内容':[content],'会员等级':[user_degree],
                            '弹幕时间点':[timepoint],'弹幕点赞':[upcount],'弹幕id':[comment_id],'集数':[self.period]})
            df = pd.concat([df,cache])
        return df

    """第一步、获取v_id"""
    def get_v_id(self):
        print('正在获取'+self.url+'的v_id')
        req = urllib.request.Request(url=self.url,headers=self.header)
        data = self.open_web(req).decode('utf-8')
        res = re.findall('https://v\.qq\.com/x/cover/(.*?)\.html', self.url)[0]
        par = '<link rel="canonical" href="https://v\.qq\.com/x/cover/'+res+'/(.*?)\.html" />'
        v_ids = re.findall(par, data)#['vid']
        s = re.findall('<meta name="twitter:title" property="og:title" content="(.*?)"', data)[0].split('_')[0]
        l = re.findall('(.*?)(第.*?)：', s)[0]
        self.name = l[0]
        self.period = l[1]
        print('已获得v_id:'+v_ids[0])
        return v_ids[0]

    """第二步、获取target_id"""
    def get_target_id(self, v_id):
        print('正在获取'+self.url+'的target_id')
        base_url = 'https://access.video.qq.com/danmu_manage/regist?vappid=97767206&vsecret=c0bdcbae120669fff425d0ef853674614aa659c605a613a4&raw=1'
        pay = {
            "wRegistType":2,
            "vecIdList":[v_id],
            "wSpeSource":0,
            "bIsGetUserCfg":1,
            "mapExtData":{
                v_id:{
                    "strCid":"gyn1y4r74ktolg7",
                    "strLid":""
                    },
                }
            }
        postData = json.dumps(pay).encode('utf-8')
        req = urllib.request.Request(url=base_url,  
                                     data=postData,  
                                     headers=self.header,
                                     )
        data = self.open_web(req).decode('utf-8')
        target_ids = re.findall('&targetid=(.*?)&vid=', data)#['3828223232']
        print('已获得target_id:'+target_ids[0])
        return target_ids[0]

    """第三步、获取弹幕"""
    def crawl_danmu(self, v_id, target_id):
        print('正在爬取弹幕，请稍后。。。')
        #1、构造单集弹幕的循环网页
        urls = []
        base_url = 'https://mfm.video.qq.com/danmu?otype=json&timestamp={}&target_id={}%26vid%3D{}&count=80&second_count=5'
        for num in range(15, 1000 * 30 + 15,30):
            url = base_url.format(num, target_id, v_id)
            urls.append(url)
        final_result = pd.DataFrame()
        try:
            for url in urls:
                result = self.parse_danmu(url)
                final_result = pd.concat([final_result,result])
        except Exception as e:
            #print(e)
            pass
        finally:
            path = self.target+'/综艺-'+self.name+'-'+self.period+'-弹幕.xlsx'
            final_result.to_excel(path, engine="xlsxwriter") #可以输出成EXCEL格式的文件
            print('所有弹幕已爬取完成，并存储到'+path+'路径的文件中')


    def main(self):
        self.url = 'https://v.qq.com/x/cover/gyn1y4r74ktolg7.html'
        v_id = self.get_v_id()
        target_id = self.get_target_id(v_id)
        self.crawl_danmu(v_id, target_id)

if __name__ =="__main__":
    
    url = 'https://v.qq.com/x/cover/gyn1y4r74ktolg7.html'
    down = TXZYdanmuDownloader(url)
    down.main()

