# 12306-QueryTool

**注意：由于 12306 的接口经常变化，本程序代码可能失效。**

## 一、简介
这是一个使用Python3实现的、基于12306网站的火车余票及价格信息查询工具。


## 二、库依赖
+ requests 库: 使用Python访问HTTP资源的必备库
+ prettytable 库: 格式化信息打印工具，能让你像MySQL那样打印数据
+ docopt 库: 命令行参数解析工具
+ colorama 库: 命令行着色工具
+ arrow 库: 日期时间库

## 三、效果截图

![](https://image-bed-1253366698.cos.ap-guangzhou.myqcloud.com/github/12306.png)

## 四、更新日志

### V 2.1 (2018-07-26)
- 由于请求列车信息的接口变化，重写了解析数据的函数
- 完善异常处理
- 完善命令行用法
- 为加快查询速度，取消了对票价的查询

### V 2.0 (2017-05-04)
- 由于请求列车信息的接口变化，重写了解析数据的函数
- 改用命令行传递参数
- 增加查询特定的一种或几种火车的功能
- 增加命令行着色
- 增加了异常处理代码，对输入的车站名和日期进行检测


### V 1.0 (2017-04-22)
- 基本的余票信息查询以及票价的显示 
- 过滤无票的车次信息




