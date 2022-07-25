import requests
from bs4 import BeautifulSoup as bs
import pandas as pd
import re

# Адрес страницы и название файла с результатом
URL_TEMPLATE = "http://thermo.karelia.ru/weather/w_history.php?town=spb&month=1&year=1885"
FILE_NAME = "Weather.csv"


def parse(url):
    # Создание результирующего списка и указание года, откуда пойдёт чтение
    result_list = []
    current_year = 1885

    # Указание последнего года
    while current_year <= 1985:
        # Добавление в начало строки года, который рассматривается
        year = []
        count = 0
        year.append(str(current_year))

        # Изменение URL ссылки по-требуемому году
        url = re.sub(r'year=(\d{4})', 'year=' + str(current_year), url)
        for month in range(12):
            # Изменение URL ссылки по-требуемому месяцу
            url = re.sub(r'month=(\d{1,2})', 'month=' + str(month + 1), url)
            # Отправка URL запроса
            r = requests.get(url)
            # Считываем код страницы
            soup = bs(r.text, "html.parser")

            data_month = ''

            # Находим и считываем нужные нам элементы
            post = soup.find_all('td', bgcolor='#FFFFFF')
            for i in range(int(len(post) / 5)):
                temp = float(post[2 + 5 * i].text)
                precipitation = float(post[4 + 5 * i].text)
                data_month += str(temp) + ',' + str(precipitation) + '\t'
                count += 1
            year.append(data_month[:-1])

        if count == 365:
            # Запись данных в результирующий список
            for n in year:
                result_list.append(n)
        elif count == 366:
            # Високосный год, требуется округлить 29 и 28 февраля
            splited_month = year[2].split()
            Feb28 = splited_month[27].split(',')
            Feb29 = splited_month[28].split(',')
            value = str(round((float(Feb28[0]) + float(Feb29[0])) / 2, 1)) + ',' + str(round((float(Feb28[1]) + float(Feb29[1])) / 2, 1))
            splited_month[27] = value
            splited_month.pop(28)
            Feb = ''
            for element in splited_month:
                Feb += element + '\t'
            year.pop(2)
            year.insert(2, Feb[:-1])
            for n in year:
                result_list.append(n)
        current_year += 1

    return result_list


# Запись в файл
df = pd.DataFrame(data=parse(URL_TEMPLATE))
df.to_csv(FILE_NAME, header=False, index=False)
