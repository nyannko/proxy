import os
import numpy


for fname in os.listdir('.'):
    l = []
    if fname.endswith('.txt'):
        with open(fname, 'r') as fr:
            for i, v in enumerate(fr):
                # if i > 350: break
                if i == 0: continue
                l.append(float(v.strip().split(' ')[-1]))

        print "name:{} len: {}, mean: {}, max: {}, min:{} std: {} ".\
            format(fname, len(l), numpy.mean(l), max(l), min(l), numpy.std(l))
