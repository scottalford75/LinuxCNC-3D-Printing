# rehashed from https://github.com/kliment/Printrun
# STL binary and ascii I/O
# also provides scaling, rotation, translation and bounding box

import sys, struct, math

I=[[1,0,0,0],
    [0,1,0,0],
    [0,0,1,0],
    [0,0,0,1]]

def cross(v1,v2):
    return [v1[1]*v2[2]-v1[2]*v2[1],v1[2]*v2[0]-v1[0]*v2[2],v1[0]*v2[1]-v1[1]*v2[0]]

def genfacet(v):
    veca = [v[1][0]-v[0][0],v[1][1]-v[0][1],v[1][2]-v[0][2]]
    vecb = [v[2][0]-v[1][0],v[2][1]-v[1][1],v[2][2]-v[1][2]]
    vecx = cross(veca,vecb)
    vlen = math.sqrt(sum(map(lambda x:x*x,vecx)))
    if vlen == 0:
        vlen = 1
    normal = map(lambda x:x/vlen, vecx)
    return [normal,v]

def transpose(matrix):
    return zip(*matrix)

def multmatrix(vector,matrix):
    return map(sum, transpose(map(lambda x:[x[0]*p for p in x[1]], zip(vector, transpose(matrix)))))

def applymatrix(facet,matrix=I):
    return genfacet(map(lambda x:multmatrix(x+[1],matrix)[:3],facet[1]))

class stl:
    def __init__(self, filename=None):
        self.facet = [[0,0,0],[[0,0,0],[0,0,0],[0,0,0]]]
        self.facets = []
        self.name = ""
        self.facetloc = 0
        if filename is None:
            self.f = list(sys.stdin)
        else:
            self.f = list(open(filename))
        if not self.f[0].startswith("solid"):
            print >> sys.stderr,"Not an ascii stl solid - attempting to parse as binary"
            f = open(filename,"rb")
            buf = f.read(84)
            while(len(buf)<84):
                newdata = f.read(84 - len(buf))
                if not len(newdata):
                    break
                buf += newdata
            facetcount = struct.unpack_from("<I",buf,80)
            facetformat = struct.Struct("<ffffffffffffH")
            for i in xrange(facetcount[0]):
                buf = f.read(50)
                while(len(buf)<50):
                    newdata = f.read(50-len(buf))
                    if not len(newdata):
                        break
                    buf += newdata
                fd = list(facetformat.unpack(buf))
                self.name = "binary solid"
                self.facet = [fd[:3],[fd[3:6],fd[6:9],fd[9:12]]]
                self.facets += [self.facet]
                facet = self.facet
            f.close()
            self.boundingbox()
            return
        for i in self.f:
            if not self.parseline(i):
                self.boundingbox()
                return

    def boundingbox(self):
        minx = miny = minz = 0
        maxx = maxy = maxz = 0
        for i in range(len(self.facets)):
            minx = min(map(lambda x:x[0], self.facets[i][1]))
            maxx = max(map(lambda x:x[0], self.facets[i][1]))
            miny = min(map(lambda x:x[1], self.facets[i][1]))
            maxy = max(map(lambda x:x[1], self.facets[i][1]))
            minz = min(map(lambda x:x[2], self.facets[i][1]))
            maxz = max(map(lambda x:x[2], self.facets[i][1]))
        self.bbox = [[minx,miny,minz],[maxx,maxy,maxz]]

    def translate(self,v=[0,0,0]):
        matrix=[
        [1,0,0,v[0]],
        [0,1,0,v[1]],
        [0,0,1,v[2]],
        [0,0,0,1]
        ]
        return self.transform(matrix)

    def rotate(self,v=[0,0,0]):
        import math
        z = v[2]
        matrix1 = [
        [math.cos(math.radians(z)),-math.sin(math.radians(z)),0,0],
        [math.sin(math.radians(z)),math.cos(math.radians(z)),0,0],
        [0,0,1,0],
        [0,0,0,1]
        ]
        y = v[0]
        matrix2=[
        [1,0,0,0],
        [0,math.cos(math.radians(y)),-math.sin(math.radians(y)),0],
        [0,math.sin(math.radians(y)),math.cos(math.radians(y)),0],
        [0,0,0,1]
        ]
        x = v[1]
        matrix3=[
        [math.cos(math.radians(x)),0,-math.sin(math.radians(x)),0],
        [0,1,0,0],
        [math.sin(math.radians(x)),0,math.cos(math.radians(x)),0],
        [0,0,0,1]
        ]
        return self.transform(matrix1).transform(matrix2).transform(matrix3)

    def scale(self,v=[0,0,0]):
        matrix=[
        [v[0],0,0,0],
        [0,v[1],0,0],
        [0,0,v[2],0],
        [0,0,0,1]
        ]
        return self.transform(matrix)

    def transform(self,m=I):
        self.facets = [applymatrix(i,m) for i in self.facets]
        self.facetloc = 0
        self.boundingbox()
        return self

    def export(self,filename=None,binary=0):
        if filename:
            f = open(filename,"w")
        else:
            f = sys.stdout
        if binary:
            buf = "".join(["\0"]*80)
            buf += struct.pack("<I",len(self.facets))
            facetformat = struct.Struct("<ffffffffffffH")
            for i in self.facets:
                l = list(i[0][:])
                for j in i[1]:
                    l += j[:]
                l += [0]
                buf += facetformat.pack(*l)
            f.write(buf)
        else:
            f.write("solid " + self.name + "\n")
            for i in self.facets:
                f.write("  facet normal "+" ".join(map(str,i[0]))+"\n")
                f.write("   outer loop"+"\n")
                for j in i[1]:
                    f.write("    vertex "+" ".join(map(str,j))+"\n")
                f.write("   endloop"+"\n")
                f.write("  endfacet"+"\n")
            f.write("endsolid "+self.name+"\n")
        f.flush()
        if filename:
            f.close()

    def parseline(self,l):
        l = l.strip()
        if l.startswith("solid"):
            self.name = l[6:]
        elif l.startswith("endsolid"):
            return 0
        elif l.startswith("facet normal"):
            l = l.replace(",",".")
            self.facetloc = 0
            self.facet = [[0,0,0],[[0,0,0],[0,0,0],[0,0,0]]]
            self.facet[0] = map(float,l.split()[2:])
        elif l.startswith("endfacet"):
            self.facets += [self.facet]
            facet = self.facet
        elif l.startswith("vertex"):
            l = l.replace(",",".")
            self.facet[1][self.facetloc] = map(float,l.split()[1:])
            self.facetloc += 1
        return 1

    def unique_vertices(self,facets):
        # Generate verts and faces lists, without duplicates
        # the facets refer to vertices as an index into the verts list
        # drop normal vector
        # this is the current mesh representation in the probekins module
        verts = []
        coords = {}
        index = 0
        faces=[]
        # face representation:
        # [[normal],[[x0,y0,z0],[x1,y1,z1],[x2,y2,z2]]]
        for i in range(len(facets)):
            vl = facets[i][1]
            p = []
            for j in range(len(vl)):
                v = vl[j]
                vertex = tuple(v)
                if not coords.has_key(vertex):
                    coords[vertex] = index
                    index += 1
                    verts.append(vertex)
                p.append(coords[vertex])
            faces.append(p)
        return (verts, faces)

if __name__=="__main__":
    s = stl("twotriangles.stl")
    (v,f) = s.unique_vertices(s.facets)
    print "unique vertices:",v
    print "faces by vertex index:", f
    sf = s.scale(v=[2,2,2])
    print "scaled:", sf.facets
    sr = s.rotate(v=[90,0,0])
    print "rotated:", sr.facets
    st = s.translate(v=[10,0,4])
    print "translated:", st.facets
    print "boundingbox:",s.bbox
    s.export()
