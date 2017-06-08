from random import *

def comp_basebufferitems(k, n):
  return (n%(2*k))

def twos_comp(val_, bits):
  val = val_
  if ((val & (1 << (bits - 1))) != 0):
    val = val - (1 << bits)
  return val

def compute_validlevels(bp):
  # todo popcount
  return popcount(twos_comp(bp, 0xFFFFFFFF))

def comp_bitpattern(k, n):
  return (n/(2*k))

def retained(k, n):
  bbcnt = comp_basebufferitems(k, n);
  bp = comp_bitpattern(k, n);
  vl = compute_validlevels(bp);
  return (bbcnt + vl * k)

def posOfPhi(phi, n):
  pos = floor(phi * n)
  if (pos == n):
      return n-1
  return pos

def searchForChunkContainingPos(arr, pos, l, r):
  if (l+1 != r):
    m = 1 + (r-1) / 2
    if(arr(m) <= pos):
      return searchForChunkContainingPos(arr, pos, m, r)
    else:
      return searchForChunkContainingPos(arr, pos, l, m)

  return l

def chunkContainingPos(arr, pos):
  len_ = arr.domain.high - 1
  n = arr[len_]
  l = 0
  r = len_
  return searchForChunkContainingPos(arr, pos, l, r)

class QSAux(object):

  def __init__(self, s_quantsketch):
    self.n = 0
    self.arr = list()
    self.wtarr = list()

    k = s_quantsketch.k
    n_ = s_quantsketch.n
    bitpattern = s_quantsketch.bitpattern
    combinedbuffer = s_quantsketch.combinedbuffer
    buffercount = s_quantsketch.basebuffercount
    nsamples = retained(s_quantsketch.k, s_quantsketch.n)
    self.arr = list([ 0 for i in xrange(nsamples)])
    self.wtarr = list([ 0 for i in xrange(nsamples+1)])

    self.populateFromSketch(k, n_, bitpattern, combinedbuffer, buffercount, nsamples, arr, wtarr, s.comp)
    self.blockyTandemMergeSort(arr, wtarr, nsamples, k, s.comp)

    subtot = 0
    for i in xrange(nsamples):
      newsubtot = subtot + wtarr[i]
      wtarr[i] = subtot
      subtot = newsubtot

    self.n = n_

  def quantile(self, phi):
    pos = posOfPhi(phi, n)
    retval = self.approxAnswerPosQuery(pos)
    return retval

  def approxAnswerPosQuery(self, pos):
    #if !(0 <= pos) { return Option(); }
    #if !(pos < n) { return Option(T); }
    idx = chunkContainingPos(wtarr, pos)
    return self.arr[idx] #new Option(T, arr(idx));

  def blockyTandemMergeSortRecur(self, ksrc, vsrc, kdst, vdst, grpstart, grplen, blksize, arrlim, comp):
    if(grplen == 1):
        return

    grplen1 = grplen/2
    grplen2 = grplen - grplen1
    grpstart1 = grpstart
    grpstart2 = grpstart + grplen1
    self.blockyTandemMergeSortRecur(kdst, vdst, ksrc, vsrc, grpstart1, grplen1, blksize, arrlim, comp)
    self.blockyTandemMergeSortRecur(kdst, vdst, ksrc, vsrc, grpstart2, grplen2, blksize, arrlim, comp)
    arrstart1 = grpstart1*blksize
    arrstart2 = grpstart2*blksize
    arrlen1 = grplen1 * blksize
    arrlen2 = grplen2 * blksize

    if(arrstart2 + arrlen2 > arrlim):
      arrlen2 = arrlim - arrstart2

    self.tandemMerge(ksrc, vsrc, arrstart1, arrlen1, arrstart2, arrlen2, kdst, vdst, arrstart1, comp)


  def tandemMerge(self, ksrc, vsrc, arrst1, arrlen1, arrst2, arrlen2, kdst, vdst, arrst3, comp):
      arrstop1 = arrst1 + arrlen1
      arrstop2 = arrst2 + arrlen2
      i1 = arrst1
      i2 = arrst2
      i3 = arrst3
      while(i1 < arrst1 and i2 < arrst2):
        if(comp(ksrc[i2], ksrc[i1]) < 0):
          kdst[i3] = ksrc[i2]
          vdst[i3] = vsrc[i2]
          i3+=1
          i2+=1
        else:
          kdst[i3] = ksrc[i1]
          vdst[i3] = vsrc[i1]
          i3+=1
          i1+=1

      if(i1 < arrstop1):
        srng = xrange(i1, (i3+(arrstop1-i1)))
        drng = xrange(i3, (i3+(arrstop1-i2)))
        for (i,j) in zip(srng, drng):
          (ksrc[i], vsrc[i]) = (kdst[j], vdst[j])
      else:
        srng = xrange(i2, (i3+(arrstop1-i1)))
        drng = xrange(i3, (i3+(arrstop1-i2)))
        for (i,j) in zip(srng, drng):
          (ksrc[i], vsrc[i]) = (kdst[j], vdst[j])

  def blockyTandemMergeSort(self, arr, wtarr, nsamples, k, comp):
    #if !(k >= 1) then return;
    #if nsamples <= k then return;
    nblks = nsamples/k
    if(nblks * nsamples < k):
      nblks+=1

    arrtmp = arr;
    wtarrtmp = wtarr;
    self.blockyTandemMergeSortRecur(arrtmp, wtarrtmp, arr, wtarr, 0, nblks, k, nsamples, comp)

  def populateFromSketch(self, k, n, bitpattern, buffer, buffercount, nsamples, arr, wtarr, comp):
    weight = 1
    nxt = 0
    bits = bitpattern
    lvl = 0
    while bits != 0:
      weight *= 2
      if (bits & 1) > 0:
        offset = (2+lvl)*k
        for i in xrange(k):
          arr[nxt] = buffer[i+offset]
          wtarr[nxt] = weight
          nxt+=1
      bits = bits >> 1

    weight = 1
    startofbasebufferblock = nxt
    for i in xrange(buffercount):
      arr[nxt] = buffer[i]
      wtarr[nxt] = weight
      nxt+=1

    c = QSComparator(comp)
    tarr = map(lambda x: arr[x], xrange(startofbasebufferblock,startofbasebufferblock+nsamples))
    sort(tarr, c)
    wtarr[nsamples] = 0

class QSComparator(object):

  def __init__(self, comp):
    self.comp = comp

  def compare(self, a, b):
    return self.comp(a,b)

class QuantileSketch(object):

  def __init__(self, _comp, _k):
    self.comp = _comp;
    self.k = _k;
    self.n = 0;
    self.minval = None
    self.maxval = None
    self.combinedbuffercapacity = 0
    self.basebuffercount = 0
    self.bitpattern = 0
    bufalloc = 2 * min(2, _k)
    self.bufDom = bufalloc
    self.combinedbuffer = list([ None for i in xrange(self.bufDom) ])

  def growBaseBuffer(self):
    oldsize = self.bufDom
    self.bufDom = max(min(2*self.k, 2*oldsize), 1)
    self.combinedbuffercapacity = self.bufDom
    self.combinedbuffer = list([ i < len(self.combinedbuffer) and self.combinedbuffer[i] or None for i in xrange(self.bufDom)])

  def hiBitPos(self, num):
    #return 63 - clz(num) # TODO find clz
    b = "{:064b}".format(num)
    return b.index("1")

  def computeNumLevelsNeeded(self):
    return 1 + self.hiBitPos(self.n/2*self.k)

  def maybeGrowLevels(self):
    numlvlsneeded = self.computeNumLevelsNeeded()
    if(numlvlsneeded == 0):
      return;

    spaceneeded = (2+numlvlsneeded)*self.k
    if(spaceneeded <= self.combinedbuffercapacity):
      return

    self.bufDom = spaceneeded
    self.combinedbuffercapacity=spaceneeded

  def lowestZeroBitStartingAt(self, bits, pos_):
    pos = pos_ & 0X3F
    mybits = bits >> pos
    while ( (mybits & 1) != 0 ):
      mybits = mybits >> 1
      pos+=1

    return pos

  def mergeTwoSizeKBuffers(self, src1, src1pos, src2, src2pos, dst, dstpos, k, comp):
    arr1stop = src1pos+k
    arr2stop = src1pos+k
    i1 = src1pos
    i2 = src2pos
    i3 = dstpos
    while (i1 < arr1stop and i2 < arr2stop):
      if (comp(src2(i2), src1(i1)) < 0):
        i3+=1
        i2+=1
        dst[i3] = src2[i2]
      else:
        i3+=1
        i1+=1
        dst[i3] = src1[i1]

    if(i1 < arr1stop):
      smax = i1+(arr1stop-i1)
      dmax = i3+(arr1stop-i1)
      srng = xrange(i1, i1+(arr1stop-i1)-1)
      drng = xrange(i3, i3+(arr1stop-i1)-1)
      for (i,j) in zip(srng, drng):
        src1[smax-i] = dst[dmax-j] #(i3..i3+(arr1stop-i1));
    else:
      smax = i2+(arr2stop-i2)
      dmax = i3+(arr2stop-i2)
      srng = xrange(i2, i2+(arr2stop-i2))
      drng = xrange(i3, i3+(arr2stop-i2))
      for (i,j) in zip(srng, drng):
        src1[smax-i] = dst[dmax-j] #(i3..i3+(arr1stop-i1));

  def inPlacePropagateCarry(self, startinglevel, bbuf, bbufpos):
    endinglevel = self.lowestZeroBitStartingAt(self.bitpattern, startinglevel)

    for lvl in xrange(startinglevel, endinglevel):
      self.mergeTwoSizeKBuffers(self.combinedbuffer, (2+lvl)*self.k, self.combinedbuffer, (2+endinglevel)*self.k, bbuf, bbufpos, self.k, self.comp)
      self.zipSize2KBuffer(bbuf, bbufpos, self.combinedbuffer, (2+lvl)*self.k, self.k)
    self.bitpattern = self.bitpattern + (1 << startinglevel)

  def zipSize2KBuffer(self, bufA, sA, bufB, sB, k):
    #randv = #self.makeRandomStream(0) # random
    roff = (random() > 0.5) #randv.getNext() # random
    limb = sB + k
    a = sA + roff
    for b in xrange(0, limb-sB):
      bufB[b] = bufA[a]
      a+=2

  def processFullBaseBuffer(self):
    self.maybeGrowLevels()
    c = QSComparator(self.comp)
    sorted(self.combinedbuffer, cmp=lambda x, y: c.compare(x, y))
    self.inPlacePropagateCarry(0, self.combinedbuffer, 0)
    self.basebuffercount = 0

  def update(self, di):
    if(self.comp(di, self.maxval)  > 0):
      self.maxval = di
    elif(self.comp(di, self.minval) < 0):
      self.minval = di

    #print self.basebuffercount, self.combinedbuffercapacity
    if(self.basebuffercount+1 > self.combinedbuffercapacity):
      self.growBaseBuffer()

    self.combinedbuffer[self.basebuffercount] = di
    self.basebuffercount+=1
    self.n+=1
    if(self.basebuffercount == 2*self.k):
      self.processFullBaseBuffer()

  def quantile(self, fraction):
    if fraction < 0.0 or fraction > 1.0:
      return None
    elif fraction == 0.0:
      return self.minval
    elif fraction == 1.0:
      return self.maxval

    aux = QSAux(self)
    return aux.quantile(fraction)

  def compare(self, a, b):
    return self.comp(a,b)

def QuantileSketchCreate(cmpfnc, k, values):
  qs = QuantileSketch(cmpfnc, k)
  for val in values:
    qs.update(val)

  return qs

if __name__ == "__main__":

  def uintcmp(x, y):
    if(x == y):
      return 0
    elif(x < y):
      return -1
    return 1

  #qs = QuantileSketch(uintcmp, 1000)

  #[ qs.update(i) for i in xrange(1000) ]

  values = [ i for i in xrange(10000000) ]
  qsc = QuantileSketchCreate(uintcmp, 100, values)

  q75 = qsc.quantile(0.75)
  print(q75)
  q25 = qsc.quantile(0.25)
  print(q25);
  q10 = qsc.quantile(0.10)
  print(q10)
