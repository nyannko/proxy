import os
import numpy


def loop_dir():
    for dir in os.listdir('.'):
        if os.path.isdir(dir):
            loop_file(dir)


def loop_file(dir):
    for dir_name, _, file_list in os.walk(dir):
        for file_name in file_list:
            cal_file(dir_name + '/' + file_name)


def cal_file(file_name):
    if file_name.endswith(".txt"):
        res = []
        with open(file_name, 'r') as fr:
            for i, v in enumerate(fr):
                v = v.strip()
                res.append(float(v.split()[-1]))
        print file_name, ": len: {}, mean: {}, max: {}, min:{} std: {} ".format(len(res), numpy.mean(res),
                                                                                max(res), min(res),
                                                                                numpy.std(res))


if __name__ == '__main__':
    loop_dir()
