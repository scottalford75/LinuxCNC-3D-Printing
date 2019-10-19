#!/usr/bin/python

import sys,os
import hal
from struct import *
from optparse import Option, OptionParser

import stltool

key = 4711
size = 14400
hdr = 8
vsize = 24
fsize = 12

options = [Option( '-d','--debug', action='store_true', dest='debug', help="enable debug output"),
           Option( '-c','--clear', action='store_true', dest='clear', help="zero corrections in the kins module"),
           Option( '-p','--print', action='store_true', dest='dump', help="print current corrections in the kins module"),
           Option( '-l','--load', action='store_true', dest='load', help="load a STL file into the kins module"),
           Option( '-s','--scale', dest='scale', help="scale STL mesh (use 'x,y,z')"),
           Option( '-r','--rotate', dest='rotate', help="rotate STL mesh (use 'x,y,z' in degrees)"),
           Option( '-t','--translate', dest='translate', help="translate STL mesh (use 'x,y,z')"),
           Option( '-g','--gcode', action='store_true', dest='gcode', help="generate G-code to preview STL mesh"),
           Option( '-b','--binary', action='store_true', dest='binary', help="save as binary STL format (default ASCII)"),
           Option( '-B','--bbox', action='store_true', dest='bbox', help="display the bounding box of the result mesh"),
          ]

def set_header(b,nvert,nface):
    pack_into('ii',b,0,nvert,nface)

def dump_buffer(b):
    (nv,nf) = unpack('ii',b[0:8])
    req = hdr + nv * vsize + nf * fsize

    print >> sys.stderr, "shared memory size: %d, used: %d" % (len(b),req)
    print >> sys.stderr, "%d vertices, %d faces" % (nv,nf)

    for i in range(nv):
        start = i*vsize + hdr
        end = start + vsize
        v = unpack('ddd',b[start:end])
        print >> sys.stderr, "vertex %d %d: %s" % (i,start,v)

    for i in range(nf):
        start = i*fsize + hdr + nv * vsize
        end = start + fsize
        f = unpack('iii',b[start:end])
        print >> sys.stderr, "face %d %d: %s " % (i,start,f)

def load_file(b, filename):
    a = stltool.stl(filename)
    (vertices, faces) = a.unique_vertices(a.facets)

    nv = len(vertices)
    nf = len(faces)
    req = hdr +  nv * vsize + nf * fsize

    if opts.debug:
        print >> sys.stderr, "%d vertices, %d faces" % (nv,nf)
        print >> sys.stderr, "shared memory size %d, used %d" % (len(b),req)

    if len(b) < req:
        raise Exception, "Buffer too small, have %d need %d" % (len(b),req)

    set_header(b,0,0) # disable while loading

    for i in range(nv):
        (v0,v1,v2) = vertices[i]
        pack_into('ddd',b,hdr + i * vsize, v0, v1, v2)

    for i in range(nf):
        (f0,f1,f2) = faces[i]
        pack_into('iii',b,hdr + nv * vsize + i * fsize, f0, f1,f2)

    set_header(b,nv,nf) # activate new set

    if opts.debug:
        print >> sys.stderr, "loaded."

def get_buffer():
    c = hal.component("notused")
    sm = hal.shm(c,key,size)
    return sm.getbuffer()

def gcode(s,filename,scale,rotate,translate):
    if filename:
        print "; converted from",filename
    if scale:
        print "; scale; ",scale
    if rotate:
        print "; rotate; ",rotate
    if translate:
        print "; translate; ",translate
    print "; boundingbox:",s.bbox

    for i in range(len(s.facets)):
        f = s.facets[i][1]
        print "G0 X%.4f Y%4f Z%4f" % (f[0][0],f[0][1],f[0][2])
        print "G1 X%.4f Y%4f Z%4f" % (f[1][0],f[1][1],f[1][2])
        print "G1 X%.4f Y%4f Z%4f" % (f[2][0],f[2][1],f[2][2])
        print "G1 X%.4f Y%4f Z%4f" % (f[0][0],f[0][1],f[0][2])
    print "m2"

def main():
    """
    """
    global opts
    (progdir, progname) = os.path.split(sys.argv[0])

    usage = "usage: %prog [options] file.stl"
    parser = OptionParser(usage=usage)
    parser.disable_interspersed_args()
    parser.add_options(options)
    (opts, args) = parser.parse_args()

    filename = None

    if len(args):
        filename = args[0]

    if opts.clear:
        b = get_buffer()
        set_header(b,0,0)

        if opts.debug:
            print >> sys.stderr, "corrections cleared"
        sys.exit(0)

    if opts.load:
        b = get_buffer()
        load_file(b,filename)
        sys.exit(0)

    if opts.dump:
        b = get_buffer()
        dump_buffer(b)
        sys.exit(0)


    scale = None
    rotate = None
    translate = None


    s = stltool.stl(filename=filename)
    if opts.scale:
        scale = map(float,opts.scale.split(',')[0:])
        if opts.debug:
            print >> sys.stderr, "scale:",scale
        s = s.scale(v=scale)

    if opts.rotate:
        rotate = map(float,opts.rotate.split(',')[0:])
        if opts.debug:
            print >> sys.stderr, "rotate:",rotate
        s = s.rotate(v=rotate)

    if opts.translate:
        translate = map(float,opts.translate.split(',')[0:])
        if opts.debug:
            print >> sys.stderr, "translate:",translate
        s = s.translate(v=translate)
    if opts.bbox:
        print >> sys.stderr, "bounding box: ", s.bbox

    if opts.gcode:
        gcode(s,filename,scale,rotate,translate)
    else:
        s.export(binary=opts.binary)

if __name__ == '__main__':
    main()
