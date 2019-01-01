import numpy

l = []
with open('RTT', 'r') as fr:
    for i, v in enumerate(fr):
        v = v.strip()
        v = float(v)
        l.append(v)
# print l[:10]
print "len: {}, mean: {}, max: {}, min:{} std: {} ".format(len(l), numpy.mean(l), max(l), min(l), numpy.std(l))
