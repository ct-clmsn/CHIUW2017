from random import *
from math import *

class ResizeFactor(object):

  def __init__(self, lg_):
    self.X1 = 0;
    self.X2 = 1;
    self.X4 = 2;
    self.X8 = 3;
    self._lg = lg_

  def lg(self):
    return self._lg

  def getRF(self, lg_):
    if lg_ == self.X1:
      return self.X1
    if lg_ == self.X2:
      return self.X2
    if lg_ == self.X4:
      return self.X4
    return self.X8;

  def getValue(self):
    return 1 << self._lg;

DEFAULT_UPDATE_SEED = 9001
MIN_LG_ARR_ITEMS = 4
MAX_ITEMS_SEEN = 0xFFFFFFFFFF

class ReservoirSketch(object):

  def startingSubMultiple(self, lgtarget, lgrf, lgmin):
    if lgtarget <= lgmin:
      return lgmin
    elif lgrf == 0:
      return lgtarget

    return ((lgtarget-lgmin) % (lgrf+lgmin))

  def getAdjustedSize(self, mxsize, resizetarget):
    if (mxsize - (resizetarget<<1)) < 0:
      return mxsize
    return resizetarget

  def __init__(self, k, rf_, randseed=DEFAULT_UPDATE_SEED):
    self.MIN_LG_ARR_ITEMS = 4
    self.MAX_ITEMS_SEEN = 0xFFFFFFFFFF
    self.DEFAULT_RESIZE_FACTOR = ResizeFactor(100)

    self.rf = ResizeFactor(100)

    #var rrand : RandomStream(real);
    #var irand : RandomStream(int);

    self.reservoirSize = k
    self.itemsSeen = 0
    self.ceilingLgK = log(self.reservoirSize ** 2)/log(2)
    self.initialLgSize = self.startingSubMultiple(self.ceilingLgK, rf_.lg(), MIN_LG_ARR_ITEMS)
    self.currItemsAlloc = self.getAdjustedSize(self.reservoirSize, 1 << int(self.initialLgSize))
    self.arrDom = self.currItemsAlloc
    self.arr = [ 0 for i in xrange(self.arrDom)]
    # TODO
    #rrand = new RandomStream(real, randseed);
    #irand = new RandomStream(int, randseed);

  def ReservoirSketch(self, data, itemsseen, rf_, k, randseed=DEFAULT_UPDATE_SEED):
    self.reservoirSize = k
    self.currItemsAlloc = len(data)
    self.itemsSeen = itemsseen
    self.rf = rf_
    self.arrDom = len(data)
    self.arr = data
    # TODO
    #rrand = new RandomStream(real, randseed);
    #irand = new RandomStream(int, randseed);

  def numsamples(self):
    return min(self.reservoirSize, self.itemsSeen)

  def update(self, item):
    if self.itemsSeen == MAX_ITEMS_SEEN:
      return False

    if self.itemsSeen < self.reservoirSize:
      if self.itemsSeen >= self.currItemsAlloc:
        self.growReservoir()

      self.arr[self.itemsSeen] = item
      self.itemsSeen +=1
    else:
      self.itemsSeen+=1;
      if (randint(self.reservoirSize) * self.itemsSeen) < self.reservoirSize:
        newSlot = random() % self.reservoirSize
        self.arr[newSlot] = item

    return True

  def reset(self):
    self.ceilingLgK = log2(pow2(self.reservoirSize))
    self.initialLgSize = self.startingSubMultiple(ceilingLgK, self.rf.lg(), MIN_LG_ARR_ITEMS)
    self.currItemsAlloc = self.getAdjustedSize(self.reservoirSize, 1 << self.initialLgSize);
    self.arrDom = currItemsAlloc
    self.itemsSeen = 0

  def downSampledCopy(self, maxK):
    ris = ReservoirSketch(maxK, self.rf)
    for item in arr:
      ris.update[item]

    if ris.itemsSeen < self.itemsSeen:
      ris.itemsSeen += self.itemsSeen - ris.itemsSeen

    return ris

  def growReservoir(self):
    self.currItemsAlloc = self.getAdjustedSize(self.reservoirSize, self.currItemsAlloc << self.rf.lg())
    if self.arrDom < (self.currItemsAlloc-1):
      self.arrDom = currItemsAlloc

  def samples(self):
    return self.arr

  def implicitSampleWeight(self):
    if itemsSeen < reservoirSize:
      return 1.0
    return ((1.0 * float(itemsSeen)) / float(reservoirSize))

  def get(self, pos):
    return self.arr[pos]

  def put(self, value, pos):
    self.arr[pos] = value

  def these(self):
    for a in self.arr:
      yield a

if __name__ == "__main__":
  rf = ResizeFactor(10)
  rs = ReservoirSketch(100, rf)

  dataDom = 100
  data = [ i for i in xrange(dataDom)]

  for i in data:
    rs.update(i)

  for i in rs.these():
    print(i)
