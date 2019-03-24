#
import os
import numpy


# def loop_dir():
#     for dir in os.listdir('.'):
#         if os.path.isdir(dir):
#             print dir
#             # loop_file(dir)


def loop_file():
    for dir_name, _, file_list in os.walk('.'):
        for file_name in file_list:
            cal_file(file_name)


def cal_file(file_name):
    if file_name.endswith(".txt"):
        time_x = []
        cpu_y = []
        with open(file_name, 'r') as fr:
            for i, v in enumerate(fr):
                v = v.strip()
                try:
                    time = float(v.split()[0])
                    cpu = float(v.split()[1])
                    # if time == 0: print time
                    if time > 0:
                        time_x.append(time)
                        cpu_y.append(cpu)
                except:
                    continue
        # print file_name, " mean: {} {}".format(numpy.mean(res), numpy.std(res))
        # print file_name, " mean: {} {}".format(numpy.mean(res_throughput), numpy.std(res_throughput))
        # print res_throughput
        # print file_name, ": len: {}, mean: {}, max: {}, min:{} std: {} ".format(len(res), numpy.mean(res),
        #                                                                         max(res), min(res),
        #                                                                         numpy.std(res))
        # print time_x
        print file_name
        print cpu_y

if __name__ == '__main__':
    loop_file()



# [4.7, 4.2, 3.7, 3.4, 3.1, 2.9, 2.6, 2.5, 2.4, 2.2, 2.1, 2.0, 2.0, 1.9, 1.8, 1.7, 1.6, 1.6, 1.5, 1.5, 1.4, 1.4, 1.3, 1.3, 1.3, 1.2, 1.2, 1.2, 1.1, 1.1, 1.1, 1.1, 1.1, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.9, 0.9, 0.9, 0.9, 0.9, 0.9, 0.9, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.7, 0.7, 0.7, 0.7, 0.7, 0.7, 0.7, 0.7, 0.7, 0.7, 0.7, 0.7, 0.7, 0.7, 0.7, 0.7, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6, 0.5, 0.6, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5]
# [4.5, 4.1, 3.6, 3.3, 3.0, 2.8, 2.6, 2.5, 2.3, 2.1, 2.1, 2.0, 1.9, 1.9, 1.8, 1.7, 1.6, 1.6, 1.5, 1.4, 1.4, 1.3, 1.3, 1.3, 1.3, 1.2, 1.2, 1.2, 1.1, 1.1, 1.1, 1.1, 1.1, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.9, 0.9, 0.9, 0.9, 0.9, 0.9, 0.9, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.7, 0.7, 0.7, 0.7, 0.7, 0.7, 0.7, 0.7, 0.7, 0.7, 0.7, 0.7, 0.7, 0.7, 0.7, 0.7, 0.7, 0.7, 0.6, 0.7, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6]
# [4.5, 4.1, 3.7, 3.5, 3.2, 3.0, 2.8, 2.6, 2.5, 2.3, 2.3, 2.2, 2.0, 2.0, 1.9, 1.8, 1.8, 1.7, 1.7, 1.6, 1.6, 1.5, 1.5, 1.5, 1.4, 1.4, 1.4, 1.3, 1.3, 1.2, 1.2, 1.2, 1.2, 1.1, 1.1, 1.1, 1.1, 1.1, 1.1, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.9, 0.9, 0.9, 0.9, 0.9, 0.9, 0.9, 0.9, 0.9, 0.9, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.7, 0.7, 0.7, 0.7, 0.7, 0.7, 0.7, 0.7, 0.7, 0.7, 0.7, 0.7, 0.7, 0.7, 0.7, 0.7, 0.7, 0.7, 0.7, 0.7, 0.7, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6]