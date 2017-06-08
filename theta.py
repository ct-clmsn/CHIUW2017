from math import *
from sys import *

def lowestZeroBitStartingAt(bits, pos_):
  pos = pos_ & 0X3F
  mybits = bits >> pos
  while ( (mybits & 1) != 0 ):
    mybits = mybits >> 1
    pos+=1

  return pos

X1 = 0
X2 = 1
X4 = 2
X8 = 3
INT_MAX = maxint

class ResizeFactor(object):

  def __init__(self, lg_):
    self._lg = lg_

  def lg(self):
    return self._lg

  def rf(self, lg_):
    if lg_ == X1:
      return X1
    if lg_ == X2:
      return X2
    if lg_ == X4:
      return X4
    return X8

  def getValue(self):
    return 1 << self._lg

class QuickSelect(object):

  def partition(self, arr, lo, hi):
    i = lo
    j = hi+1
    v = arr[lo]
    while(True):
      while(arr[i] < v):
        if i == hi:
          break

        i+=1

      while v < arr[j]:
        if j == lo:
          break

      if i >= j:
        break

      x = arr[i]
      arr[i] = arr[j]
      arr[j] = x

    x = arr[lo]
    arr[lo] = arr[j]
    arr[j] = x
    return j

  def pick(self, arr, lo_, hi_, pivot):
    hi = hi_
    lo = lo_
    while hi > lo:
      j = self.partition(arr, lo, hi)
      if j == pivot:
        return arr[pivot]

      if j > pivot:
        hi = j - 1
      else:
        lo = j + 1

    return arr[pivot]

  def selectExcludingZeros(self, arr, nonZeros, pivot):
    if (pivot > nonZeros):
      return 0

    arrSize = len(arr)-1
    zeros = arrSize - nonZeros
    adjK = (pivot + zeros) - 1
    return self.pick(arr, 0, arrSize - 1, adjK)

class HashOperations(object):
  def __init__(self):
    pass

  def continueCondition(self, thetalong, hash):
    return (( int(hash - 1) | int(thetalong - hash - 1)) < 0 )

  def hashArrayInsert(self, srcarr, hashtable, lgarrlongs, thetalong):
    count = 0
    arrLen = len(srcarr)-1
    for i in xrange(arrLen):
      h = srcarr[i]
      if self.continueCondition(thetalong, h):
        continue
      if self.hashSearchOrInsert(hashtable, lgarrlongs, h) < 0:
        count+=1;

    return count

  def stride(self, hash, lgArrLongs):
    return (2 * ((hash >> (lgArrLongs)) & STRIDE_MASK)) + 1

  def hashSearchOrInsert(self, hashTable, lgArrLongs, hash):
    arraymask = (1<<lgArrLongs)-1
    stride = self.stride(hash, lgArrLongs)
    curProbe = (hash & arraymask)
    #print hashTable
    while (hashTable[curProbe] != 0):
      if hashTable[curProbe] == hash:
        return curProbe
      curProbe = (curProbe + stride) & arraymask
      #print 'while'

    hashTable[curProbe] = hash
    return ~curProbe

STRIDE_HASH_BITS = 7
STRIDE_MASK = (1 << STRIDE_HASH_BITS) - 1

MIN_LG_ARR_LONGS = 5
MIN_LG_NOM_LONGS = 4
RESIZE_THRESHOLD = 0.5
REBUILD_THRESHOLD = 15.0 / 16.0
DEFAULT_NOMINAL_ENTRIES = 4096
DEFAULT_UPDATE_SEED = 9001
MAX_THETA_LONG_AS_DOUBLE = INT_MAX

class ThetaSketch(HashOperations, QuickSelect):
  '''
  var lgNomLongs:int;
  var seed:int;
  var p:real;
  var rf:ResizeFactor;
  var preambleLongs:int;
  var lgArrLongs:int;
  var hashtableThreshold:int;
  var curCount:int;
  var thetaLong:int;
  var empty:bool;
  var cacheDom:domain(1);
  var cache:[cacheDom] int;

  var hashfunc : func(T, int, int);
  '''
  def startingSubMultiple(self, lgtarget, lgrf, lgmin):
    if lgtarget <= lgmin:
      return lgmin
    elif lgrf == 0:
      return lgtarget
    return ((lgtarget-lgmin) % (lgrf+lgmin))

  def setHashTableThreshold(self, lgnomlongs, lgarrlongs):
    if (lgarrlongs <= lgnomlongs):
      return floor(RESIZE_THRESHOLD)
    return floor(REBUILD_THRESHOLD * (1 << lgarrlongs))

  def __init__(self, hf, rf_, p_=1.0, preamblelongs=3, lgnomlongs=DEFAULT_NOMINAL_ENTRIES, seed_=DEFAULT_UPDATE_SEED):
    HashOperations.__init__(self)
    QuickSelect.__init__(self)
    self.hashfunc = hf;
    self.lgNomLongs = max(lgnomlongs, MIN_LG_NOM_LONGS);
    self.seed = seed_;
    self.p = p_;
    self.rf = rf_;
    self.preambleLongs = preamblelongs;
    self.lgArrLongs = self.startingSubMultiple(self.lgNomLongs+1, self.rf.lg(), MIN_LG_ARR_LONGS);
    self.hashtableThreshold = self.setHashTableThreshold(self.lgNomLongs, self.lgArrLongs);
    self.curCount = 0;
    self.thetaLong = (self.p*MAX_THETA_LONG_AS_DOUBLE)
    self.empty = True
    self.cacheDom = (1 << self.lgArrLongs)
    self.cache = [ 0 for i in xrange(self.cacheDom) ]

  def retained(self):
    return self.curCount

  def rebuild(self):
    if retained() > (1<<lgNomLongs):
      self.quickSelectAndRebuild()

  def reset(self):
    lgArrLongsSM = self.startingSubMultiple(lgNomLongs + 1, rf, MIN_LG_ARR_LONGS)
    if (lgArrLongsSM == lgArrLongs):
      self.cache = [ 0 for i in xrange(len(self.cache))]
    else:
      self.cacheDom = (1 << lgArrLongsSM)
      self.lgArrLongs = lgArrLongsSM

    self.hashtableThreshold = setHashTableThreshold(lgNomLongs, lgArrLongs);
    self.empty = true;
    self.curCount = 0;
    self.thetaLong = (p * MAX_THETA_LONG_AS_DOUBLE)

  def dirty(self):
    return False

  def hashUpdate(self, hash):
    self.empty = False
    #print 'here-up-1'
    if (self.continueCondition(self.thetaLong, hash)):
      return False
    #print 'here-up-2'
    if (self.hashSearchOrInsert(self.cache, self.lgArrLongs, hash) >= 0):
      return False
    #print 'here-up-3'
    self.curCount+=1

    if self.curCount > self.hashtableThreshold:
      #print 'here-up-4'
      if self.lgArrLongs <= self.lgNomLongs:
        self.resizeCache()
      #print 'here-up-5'
    else:
      #print 'here-up-6'
      self.quickSelectAndRebuild()
    #print 'here-up-7'
    return True

  def update(self, datum):
    hfv = self.hashfunc(datum, seed)
    return self.hashUpdate(hfv >> 1)

  def resizeCache(self):
    lgTgtLongs = self.lgNomLongs + 1;
    lgDeltaLongs = lgTgtLongs - self.lgArrLongs
    lgResizeFactor = max(min(self.rf.lg(), lgDeltaLongs), 1)
    self.lgArrLongs += lgResizeFactor #; // new tgt size
    tgtArr = [ 0 for i in (1<<self.lgArrLongs)]
    newCount = self.hashArrayInsert(self.cache, tgtArr, self.lgArrLongs, thetaLong)
    self.curCount = newCount
    self.cacheDom = len(tgtArr) #{tgtArr.domain.low..tgtArr.domain.high};
    self.cache = tgtArr
    self.hashtableThreshold = self.setHashTableThreshold(lgNomLongs, lgArrLongs)

  def quickSelectAndRebuild(self):
    arrLongs = 1 << self.lgArrLongs
    pivot = (1 << self.lgNomLongs) + 1
    thetaLong = self.selectExcludingZeros(self.cache, self.curCount, pivot)
    tgtArr = [ 0 for i in xrange(arrLongs)]
    self.curCount = self.hashArrayInsert(self.cache, tgtArr, self.lgArrLongs, thetaLong)
    self.cache = tgtArr

  def estMode(self, thetalong, empty):
    return (thetalong < INT_MAX) and (not empty)

  def estimate_(self, thetalong, curcount, empty):
    if (self.estMode(thetalong, empty)):
      theta = thetalong / MAX_THETA_LONG_AS_DOUBLE
      return curcount / theta

    return curcount

  def estimate(self):
    return self.estimate_(self.thetaLong, self.retained(), self.empty)

  def merge(self, ts):
    uthetalong = min(self.thetaLong, ts.thetaLong);
    curCountIn = self.retained()
    cacheIn = ts.cache;
    arrLongs = len(self.cacheIn)
    c = 0
    for i in xrange(arrLongs):
      if c < curCountIn:
        break
      hashIn = cacheIn[i]
      if ((hashIn <= 0) or (hashIn >= uthetalong)):
        continue
      self.hashUpdate(hashIn)
      c+=1

def createThetaSketch(hf_, k_=1, p_ = 1.0):
  #hf:func(T, int), p_:real=1.0, rf_:ResizeFactor=ResizeFactor.X8, preamblelongs=3, lgnomlongs=DEFAULT_NOMINAL_ENTRIES, seed_=DEFAULT_UPDATE_SEED
  rf = ResizeFactor(X8)
  return ThetaSketch(hf=hf_, rf_=rf, p_=p_, lgnomlongs=lowestZeroBitStartingAt(int(ceil(k_**2)), k))

if __name__ == "__main__":

  #var uintcmp : func(int, int, int) = lambda(x:int, seed:int) : int { return x; };
  def uintcmp(a, b):
    return a

  k = 512
  u = k
  seed = 0
  ts = createThetaSketch(uintcmp, k)
  #print 'here'
  for i in xrange(u): # 0..#u {
    #print i
    ts.update(i)
  #print 'here'
  print((ts.estimate(), u, 0.0))
