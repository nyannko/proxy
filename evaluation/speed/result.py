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
                res.append(float(v.split(',')[-1])/1024.0)
        print file_name, ": mean: {}, max: {}, min:{} std: {} ".format(numpy.mean(res),
                                                                                max(res), min(res),
                                                                                numpy.std(res))
def for_graph():
    with open('result.txt', 'r') as fr:
        mean_vals = []
        std_vals = []
        for i, v in enumerate(fr):
            res = [i.strip().split(',') for i in v.split(':')]
            res = [j for i in res for j in i]
            # print res
            mean_vals.append(res[2])
            std_vals.append(res[-1])
        print "["+(', '.join(mean_vals))+"]"
        print "["+(', '.join(std_vals))+"]"



if __name__ == '__main__':
    # loop_dir()
    for_graph()