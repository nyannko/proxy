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
        file_list.sort()
        time_line = []
        throughput_line = []
        time_std = []
        throughput_std = []
        for file_name in file_list:
            # print file_name
            cal_file(file_name, time_line, throughput_line, time_std, throughput_std)
        print time_line
        print time_std
        print throughput_line
        print throughput_std


def cal_file(file_name, time_line, throughput_line, time_std, throughput_std):
    if file_name.endswith(".txt"):
        time_res = []
        throughtput_res = []
        with open(file_name, 'r') as fr:
            for i, v in enumerate(fr):
                v = v.strip()
                line = v.split()
                time = float(line[-1])
                throughput = float(line[0])
                # if time == 0: print time
                if time >= 1.0: continue
                time_res.append(time)
                throughtput_res.append(throughput)
        print file_name, " time mean: {}, throughtput mean: {}".format(numpy.mean(time_res), numpy.mean(throughtput_res))
        time_line.append(numpy.mean(time_res))
        time_std.append(numpy.std(time_res))
        throughput_line.append(numpy.mean(throughtput_res)/1000)
        throughput_std.append(numpy.std(throughtput_res)/1000)

        # print file_name, ": len: {}, mean: {}, max: {}, min:{} std: {} ".format(len(res), numpy.mean(res),
        #                                                                         max(res), min(res),
        #                                                                         numpy.std(res))


if __name__ == '__main__':
    loop_file()
