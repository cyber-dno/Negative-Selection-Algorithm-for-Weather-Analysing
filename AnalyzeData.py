import csv
import datetime
import numpy as np
from scipy.cluster.hierarchy import fclusterdata, centroid
import matplotlib.pyplot as plt
import pandas as pd


def cluster_formation(file):
    # открытие файла
    with open(file, 'r') as csv_file:
        reader = csv.reader(csv_file)
        # создадим массив с данными и заполним его
        num_row = -1
        data = [[] for _ in range(365)]
        for row in reader:
            num_row += 1
            if num_row % 13 == 0:
                index = 0
                continue
            month = row[0].split('\t')
            for day in month:
                day = np.array(day.split(','), dtype=float)
                data[index].append(day)
                index += 1

        # кластеризация данных
        data_np = np.array(data)
        cur_month = 1
        date = datetime.date(2018, 1, 1)
        data_sorted = [[] for _ in range(365)]
        average_data = []

        # maximum_data_precipitation = []
        # minimum_data_temperature = []
        # maximum_data_temperature = []

        i = 0
        for day_reg in data_np:
            # запись максимального и минимального показания погоды
            # day_reg = day_reg.transpose()
            # minimum_data_temperature.append(day_reg[0].min())
            # maximum_data_temperature.append(day_reg[0].max())
            # maximum_data_precipitation.append(day_reg[1].max())
            # day_reg = day_reg.transpose()

            if cur_month != int(date.strftime('%m')):
                average_data.append('')
                cur_month = int(date.strftime('%m'))

            # кластеризация
            clusters = fclusterdata(day_reg, t=10, criterion='distance', method='centroid')
            """
            # Визуализация кластеров
            cl = [[] for _ in range(max(clusters))]
            for i in range(len(day_reg)):
                cl[clusters[i]-1].append(day_reg[i])
            plt.title("Кластеризация данных")  # заголовок
            plt.xlabel("Количество осадков")  # ось абсцисс
            plt.ylabel("Температура")  # ось ординат
            plt.grid()  # включение отображение сетки
            for i in cl:
                i = np.array(i).transpose()
                plt.scatter(i[1], i[0])
            plt.show()
            """

            # номер наибольшего кластера
            index = np.argmax(np.bincount(clusters))
            j = 0
            for clust_index in clusters:
                if clust_index == index:
                    data_sorted[i].append(day_reg[j])
                j += 1
            Z = centroid(np.array(data_sorted[i]))
            distance = Z[-1][-2]

            rec = str(i+1)
            for param in range(len(data_sorted[0][0])):
                day_param = []
                for day in data_sorted[i]:
                    day_param.append(day[param])
                value = round(sum(day_param) / len(day_param), 1)
                rec += ',' + str(value)
            rec += ':' + str(distance)
            average_data.append(rec)
            i += 1
            date += datetime.timedelta(days=1)
        average_data.append('')
        # Запись в файл
        df = pd.DataFrame(data=average_data)
        df.to_csv('AverageData.csv', header=False, index=False)

        """
        plt.title("Показатели температуры за год")  # заголовок
        plt.xlabel("День в году")  # ось абсцисс
        plt.ylabel("Температура")  # ось ординат
        plt.grid()  # включение отображение сетки
        plt.plot([i for i in range(1, 366)], average_data, 'g', label='Средняя')  # построение графика
        plt.plot([i for i in range(1, 366)], minimum_data, 'b', label='Минимальная')  # построение графика
        plt.plot([i for i in range(1, 366)], maximum_data, 'r', label='Максимальная')  # построение графика
        plt.legend()
        plt.show()
        """


cluster_formation('Weather.csv')
