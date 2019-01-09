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

# name:normal.txt len: 3406, mean: 0.161294480329, max: 1.674, min:0.121 std: 0.0285425048816
# name:hop1.txt len: 3316, mean: 0.239474366707, max: 0.461, min:0.17 std: 0.016835781919
# name:hop2.txt len: 3304, mean: 0.246213377724, max: 2.453, min:0.182 std: 0.0421215760591
# name:hop3.txt len: 3301, mean: 0.246238109664, max: 1.937, min:0.192 std: 0.0348209112979

