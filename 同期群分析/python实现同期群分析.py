import pandas as pd


def Cohort_Analysis(df):
    '''
    计算同期的留存量和留存率
    :param df:
    :param df_f: 同期留存量
    :param df_1: 同期留存率
    :return:
    '''
    df.drop(index=df[df['订单状态'] == '交易失败'].index, axis=1, inplace=True)
    # 获取每个客户首单时间
    df_f = df.groupby(by='客户昵称')['付款时间'].min().to_frame(name='首单时间')
    df_f.reset_index(inplace=True)

    # 合并新的dataframe，包含客户昵称，付款时间，首单时间
    df_f = df[['客户昵称', '付款时间']].merge(df_f)

    # 通过首单时间及付款时间进行分组，获得每个时间段单独的不重复的客户数量
    df_f = df_f.groupby(by=[pd.Grouper(key='首单时间', freq='m'), pd.Grouper(key='付款时间', freq='m')])['客户昵称'].nunique()

    # 对复合索引的series转置为dataframe
    df_f = df_f.unstack()

    # 将首月客户数量对齐
    for i in range(len(df_f.index)):
        df_f.iloc[i] = df_f.iloc[i].shift(periods=-i)

    # 重置columns
    df_f.columns = ['本月新增', '+1月', '+2月', '+3月', '+4月', '+5月']

    # 计算留存率
    df_1 = df_f.apply(count_per, axis=0, args=(df_f['本月新增'],))
    df_1['本月新增']=df_f['本月新增']

    print(df_f)
    print('-' * 15)
    print(df_1)


def count_per(s, dx):
    a=[f'{i}%' if str(i)!='nan' else 0 for i in round((s / dx) * 100, 2)]
    return a


def main():
    df = pd.read_excel('同期群订单数据.xlsx')
    # 同期群分析
    Cohort_Analysis(df)


if __name__ == '__main__':
    main()