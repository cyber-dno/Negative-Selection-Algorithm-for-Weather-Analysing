import datetime
import re

import pandas as pd
import requests
from bs4 import BeautifulSoup as bs

# Адрес страницы и название файла с результатом
URL_TEMPLATE = "https://pogodaspb.info/arch.php?date=ymd"
FILE_NAME = "Weather.csv"


def parse(url, year):
    # Создание результирующего списка и указание года, откуда пойдёт чтение
    data = []
    if year % 4 == 0:
        leap_year = True
    else:
        leap_year = False
    day = 1
    month = 1
    date = datetime.date(year, 1, 1)

    # Указание последнего года
    while True:
        # Добавление в начало строки года, который рассматривается
        temp_list = []
        prec_list = []
        cur_date = date.strftime('%Y-%m-%d')
        cur_month = int(date.strftime('%m'))
        cur_year = int(date.strftime('%Y'))

        if cur_month != month:
            month = cur_month
            data.append('')
        if cur_year != year:
            return data

        # Изменение URL ссылки по-требуемому месяцу
        cur_url = url.replace('ymd', cur_date)
        # Отправка URL запроса
        r = requests.get(cur_url)
        # Считываем код страницы
        soup = bs(r.text, "html.parser")

        # Находим и считываем нужные нам элементы
        post = soup.find_all('p', {"class": "h5 color1"})
        for i in range(int(len(post) / 2)):
            temp = post[1 + 2 * i].text
            temp_list.append(float(temp[:-1]))
        post = soup.find_all('p', {"class": "h8"})
        for i in range(len(post)):
            prec = post[i].text
            if len(re.findall('(\d+)', prec)) != 0:
                prec_list.append(float(prec[41:-6]))
            else:
                prec_list.append(0.0)

        if leap_year and day == 59:
            average = [round(sum(temp_list) / len(temp_list), 1), round(sum(prec_list) / len(prec_list) * 10, 1)]
        elif leap_year and day == 60:
            day -= 1
            leap_year = False
            data.append(str(day) + ',' + str(round((round(sum(temp_list) / len(temp_list), 1) + average[0]) / 2, 1)) +
                        ',' + str(round((round(sum(prec_list) / len(prec_list) * 10, 1) + average[1]) / 2, 1)))
        else:
            data.append(str(day) + ',' + str(round(sum(temp_list) / len(temp_list), 1)) +
                        ',' + str(round(sum(prec_list) / len(prec_list) * 10, 1)))

        day += 1
        date = date + datetime.timedelta(days=1)


# Запись в файл
df = pd.DataFrame(data=parse(URL_TEMPLATE, 2014))
df.to_csv(FILE_NAME, header=False, index=False)
