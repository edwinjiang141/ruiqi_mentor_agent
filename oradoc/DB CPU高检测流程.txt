检测DB CPU异常及原因
1、使用SQL执行指标异常的检测模型，找出真实异常的SQL语句，并存放在结果表中
2、DB CPU的异常检测模型训练：使用Data Mining的异常检测算法进行算法模
3、特征抽取的模型训练：找到异常的DB CPU后，使用Data Mining的特征抽取算法对当前这个异常点，提取出影响大的前3个（数量待定）特征。
4、根据对DB CPU的4组大的分类：  根绝前面找到的主要特征所属的大类，分别找出TOP 5 的SQL语句的历史执行数据。
  1：SQL Execute elapsed time        2: parse time elapsed 
  3: PL/SQL execution elapsed time   4: Other       
5、SQL执行指标异常的检测模训练：对这些TOP 5的SQL语句的历史执行数据再进行一次异常检测模型的训练。