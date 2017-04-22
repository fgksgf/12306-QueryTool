import requests
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

    def __init__(self, info, date):
        """
        初始化相应信息,并将车次相关信息转换为列表，便于使用prettytable打印输出
        """
        self.date = date
        self.__no = info["train_no"]
        self.__types = info["seat_types"]
        self.__from_no = info["from_station_no"]
        self.__to_no = info["to_station_no"]

        self.__code = info['station_train_code']
        self.__from_station = info['from_station_name']
        self.__to_station = info['to_station_name']
        self.__start = info['start_time']
        self.__arrive = info['arrive_time']
        self.__period = info['lishi']
        self.__seats = [info["swz_num"], info["tz_num"], info["zy_num"],
                        info["ze_num"], info["rw_num"], info["yw_num"],
                        info["rz_num"], info["yz_num"], info["wz_num"]]

        self.__row = [self.__code,
                      '\n'.join([self.__from_station, self.__to_station]),
                      '\n'.join([self.__start, self.__arrive]),
                      self.__period]
        self.__row.extend(self.__seats)

    def get_price_info(self):
        """
        获得每种座位的价格信息
        """
        url = PRICE_URL.format(self.__no, self.__from_no,
                               self.__to_no, self.__types, self.date)
        prices = get_response(url)
        l = ['A9', 'P', 'M', 'O', 'A4', 'A3', 'A2', 'A1', 'WZ']
        for tag in l:
            if prices.get(tag):
                self.__row[l.index(tag)+4] = \
                    '\n'.join([self.__row[l.index(tag)+4], prices.get(tag)])

    def get_row(self):
        return self.__row


def get_response(url):
    """
    使用get方法从url获得字典格式的回复
    :param url: 目标url
    :return: 字典格式数据
    """
    try:
        requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
        r = requests.get(url, verify=False)
        r.raise_for_status()
        info = r.json()['data']
        return info
    except Exception:
        return ''


def make_info_url(date, from_station, to_station):
    """
    根据输入的日期和车站信息生成请求车次信息的url
    :param date: 要查询的日期
    :param from_station: 出发站
    :param to_station: 目的站
    :return: 要请求车次信息的url
    """
    return INFO_URL.format(date, stations.get(from_station), stations.get(to_station))


def pretty_print(infos, date):
    """
    输出车次信息
    """
    pt = PrettyTable(HEADER)
    for info in infos:
        if info['queryLeftNewDTO']['canWebBuy'] != 'N':  # 过滤掉不能预订的车次信息
            train = TrainInfo(info['queryLeftNewDTO'], date)
            train.get_price_info()
            pt.add_row(train.get_row())
    print(pt)


def main():
    while True:
        date = input('Date (eg.2017-05-01): ')
        from_station = input('From_station: ')
        to_station = input('To_station: ')
        url = make_info_url(date, from_station, to_station)
        infos = get_response(url)
        pretty_print(infos, date)
        print('\n\n\n\n\n')


main()
