g = "global"
l = [1,2,3]
class A:
    master = None
    def __init__(self, para):
        self.para = para
        print "init", A.master

    def m1(self):
        print(self.para)

    print "master", master

if __name__=='__main__':
    a = A(1)
    a.master = l[0]
    print a.master
    a.m1()
    a.__init__(10)

