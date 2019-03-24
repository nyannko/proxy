import sys

row, col = sys.stdin.readline().split()
row = int(row)
matrix = []
try:
    for i in range(row):
        line = sys.stdin.readline().strip().split()
        if line == '':
            break
        matrix.append([int(i) for i in line])
except:
    pass

# print matrix
sum = 0
for line in matrix:
    for j in line:
        print j
        if j > 0:
            sum += j
print sum
