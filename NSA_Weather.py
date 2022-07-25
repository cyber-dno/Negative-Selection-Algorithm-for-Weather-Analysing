import csv

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.spatial import distance
import dearpygui.dearpygui as dpg


# Чтение данных из файла
def GetData(file):
    data = []
    dist_list = []
    month = []
    flag = False
    with open(file, 'r') as csv_file:
        reader = csv.reader(csv_file)
        for row in reader:
            if row[0] == '':
                data.append(month)
                month = []
            elif row[0].find(':') != -1:
                flag = True
                params, dist = row[0].split(':')
                params = params.split(',')
                params = [float(i) for i in params]
                dist = float(dist)
                month.append(np.array(params))
                dist_list.append(dist)
            else:
                params = row[0].split(',')
                params = [float(i) for i in params]
                month.append(np.array(params))
    if flag:
        return data, dist_list
    else:
        return data


# Подсчёт расстояния между точками. Евклидова метрика
def CalculateDistance(x1, x2):
    return distance.euclidean(x1, x2)


# Вычисление оптимального радиуса детектора
def CalculateRadius(individ, data, detect_list, affinity):
    min_dist = float('inf')
    index = 0
    # Вычисление расстояния до самого близкого элемента нормы
    for month in data:
        for elem in month:
            dist = CalculateDistance(individ, elem) - affinity[index]
            if dist < min_dist:
                min_dist = dist
            index += 1

    # Вычисление расстояния до самого близкого детектора
    nearest_detector = None
    for i in range(len(detect_list)):
        dist = CalculateDistance(individ, detect_list[i][0])
        if dist < detect_list[i][1]:
            return -1  # сгенерирован детектор, который находится в области уже созданного детектора
        if dist < min_dist:
            min_dist = dist
            nearest_detector = i

    # Вычисление итогового радиуса текущего детектора
    if nearest_detector is not None:
        radius = min_dist - detect_list[nearest_detector][1]
    else:
        radius = min_dist

    return radius


# Создание детектора путём отбора лучшей особи в ГА
def CreateDetector(data, num_of_individ, detect_list, affinity, num_iter):
    population = []  # популяция особей

    # Начальная инициализация особей
    num_of_dimension = len(data[0][0])
    for i in range(num_of_individ):
        coordinates = [np.random.randint(0, 366),
                       np.random.uniform(-50, 50),
                       np.random.uniform(0, 50)]
        radius = CalculateRadius(coordinates, data, detect_list, affinity)
        while radius <= 0:
            coordinates = [np.random.randint(0, 366),
                           np.random.uniform(-50, 50),
                           np.random.uniform(0, 50)]
            radius = CalculateRadius(coordinates, data, detect_list, affinity)

        population.append([coordinates, radius])

    # Количество поколений
    for _ in range(num_iter):
        population = Crossover(population, num_of_dimension, num_of_individ,
                               data, detect_list, affinity)  # применение кроссовера

    # вычисление номера детектора, имеющего наибольшее покрытие
    distance_list = []
    for i in range(num_of_individ):
        distance_list.append(population[i][1])
    position = np.arange(num_of_individ)
    position = [i for _, i in sorted(zip(distance_list, position), reverse=True)]
    position = position[:1]

    return population[position[0]]


# Мутация особей
def Mutation(coords, dimension, num_of_individ):
    total_num = dimension * int(num_of_individ / 2)
    num_of_mutation = int(.2 * total_num)  # 20% генов подвергается мутации
    arr = np.array([1] * num_of_mutation + [0] * (total_num - num_of_mutation))
    np.random.shuffle(arr)
    arr = np.reshape(arr, (int(num_of_individ / 2), dimension))
    indices = np.argwhere(arr == 1)  # генерация новых значений для мутирующих генов
    for i in indices:
        if i[1] == 2:
            coords[i[0]][i[1]] = np.random.uniform(0, 50)
        if i[1] == 1:
            coords[i[0]][i[1]] = np.random.uniform(-50, 50)
        if i[1] == 0:
            coords[i[0]][i[1]] = np.random.randint(1, 366)
    return coords


# Кроссинговер особей
def Crossover(population, dimension, num_of_individ,
              data, detect_list, affinity):
    distance_list = []
    for i in range(num_of_individ):
        distance_list.append(population[i][1])

    median = np.median(distance_list)  # медиана вектора дистанций
    coords_list = []
    for i in range(int(num_of_individ / 2)):  # скрещивание генов новых особей
        first_parent = population[i * 2]
        second_parent = population[i * 2 + 1]
        coords = []
        for j in range(dimension):
            if j % 2 == 0:
                coords.append(first_parent[0][j])
            else:
                coords.append(second_parent[0][j])
        coords_list.append(coords)
    coords_list = Mutation(coords_list, dimension, num_of_individ)

    new_population = []  # новое поколение особей
    for i in range(int(num_of_individ / 2)):
        radius = CalculateRadius(coords_list[i], data, detect_list, affinity)
        while radius <= 0:
            coords_list[i] = [np.random.randint(0, 366),
                              np.random.uniform(-50, 50),
                              np.random.uniform(0, 50)]
            radius = CalculateRadius(coords_list[i], data, detect_list, affinity)
        new_population.append([coords_list[i], radius])

    # если особь имеет характеристики ниже медианы, то она заменяется на особь из нового поколения
    num_of_new_individual = len(new_population) - 1
    for i in range(len(population)):
        if population[i][1] < median and num_of_new_individual >= 0:
            population[i] = new_population[num_of_new_individual]
            num_of_new_individual -= 1
        if num_of_new_individual < 0:
            break

    return population


# Заполнение списка детекторами
def GetDetectors(num_of_detectors, data, num_of_individ, affinity, num_iter, id_out, str_out):
    detector_list = []  # список детекторов

    for i in range(num_of_detectors):
        detector = CreateDetector(data, num_of_individ, detector_list, affinity, num_iter)
        detector_list.append(detector)
        str_out += 'Create detector number ' + str(i + 1) + ' with coords: ' + ' '.join(
            str(i) for i in detector[0]) + ' and radius: ' + str(detector[1]) + '\n'
        dpg.set_value(id_out, str_out)

    return detector_list, str_out


# Визуализация данных
def Visualization(correct, test, sum_anomaly):
    correct_list = []
    test_list = []
    standard_precipitation = []
    check_precipitation = []
    days_check_precipitation = []

    for month in range(len(correct)):
        standard_precipitation_sum = 0
        check_precipitation_sum = 0
        check_days = 0
        for day in range(len(correct[month])):
            correct_list.append(correct[month][day][1])
            test_list.append(test[month][day][1])
            if correct[month][day][2] != 0.0:
                standard_precipitation_sum += correct[month][day][2]
            if test[month][day][2] != 0.0:
                check_precipitation_sum += test[month][day][2]
                check_days += 1
        standard_precipitation.append(round(standard_precipitation_sum, 1))
        check_precipitation.append(round(check_precipitation_sum, 1))
        days_check_precipitation.append(round(check_days, 1))

    fig, ax = plt.subplots(2, 2, figsize=(12, 12))

    ax[0, 0].set_title("Показатели температуры за год")  # заголовок
    ax[0, 0].set_xlabel("День в году")  # ось абсцисс
    ax[0, 0].set_ylabel("Температура")  # ось ординат
    ax[0, 0].grid()  # включение отображение сетки
    ax[0, 0].plot([i for i in range(1, 366)], correct_list, 'g', label='Средний показатель')
    ax[0, 0].plot([i for i in range(1, 366)], test_list, 'r', label='Рассматриваемый показатель')
    ax[0, 0].set_xlim(0, 365)
    ax[0, 0].set_ylim(-50, 50)
    ax[0, 0].legend()

    ax[0, 1].set_title("Среднемесячное количество осадков")  # заголовок
    ax[0, 1].set_xlabel("Месяц")  # ось абсцисс
    ax[0, 1].set_ylabel("Кол-во осадков, мм.")  # ось ординат
    ax[0, 1].grid()  # включение отображение сетки
    ax[0, 1].bar([i - 0.2 for i in range(1, 13)], standard_precipitation, width=0.4, label='Средний показатель')
    ax[0, 1].bar([i + 0.2 for i in range(1, 13)], check_precipitation, width=0.4, label='Рассматриваемый показатель')
    ax[0, 1].legend()

    ax[1, 0].set_title("Количество аномальных дней за месяц")  # заголовок
    ax[1, 0].set_xlabel("Месяц")  # ось абсцисс
    ax[1, 0].set_ylabel("Дни")  # ось ординат
    ax[1, 0].grid()  # включение отображение сетки
    ax[1, 0].bar([i for i in range(1, 13)], sum_anomaly)

    ax[1, 1].set_title("Количество дней с осадками за месяц")  # заголовок
    ax[1, 1].set_xlabel("Месяц")  # ось абсцисс
    ax[1, 1].set_ylabel("Дни")  # ось ординат
    ax[1, 1].grid()  # включение отображение сетки
    ax[1, 1].bar([i for i in range(1, 13)], days_check_precipitation)
    ax[1, 1].set_ylim(0, 35)

    plt.show()


# Проверка элементов на принадлежность к детекторам
def AnomalyCheck(detectors, test_data, id_out, str_out):
    str_out += '\n\nSearching for anomalies...\n'
    sum_anomaly = []
    for month in test_data:
        num_anomaly = 0
        for data in month:
            for detector in detectors:
                if CalculateDistance(data, detector[0]) <= detector[1]:
                    str_out += 'Value ' + str(data) + ' is anomaly for detector: ' + str(detector) + '\n'
                    dpg.set_value(id_out, str_out)
                    num_anomaly += 1
                    break
        sum_anomaly.append(num_anomaly)
    return sum_anomaly


'''
Алгоритм отрицательного отбора.
Считывание файла корректных и проверяемых значений, создание детекторов двумя вариантами:
1. генерация с заданными параметрами; 2. считывание детекторов из заданного файла.
Дальнейший анализ тестовых данных на поиск аномалий и визуализация.

Параметры функции:
- file: путь к файлу расширения csv, содержащему данные о стандартном поведении ВР
- check_file: путь к файлу расширения csv, содержащему данные о проверяемом ВР
- id_out: идентификатор элемента окна, где происходит вывод информации
- self_radius: расстояние от "своих" элементов, которое считается приемлемым (по умолчанию = 10)
- num_of_detectors: количество генерируемых детекторов (по умолчанию = 100)
- num_of_individuals: количество особей в ГА для генерации детекторов (по умолчанию = 30)
- num_of_iterations: количество поколений в ГА для генерации детекторов (по умолчанию = 30)
- mode: установка для работы алгоритма (по умолчанию = 1)
    mode = 1: генерация новых детекторов по указанным параметрам
    mode = 2: считывание детекторов из csv файла
- detectors_file_write: путь к файлу расширения csv, куда будут записываться данные о
детекторах (по умолчанию = 'Detectors.csv')
- detectors_file_read: путь к файлу расширения csv, задающему расположение детекторов
(по умолчанию = 'Detectors.csv')
'''


def NSA(file, check_file, id_out, num_of_detectors=100, num_of_individuals=30,
        num_of_iterations=30, mode=1, detectors_file_write='Detectors.csv', detectors_file_read='Detectors.csv'):
    correct_data, affinity = GetData(file)
    test_data = GetData(check_file)
    detectors = []
    str_out = '\n'

    if mode == 1:
        detectors, str_out = GetDetectors(num_of_detectors, correct_data, num_of_individuals, affinity,
                                          num_of_iterations, id_out, str_out)
        # Запись в файл
        detect_out = []
        for elem in detectors:
            detect = [x for x in elem[0]]
            detect.append(elem[1])
            detect_out.append(detect)

        df = pd.DataFrame(data=detect_out)
        df.to_csv(detectors_file_write, header=False, index=False)

    elif mode == 2:
        with open(detectors_file_read, 'r') as csv_file:
            reader = csv.reader(csv_file)
            for row in reader:
                coordinates = [float(x) for x in row[:-1]]
                detectors.append([coordinates, float(row[-1])])

    sum_anomaly = AnomalyCheck(detectors, test_data, id_out, str_out)
    Visualization(correct_data, test_data, sum_anomaly)


# функция запуска оконной формы
def Window():
    dpg.create_context()
    dpg.create_viewport(title='Negative Selection Algorithm', width=800, height=600)
    dpg.setup_dearpygui()

    with dpg.window(no_title_bar=True, width=800, height=600):
        with dpg.collapsing_header(label='Generate new detectors'):
            dpg.add_text('')
            with dpg.group():
                source_path1 = dpg.add_text('', label="")
                with dpg.file_dialog(label="Choose path", file_count=1, width=500, height=400, show=False,
                                     user_data=source_path1,
                                     callback=lambda s, a, u: dpg.set_value(u, a['file_path_name'])):
                    dpg.add_file_extension(".csv", color=(255, 255, 255, 255))

                dpg.add_button(label="Select the pass to the source data file", width=800,
                               user_data=dpg.last_container(),
                               callback=lambda s, a, u: dpg.configure_item(u, show=True))

            dpg.add_text('')
            with dpg.group():
                test_path1 = dpg.add_text('', label="")
                with dpg.file_dialog(label="Choose path", file_count=1, width=500, height=400, show=False,
                                     user_data=test_path1,
                                     callback=lambda s, a, u: dpg.set_value(u, a['file_path_name'])):
                    dpg.add_file_extension(".csv", color=(255, 255, 255, 255))
                dpg.add_button(label="Select the pass to the test data file", width=800, user_data=dpg.last_container(),
                               callback=lambda s, a, u: dpg.configure_item(u, show=True))

            dpg.add_text('')
            det_num = dpg.add_slider_int(label='Num of detectors', min_value=0, max_value=500, default_value=100,
                                         width=600)
            dpg.add_text('')
            ind_num = dpg.add_slider_int(label='Num of individs', min_value=0, max_value=100, default_value=30,
                                         width=600)
            dpg.add_text('')
            iter_num = dpg.add_slider_int(label='Num of iterations', min_value=0, max_value=100,
                                          default_value=30, width=600)

            dpg.add_text('')
            end1 = dpg.add_text('', wrap=400)
            cons_box1 = dpg.add_text('', wrap=800, before=end1)
            dpg.add_button(label="Start NSA", height=40, width=800, before=cons_box1,
                           callback=lambda s, a, u: NSA(dpg.get_value(source_path1), dpg.get_value(test_path1),
                                                        cons_box1,
                                                        mode=1, num_of_detectors=dpg.get_value(det_num),
                                                        num_of_individuals=dpg.get_value(ind_num),
                                                        num_of_iterations=dpg.get_value(iter_num)))

        with dpg.collapsing_header(label='Download detectors from file'):
            dpg.add_text('')
            with dpg.group():
                source_path2 = dpg.add_text('', label="")
                with dpg.file_dialog(label="Choose path", file_count=1, width=500, height=400, show=False,
                                     user_data=source_path2,
                                     callback=lambda s, a, u: dpg.set_value(u, a['file_path_name'])):
                    dpg.add_file_extension(".csv", color=(255, 255, 255, 255))

                dpg.add_button(label="Select the pass to the source data file", width=800,
                               user_data=dpg.last_container(),
                               callback=lambda s, a, u: dpg.configure_item(u, show=True))

            dpg.add_text('')
            with dpg.group():
                test_path2 = dpg.add_text('', label="")
                with dpg.file_dialog(label="Choose path", file_count=1, width=500, height=400, show=False,
                                     user_data=test_path2,
                                     callback=lambda s, a, u: dpg.set_value(u, a['file_path_name'])):
                    dpg.add_file_extension(".csv", color=(255, 255, 255, 255))
                dpg.add_button(label="Select the pass to the test data file", width=800, user_data=dpg.last_container(),
                               callback=lambda s, a, u: dpg.configure_item(u, show=True))

            dpg.add_text('')
            with dpg.group():
                detectors_path = dpg.add_text('', label="")
                with dpg.file_dialog(label="Choose path", file_count=1, width=500, height=400, show=False,
                                     user_data=detectors_path,
                                     callback=lambda s, a, u: dpg.set_value(u, a['file_path_name'])):
                    dpg.add_file_extension(".csv", color=(255, 255, 255, 255))
                dpg.add_button(label="Select the pass to the detectors file", width=800, user_data=dpg.last_container(),
                               callback=lambda s, a, u: dpg.configure_item(u, show=True))

            dpg.add_text('')
            end2 = dpg.add_text('', wrap=400)
            cons_box2 = dpg.add_text('', wrap=800, before=end2)
            dpg.add_button(label="Start NSA", height=40, width=800, before=cons_box2,
                           callback=lambda s, a, u: NSA(dpg.get_value(source_path2), dpg.get_value(test_path2),
                                                        cons_box2,
                                                        mode=2, detectors_file_read=dpg.get_value(detectors_path)))

    dpg.show_viewport()
    dpg.start_dearpygui()
    dpg.destroy_context()


Window()
