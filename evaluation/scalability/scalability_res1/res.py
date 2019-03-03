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
        res = []
        with open(file_name, 'r') as fr:
            for i, v in enumerate(fr):
                v = v.strip()
                try:
                    time = float(v.split()[-1])
                    # if time == 0: print time
                    if time > 0 and time < 5:
                        res.append(time)
                except:
                    continue
        # print file_name, " mean: {}".format(numpy.mean(res))
        print file_name, ": len: {}, mean: {}, max: {}, min:{} std: {} ".format(len(res), numpy.mean(res),
                                                                                max(res), min(res),
                                                                                numpy.std(res))


if __name__ == '__main__':
    loop_file()

# node001.txt  mean: 0.513646234676
# node025.txt  mean: 0.519623576028
# node050.txt  mean: 0.514369755792
# node100.txt  mean: 0.507876383204
# node150.txt  mean: 0.511698688906
# node200.txt  mean: 0.508039319973
# node250.txt  mean: 0.517175920836
# node300.txt  mean: 0.538763490128
