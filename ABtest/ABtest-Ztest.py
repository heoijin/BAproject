import pandas as pd
import statsmodels.stats.weightstats as sw


def open_file():
    df=pd.read_csv('ABtest.csv')
    df['timestamp']=pd.to_datetime(df['timestamp'])
    return clean_df(df)

def clean_df(df: pd):
    # 判断group为treatment但landing_page不为new_page的行，并进行反选
    df=df.loc[~((df['group']=='treatment')!=(df['landing_page']=='new_page'))]
    df.drop_duplicates('user_id',keep='first',inplace=True)
    return df

def ztest(df: pd):
    # 提取两个样本的数据值
    N_arry=df[df['group']=='treatment']['converted']
    O_arry=df[df['group']=='control']['converted']
    # 计算均值
    print(f'整体转化率为：{df["converted"].mean()}')
    print(f'新页面转化率为：{N_arry.mean()}')
    print(f'旧页面转化率为：{O_arry.mean()}')
    print(f'用户收到新页面的概率为：{N_arry.count()/df.shape[0]}')

    # 使用t检验检测
    result=sw.ztest(O_arry,N_arry,value=0)
    # tstat = 1.3109235634981506
    # pvalue = 0.18988358901317048
    print(result)

def main():
    df=open_file()
    ztest(df)


if __name__ == '__main__':
    main()