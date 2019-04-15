#coding:utf-8
import xlrd
import re
"""
<?xml version="1.0" encoding="UTF-8"?>
<i>
<d p="179.52200,5,18,15138834,1555065711,0,3552b790,14639974983925764">电视里是</d>
</i>

第一个参数是弹幕出现的时间 以秒数为单位。
第二个参数是弹幕的模式1..3 滚动弹幕 4底端弹幕 5顶端弹幕 6.逆向弹幕 7精准定位 8高级弹幕
第三个参数是字号， 12非常小,16特小,18小,25中,36大,45很大,64特别大
第四个参数是字体的颜色 以HTML颜色的十位数为准
第五个参数是Unix格式的时间戳。基准时间为 1970-1-1 08:00:00
第六个参数是弹幕池 0普通池 1字幕池 2特殊池 【目前特殊池为高级弹幕专用】
第七个参数是发送者的ID，用于“屏蔽此弹幕的发送者”功能
第八个参数是弹幕在弹幕数据库中rowID 用于“历史弹幕”功能。
"""

filename = '倚天屠龙记第43集弹幕.xlsx'
num = re.findall('[0-9]{2}', filename)[0]
f = open('E'+str(num).zfill(2)+'.xml', 'w', encoding='utf-8')
f.write('<?xml version="1.0" encoding="UTF-8"?>')
f.write('<i>')
f.write('<chatserver>chat.bilibili.com</chatserver>')
f.write('<chatid>85868779</chatid>')
f.write('<mission>0</mission>')
f.write('<maxlimit>1000</maxlimit>')
f.write('<state>0</state>')
f.write('<real_name>0</real_name>')
f.write('<source>k-v</source>')

workbook = xlrd.open_workbook(filename)
sheet = workbook.sheet_by_index(0)
nrows = sheet.nrows#行

for i in range(1, nrows):
    contents = sheet.cell(i, 2).value
    times = sheet.cell(i, 4).value
    d = '<d p="'+str(times)+',1,25,16777215,1555065711,0,root,0">'+str(contents)+'</d>'
    f.write(d)
workbook.release_resources()
f.write('</i>')
f.close()
