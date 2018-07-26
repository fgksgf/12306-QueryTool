"""12306 Query Tool

Usage:
    tickets.py -h
    tickets.py --version
    tickets.py [-gdktzc] <date> <from> <to>

Options:
    -h          查看帮助
    -d          动车
    -g          高铁
    -k          快速
    -t          特快
    -z          直达
    -c          城际
    --version   显示版本信息

Example:
    tickets.py 2017-10-10 北京 上海
    tickets.py -dg 2017-10-10 成都 南京
"""

import arrow
import requests
from colorama import init, Fore
from docopt import docopt
from prettytable import PrettyTable
from urllib3.exceptions import InsecureRequestWarning

from stations import stations

INFO_URL = 'https://kyfw.12306.cn/otn/leftTicket/query?leftTicketDTO.train_date={}' \
           '&leftTicketDTO.from_station={}&leftTicketDTO.to_station={}&purpose_codes=ADULT'

PRICE_URL = 'https://kyfw.12306.cn/otn/leftTicket/queryTicketPrice?train_no={}' \
            '&from_station_no={}&to_station_no={}&seat_types={}&train_date={}'

HEADER = '车次 车站 时间 历时 商务/特等 一等 二等 软卧 硬卧 软座 硬座 无座'.split()


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
        self.__seats = [info[-5],  # 商务座/特等座
                        info[-6],  # 一等座
                        info[-7],  # 二等座
                        info[-14],  # 软卧
                        info[-9],  # 硬卧
                        info[-13],  # 软座
                        info[-8],  # 硬座
                        info[-11]]  # 无座

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
            lst = ['A9', 'M', 'O', 'A4', 'A3', 'A2', 'A1', 'WZ']
            for tag in lst:
                if prices.get(tag):
                    self.__row[lst.index(tag) + 4] = \
                        '\n'.join([self.__row[lst.index(tag) + 4], prices.get(tag)])

    def get_row(self):
        return self.__row


def get_response(url):
    """获取返回的json数据

    使用get方法从url获得json的回复

    :param url: 目标url
    :return: json格式数据
    """
    ret = ''
    try:
        requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
        r = requests.get(url, verify=False, timeout=10)
        r.raise_for_status()
        ret = r.json()
    except requests.ConnectTimeout:
        print("请求超时。")
    except requests.ConnectionError:
        print("网络连接错误。")
    finally:
        return ret


def make_info_url(date, from_station, to_station):
    """生成请求url

    根据输入的日期和车站名称生成请求车次信息的url

    :param date: 要查询的日期
    :param from_station: 出发站
    :param to_station: 目的站
    :return: 要请求车次信息的url
    """
    return INFO_URL.format(date, from_station, to_station)


def filter_train(options, info):
    ret = True
    if info[11] == 'Y':  # 过滤掉不能预订的车次信息
        if len(options) == 0:
            ret = False
        else:  # 当输入短参数时过滤相应车型
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


def verify_date(date):
    """检验日期的有效性

    1.判断是否符合YYYY-MM-DD格式
    2.判断是否早于当前日期
    3.判断是否在车票预售日期范围内

    :param date:要检验的日期
    :return: 返回转换为正确格式的日期字符串
    """
    temp = date.split('-')
    if len(temp) == 3:
        d = arrow.get(int(temp[0]), int(temp[1]), int(temp[2]))
        if d < arrow.now():
            raise ValueError('日期不能早于当前日期。')
        elif d > arrow.now().shift(days=29):
            raise ValueError('日期不在预售日期范围内。')
        else:
            return d.format('YYYY-MM-DD')
    else:
        raise ValueError('日期格式有误，格式应为：YYYY-MM-DD。')


def verify_station(from_sta, to_sta):
    """检验车站名的有效性

    判断该车站是否存在

    :param from_sta: 出发车站
    :param to_sta: 到达车站
    :return: 返回出发车站和到达车站对应的字母编码
    """
    from_station = stations.get(from_sta)
    to_station = stations.get(to_sta)
    if from_station is None:
        raise NameError("出发车站名有误。")
    if to_station is None:
        raise NameError("到达车站名有误。")
    return from_station, to_station


def main():
    args = docopt(__doc__, version="12306-QueryTool 3.0")
    options = [key for key, value in args.items() if value is True]

    try:
        date = verify_date(args['<date>'])
        from_station, to_station = verify_station(args['<from>'], args['<to>'])
        url = make_info_url(date, from_station, to_station)
        res = analysis_response(get_response(url))
        if res is not None:
            pretty_print(options, res, args['<from>'], args['<to>'], date)
        else:
            print("查询失败，本程序可能已失效。")
    except ValueError as v:
        print(v)
    except NameError as n:
        print(n)
    except BaseException as e:
        print(e)


if __name__ == '__main__':
    init()
    main()
