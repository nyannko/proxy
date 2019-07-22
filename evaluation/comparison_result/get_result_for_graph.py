web=['google', 'instagram', 'twitter', 'facebook', 'youtube']
# web =['youtube']
for wb in web:
    with open('result.txt', 'r') as fr:
        mean_vals = []
        std_vals = []
        for i, v in enumerate(fr):
            if v.startswith(wb):
                res = [i.strip().split(',') for i in v.split(':')]
                res = [j for i in res for j in i]
                # print res
                mean_vals.append(str(float(res[2])*1000))
                std_vals.append(str(float(res[-1])*1000))
        print "("+(', '.join(mean_vals))+")" + "," +"("+(', '.join(std_vals))+")"

