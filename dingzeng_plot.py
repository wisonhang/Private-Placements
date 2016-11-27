# coding: utf-8
from pandas import *
import numpy as np
import sqlite3
import matplotlib.pyplot as plt # side-stepping mpl backend
import matplotlib as mpl
import seaborn as sns
from ipywidgets import interact
from matplotlib import colors
from sklearn.linear_model import LassoCV
from sklearn import preprocessing
sns.set_style('darkgrid')
mpl.rcParams['font.sans-serif'] = ['SimHei'] #指定默认字体  
mpl.rcParams['axes.unicode_minus'] = False 
sns.set_context("talk")
###############################################
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
    
################################################
def money_spit(x):
    if x<=5.0:
        return("<5 亿")
    if (x>5.0) & (x <=10.0):
        return('5-10 亿')
    if (x>10) & (x <=30):
        return('10-30 亿')
    if (x>30) & (x <= 50):
        return('30-50 亿')
    if (x>50) & (x <=100):
        return('50-100 亿')
    if (x>100) & (x<=150) :
        return('100-150 亿')
    if x>150:
        return('>150 亿')
###############################################
def fx_duixiang(x):
    if ('机构投资者' in x) & ('大股东' in x):
        return('机构投资者,大股东')
    elif '机构投资者' in x:
        return('机构投资者')
    elif '大股东' in x :
        return('大股东')
    else:
        return('无机构投资者及大股东')
##############################################
def group_summary(kw=['年'],data=[]):   
    groupdata=data.groupby(kw)
    name=groupdata.count().index
    summary=DataFrame()
    for key in name:
        #print(key)
        tempdata=groupdata.get_group(key)
        info_dict={'定增发行数':int(tempdata['代码'].count()),'平均募资':round(tempdata['实际募资总额(亿元)'].mean(),3),
                   '总募资(亿)':round(tempdata['实际募资总额(亿元)'].sum(),3),
                       '平均折价':round(tempdata['折价'].mean(),3),
                  '平均收益':round(tempdata['后复权净值'].mean(),3)}
        if len(kw)==1:
            info_dict.update({kw[0]:key})
        else:
            for i in range(len(kw)):
                info_dict.update({kw[i]:key[i]})
        ttdata=Series(info_dict,index=kw+['定增发行数','平均募资','总募资(亿)','平均折价','平均收益'])
        summary=summary.append(DataFrame(ttdata).T)
    summary.index=range(summary.shape[0])
    return(summary)

def summary_table(year,return_data,qixian=[1,3],fangshi=['现金','资产'],kw='规模'):
    data=group_summary(kw=['期限','认购方式','年']+[kw],data=return_data)
    data['发行数']=1
    table=DataFrame(index=list(data[kw].unique())+['总计'])
    for t in qixian:
        for k in fangshi:
            td=data.query('年==%s'%year).query('认购方式=="%s"'%k).query('期限==%s'%t)
            tt=td[['定增发行数','总募资(亿)','平均折价']].copy()
            tt['平均折价']=tt['平均折价']*100
            tt.index=td[kw]
            tt_total=tt.sum()
            tt_total['平均折价']=(tt['定增发行数']*tt['平均折价']).sum()/tt['定增发行数'].sum()
            tt_total.name='总计'
            tt=tt.append(tt_total)
            tt.columns=[(str(t)+'年期'+k+'定增',i) for i in tt.columns]
            table=table.join(tt)
    table=DataFrame(table.to_dict()).T
    if kw=='规模':
        table=table[['<5 亿', '5-10 亿','10-30 亿', '30-50 亿','50-100 亿','100-150 亿','>150 亿']+['总计']]
    else:
        table=table[list(data[kw].unique())+['总计']]
    table=table.fillna(0)
    table=table.applymap(lambda x: int(x))
    return(table)
####################################################################
def total_summary(kw=['年'],data=[],gp=True,forma=False):   
    groupdata=data.groupby(kw)
    name=groupdata.count().index
    summary=DataFrame()
    for key in name:
        #print(key)
        tempdata=groupdata.get_group(key)
        profit=(tempdata.mean()[['后复权净值', '上证净值','深成净值', '创业板净值', '中小板净值']]-1)
        info_dict={'总数':tempdata['代码'].count(),'平均募资':round(tempdata['实际募资总额(亿元)'].mean(),3),
                   '平均折价':round(tempdata['折价'].mean(),3),
                   '平均折价收益率':(1/tempdata['折价']-1).mean(),'平均定增收益率':profit['后复权净值'],
                  '盈利数':tempdata[tempdata['后复权净值']>1]['后复权净值'].count(),
                  '平均盈利':round(tempdata[tempdata['后复权净值']>1]['后复权净值'].mean(),4)-1,
                 '亏损数':tempdata[tempdata['后复权净值']<=1]['后复权净值'].count(),
                 '平均亏损':round(tempdata[tempdata['后复权净值']<=1]['后复权净值'].mean(),4)-1,
                 #'加权定增收益率':round((tempdata['实际募资总额(亿元)']/tempdata['实际募资总额(亿元)'].sum()*tempdata['后复权净值']).sum()-1,4),
                 '上证收益率':profit['上证净值'],
                 '深成收益率':profit['深成净值'],'中小板收益率':profit['中小板净值'],'创业板收益率':profit['创业板净值']}
        if not gp:
            if len(kw)==1:
                info_dict.update({kw[0]:key})
            else:
                for i in range(len(kw)):
                    info_dict.update({kw[i]:key[i]})
            ttdata=Series(info_dict,['总数', '平均募资','平均折价','平均定增收益率',
                                     #'加权定增收益率',
                                     '盈利数','平均盈利','亏损数','平均亏损',
                         '平均折价收益率','上证收益率','深成收益率','中小板收益率','创业板收益率']+kw)
        else:
            ttdata=Series(info_dict,['总数', '平均募资','平均折价','平均定增收益率',
                                     #'加权定增收益率',
                                     '盈利数','平均盈利','亏损数','平均亏损',
                         '平均折价收益率','上证收益率','深成收益率','中小板收益率','创业板收益率'])
        summary=summary.append(DataFrame(ttdata).T)
    if not gp:
        summary.index=range(summary.shape[0])
    else:
        summary.index=name
    if forma:
        summary=summary.applymap(lambda x : "%.2f%%"  %(x*100))
        summary[['总数', '平均募资','盈利数','亏损数']]=summary[['总数', '平均募资','盈利数','亏损数']].applymap(lambda x : int(int(x[0:x.index('.')])/100))
    return(summary)
#####################################################################

######################################################################
def summay_plot(data,x='年',by='定向增发目的',col=3,title='历年定向增发',fontsize=10,
               sharex=True,sharey=True,top=.9,wspace=.2,hspace=.2,bottom=.1,right=0.95,left=0.05):
    sns.set_style('darkgrid')
    mpl.rcParams['font.sans-serif'] = ['SimHei'] #指定默认字体  
    mpl.rcParams['axes.unicode_minus'] = False 
    sns.set_context("talk")
    font = mpl.font_manager.FontProperties(fname=r"c:\windows\fonts\simsun.ttc", size=fontsize)
    mpl.rcParams['axes.titlesize']=1.5*fontsize
    mpl.rcParams['figure.titlesize']=2*fontsize
    data.index=data[x].apply(lambda t : str(int(t))+x)
    dd=DataFrame(index=data.sort_values(x).index.unique())
    num=len(data[by].unique())
    row=int(np.ceil(num/col))
    #print(row)
    fig,ax=plt.subplots(row,col,sharex=sharex,sharey=sharey,figsize=[20,15])
    for i in range(row):
        for j in range(col):
            #print(i*col+j)
            if (i*col+j)<num:
                df=dd.join(data.query('%s=="%s"'%(by,data[by].unique()[i*col+j]))).fillna(0)
            else:
                ax[i,j].set_axis_off()
                continue
            df[['平均折价']].plot(secondary_y=True,ax=ax[i,j],style='r-',legend=True,linewidth=2.0,alpha=0.8)
            #print(df)
            df[['总数','平均募资']].plot.bar(ax=ax[i,j], alpha=0.7)
            l1=ax[i,j].right_ax.get_lines()
            l2=ax[i,j].get_legend_handles_labels()
            ax[i,j].legend(l1+l2[0], [l1[0].get_label()]+l2[1],loc='upper left',fontsize=fontsize)
            ax[i,j].set_ylabel('发行总数/个,平均募资/亿',fontproperties=font)
            ax[i,j].right_ax.set_ylabel('平均折价',fontproperties=font)
            ax[i,j].set_xlabel('时间',fontproperties=font)
            ax[i,j].set_title(data[by].unique()[i*col+j])
            #yn=len(ax[i,j].get_yticks())
            #yr=ax[i,j].right_ax.get_yticks()
            #ax[i,j].right_ax.set_yticks(np.linspace(yr.min(),yr.max(),yn))
            #ax[i,j].right_ax.set_yticks([np.round(i,2) for i in np.linspace(0,1.2,10)])
            for label in ax[i,j].get_xticklabels() +ax[i,j].get_yticklabels()+ax[i,j].right_ax.get_yticklabels():
                label.set_font_properties(font)
    for i in range(row):
        for j in range(col):
            #print(i*col+j)
            if (i*col+j)<num:
                yn=len(ax[i,j].get_yticks())
                ymax=np.ceil(data['平均折价'].max()*10)/10
                ax[i,j].right_ax.set_yticks(np.linspace(0,ymax,yn))
            else:
                ax[i,j].set_axis_off()    
    plt.suptitle(title)
    plt.subplots_adjust(top=top,wspace=wspace,hspace=hspace,bottom=bottom,right=right,left=left)
    plt.show()  
########################################################################
def return_plot(data,hue='定向增发目的',idd='沪深300',col=None,col_wrap=None,col_order=None,
                 sharex=True,sharey=True,index_on=True,legend_out=True,palette='Set1',figsize=6,c_size=1,
                 fontscale=1.5,fontsize=25,title='一年期现金认购定增收益倍数分布',ylim=[0,2],
                 top=.9,wspace=.05,hspace=.15,bottom=.1,right=0.9,left=0.05,**kwargs):
    sns.set_style('dark')
    mpl.rcParams['font.sans-serif'] = ['SimHei'] #指定默认字体  
    mpl.rcParams['axes.unicode_minus'] = False 
    sns.set_context("talk",font_scale=fontscale)
    font = mpl.font_manager.FontProperties(fname=r"c:\windows\fonts\simsun.ttc", size=fontsize)
    order_size=data['实际募资总额(亿元)']
    if col:
        if not col_wrap:
            col_wrap=2
    if col=='板块':
        #col_order=['上证主板','深证主板','中小板','创业板']
        col_order=['上证主板','中小板','创业板','深证主板']
        order_size=data[['发行日期','板块','实际募资总额(亿元)']].sort_values(['板块','发行日期'])['实际募资总额(亿元)']
        if  not idd:
            idset=['上证','中小板','创业板','深成']
        else:
            idset=[idd,idd,idd,idd]
    else:
        idset=None
    g = sns.FacetGrid(data,size=figsize,hue=hue,col=col,col_wrap=col_wrap,col_order=col_order,legend_out=legend_out,
                     sharex=sharex,sharey=sharey,palette=palette)
    g=g.map(plt.scatter,'发行日期','后复权净值',s=order_size*c_size,edgecolors='g',linewidths=1,alpha=0.9).add_legend()
    if not index_on :
        g.set(ylim=ylim).fig.subplots_adjust(top=top,wspace=wspace,hspace=hspace,bottom=bottom,right=right,left=left)
        g.fig.suptitle(title)
        plt.show()
        return      
    for i,ax in enumerate(g.axes):
        if not col:
            ax=ax[0]
        if idset:
            idd=idset[i]
        ax_new=ax.twinx()
        ax.plot(data['发行日期'],data[idd+'净值'],color='y',alpha=0.8)
        ax.plot(data['发行日期'],data['折价'].rolling(window=10).mean(),color='b',alpha=0.3)
        ax_new.plot(data['发行日期'],data[idd],color='r',alpha=0.5)
        l=ax.get_lines()
        l1=ax.get_legend_handles_labels()
        l2=ax_new.get_lines()
        if legend_out:
            ax.legend(l+l2, ["同期"+idd+'收益倍数']+["同期折价移动平均"]+[l2[0].get_label()+'指数走势(右轴)'],loc='upper left',
                     fontsize=fontsize*0.75)
        else:
            ax.legend(l+l2+l1[0][2:], ["同期"+idd+'收益倍数']+["同期折价移动平均"]+[l2[0].get_label()+'指数走势(右轴)']+l1[1][2:],
                  loc='upper left',fontsize=fontsize*0.75)
        ax_new.set_ylabel(idd+'指数',fontproperties=font)
        ax.set_ylabel('定增收益倍数,定增折价',fontproperties=font)
        ax.set_xlabel('发行日期',fontproperties=font)
        #ticklabels=ax.get_xticklabels()
        #ax.set_xticklabels(ticklabels,rotation=45)
        #yn=len(ax.get_yticks())
        #yr=ax_new.get_yticks()
        #ax_new.set_yticks(np.linspace(yr.min(),yr.max(),yn))
    g.set(ylim=ylim).fig.subplots_adjust(top=top,wspace=wspace,hspace=hspace,bottom=bottom,right=right,left=left)
    g.fig.suptitle(title)
    plt.show()
#######################################################################

#######################################################################
def zhejia_plot(data,hue='定向增发目的',idd='沪深300',col=None,col_wrap=None,col_order=None,
                 sharex=True,sharey=True,index_on=True,palette='Set1',figsize=6,c_size=1,
                 fontscale=1.5,fontsize=25,title='一年期定增折价分布',ylim=[0.2,1.4],
                 top=.9,wspace=.05,hspace=.15,bottom=.1,right=0.85,left=0.05,**kwargs):
    sns.set_style('dark')
    mpl.rcParams['font.sans-serif'] = ['SimHei'] #指定默认字体  
    mpl.rcParams['axes.unicode_minus'] = False 
    sns.set_context("talk",font_scale=fontscale)
    font = mpl.font_manager.FontProperties(fname=r"c:\windows\fonts\simsun.ttc", size=fontsize)
    order_size=data['实际募资总额(亿元)']
    if col:
        if not col_wrap:
            col_wrap=2
    if col=='板块':
        col_order=['上证主板','中小板','创业板','深证主板']
        order_size=data[['发行日期','板块','实际募资总额(亿元)']].sort_values(['板块','发行日期'])['实际募资总额(亿元)']
        if  not idd:
            idset=['上证','中小板','创业板','深成']
        else:
            idset=[idd,idd,idd,idd]
    else:
        idset=None
    g = sns.FacetGrid(data,size=figsize,hue=hue,col=col,col_wrap=col_wrap,col_order=col_order,
                     sharex=sharex,sharey=sharey,palette=palette)
    g=g.map(plt.scatter,'发行日期','折价',s=order_size*c_size,edgecolors='g',linewidths=1,alpha=0.9).add_legend()
    if not index_on :
        g.set(ylim=ylim).fig.subplots_adjust(top=top,wspace=wspace,hspace=hspace,bottom=bottom,right=right,left=left)
        g.fig.suptitle(title)
        plt.show()
        return      
    for i,ax in enumerate(g.axes):
        if not col:
            ax=ax[0]
        if idset:
            idd=idset[i]
        ax_new=ax.twinx()
        ax_new.plot(data['发行日期'],data[idd],color='r',alpha=0.5)
        ax_new.set_ylabel(idd+'指数',fontproperties=font)
        ax.set_ylabel('平均折价率',fontproperties=font)
        #ticklabels=ax.get_xticklabels()
        #ax.set_xticklabels(ticklabels,rotation=45)
        ax.set_xlabel('发行日期',fontproperties=font)
    g.set(ylim=ylim).fig.subplots_adjust(top=top,wspace=wspace,hspace=hspace,bottom=bottom,right=right,left=left)
    g.fig.suptitle(title)
    plt.show()
    
def initiate_data():
    con=sqlite3.connect('定增.db')
    data=read_sql('select * from 合并 where 期限==1 or 期限==3',con)
    sampledata=data[['代码','名称','发行日期','限售股份解禁日','实际募资总额(亿元)','折价','发行对象','定向增发目的','年','月','期限','企业性质','认购方式','证监会行业','Wind行业',]].copy()
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
    con=sqlite3.connect('定增.db')
    jiejin=read_sql('select * from 解禁',con)
    un_jiejin=read_sql('select * from 未解禁',con)
    data=merge(combine_data,jiejin.append(un_jiejin,ignore_index=True),on=['代码','实际募资总额(亿元)'],how='left')
    unjiejin=merge(combine_data,un_jiejin,on=['代码','实际募资总额(亿元)'],how='inner')
    jiejin=merge(combine_data,jiejin,on=['代码','实际募资总额(亿元)'],how='inner')
    data['规模']=data['实际募资总额(亿元)'].apply(money_spit)
    data['发行对象']=data['发行对象'].apply(fx_duixiang)
    return(unjiejin,jiejin,data)

##################################################################
def all_summary_plot(jiejin,unjiejin):
    unjj=unjiejin[['代码','名称','发行日期','限售股份解禁日','期限','后复权净值','实际募资总额(亿元)', '折价','定向增发目的']].sort_values('实际募资总额(亿元)')
    unjj.index=list(range(0,len(unjj)))
    unjj['年']=unjj['限售股份解禁日'].apply(lambda x : x.year)
    unjj['月']=unjj['限售股份解禁日'].apply(lambda x : x.month)
    unjj_sum=pivot_table(data=unjj,values='实际募资总额(亿元)',index=['年','月'],columns='期限',aggfunc=np.sum)
    unjj_r=pivot_table(data=unjj,values='后复权净值',index=['年','月'],columns='期限',aggfunc=np.mean)*100
    unjj_c=unjj.groupby(['年','月']).sum()['期限']
    unjj_r.columns=['一年期净值','三年期净值']
    unjj_sum.columns=['一年期','三年期']
    unjj_c.name='定增数目'
    fig= plt.figure()
    ax=fig.add_subplot(1,1,1)
    unjj_c.plot(ax=ax,secondary_y=True,color='b',alpha=0.6,legend=True)
    unjj_r.plot(ax=ax,secondary_y=True,alpha=0.7,color=['r','y'])
#ax.right_ax.addlegend()
    unjj_sum.plot(ax=ax,kind='bar',stacked=True,figsize=(20,5))
    fig.suptitle('未解禁定增股汇总',fontsize=20)
    ax.set_ylabel('解禁股总额 (亿元)')
    ax.set_xlabel('解禁时间',fontsize=15)
    ax.right_ax.set_ylabel('定增数目(只) 平均净值(%)')
    
    jj=jiejin[['代码','名称','发行日期','限售股份解禁日','期限','后复权净值','实际募资总额(亿元)', '折价','定向增发目的']].sort_values('实际募资总额(亿元)')
    jj.index=list(range(0,len(jj)))
    jj['年']=jj['限售股份解禁日'].apply(lambda x : x.year)
    jj['月']=jj['限售股份解禁日'].apply(lambda x : x.month)
    jj_sum=pivot_table(data=jj,values='实际募资总额(亿元)',index=['年','月'],columns='期限',aggfunc=np.sum)
    jj_r=pivot_table(data=jj,values='后复权净值',index=['年','月'],columns='期限',aggfunc=np.mean)*100
    jj_c=jj.groupby(['年','月']).sum()['期限']
    jj_r.columns=['一年期解禁平均净值','三年期解平均禁净值']
    jj_sum.columns=['一年期','三年期']
    jj_c.name='定增数目'
    fig= plt.figure()
    ax=fig.add_subplot(1,1,1)
    jj_c.plot(ax=ax,secondary_y=True,color='b',alpha=0.6,legend=True)
    jj_r.plot(ax=ax,secondary_y=True,alpha=0.7,color=['r','y'])
#ax.right_ax.addlegend()
    jj_sum.plot(ax=ax,kind='bar',stacked=True,figsize=(20,10))
    fig.suptitle('解禁定增股汇总',fontsize=20)
    ax.set_ylabel('解禁股总额 (亿元)')
    ax.set_xlabel('解禁时间',fontsize=15)
    ax.right_ax.set_ylabel('定增数目(只) 平均净值(%)')
    ax.right_ax.set_yticks(np.linspace(0,800,9))
################################################################
class plot_data:
    def __init__(self,return_data,method=[1,'现金']):
        self.all_data = return_data
        self.return_data=self.all_data.query('认购方式=="%s"'%method[1]).query('期限==%s'%method[0])
        self.term=method[0]
        self.style=method[1]
        #self.bankui=
        
    def re_set(self,method=[1,'现金']):
        self.return_data=self.all_data.query('认购方式=="%s"'%method[1]).query('期限==%s'%method[0])
        self.term=method[0]
        self.style=method[1]
        
    def full_plot(self):
        return_data=self.all_data
        df1=pivot_table(return_data.query('期限==1'),values='实际募资总额(亿元)',columns='定向增发目的',index='年',aggfunc=np.sum)
        df2=pivot_table(return_data.query('期限==1'),values='折价',index='年',aggfunc=np.mean)*100
        df3=return_data.query('期限==1').groupby('年').count()['代码']
        df23=DataFrame([df2,df3]).T
        df1_16=pivot_table(return_data.query('期限==1'),values='实际募资总额(亿元)',columns='年',index='月',aggfunc=np.sum)[[2015.0,2016.0]]

        df4=pivot_table(return_data.query('期限==3'),values='实际募资总额(亿元)',columns='定向增发目的',index='年',aggfunc=np.sum)
        df5=pivot_table(return_data.query('期限==3'),values='折价',index='年',aggfunc=np.mean)*100
        df6=return_data.query('期限==3').groupby('年').count()['代码']
        df56=DataFrame([df5,df6]).T
        df3_16=pivot_table(return_data.query('期限==3'),values='实际募资总额(亿元)',columns='年',index='月',aggfunc=np.sum)[[2015.0,2016.0]]
        df1_16.index=df3_16.index=[str(int(i))+'月' for i in df1_16.index]
        df1_16.columns=df3_16.columns=['2015年','2016年']
        df1.index=df23.index=df4.index=df56.index=[str(int(i))+'年' for i in df1.index]

        fig = plt.figure()
        ax1=fig.add_subplot(2,2,1)
        ax0=ax1.twinx()
        df23.plot(ax=ax0,alpha=0.8,legend=False)
        df1.plot(ax=ax1,kind='bar', stacked=True, alpha=0.8,color=colors.cnames,figsize=[20,10])
        ax1.set_ylabel('募集资金总额 (亿元)')
        ax1.set_xlabel('发行年份')
        ax1.set_title('一年期定增发行概况')
        ax0.set_ylabel('发行数量 (只), 定增折价率 (%)')

        ax2=fig.add_subplot(2,2,3)
        ax00=ax2.twinx()
        df56.plot(ax=ax00,alpha=0.8,legend=False)
        df4.plot(ax=ax2,kind='bar', stacked=True, alpha=0.8,color=colors.cnames,figsize=[20,10])
        ax2.set_ylabel('募集资金总额 (亿元)')
        ax2.set_xlabel('发行年份')
        ax2.set_title('三年期定增发行概况')
        ax00.set_ylabel('发行数量 (只), 定增折价率 (%)')
        ax00.set_yticks(np.linspace(0,400,7))

        ax3=fig.add_subplot(2,2,2)
        df1_r=pivot_table(return_data.query('期限==1'),values='后复权净值',columns='年',index='月',aggfunc=np.mean)[[2015.0,2016.0]]*100
        df1_r.index=[str(int(i))+'月' for i in df1_r.index]
        df1_r.columns=['2015年平均净值','2016平均净值']
        df1_r.plot(ax=ax3,secondary_y=True,alpha=0.6,legend=True)
        df1_16.plot(ax=ax3,kind='bar')
        ax3.right_ax.set_ylabel('平均净值(%)')
        ax3.set_ylabel('募集资金总额 (亿元)')
        ax3.set_title('15-16年一年期定增发行对比')
        ax3.set_yticks(np.linspace(0,2200,11))
        ax3.right_ax.set_yticks(np.linspace(0,220,11))

        ax4=fig.add_subplot(2,2,4)
        df3_r=pivot_table(return_data.query('期限==3'),values='后复权净值',columns='年',index='月',aggfunc=np.mean)[[2015.0,2016.0]]*100
        df3_r.columns=['2015年平均净值','2016平均净值']
        df3_r.index=[str(int(i))+'月' for i in df3_r.index]
        df3_r.plot(ax=ax4,secondary_y=True,alpha=0.6,legend=True)
        df3_16.plot(ax=ax4,kind='bar')
        ax4.set_yticks(np.linspace(0,1500,6))
        ax4.right_ax.set_yticks(np.linspace(0,350,6))
        ax4.right_ax.set_ylabel('平均净值(%)')
        ax4.set_ylabel('募集资金总额 (亿元)')
        ax4.set_xlabel('发行月份')
        ax4.set_title('15-16年三年期定增发行对比')
        plt.tight_layout()
        plt.show()
        
    def industry_plot(self,year):
        sns.set_style('darkgrid')
        mpl.rcParams['font.sans-serif'] = ['SimHei'] #指定默认字体  
        mpl.rcParams['axes.unicode_minus'] = False 
        self.all_data['发行数']=1
        tt=group_summary(kw=['证监会行业','年'],data=self.all_data)
        fig = plt.figure() 
        axes1 = fig.add_subplot(111) 
        df1=pivot_table(tt.query('年==%s'%(year)),values='平均募资',index='证监会行业',aggfunc=np.sum)
        df2=pivot_table(tt.query('年==%s'%(year)),values='定增发行数',index='证监会行业',aggfunc=np.sum)
        df=(df1*df2)
        df.index=[(a,str(b)+'只',str(c)+'亿') for a,b,c in zip(list(df.index),df2,df1)]
        df=df.sort_values(na_position='last')
        df.plot(ax=axes1,kind='barh', stacked=False, alpha=0.8,color=colors.cnames,figsize=[20,len(df)/4])
        axes1.set_title(str(year)+'年定增各行业总募资规模',{'fontsize':20})
        axes1.set_xlabel('总募集金额 亿元')
        
        def hy_plot(self,ax,year=year,method=[1,'现金']):
            mpl.rcParams['xtick.labelsize']=10
            mpl.rcParams['ytick.labelsize']=12
            mpl.rcParams['axes.labelsize']=14
            df=pivot_table(self.all_data.query('年==%s'%year).query('认购方式=="%s"'%method[1]).query('期限==%s'%method[0]),
                           values='发行数',index='证监会行业',aggfunc=np.sum)
            df1=pivot_table(self.all_data.query('年==%s'%year).query('认购方式=="%s"'%method[1]).query('期限==%s'%method[0]),
                            values='实际募资总额(亿元)',index='证监会行业',aggfunc=np.sum)
            df1=df1.sort_values(ascending=False)
            df.plot(ax=ax,secondary_y=True,alpha=0.5,color='r')
            ax.right_ax.set_ylabel('定增发行数 ')
            df1.plot(ax=ax,kind='bar', stacked=True)
            ax.set_title(str(year)+'年%s年期%s认购类定增汇总'%(method[0],method[1]),{'fontsize':20})
            ax.set_ylabel('总募资规模(亿元)')
            yn=len(ax.right_ax.get_yticks())
            yr=ax.get_yticks()
            yy=np.linspace(0,yr.max(),yn)
            ax.set_yticks([round(i,0) for i in yy])
        
        figs1 = plt.figure(figsize=(20,4)) 
        ax0=figs1.add_subplot(121)
        hy_plot(self,ax=ax0,year=year,method=[1,'现金'])
        ax2=figs1.add_subplot(122)
        hy_plot(self,ax=ax2,year=year,method=[3,'现金']) 
        #plt.tight_layout()
        
        figs2 = plt.figure(figsize=(20,4)) 
        ax1=figs2.add_subplot(121)
        hy_plot(self,ax=ax1,year=year,method=[3,'现金'])
        ax3=figs2.add_subplot(122)
        hy_plot(self,ax=ax3,year=year,method=[3,'现金'])
        #plt.tight_layout()
        
    def objective_plot(self,year,kw='定向增发目的'):
        fig=plt.figure()
        full_kw=DataFrame(columns=self.all_data[kw].unique())
        def os_plot(self,ax,year=year):
            df=full_kw.append(pivot_table(self.return_data.query('年==%s'%year),values='实际募资总额(亿元)',index='月',columns=kw,aggfunc=np.sum))
            df1=pivot_table(self.return_data.query('年==%s'%year),values='折价',index='月',aggfunc=np.mean)
            df.index=df1.index=[str(int(i))+'月' for i in df1.index]
            axx=ax.twinx()
            df1.plot(ax=axx,alpha=0.8,figsize=[20,10],color='g')
            axx.set_ylabel('平均折价 ')
            df.plot(ax=ax,kind='bar', stacked=True, alpha=0.8,color=colors.cnames,figsize=[20,10])
            ax.set_title(str(year)+'年%s年期%s认购类定增汇总'%(self.term,self.style),{'fontsize':20})
            ax.set_ylabel('总募资规模 亿元')
            yn=len(ax.get_yticks())
            yr=axx.get_yticks()
            yy=np.linspace(0,yr.max()+0.2,yn)
            axx.set_yticks([round(i,3) for i in yy])
        
        ax0=fig.add_subplot(221)
        self.re_set(method=[1,'现金'])
        os_plot(self,ax=ax0,year=year)
        ax2=fig.add_subplot(222)
        self.re_set(method=[3,'现金'])
        os_plot(self,ax=ax2,year=year) 
        ax1=fig.add_subplot(223)
        self.re_set(method=[1,'资产'])
        os_plot(self,ax=ax1,year=year)
        ax3=fig.add_subplot(224)
        self.re_set(method=[3,'资产'])
        os_plot(self,ax=ax3,year=year)
        plt.tight_layout()
        
        self.re_set(method=[1,'现金'])
        
    def return_summary(self,kw=['年'],gp=True,forma=False):
        data=self.return_data
        return(total_summary(kw=kw,data=data,gp=gp,forma=forma))
    
    def return_plot(self,year):
        tt=self.return_data.query('年>=%s'%year)
        ylim=[min(np.percentile(tt['后复权净值'],0),0.3),np.percentile(tt['后复权净值'],95)]
        return_plot(tt,hue='定向增发目的',idd=None,col='板块',col_wrap=2,fontsize=10,fontscale=1,
                    hspace=0.20,wspace=0.2,right=0.8,
                    ylim=ylim,title='历年%s年期%s认购类定增收益倍数分布'%(self.term,self.style))
        
    def zhejia_plot(self,year):
        data=self.return_data.query('年>=%s'%year)
        zhejia_plot(data,col='板块',hue='定向增发目的',idd=None,col_wrap=2,fontsize=10,fontscale=1,
                    hspace=0.20,wspace=0.2,right=0.8,
                    title='历年%s年期%s认购类定增折价分布'%(self.term,self.style)) 
#####################################################################
class lasso_obj:
    def __init__(self,return_data,bench_mark=['沪深300净值','创业板净值']):
        self.all_data = return_data
        self.bench_mark=bench_mark
        self.x_set=['发行日期','年','板块','后复权净值','折价']+bench_mark
        self.dummy={}
    def ols_set(self,method=[1,'现金']):
        self.return_data=self.all_data.query('认购方式=="%s"'%method[1]).query('期限==%s'%method[0])
        self.term=method[0]
        self.style=method[1]
        olsdata=self.return_data[['发行日期','年','板块', '后复权净值','折价','定向增发目的','Wind行业','发行对象','规模',
                                                 '企业性质','实际募资总额(亿元)']+self.bench_mark].copy()
        olsdata[['后复权净值']+self.bench_mark]=olsdata[['后复权净值']+self.bench_mark]-1
        olsdata['折价']=1/olsdata['折价']-1
        self.olsdata=olsdata
        self.dummy.update({'目的':get_dummies(olsdata['定向增发目的'], prefix='目的')})
        self.dummy.update({'行业':get_dummies(olsdata['Wind行业'], prefix='行业')})
        self.dummy.update({'对象':get_dummies(olsdata['发行对象'], prefix='对象')})
        self.dummy.update({'性质':get_dummies(olsdata['企业性质'], prefix='性质')})
        self.dummy.update({'规模':get_dummies(olsdata['规模'], prefix='规模')})
        
    def return_lasso(self,kw='板块',normalize=True):
            testdata=self.olsdata[self.x_set]
            for key in ['目的','行业','对象','性质','规模']:
                testdata=testdata.join(self.dummy[key])
   
            group=testdata.groupby(kw)
            name=group.count().index
            cof={}
            fig = plt.figure(figsize=(20,10))
            fig.suptitle('LASSO Regression with ' + ' dummy variable for '+str(self.term)+ ' 年期'+self.style+'认购类定增',fontsize=20)
            for i,group_name in enumerate(name):
                plt.subplot('22%s'%(i+1))
                xydata=group.get_group(group_name)
                if normalize:
                    reg = LassoCV(cv=10,fit_intercept=False,normalize=True)
                    x=preprocessing.scale(xydata.ix[:,'折价':].fillna(0))
                    y=preprocessing.scale(xydata['后复权净值'].fillna(0))
                    reg.fit(x,y)
                    coeff=Series(reg.coef_,list(xydata.ix[:,'折价':].columns))
                    cof.update({i:coeff.to_dict()})
                else:
                    reg = LassoCV(cv=20,fit_intercept=True,normalize=False)
                    x=xydata.ix[:,'折价':].fillna(0)
                    y=xydata['后复权净值'].fillna(0)
                    reg.fit(x,y)
                    coeff=Series(reg.coef_,list(x.columns))
                    coeff['intercept']=reg.intercept_
                    cof.update({i:coeff.to_dict()})
                plt.scatter(np.array(xydata['发行日期']),np.array(y),c='b')
                plt.plot(xydata['发行日期'],reg.predict(x),'g-')
                plt.title(group_name+"alpha ="+str(reg.alpha_))
            plt.show()
            fig.subplots_adjust(top=0.9)
            coefficient=DataFrame(cof).T
            coefficient.index=name
            self.lasso_coef=coefficient.T
            
    def mw_lasso(self,normalize=True,pl=True):
            testdata=self.olsdata[self.x_set]
            for key in ['目的','行业','对象','性质','规模']:
                testdata=testdata.join(self.dummy[key])
            cof={}
            xydata=testdata
            if normalize:
                reg = LassoCV(cv=10,fit_intercept=False,normalize=True)
                x=preprocessing.scale(xydata.ix[:,'折价':].fillna(0))
                y=preprocessing.scale(xydata['后复权净值'].fillna(0))
                try:
                    reg.fit(x,y)
                    coeff=Series(reg.coef_,list(xydata.ix[:,'折价':].columns))
                except Exception as e:
                    coeff=Series()
            if pl:
                fig = plt.figure(figsize=(10,5))
                plt.subplot(111)
                plt.scatter(np.array(xydata['发行日期']),np.array(y),c='b')
                plt.plot(xydata['发行日期'],reg.predict(x),'g-')
                plt.title("alpha ="+str(reg.alpha_))
            self.lasso_coef=coeff
#####################################################################
if __name__=="__main__":
    combine_data,return_data=initiate_data()
    testdata=combine_data.query('认购方式=="现金"').query('期限==1')
    tt=group_summary(kw=['定向增发目的','年'],data=testdata)
    summay_plot(tt,x='年',by='定向增发目的',col=3,title='历年一年期现金认购类定向增发',fontsize=15)
    pp=plot_data(return_data,method=[1,"现金"])
    pp.full_plot()
    year_range=(2009,2016,1)
    interact(pp.industry_summary,year=year_range)
    interact(pp.objective_summary,year=year_range)
    print('#####################################一年期现金认购类定增收益率统计########################')
    pp.return_summary(kw=['年'],forma=True)
    interact(pp.return_plot,year=year_range)
    interact(pp.zhejia_plot,year=year_range)
    
    LB1=lasso_obj(return_data)
    LB1.ols_set(method=[1,'现金'])
    LB1.return_lasso()

    LB3=lasso_obj(return_data)
    LB3.ols_set(method=[3,'现金'])
    LB3.return_lasso()
