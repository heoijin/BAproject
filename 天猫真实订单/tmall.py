import pandas as pd
from matplotlib import pyplot as plt
from pyecharts import options as opts
import seaborn as sns
import warnings
# 漏斗图
from pyecharts.charts import Funnel
# 地图
from pyecharts.charts import Map
# pyecharts转存为png所需要的库
from  pyecharts.render import make_snapshot
from snapshot_selenium import snapshot

plt.rcParams['font.sans-serif']=['SimHei'] # 用来正常显示中文标签
plt.rcParams['axes.unicode_minus']=False # 用来正常显示负号
pd.set_option('display.max_columns', None) # 显示所有列
warnings.filterwarnings('ignore')

def open_file():
    df=pd.read_csv('report.csv')
    df['订单创建时间']=pd.to_datetime(df['订单创建时间'])
    df['订单付款时间']=pd.to_datetime(df['订单付款时间'])
    return df

def totle_sales_amount(df):
    '''
    计算每日销售额情况
    :param df:
    :return:
    '''
    df_=df.groupby(pd.Grouper(key='订单付款时间',freq='D'))['买家实际支付金额'].sum()
    _x=[f'{m}月{d}日' for m,d in zip(df_.index.month, df_.index.day)]
    plt.figure(figsize=(16,9),dpi=160)
    plt.plot(range(len(_x)), df_)
    plt.text(0,df_.max(),f'2月总销售额情况为{round(df_.sum(),2)}元',fontsize=20)
    for x,y in zip(range(len(_x)),df_.values):
         plt.text(x, y+7000,int(y),ha='center')
    plt.xticks(range(len(_x)),_x,rotation=45)
    plt.ylabel('销售额')
    plt.xlabel('日期')
    plt.title('销售额每日走势',fontsize=25)
    plt.savefig('销售额每日走势.jpg')
    plt.show()


def order_creation(df):
    '''
    按订单付款时间，统计每日订单创建量
    :param df:
    :return:
    '''
    amount=df.groupby(pd.Grouper(key='订单付款时间',freq='D'))['订单创建时间'].count().to_frame('订单创建数')

    # 设置x轴坐标
    _x=[f'{m}月{i}日' for m,i in zip(amount.index.month, amount.index.day)]

    # 画图部分
    plt.figure(figsize=(16,9),dpi=160)
    plt.plot(range(len(_x)),amount['订单创建数'])
    # 设置数据文本标签
    plt.text(0,amount['订单创建数'].max(),f'2月1日-3月1日订单创建数为:{amount.sum().values[0]}',fontsize=20)
    for x,y in zip(range(len(_x)),amount['订单创建数']):
        plt.text(x, y+15,y,ha='center')
    plt.xticks(range(len(_x)),_x,rotation=45)
    plt.ylabel('销量')
    plt.xlabel('日期')
    plt.title('每日订单创建走势',fontsize=20)
    plt.savefig('每日订单创建数走势.jpg')
    plt.show()

def Conversion_rates(df):
    '''
    目标：订单每个环节的转化转化率
    :param df:
    :return:
    '''
    rates = pd.Series({
        '创建':df['订单创建时间'].count(),
        '付款':df['订单付款时间'].count(),
        '实际成交':df[df['买家实际支付金额']>0].shape[0],
        '全额成交':df[df['买家实际支付金额']==df['总金额']].shape[0],
    },name='订单量').to_frame()
    # 绝对转化率=各项指标/订单创建数
    rates['整体转化率']=rates['订单量'].apply(lambda x: round(x*100/rates.iloc[0,0],3))
    # 相对转化率=各项指标/上一个流程的指标
    # rates['相对转化率']=(rates/rates.shift())['订单量'].fillna(1)
    print(f'\n{"-"*5}各环节绝对转化率(%){"-"*5}\n')
    print(rates)

    c=(
        Funnel()
        .add(
            '转化率',
            [list(z) for z in zip(rates.index,rates['整体转化率'])],
            # 设置标签位置及数据展现形式
            label_opts=opts.LabelOpts(position='inside',formatter='{b}:{c}')
        )
        .set_global_opts(title_opts=opts.TitleOpts(title='整体转化率（%）'))
    )
    # 转存
    make_snapshot(snapshot,c.render(),'转化率1.png')

def hot_sales(df):
    df=df[df['买家实际支付金额']>0]
    hot_=pd.DataFrame({
        '销量':df['总金额'].value_counts(),
        '全额付款销量':df[df['买家实际支付金额']==df['总金额']]['总金额'].value_counts()
    }).sort_values(by='销量',ascending=False)
    hot_['总销量占比(%)']=hot_['销量'].apply(lambda x : round((x/hot_['销量'].sum())*100,2))
    hot_['销售额']=df.groupby(by='总金额')['买家实际支付金额'].sum()
    hot_['销售额占比(%)']=hot_['销售额'].apply(lambda x : round((x/hot_['销售额'].sum())*100,2))
    print(f'{"-"*20}热卖前20{"-"*20}')
    print(hot_.head(20))

    plt.figure(figsize=(16,9),dpi=160)
    # 将销售量前10之外的品类归为其他
    a=hot_.iloc[10:].sum().to_frame('其他').unstack().unstack()
    hot_=pd.concat([hot_.head(10), a])
    # 色板
    color=sns.color_palette('hls',11)
    # 画图
    plt.pie(hot_['总销量占比(%)'], autopct='%3.1f%%', labels=hot_.index, startangle=45,colors=color)
    plt.title('各品类销量情况')
    plt.savefig('各品类实际成交情况。jpg')
    plt.show()

def location_distribution(df):
    '''
    目标：计算各城市的实际成交订单情况
    :param df:
    :return:
    '''
    amount=df[df['买家实际支付金额'] > 0].groupby('收货地址')['买家实际支付金额'].count().sort_values(ascending=False).to_frame('实际成交数')

    # 处理省份名称为pyecharts可识别的形式
    _x=[i.replace('省','').replace('自治区','') for i in amount.index]
    _x=[x if len(x)<4 else x[:2] for x in _x]

    # 计算最大值作为pyecharts色块分组中的最大值
    max_=int(amount['实际成交数'].max())
    c=(
        Map()
        .add(
            '订单数',[list(i) for i in zip(_x, amount['实际成交数'].to_list())],'china'
        )
        .set_global_opts(
            title_opts=opts.TitleOpts(title='各地区实际成交订单数'),
            visualmap_opts=opts.VisualMapOpts(max_=max_,is_piecewise=True)
        )
    )
    make_snapshot(snapshot,c.render(),'各地区实际成交订单数1.png')
    # c.render('成交单数.html')

def location_rates(df):
    # 找到所有实际成交或全额成交的所有行
    df['成交情况']=0
    df.loc[df[df['买家实际支付金额']>0].index.to_list(),'成交情况']=1

    # 分组求和
    df_=df.groupby(by=['收货地址',pd.Grouper(key='订单付款时间',freq='W')]).agg(
        订单创建数=('订单创建时间', 'count'),
        订单成交数=('成交情况', 'sum')
    )
    # 计算整体转化率情况
    df_t=df_['订单成交数'].unstack().sum()/df_['订单创建数'].unstack().sum()
    df_=df_.loc[['上海','广东省','北京','江苏省','浙江省']]
    print(f'{"-" * 15}销量前5的省市订单创建量量情况{"-" * 15}\n')
    print(df_['订单创建数'].unstack())
    # 求转化率
    df_['实际成交转化率']=df_['订单成交数']/df_['订单创建数']
    print(f'{"-" * 15}整体转化率情况{"-" * 15}\n')
    print(df_t)
    print(f'\n{"-" * 15}销量前5的省市的转化率情况{"-" * 15}\n')
    print(df_['实际成交转化率'].unstack())

def location_product_rates(df):
    df=df[(df['收货地址'].isin(['北京','上海','广东省']))&(df['订单创建时间']>'2020-02-16')]
    df['成交情况']=0
    df.loc[df[df['买家实际支付金额']>0].index.to_list(),'成交情况']=1
    df_=df.groupby(by=['收货地址','总金额']).agg(
        订单创建数=('订单创建时间', 'count'),
        订单成交数=('成交情况', 'sum')
    )
    # 筛选每个省市的销量前5
    df_=df_.reset_index().groupby('收货地址').apply(lambda x: x.nlargest(5,'订单创建数',keep='all')).set_index(['收货地址','总金额'])
    df_['实际成交转化率']=df_['订单成交数']/df_['订单创建数']
    print(f'{"-" * 15}重点省市销量前5产品的订单创建量量情况{"-" * 15}\n')
    print(df_['订单创建数'].unstack())
    print(f'\n{"-" * 15}重点省市销量前5产品的转化率情况{"-" * 15}\n')
    print(df_['实际成交转化率'].unstack())

def main_func():
    df=open_file()
    
    # 统计日维度下的总销售额情况
    # totle_sales_amount(df)

     # 转化率情况
    # Conversion_rates(df)

    # 订单创建情况
    # order_creation(df)

    # 热卖商品
    # hot_sales(df)

    # 城市分布情况
    # location_distribution(df)

    # 细分维度下的转化率情况
    # location_rates(df)

    # 多维度交叉分析：地理位置：北上广，时间：2月17-3月1日，销量前4产品
    location_product_rates(df)

if __name__ == '__main__':
    main_func()

