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
        res_throughput = []
        with open(file_name, 'r') as fr:
            for i, v in enumerate(fr):
                v = v.strip()
                try:
                    time = float(v.split()[-1])
                    throughput = float(v.split()[0])
                    # if time == 0: print time
                    if time > 0:
                        res.append(time)
                        res_throughput.append(throughput)
                except:
                    continue
        # print file_name, " mean: {} {}".format(numpy.mean(res), numpy.std(res))
        # print file_name, " mean: {} {}".format(numpy.mean(res_throughput), numpy.std(res_throughput))
        # print res_throughput
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

# node0001.txt  mean: 3326996.51613
# node0025.txt  mean: 3123246.44828
# node0050.txt  mean: 1159560.64064
# node0100.txt  mean: 695785.425532
# node0150.txt  mean: 532185.510451
# node0200.txt  mean: 527359.228935
# node0250.txt  mean: 471813.552653
# node0300.txt  mean: 455436.6839

# node0001.txt  mean: 3.2004516129
# node0025.txt  mean: 3.40931034483
# node0050.txt  mean: 13.7819793039
# node0100.txt  mean: 27.4041453901
# node0150.txt  mean: 49.0140308031
# node0200.txt  mean: 51.0447281399
# node0250.txt  mean: 64.3305959184
# node0300.txt  mean: 73.3000539143


# node0001.txt  mean: 3326996.51613 0.613876007867
# node0025.txt  mean: 3123246.44828 0.463417745813
# node0050.txt  mean: 1159560.64064 9.44968077345
# node0100.txt  mean: 695785.425532 18.8539221922
# node0150.txt  mean: 532185.510451 27.2258935881
# node0200.txt  mean: 527359.228935 38.2502476349
# node0250.txt  mean: 471813.552653 48.986322341
# node0300.txt  mean: 455436.6839 59.674617854


# node0001.txt  mean: 3.2004516129 0.613876007867
# node0025.txt  mean: 3.40931034483 0.463417745813
# node0050.txt  mean: 13.7819793039 9.44968077345
# node0100.txt  mean: 27.4041453901 18.8539221922
# node0150.txt  mean: 49.0140308031 27.2258935881
# node0200.txt  mean: 51.0447281399 38.2502476349
# node0250.txt  mean: 64.3305959184 48.986322341
# node0300.txt  mean: 73.3000539143 59.674617854
