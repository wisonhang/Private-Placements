# coding: utf-8
from pandas import *
from numpy import *
import tushare as ts
import os
import sqlite3
import threading
import time
from pyquery import PyQuery as pq
from urllib.request import urlopen, Request
import json
from datetime import datetime,date
from tushare.stock import cons as ct
import os 
import requests
from bs4 import BeautifulSoup

###############################################
lock = threading.Lock()
class SQLiteWraper(object):
    """
    数据库的一个小封装，更好的处理多线程写入
    """
    def __init__(self,path,command='',*args,**kwargs):  
        self.lock = threading.RLock() #锁  
        self.path = path #数据库连接参数  

        if command!='':
            conn=self.get_conn()
            cu=conn.cursor()
            cu.execute(command)

    def get_conn(self):  
        conn = sqlite3.connect(self.path)#,check_same_thread=False)  
        conn.text_factory=str
        return conn   

    def conn_close(self,conn=None):  
        conn.close()  

    def conn_trans(func):  
        def connection(self,*args,**kwargs):  
            self.lock.acquire()  
            conn = self.get_conn()  
            kwargs['conn'] = conn  
            rs = func(self,*args,**kwargs)  
            self.conn_close(conn)  
            self.lock.release()  
            return rs  
        return connection  

    @conn_trans    
    def execute(self,command,method_flag=0,conn=None):  
        cu = conn.cursor()
        try:
            if not method_flag:
                cu.execute(command)
            else:
                cu.execute(command[0],command[1])
            conn.commit()
        except sqlite3.IntegrityError as e:
            #print (e)
            return -1
        except Exception as e:
            #print (e)
            return -2
        return 0

    @conn_trans
    def fetchall(self,command="",conn=None):
        cu=conn.cursor()
        lists=[]
        try:
            cu.execute(command)
            lists=cu.fetchall()
        except Exception as e:
            print (e)
            pass
        return lists
###################################
def gen_index_insert_command(info_dict,code='上证'):
    """
    生成指数数据库插入命令
    """
    info_list=['日期','开盘价','最高价','最低价','收盘价','涨跌额','涨跌幅(%)','成交量(股)','成交金额(元)']
    t=[]
    for il in info_list:
        if il in info_dict:
            t.append(info_dict[il])
        else:
            t.append('')
    t=tuple(t)
    command=(r"insert into '%s' values(?,?,?,?,?,?,?,?,?)"%(code),t)
    return command
###################################
def get_index_hq(url,code,index_db=None,retry_count=3,pause=0.001):
    for _ in range(retry_count):
        time.sleep(pause)
        try:
            request = Request(url)
            lines = urlopen(request, timeout = 10).read()
        except Exception as e:
            print(e)
        else:
            doc=pq(lines.decode('utf-8'))
            data=read_html(str(doc('table')),skiprows=0,header=1)[3]
            data=data.sort_values('日期')
            if index_db:
                for i in range(data.shape[0]):
                    command=gen_index_insert_command(data.iloc[i].to_dict(),code=code)
                    #print(command)
                    index_db.execute(command,1)
            else:
                return(data)


def index_spider(index_db,code='000001',sty=2006,endy=2017,quarter=1):
    base_url='http://quotes.money.163.com/trade/lsjysj_zhishu_%s.html?year=%s&season=%s'
    threads=[]
    for year in range(sty,endy):
        for season in range(quarter,5):
            url=base_url%(code,year,season)
            t=threading.Thread(target=get_index_hq,args=(url,code,index_db))
            threads.append(t)
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    print("finished spider",code,'data')
####################################################################################
headers={
'Host': 'data.bank.hexun.com',
'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; WOW64; rv:49.0) Gecko/20100101 Firefox/49.0',
'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3',
'Accept-Encoding': 'gzip, deflate',
'Connection': 'keep-alive',
'Upgrade-Insecure-Requests': '1'
}
cookies={"vjuids":"-3f8b123c2.15730b4caf3.0.daff1af5531488",
         " vjlast":"1473990937.1477303523.11",
         " ADVC":"345ddea9a8a6d2"," ASL":"17073,jzzoj,74e3706074e370606550208bb4ad0b8fb4ad0bfa",
         " HexunTrack":"SID=201609170914490132378967bb9824911b8e99b0beaa7c3ae&CITY=31&TOWN=0",
         " __jsluid":"66597500494ed2586c323a96aee99e4e"," hxck_sq_common":"LoginStateCookie=",
         " ADVS":"346771c267a4a2"," __utma":"194262068.1067827675.1475051452.1475051452.1475113787.2",
         " __utmz":"194262068.1475113787.2.2.utmcsr=funds.hexun.com|utmccn=(referral)|utmcmd=referral|utmcct=/",
         " _ga":"GA1.2.1067827675.1475051452"," _gat":"1",
         " hxck_sq_zyjca":"JgJkWVQ1a8fcq11a/O2pOO94sMuvHux4HVx4NGAs1wc=",
         " __utmt":"1"," hxck_webdev1_general":"fundlist=000750_0|000989_0",
         " Hm_lvt_f65ab30a4196388f1696a9a62fbdc763":"1475045225"," Hm_lpvt_f65ab30a4196388f1696a9a62fbdc763":"1475113853"}

def gen_shibor_insert_command(info_dict,code='shibor'):
    """
    生成指数数据库插入命令
    """
    info_list=['日期','拆借利率','涨跌额BP','涨跌幅']
    t=[]
    for il in info_list:
        if il in info_dict:
            t.append(info_dict[il])
        else:
            t.append('')
    t=tuple(t)
    command=(r"insert into '%s' values(?,?,?,?)"%(code),t)
    return command

def get_shibor_hq(url,code,index_db=None,retry_count=3,pause=1):
    for _ in range(retry_count):
        time.sleep(pause)
        try:
            s=requests.session()
            r=s.post(url,headers=headers,cookies=cookies,timeout=60)
            soup=BeautifulSoup(r.content.decode('utf-8','ignore'),'lxml')
        except Exception as e:
            print(e)
        else:
            data=read_html(str(soup.find_all('table',attrs={"class":"liborTable"})[0]),flavor='lxml',skiprows=1)[0]
            data.columns=['日期','拆借利率','涨跌额BP','涨跌幅']
            if index_db:
                for i in range(data.shape[0]):
                    command=gen_shibor_insert_command(data.iloc[i].to_dict(),code=code)
                    #print(command)
                    index_db.execute(command,1)
            else:
                return(data)
def shibor_spider(index_db,code='shibor',page=125,quarter=1):
    base_url='http://data.bank.hexun.com/yhcj/cj.aspx?r=1000000000000000&t=21&page=%s'
    threads=[]
    for p in range(1,page+1):
        url=base_url%(p)
        #print(url)
        t=threading.Thread(target=get_shibor_hq,args=(url,code,index_db))
        threads.append(t)
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    print("finished spider",code,'data')       
####################################################################################
if __name__=="__main__":
    
    info_dict={'上证指数': '000001','深证成指': '399001','创业板指':'399006',
               '中小板指数':'399005','沪深300':'000300','中证500':'399905','上证50':'000016'}
    for idx in info_dict:
        code=info_dict[idx]
        command="create table if not exists '%s' (日期 INTEGER,开盘价 Real,最高价 Real,最低价 Real,收盘价 Real,涨跌额 Real,涨跌幅 BLOB,成交量 Real,成交金额 Real, primary key(日期))"%code  
        index_db=SQLiteWraper('index.db',command)
        index_spider(index_db,code=code,sty=2016,quarter=4)
    command="create table if not exists shibor (日期 TEXT primary key UNIQUE,拆借利率 Real,涨跌额BP Real,涨跌幅 Real)"
    index_db=SQLiteWraper('index.db',command)
    shibor_spider(index_db,code='shibor',page=2)
    
    con=sqlite3.connect('index.db')
    sql='select "日期","拆借利率" from shibor order by "日期"'
    shibor=read_sql(sql,con)
    shibor.columns=['发行日期','shibor']
    shibor['发行日期']=shibor['发行日期'].apply(lambda x:datetime.strptime(str(x),'%Y-%m-%d'))
    info_dict={'上证指数': '000001','深证成指': '399001','中小板指数':'399005','创业板指':'399006','沪深300':'000300',
               '中证500':'399905','上证50':'000016'}
    for i,idx in enumerate(info_dict):
        code=info_dict[idx]
        con=sqlite3.connect('index.db')
        sql='select * from "%s" order by 日期 '%(code)
        index_data=read_sql(sql,con)[['日期','收盘价']]
        index_data['日期']=index_data['日期'].apply(lambda x:datetime.strptime(str(x),'%Y%m%d'))
        index_data.columns=['发行日期',idx]
        if i==0:
            index_combine=DataFrame(date_range('01/01/2006',datetime.today()),columns=['发行日期'])
        index_combine=merge(index_combine,index_data,on='发行日期',how='outer')
    index_combine=merge(index_combine,shibor,on='发行日期',how='outer').sort_values('发行日期')
    
    info_dict={'上证': '000001','深成': '399001','创业板':'399006','中小板':'399005','沪深300':'000300','中证500':'399905'}
    for i,idx in enumerate(info_dict):
        code=info_dict[idx]
        con=sqlite3.connect('index.db')
        sql='select * from "%s" order by 日期 '%(code)
        index_data=read_sql(sql,con)[['日期','收盘价']]
        index_data['日期']=index_data['日期'].apply(lambda x:datetime.strptime(str(x),'%Y%m%d'))
        index_data.columns=['日期',idx]
        if i==0:
            index_combine=DataFrame(date_range('01/01/2006',datetime.today()),columns=['日期'])
        index_combine=merge(index_combine,index_data,on='日期',how='outer')
    index_data=index_combine[['上证','深成','中小板','创业板','沪深300','中证500']]
    index_data=index_data.fillna(method='ffill')
    index_data.index=index_combine['日期']+timedelta64(5, 'ms')