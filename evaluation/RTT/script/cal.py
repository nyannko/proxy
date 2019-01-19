import numpy
import os

l = []
for filename in os.listdir():
    with open('RTT', 'r') as fr:
        for i, v in enumerate(fr):
            v = v.strip()
            v = float(v)
            l.append(v)
# print l[:10]
    print filename, ": len: {}, mean: {}, max: {}, min:{} std: {} ".format(len(l), numpy.mean(l), max(l), min(l), numpy.std(l))

# len: 9429, mean: 0.0028150966633, max: 0.0129101276398, min:0.00178909301758 std: 0.000501931349467