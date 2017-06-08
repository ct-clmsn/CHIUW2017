from random import *
from math import *

LG_MIN_MAPSIZE = 3;
SAMPLE_SIZE = 1024;

class Row(object):
  def __init__(self, item, est, ub, lb):
    self.item = item
    self.est = est
    self.ub = ub
    self.lb = lb

class RowComparator(object):
    def RowComparator(self):
      pass

    def compare(self, a,b):
      if a.est < b.est:
        return -1
      elif a.est > b.est:
        return 1
      return 0

class QuickSelect(object):
  def QuickSelect(self):
    pass

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

NO_FALSE_NEG = 0
NO_FALSE_POS = 1

def hash(key_):
  key = key_
  key ^= key >> 33
  key *= 0xff51afd7ed558ccd
  key ^= key >> 33
  key *= 0xc4ceb9fe1a85ec53
  key ^= key >> 33
  return key

class ReversePurgeItemHashMap(object):
  def __init__(self, mapsize, hashfunc_):
    self.loadfactor = 0.75;
    self.drift_limit = 1024;
    self.lglen = 0
    self.loadthreshold = 0

    self.keydom = mapsize
    self.keys = [ None for i in xrange(mapsize)]
    self.valdom = mapsize
    self.vals = [ 0 for i in xrange(mapsize)]
    self.statedom = mapsize
    self.states = [ 0 for i in xrange(mapsize)]
    self.numactive = 0

    self.hashfunc = hashfunc_
    self.lglen = log(mapsize)/log(2)
    self.loadthreshold = (float(mapsize)*self.loadfactor)

  def active(self, probe):
    return self.states[probe] > 0

  def hashprobe(self, k):
    arraymask = self.keydom-1;
    probe = hash(self.hashKey(k)) & arraymask
    while ( self.states[probe] > 0 and (self.keys[probe]!=k) ):
      probe = (probe+1) & arraymask
    return probe

  def get(self, k):
    probe = self.hashprobe(k) #self.hashKey(k)
    if self.states[probe] > 0:
      return self.vals[probe]
    return 0

  def hashKey(self, k):
    return self.hashfunc(k)

  def adjustOrPutValue(self, k, adjustamt):
    arrmask = self.keydom-1
    probe = hash(self.hashKey(k)) & arrmask
    drift = 1;

    while( self.states[probe] != 0 and (self.keys[probe] == k) ):
      probe = (probe+1) & arrmask
      drift+=1

    if self.states[probe] == 0:
      self.keys[probe] = k
      self.vals[probe] = adjustamt
      self.states[probe] = drift
      self.numactive+=1
    else:
      self.vals[probe] += adjustamt;

  def keepOnlyPositiveCounts(self):
    firstprobe = self.statedom-1
    while(self.states[firstprobe] > 0):
      firstprobe-=1

    for probe in xrange(firstprobe):
      if self.states[probe] > 0 and self.vals[probe] <= 0:
        self.hashDelete(probe)
        self.numactive-=1

    for probe in xrange(firstprobe, self.statedom):
      if self.states[probe] > 0 and self.vals[probe] <= 0:
        self.hashDelete(probe)
        self.numactive-=1

  def adjustAllValuesBy(self, adjustamt):
    for i in xrange(self.valdom):
      self.vals[i] += adjustamt

  def getActiveKeys(self):
    #var retkeydom : domain(1) = {0..#numactive};
    #var retkeys:[retkeydom] T;
    retkeydom = xrange(self.numactive)
    retkeys = [ None for i in xrange(retkeydom) ]

    j = 0;
    for i in xrange(self.keydom):
      if self.active(i):
        retkeys[j] = self.keys[i]
        j+=1

    return retkeys

  def getActiveValues(self):
    retdom = xrange(self.numactive)
    ret = [ None for i in retdom ]

    j = 0
    for i in xrange(self.keydom):
      if self.active(i):
        ret[j] = self.vals[i]
        j+=1

    return ret

  def resize(self, newsize):
    oldkeylen = self.keydom
    self.keydom = newsize
    self.valdom = newsize
    self.statedom = newsize
    self.loadthreshold = int(float(newsize) * self.loadfactor)
    self.lglen = ctz(newsize) # TODO ctz
    self.numactive = 0

    for i in xrange(oldkeylen):
      if(self.states[i] > 0):
        self.adjustOrPutValue(self.keys[i], self.vals[i])

  def purge(self, samplesize):
    limit = min(samplesize, self.numactive)
    numsamples = 0
    i = 0
    samples = [ 0 for i in xrange(limit)]

    while numsamples < limit:
      if self.active(i):
        samples[numsamples] = self.vals[i]
        numsamples+=1
      i+=1

    qs = QuickSelect()
    val = qs.pick(samples, 0, numsamples-1, limit/2)
    self.adjustAllValuesBy(-1*val)
    self.keepOnlyPositiveCounts()
    return val

  def hashDelete(self, deleteprobe_):
    deleteprobe = deleteprobe_
    self.states[deleteprobe] = 0
    drift = 1
    arraymask = self.keydom-1
    probe = (deleteprobe + drift) & arraymask

    while self.states[probe] != 0:
      if self.states[probe] > drift:
        self.keys[deleteprobe] = self.keys[probe]
        self.vals[deleteprobe] = self.vals[probe]
        self.states[deleteprobe] = self.states[probe] - drift
        self.states[probe] = 0
        drift = 0
        deleteprobe = probe

      probe = (probe+1) & arraymask
      drift+=1

  def hashProbe(self, key):
    arraymask = self.keydom
    probe = self.hashfunc(key) & arraymask
    while self.states[probe] > 0 and (self.keys[probe] != key):
      probe = (probe+1) & arraymask
    return probe

  def these(self):
    for i in xrange(self.keydom):
      yield (self.keys[i], self.vals[i], self.states[i], self.numactive)

class HeavyHitter(object):

  def __init__(self, maxmapsize, hashfunc):
    self.lgMaxMapSize = 0
    self.curMapCap = 0
    self.offset = 0
    self.streamLen = 0
    self.sampleSize = 0

    self.lgMaxMapSize = int(max(int(log(maxmapsize)/log(2)), LG_MIN_MAPSIZE))
    self.lgcurmapsz = LG_MIN_MAPSIZE
    self.hashmap = ReversePurgeItemHashMap(1<<self.lgcurmapsz, hashfunc)
    self.curMapCap = self.hashmap.loadthreshold
    self.maxmapcap = min(SAMPLE_SIZE, int(float(1<<self.lgMaxMapSize)*self.hashmap.loadfactor))
    self.offset = 0
    self.sampleSize = min(SAMPLE_SIZE, self.maxmapcap)

  def update(self, element):
    self.update(element, 1)

  def update(self, element, count):
    self.streamLen+=count

    self.hashmap.adjustOrPutValue(element, count)

    if self.hashmap.numactive > self.curMapCap:
      if self.hashmap.lglen < self.lgMaxMapSize:
        self.hashmap.resize(2*self.hashmap.keydom);
        self.curMapCap = self.hashmap.loadthreshold
    else:
        self.offset += self.hashmap.purge(self.sampleSize);

  #def update(self, elements, counts):
  #  for (i,j) in zip(xrange(elements), xrange(counts)):
  #    self.update(elements[i], counts[j])

  def merge(self, other):
    streamlen = self.streamLen + other.streamLen
    [ self.update(k,v) for (k,v,s,na) in other.hashmap ]


    self.offset += other.offset
    self.streamLen = streamlen

  def estimate(self, item):
    itemCount = self.hashmap.get(item)
    if itemCount > 0:
      return itemCount + offset
    return 0

  def upperbound(self, item):
    return self.hashmap.get(item) + self.offset

  def lowerbound(self, item):
    return self.hashmap.get(item)

  def sortItems(self, threshold, err):
    rowlist = list()

    if err == NO_FALSE_NEG:
      for (k,v,s,na) in self.hashmap.these():
        est = self.estimate(k)
        ub = self.upperbound(k)
        lb = self.lowerbound(k)
        if ub >= threshold:
          row = Row(k, est, ub, lb)
          rowlist.append(row)
    else:
      for (k,v,s,na) in self.hashmap.these():
        est = self.estimate(k)
        ub = self.upperbound(k)
        lb = self.lowerbound(k)
        if lb >= threshold:
          row = Row(k, est, ub, lb)
          rowlist.append(row)

    cmp = RowComparator()
    rl = [ None for i in xrange(len(rowlist))] #Rows

    for rli in xrange(len(rl)):
      rl[rli] = rowlist.pop();

    sorted(rl, lambda x, y: cmp.compare(x, y))

    return rowlist

  def frequentitems(self, threshold, errt):
    val = 0
    if threshold > offset:
      val = threshold
    else:
      val = offset

    return self.sortItems(val, errt)

  def frequentitems(self, errt):
    return self.sortItems(self.offset, errt)

# demo program

if __name__ == "__main__":
  #const uintcmp : func(int, int) = lambda(x:int) : int { return x; };
  def uintcmp(x):
      return x

  hh = HeavyHitter(100, uintcmp)
  #var values : [0..100] int;
  values = [ i for i in xrange(100) ]

  for i in values:
    hh.update(values[i], 1);

  print hh.frequentitems(NO_FALSE_POS)
  print hh.frequentitems(NO_FALSE_NEG)
