# coding: utf-8
from pandas import *
import numpy as np
import sqlite3
import matplotlib.pyplot as plt # side-stepping mpl backend
import matplotlib as mpl
import seaborn as sns
from ipywidgets import interact
from matplotlib import colors
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
###############################################
def group_summary(kw=['年'],data=[]):   
    groupdata=data.groupby(kw)
    name=groupdata.count().index
    summary=DataFrame()
    for key in name:
        #print(key)
        tempdata=groupdata.get_group(key)
        info_dict={'总数':tempdata['代码'].count(),'平均募资':round(tempdata['实际募资总额(亿元)'].mean(),3),
                       '平均折价':round(tempdata['折价'].mean(),3)}
        if len(kw)==1:
            info_dict.update({kw[0]:key})
        else:
            for i in range(len(kw)):
                info_dict.update({kw[i]:key[i]})
        ttdata=Series(info_dict,index=kw+['总数','平均募资','平均折价'])
        summary=summary.append(DataFrame(ttdata).T)
    summary.index=range(summary.shape[0])
    return(summary)
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
            ax[i,j].set_ylabel('总数/个,平均募资/亿',fontproperties=font)
            ax[i,j].right_ax.set_ylabel('平均折价',fontproperties=font)
            ax[i,j].set_xlabel('时间',fontproperties=font)
            ax[i,j].set_title(data[by].unique()[i*col+j])
            #yn=len(ax[i,j].get_yticks())
            #yr=ax[i,j].right_ax.get_yticks()
            #ax[i,j].right_ax.set_yticks(np.linspace(yr.min(),yr.max(),yn))
            ax[i,j].right_ax.set_yticks([np.round(i,2) for i in np.linspace(0,1,10)])
            for label in ax[i,j].get_xticklabels() +ax[i,j].get_yticklabels()+ax[i,j].right_ax.get_yticklabels():
                label.set_font_properties(font)
    plt.suptitle(title)
    plt.subplots_adjust(top=top,wspace=wspace,hspace=hspace,bottom=bottom,right=right,left=left)
    plt.show()  
########################################################################
def return_plot(data,hue='定向增发目的',idd='沪深300',col=None,col_wrap=None,col_order=None,
                 sharex=True,sharey=True,index_on=True,legend_out=True,palette='Set1',
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
    g = sns.FacetGrid(data,size=10,hue=hue,col=col,col_wrap=col_wrap,col_order=col_order,legend_out=legend_out,
                     sharex=sharex,sharey=sharey,palette=palette)
    g=g.map(plt.scatter,'发行日期','后复权净值',s=order_size*3,edgecolors='g',linewidths=1,alpha=0.9).add_legend()
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
        #yn=len(ax.get_yticks())
        #yr=ax_new.get_yticks()
        #ax_new.set_yticks(np.linspace(yr.min(),yr.max(),yn))
    g.set(ylim=ylim).fig.subplots_adjust(top=top,wspace=wspace,hspace=hspace,bottom=bottom,right=right,left=left)
    g.fig.suptitle(title)
    plt.show()
#######################################################################

#######################################################################
def zhejia_plot(data,hue='定向增发目的',idd='沪深300',col=None,col_wrap=None,col_order=None,
                 sharex=True,sharey=True,index_on=True,palette='Set1',
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
    g = sns.FacetGrid(data,size=10,hue=hue,col=col,col_wrap=col_wrap,col_order=col_order,
                     sharex=sharex,sharey=sharey,palette=palette)
    g=g.map(plt.scatter,'发行日期','折价',s=order_size*3,edgecolors='g',linewidths=1,alpha=0.9).add_legend()
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
        ax.set_xlabel('发行日期',fontproperties=font)
    g.set(ylim=ylim).fig.subplots_adjust(top=top,wspace=wspace,hspace=hspace,bottom=bottom,right=right,left=left)
    g.fig.suptitle(title)
    plt.show()
    
def initiate_data():
    con=sqlite3.connect('定增.db')
    data=read_sql('select * from 合并 where 期限==1 or 期限==3',con)
    sampledata=data[['代码','发行日期','限售股份解禁日','实际募资总额(亿元)','折价','发行对象','定向增发目的','年','月','期限','企业性质','认购方式','证监会行业','Wind行业',]].copy()
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
    return(combine_data,data)

##################################################################

class plot_data:
    def __init__(self,return_data,method=[1,'现金']):
        self.all_data = return_data
        self.return_data=self.all_data.query('认购方式=="%s"'%method[1]).query('期限==%s'%method[0])
        self.term=method[0]
        self.style=method[1]
        #self.bankui=
    
    def industry_summary(self,year):
        sns.set_style('darkgrid')
        mpl.rcParams['font.sans-serif'] = ['SimHei'] #指定默认字体  
        mpl.rcParams['axes.unicode_minus'] = False 
        tt=group_summary(kw=['证监会行业','年'],data=self.return_data)
        fig = plt.figure() 
        axes1 = fig.add_subplot(111) 
        df1=pivot_table(tt.query('年==%s'%(year)),values='平均募资',index='证监会行业',aggfunc=np.sum)
        df2=pivot_table(tt.query('年==%s'%(year)),values='总数',index='证监会行业',aggfunc=np.sum)
        df=(df1*df2)
        df.index=[(a,str(b)+'只',str(c)+'亿') for a,b,c in zip(list(df.index),df2,df1)]
        df=df.sort_values(na_position='last')
        df.plot(ax=axes1,kind='barh', stacked=False, alpha=0.8,color=colors.cnames,figsize=[20,len(df)/2])
        axes1.set_title(str(year)+'年%s年期%s认购类定增各行业总募资规模'%(self.term,self.style),{'fontsize':20})
        axes1.set_xlabel('总募集金额 亿元')
        
    def objective_summary(self,year):
        sns.set_style('darkgrid')
        mpl.rcParams['font.sans-serif'] = ['SimHei'] #指定默认字体  
        mpl.rcParams['axes.unicode_minus'] = False
        tt=group_summary(kw=['定向增发目的','月','年'],data=self.return_data)
        fig,ax=plt.subplots(3,1,sharex=True)
        df=pivot_table(tt.query('年==%s'%(year)),values='平均折价',columns='定向增发目的',index='月',aggfunc=np.sum).mean(axis=1)
        df1=pivot_table(tt.query('年==%s'%(year)),values='平均募资',columns='定向增发目的',index='月',aggfunc=np.sum)
        df2=pivot_table(tt.query('年==%s'%(year)),values='总数',columns='定向增发目的',index='月',aggfunc=np.sum)
        df0=df1*df2
        df1.index=df0.index=df.index=df2.index=[str(int(i))+'月' for i in df.index]
        axx=ax[0].twinx()
        df.plot(ax=axx,alpha=0.8,figsize=[20,10],color='r')
        axx.set_ylabel('平均折价 ')
        df0.plot(ax=ax[0],kind='bar', stacked=True, alpha=0.8,color=colors.cnames,figsize=[20,10])
        ax[0].set_title(str(year)+'年%s年期%s认购类定增汇总'%(self.term,self.style),{'fontsize':20})
        ax[0].set_xlabel('总募资规模 亿元')
        yn=len(ax[0].get_yticks())
        yr=axx.get_yticks()
        yy=np.linspace(yr.min(),yr.max(),yn)
        axx.set_yticks([round(i,2) for i in yy])
        df1.plot(ax=ax[1],kind='bar', stacked=False, alpha=0.8,color=colors.cnames,figsize=[20,10])
        ax[1].set_ylabel('平均募资规模 亿元')
        ax[1].set_title(str(year)+'年%s年期%s认购类定增平均募资规模'%(self.term,self.style),{'fontsize':20})
        #df2=pivot_table(tt.query('年==%s'%(year)),values='总数',columns='定向增发目的',index='月',aggfunc=np.sum)
        df2.plot(ax=ax[2],kind='bar', stacked=False, alpha=0.8,color=colors.cnames,figsize=[20,10])
        ax[2].set_ylabel('增发数 只')
        ax[2].set_xlabel('发行时间')
        ax[2].set_title(str(year)+'年%s年期%s认购类定增发行数量'%(self.term,self.style),{'fontsize':20})
        plt.tight_layout()
        
    def return_summary(self,kw=['年'],gp=True,forma=False):
        data=self.return_data
        groupdata=data.groupby(kw)
        name=groupdata.count().index
        summary=DataFrame()
        for key in name:
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
    
    
    def return_plot(self,year):
        tt=self.return_data.query('年>=%s'%year)
        ylim=[min(np.percentile(tt['后复权净值'],0),0.3),np.percentile(tt['后复权净值'],95)]
        return_plot(tt,hue='定向增发目的',idd=None,col='板块',col_wrap=2,fontsize=20,font_scale=1.5,
                    hspace=0.20,wspace=0.2,right=0.85,
                    ylim=ylim,title='历年%s年期%s认购类定增收益倍数分布'%(self.term,self.style))
        
    def zhejia_plot(self,year):
        data=self.return_data.query('年>=%s'%year)
        zhejia_plot(data,col='板块',hue='定向增发目的',idd=None,col_wrap=2,fontsize=20,font_scale=1.5,
                    hspace=0.20,wspace=0.2,right=0.85,
                    title='历年%s年期%s认购类定增折价分布'%(self.term,self.style)) 
#####################################################################
if __name__=="__main__":
    con=sqlite3.connect('定增.db')
    data=read_sql('select * from 合并 where 期限==1 or 期限==3',con)
    #data=read_sql('select * from 合并 where 期限==1',con)
    sampledata=data[['代码','发行日期','限售股份解禁日','实际募资总额(亿元)','折价','发行对象','定向增发目的','年','月','期限','企业性质','认购方式','证监会行业','Wind行业',]].copy()
    sampledata['认购方式']=sampledata['认购方式'].apply(lambda x : '未知' if x is None else x )
    sampledata['发行日期']=sampledata['发行日期'].apply(lambda x:datetime.strptime(x[0:10],'%Y-%m-%d'))
    sampledata['限售股份解禁日']=sampledata['限售股份解禁日'].apply(lambda x:datetime.strptime(x[0:10],'%Y-%m-%d'))
    #sampledata=sampledata[sampledata['限售股份解禁日']<datetime.today()].sort_values('发行日期')
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
    
    testdata=combine_data.query('年>2015').query('认购方式=="现金"').query('期限==1')
    tt=group_summary(kw=['定向增发目的','月'],data=testdata)
    summay_plot(tt,x='月',by='定向增发目的',col=3,title='2016年每月定向增发',fontsize=20)
    '''
    zhejia_plot(combine_data,idd='沪深300',col='认购方式',col_order=['现金','资产','未知'],hue='定向增发目的',wspace=0.15)
    zhejia_plot(combine_data,idd='沪深300',hue='定向增发目的')
    zhejia_plot(combine_data,col='板块',hue='定向增发目的',idd='沪深300',wspace=0.15,hspace=0.20,fontsize=15)
    ##指定指数为沪深300
    zhejia_plot(combine_data,col='板块',hue='定向增发目的',idd=None,wspace=0.15,hspace=0.20,fontsize=15)
    ##不指定指数,默认为各板块对应指数
    testdata=combine_data.query('年>2014')
    zhejia_plot(testdata[testdata['认购方式']=='现金'],idd='上证',col='板块',hue='定向增发目的',title='15-16年现金认购类一年期定增折价分布图',
                 wspace=0.15)
    zhejia_plot(testdata[testdata['认购方式']=='现金'],idd=None,col='板块',hue='定向增发目的',title='15-16年现金认购类一年期定增折价分布图',
                 wspace=0.15)
    '''
    con=sqlite3.connect('定增.db')
    jiejin=read_sql('select * from 解禁',con)
    un_jiejin=read_sql('select * from 未解禁',con)
    data=merge(combine_data,jiejin.append(un_jiejin,ignore_index=True),on=['代码','实际募资总额(亿元)'],how='left')
    testdata=data[['发行日期', '中证500', '沪深300', '创业板', '中小板', '深成', '上证','折价','板块','年','月',
             '期限','后复权净值', '上证净值','定向增发目的','认购方式','实际募资总额(亿元)',
             '深成净值', '创业板净值', '中小板净值', '沪深300净值', '中证500净值']]
    tt=testdata.query('认购方式=="现金"').query('期限==1')
    return_plot(tt,hue='定向增发目的',idd=None,col='板块',col_wrap=2,ylim=[0,5],wspace=0.2,right=0.9,title='历年一年期现金认购定增收益倍数分布')
    tt=testdata.query('认购方式=="现金"').query('期限==1').query('年>2014')
    return_plot(tt,hue='定向增发目的',idd=None,col='板块',col_wrap=2,ylim=[0.5,2.5],wspace=0.2,right=0.9,title='15-16一年期现金认购定增收益倍数分布')
    return_plot(tt,hue='定向增发目的',idd='上证',ylim=[0.5,2],wspace=0.2,right=0.85,title='15-16一年期现金认购定增收益倍数分布')
    
    data_summary=total_summary(['板块','定向增发目的'],data.query('期限==1').query('认购方式=="现金"'),forma=True)