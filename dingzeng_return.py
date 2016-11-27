from index_get import *
#from dingzeng_plot import *
from WindPy import * 
from datetime import * 
import time
from pandas import* 
from numpy import *
from numpy import transpose as t
import shutil
w.start()

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

def bankuai(x):
    if x[0:2]=='60':
        return('上证主板')
    elif x[0:3]=='000':
        return('深证主板')
    elif x[0:3]=='300':
        return('创业板')
    elif (x[0:3]=='001')|(x[0:3]=='002'):
        return('中小板')
    else:
        return('error')
def initial():
    #%run index_get.py
    rawdata1=read_excel('增发实施.xlsx',header=1)
    rawdata2=read_excel('定向增发发行资料.xlsx')
    con=sqlite3.connect('定增.db')
    rawdata1.to_sql('实施',con,if_exists='replace')
    rawdata2.to_sql('资料',con,if_exists='replace')
    d1=read_sql('select * from 实施',con,index_col='index').query('发行方式!="公开发行"')
    d2=read_sql('select * from 资料',con,index_col='index')
    merge_data=merge(d2[['代码', '名称', '增发价格', '自发行价涨跌幅(后复权)',
        '预计募集资金(亿元)', '实际募资总额(亿元)','定向增发目的', '发行对象', '发行折价率(%)',
       '大股东是否参与认购', '大股东认购比例(%)', '大股东认购金额(亿元)', '大股东认购方式', 
       '定向基准日类型', '发行日期', '上市日','限售股份解禁日', '企业性质', '证监会行业', 'Wind行业']]
        ,d1[['代码','增发日收盘价','最新收盘价','实际募资总额(亿元)','发行日期','认购方式']],on=['代码','实际募资总额(亿元)','发行日期'],how='inner')
    merge_data['年']=merge_data['发行日期'].apply(lambda x : int(x[0:4]) if isinstance (x,str) else np.nan )
    merge_data['月']=merge_data['发行日期'].apply(lambda x : int(x[5:7]) if isinstance (x,str) else np.nan )
    days=merge_data['限售股份解禁日'].apply(lambda x : datetime.strptime(x[0:10],'%Y-%m-%d') if isinstance (x,str) else np.nan )-merge_data['发行日期'].apply(lambda x : datetime.strptime(x[0:10],'%Y-%m-%d') if isinstance (x,str) else np.nan )
    merge_data['期限']=[round(i.days/365) if isinstance (i,pandas.tslib.Timedelta) else np.nan for i in days ]
    merge_data.reindex(range(merge_data.shape[0]))
    merge_data['折价']=merge_data['增发价格']/merge_data['增发日收盘价']
    merge_data.to_sql('合并',con,if_exists='replace')
    con=sqlite3.connect('定增.db')
    data=read_sql('select * from 合并 where 期限==1 or 期限==3',con)
    sampledata=data[['代码','发行日期','限售股份解禁日','实际募资总额(亿元)','折价','增发价格','增发日收盘价',
                     '发行对象','定向增发目的','年','月','期限','企业性质','认购方式','证监会行业','Wind行业',]].copy()
    sampledata['认购方式']=sampledata['认购方式'].apply(lambda x : '未知' if x is None else x )
    sampledata['发行日期']=sampledata['发行日期'].apply(lambda x:datetime.strptime(x[0:10],'%Y-%m-%d'))
    sampledata['限售股份解禁日']=sampledata['限售股份解禁日'].apply(lambda x:datetime.strptime(x[0:10],'%Y-%m-%d'))
    info_dict={'上证': '000001','深成': '399001','创业板':'399006','中小板':'399005','沪深300':'000300','中证500':'399905'}
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
    index_combine=index_combine.fillna(method='ffill')
    combine_data=merge(index_combine,sampledata,on='发行日期',how='right')
    combine_data['板块']=combine_data['代码'].apply(bankuai)
    return(combine_data)


def gen_return_insert_command(info_dict,table='解禁'):
    """
    生成指数数据库插入命令
    """
    info_list=['代码','实际募资总额(亿元)','后复权净值','前复权净值', '上证净值', '深成净值',
       '创业板净值', '中小板净值', '沪深300净值','中证500净值']
    t=[]
    for il in info_list:
        if il in info_dict:
            t.append(info_dict[il])
        else:
            t.append('')
    t=tuple(t)
    command=(r"insert into '%s' values(?,?,?,?,?,?,?,?,?,?)"%(table),t)
    return command

#base_path=os.getcwd()

def get_dingzeng_info(info,jiejin=True):
    '''
    根据定增发行信息计算定增收益及同期benchmark收益
    '''
    base_path=os.getcwd()
    count=str(info.name)
    temp_stock=info
    code=temp_stock['代码']
    issue_date=temp_stock['发行日期']
    release_date=temp_stock['限售股份解禁日'].strftime('%Y-%m-%d %H:%M:%S')
    now_day=datetime.today().strftime('%Y-%m-%d %H:%M:%S')
    if now_day<=release_date:
        release_date=now_day
        jiejin=False   
    issue_price=temp_stock['增发价格']
    issue_close_price=temp_stock['增发日收盘价']
    issue_dis=issue_price/issue_close_price
    tempdata=w.wsd(code,'close',issue_date,release_date,'Days=Alldays')
    tempdataF=w.wsd(code,'close',issue_date,release_date,'Days=Alldays', 'Fill=Black','PriceAdj=F')
    tempdataB=w.wsd(code,'close',issue_date,release_date,'Days=Alldays', 'Fill=Black','PriceAdj=B')
    data=DataFrame({'股价':Series(tempdata.Data[0]),'前复权':Series(tempdataF.Data[0]),'后复权':Series(tempdataB.Data[0])})
    data.index=tempdata.Times
    data['定增价']=issue_price
    data['后复权净值']=data['后复权']/data['后复权'][0]/issue_dis
    data['前复权净值']=data['前复权']/data['前复权'][0]/issue_dis
    #hs300=w.wsd('000300.SH','close',issue_date,release_date,'Days=Alldays')
    #zz500=w.wsd('399905.SZ','close',issue_date,release_date,'Days=Alldays')
    #cyb=w.wsd('399006.SZ','close',issue_date,release_date,'Days=Alldays')
    #sc=w.wsd('399001.SZ','close',issue_date,release_date,'Days=Alldays')
    #zx=w.wsd('399005.SZ','close',issue_date,release_date,'Days=Alldays')
    #sz=w.wsd('000001.SH','close',issue_date,release_date,'Days=Alldays')
    #indexdata=DataFrame({'沪深300':Series(hs300.Data[0],index=hs300.Times),'中证500':Series(zz500.Data[0],index=zz500.Times),
                    # '创业板':Series(cyb.Data[0],index=cyb.Times),'深成':Series(sc.Data[0],index=sc.Times),
                    #'中小板':Series(zx.Data[0],index=zx.Times),'上证':Series(sz.Data[0],index=sz.Times)})
    savedata=data.join(index_data)
    if jiejin:
        savedata.to_csv(base_path+'\\stock\\解禁\\'+count+'-'+code+'.csv')
    else:
        savedata.to_csv(base_path+'\\stock\\未解禁\\'+count+'-'+code+'.csv')
    index_return=savedata[['上证','深成','中小板','创业板','沪深300','中证500']].fillna(method='ffill').apply(lambda x: x/x[0]).iloc[-1]
    index_return.index=index_return.index+'净值'
    result=savedata.iloc[-1][['后复权净值','前复权净值']].append(info[['代码','实际募资总额(亿元)']]).append(index_return)
    #print(count,'finished calculate',code)
    return(result)
##############################################################################
def dingzeng_info(data,db,table='未解禁'):
    unjiejin_data=data.apply(get_dingzeng_info,axis=1)
    for info in unjiejin_data.to_dict(orient='records'):
        command=gen_return_insert_command(info,table=table)
        db.execute(command,1)
    #print("finished ",data.index)

def do_dingzeng_info(data,db,table='未解禁'):
    threads=[]
    for i in range(0,len(data),50):
        testdata=data.iloc[i:(i+50)]
        t=threading.Thread(target=dingzeng_info,args=(testdata,db,table))
        threads.append(t)
    for t in threads:
        t.start()
    for t in threads:
        t.join()

####################################################################

if __name__=="__main__":
    base_path=os.getcwd()
    os.chdir(base_path+'\\stock\\')
    shutil.rmtree('未解禁')
    os.mkdir('未解禁')
    os.chdir(base_path)
    combine_data=initial()
    command='create table if not exists 解禁 (代码 Text,"实际募资总额(亿元)" Real,后复权净值 Real,前复权净值 Real, 上证净值 Real, 深成净值 Real,创业板净值 Real,中小板净值 Real, 沪深300净值 Real, 中证500净值 Real ,primary key(代码,"实际募资总额(亿元)") ) '
    jiejin_db=SQLiteWraper('定增.db',command)
    con=sqlite3.connect('定增.db')
    c=con.cursor()
    c.execute('drop table 未解禁')
    con.commit()
    command='create table if not exists 未解禁 (代码 Text,"实际募资总额(亿元)" Real,后复权净值 Real,前复权净值 Real, 上证净值 Real, 深成净值 Real,创业板净值 Real,中小板净值 Real, 沪深300净值 Real, 中证500净值 Real ,primary key(代码,"实际募资总额(亿元)") ) '
    unjiejin_db=SQLiteWraper('定增.db',command)
    un_jiejin=combine_data[combine_data['限售股份解禁日']>=datetime.today()].sort_values('发行日期')
    jiejin=combine_data[combine_data['限售股份解禁日']<datetime.today()].sort_values('发行日期')
    sql='select * from 解禁'
    jiejin_done=read_sql(sql,con)
    jiejin_to_update=jiejin[[np.isnan(i) for i in merge(jiejin,jiejin_done,on=['代码','实际募资总额(亿元)'],how='left')['后复权净值']]]
    un_jiejin.index=range(len(un_jiejin))
    jiejin_to_update.index=range(len(jiejin_done),len(jiejin_done)+len(jiejin_to_update))
    jiejin_data=jiejin_to_update.apply(get_dingzeng_info,axis=1)
    #已解禁的定增股票的收益更新
    for info in jiejin_data.to_dict(orient='records'):
        command=gen_return_insert_command(info,table='解禁')
        jiejin_db.execute(command,1)   
    do_dingzeng_info(un_jiejin,unjiejin_db)
    #多线程进行未解禁定增股收益计算
    #do_dingzeng_info(jiejin_to_update,jiejin_db,table='解禁')
    con=sqlite3.connect('定增.db')
    sql1='select * from 解禁'
    sql2='select * from 未解禁'
    data=merge(combine_data,read_sql(sql1,con).append(read_sql(sql2,con),ignore_index=True),on=['代码','实际募资总额(亿元)'],how='left')
    data.to_sql('定增汇总',con,if_exists='replace')
    
    print('完成定增股解禁(或当前)收益率更新')