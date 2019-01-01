sum = 0
with open('normal.txt', 'r') as fr:
    for i, v in enumerate(fr):
        if i == 0: continue
        sum += float(v.strip().split(' ')[-1])
    print sum / i


sum = 0
with open('hop0.txt', 'r') as fr:
    for i, v in enumerate(fr):
        if i > 100: break
        if i == 0: continue
        sum += float(v.strip().split(' ')[-1])

    print sum / i


sum = 0
with open('hop1.txt', 'r') as fr:
    for i, v in enumerate(fr):
        if i > 350: break
        if i == 0: continue
        sum += float(v.strip().split(' ')[-1])
    print sum / i

sum = 0
with open('hop2.txt', 'r') as fr:
    for i, v in enumerate(fr):
        if i > 350: break
        if i == 0: continue
        sum += float(v.strip().split(' ')[-1])
    print sum / i

sum = 0
with open('hop3.txt', 'r') as fr:
    for i, v in enumerate(fr):
        if i > 350: break
        if i == 0: continue
        sum += float(v.strip().split(' ')[-1])
    print sum / i