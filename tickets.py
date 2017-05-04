"""12306 query tool

Usage:
    tickets.py [-gdk] <date> <from> <to>

Options:
    -h         查看帮助
    -d         动车
    -g         高铁
    -k         快速
    -t         特快
    -z         直达

Example:
    tickets.py 2017-10-10 北京 上海 
    tickets.py -dg 2017-10-10 成都 南京
"""

import requests
from colorama import init, Fore
from docopt import docopt
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from prettytable import PrettyTable
from stations import stations

INFO_URL = 'https://kyfw.12306.cn/otn/leftTicket/query?leftTicketDTO.train_date={}' \
           '&leftTicketDTO.from_station={}&leftTicketDTO.to_station={}&purpose_codes=ADULT'

PRICE_URL = 'https://kyfw.12306.cn/otn/leftTicket/queryTicketPrice?train_no={}' \
            '&from_station_no={}&to_station_no={}&seat_types={}&train_date={}'

HEADER = '车次 车站 时间 历时 商务座 特等 一等 二等 软卧 硬卧 软座 硬座 无座'.split()


class TrainInfo:
    date = ''

    def __init__(self, info, _from, _to, date):
        """
        初始化相应信息,并将车次相关信息转换为列表，便于使用prettytable打印输出
        """
        self.date = date
        self.__no = info[2]
        self.__types = info[-1]
        self.__from_no = info[16]
        self.__to_no = info[17]

        self.__code = info[3]
        self.__from_station = _from
        self.__to_station = _to
        self.__start = info[8]
        self.__arrive = info[9]
        self.__period = info[10]
        self.__seats = [info[-3],       # 商务座
                        info[-10],      # 特等座
                        info[-4],       # 一等座
                        info[-5],       # 二等座
                        info[-12],      # 软卧
                        info[-7],       # 硬卧
                        info[-11],      # 软座
                        info[-6],       # 硬座
                        info[-9]]       # 无座

        self.__row = [self.__code,
                      '\n'.join([Fore.GREEN + self.__from_station + Fore.RESET,
                                 Fore.RED + self.__to_station + Fore.RESET]),
                      '\n'.join([Fore.GREEN + self.__start + Fore.RESET,
                                 Fore.RED + self.__arrive + Fore.RESET]),
                      self.__period]
        self.__row.extend(self.__seats)

        # 使用绿色显示有票 用红色显示无票
        for i in range(-9, 0):
            if self.__row[i] not in ['无', '']:
                self.__row[i] = Fore.GREEN + self.__row[i] + Fore.RESET
            else:
                self.__row[i] = Fore.RED + self.__row[i] + Fore.RESET

    def get_price_info(self):
        """
        获得每种座位的价格信息
        """
        url = PRICE_URL.format(self.__no, self.__from_no,
                               self.__to_no, self.__types, self.date)
        prices = get_response(url).get('data')
        if len(prices) != 0:
            l = ['A9', 'P', 'M', 'O', 'A4', 'A3', 'A2', 'A1', 'WZ']
            for tag in l:
                if prices.get(tag):
                    self.__row[l.index(tag) + 4] = \
                        '\n'.join([self.__row[l.index(tag) + 4], prices.get(tag)])

    def get_row(self):
        return self.__row


def get_response(url):
    """
    使用get方法从url获得字典格式的回复
    :param url: 目标url
    :return: 字典格式数据
    """
    ret = ''
    try:
        requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
        r = requests.get(url, verify=False, timeout=15)
        r.raise_for_status()
        ret = r.json()
    except requests.ConnectTimeout:
        print("Request time out.")
    except requests.ConnectionError:
        print("Can not acquire response.")
    finally:
        return ret


def make_info_url(date, from_station, to_station):
    """
    根据输入的日期和车站信息生成请求车次信息的url
    :param date: 要查询的日期
    :param from_station: 出发站
    :param to_station: 目的站
    :return: 要请求车次信息的url
    """
    return INFO_URL.format(date, from_station, to_station)


def filter_train(options, info):
    ret = True
    if info[11] == 'Y':   # 过滤掉不能预订的车次信息
        if len(options) == 0:
            ret = False
        else:             # 当输入短参数时过滤相应车型
            for opt in options:
                if info[3][0].lower() in opt:
                    ret = False
    return ret


def pretty_print(options, infos, _from, _to, date):
    """
    输出车次信息
    """
    pt = PrettyTable(HEADER)
    for info in infos:
        info = info.split('|')
        if not filter_train(options, info):
            train = TrainInfo(info, _from, _to, date)
            train.get_price_info()
            pt.add_row(train.get_row())
    print(pt)


def analysis_response(res):
    ret = None
    if len(res.get('messages')) > 0:
        # 当查询日期不在预售日期范围内时抛出异常
        raise NameError(res.get('messages')[0])
    elif len(res.get('data')) > 0:
        ret = res.get('data').get('result')
    return ret


def main():
    args = docopt(__doc__)
    date = args['<date>']
    from_station = stations.get(args['<from>'])
    to_station = stations.get(args['<to>'])
    options = [key for key, value in args.items() if value is True]

    try:
        if from_station is None or to_station is None:
            raise ValueError("Wrong station name.")
        url = make_info_url(date, from_station, to_station)
        res = analysis_response(get_response(url))
        if res is not None:
            pass
            pretty_print(options, res, args['<from>'], args['<to>'], date)
        else:
            print("Can't acquire the information.Please try again later.")
    except ValueError:
        print("Please append right station's name.")
        print("eg. tickets.py 2017-05-01 北京 上海")
    except NameError:
        print("选择的查询日期不在预售日期范围内.")
        print("The selected query date is not within the pre-sale date range.")
        print("Please append proper date.")


init()
main()
