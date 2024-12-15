import json


SIMPLE_MODULE_STATS = 'simple_module_stats'
COMPLEX_MODULE_STATS = 'complex_module_stats'
TIP_OF_THE_DAY_STATS = 'tip_of_the_day_stats'


def get_stat():
    with open('../admin/stat.json', 'r') as file:
        data = json.load(file)
        simple_usage = data[SIMPLE_MODULE_STATS]
        complex_usage = data[COMPLEX_MODULE_STATS]
        totd_usage = data[TIP_OF_THE_DAY_STATS]
        sum_usage = simple_usage + complex_usage + totd_usage
        str = f'total number of uses: {sum_usage}\n' \
                f'Using a simple module: {simple_usage}({int(simple_usage/sum_usage*100)}%)\n'\
                f'Using a complex module: {complex_usage}({int(complex_usage/sum_usage*100)}%)\n'\
                f'Using the Council of the Day module: {totd_usage}({int(totd_usage/sum_usage*100)}%)\n'
        return str


def increase_stat(module):
    with open('../admin/stat.json', 'r+') as file:
        data = json.load(file)
        data[module] += 1
        file.seek(0)
        json.dump(data, file)
        file.truncate()
        file.close()
