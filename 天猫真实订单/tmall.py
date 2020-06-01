import pandas as pd
from matplotlib import pyplot as plt
from pyecharts import options as opts
import seaborn as sns
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

def open_file():
    df=pd.read_csv('report.csv')
    df['订单创建时间']=pd.to_datetime(df['订单创建时间'])
    df['订单付款时间']=pd.to_datetime(df['订单付款时间'])
    return df
def sales(df):
    '''
    按订单付款时间，统计实际成交数量
    :param df:
    :return:
    '''
    amount=df[df['买家实际支付金额']>0][['订单付款时间','买家实际支付金额']]
    sell_amount=amount.groupby(pd.Grouper(key='订单付款时间',freq='D'))['买家实际支付金额'].count().to_frame('实际成交数')

    # 设置x轴坐标
    _x=[f'{m}月{i}日' for m,i in zip(sell_amount.index.month, sell_amount.index.day)]

    # 画图部分
    plt.figure(figsize=(16,9),dpi=160)
    plt.plot(range(len(_x)),sell_amount['实际成交数'])
    # 设置数据文本标签
    plt.text(0,sell_amount['实际成交数'].max(),f'2月1日-3月1日实际成交订单数为:{sell_amount.sum().values[0]}')
    for x,y in zip(range(len(_x)),sell_amount['实际成交数']):
        plt.text(x, y+15,y,ha='center')
    plt.xticks(range(len(_x)),_x,rotation=45)
    plt.ylabel('销量')
    plt.xlabel('日期')
    plt.title('每日成交量走势')
    plt.savefig('每日成交量走势V1.jpg')
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
    hot_['全额付款占比']=hot_['全额付款销量']/hot_['销量']
    hot_['占比(%)']=hot_['销量'].apply(lambda x : round((x/hot_['销量'].sum())*100,2))
    print(f'{"-"*20}热卖前10{"-"*20}')
    print(hot_.head(10))
    plt.figure(figsize=(16,9),dpi=160)
    a=hot_.iloc[10:].sum().to_frame('其他').unstack().unstack()
    hot_=pd.concat([hot_.head(10), a])
    color=sns.color_palette('hls',11)
    plt.pie(hot_['占比(%)'], autopct='%3.1f%%', labels=hot_.index, startangle=45,colors=color)
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
    df['成交情况'],df['全价成交']=0,0
    df.loc[df[df['买家实际支付金额']>0].index.to_list(),'成交情况']=1
    df.loc[df[df['买家实际支付金额']==df['总金额']].index.to_list(),'全价成交']=1

    # 分组聚合，按成交数进行降序
    df_=df.groupby('收货地址').agg(
        订单创建数=('订单创建时间', 'count'),
        订单付款数=('订单付款时间', 'count'),
        订单成交数=('成交情况', 'sum'),
        全额成交数=('全价成交', 'sum'),
    ).sort_values(by=['订单成交数','全额成交数'],ascending=False)

    # 计算成交数总量，找出累计成交量小于整体成交量80%且成交量最多的前N个省市
    max_=df_['订单成交数'].sum()
    df_['累计成交数']=df_['订单成交数'].cumsum()
    df_max=df_[df_['累计成交数']<=max_*0.8].copy()
    index_=df_max.index
    df_max.drop(columns='累计成交数',inplace=True)

    # 计算转化率
    df_rates = df_max.apply(lambda x: round((x / df_['订单创建数']) * 100, 2), axis=0).sort_values(by=['订单成交数','全额成交数'],ascending=False)

    print(f'\n{"-" * 15}销量前{len(index_)}个省市的订单量情况{"-" * 15}\n')
    print(df_max)
    print(f'\n{"-" * 15}销量前{len(index_)}个省市的转化率情况{"-" * 15}\n')
    print(df_rates.loc[index_])

def main_func():
    df=open_file()

    # 时间维度下的销量情况
    # sales(df)

    # 转化率情况
    # Conversion_rates(df)

    # 热卖商品
    # hot_sales(df)

    # 城市分布情况
    # location_distribution(df)

    # 细分维度下的转化率情况
    location_rates(df)

if __name__ == '__main__':
    main_func()

