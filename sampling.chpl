use Random;

record ResizeFactor {
  var X1 = 0;
  var X2 = 1;
  var X4 = 2;
  var X8 = 3;

  var _lg:int;

  proc ResizeFactor(lg_) {
    _lg = lg_;
  }

  proc lg() { return _lg; }

  proc getRF(lg_) {
    select lg_ {
      when X1 do return X1;
      when X2 do return X2;
      when X4 do return X4;
    }

    return X8;
  }

  proc getValue() {
    return 1 << _lg;
  }
}

const DEFAULT_UPDATE_SEED = 9001:int;

record ReservoirSketch {
  type T;

  var MIN_LG_ARR_ITEMS = 4;
  var MAX_ITEMS_SEEN = 0xFFFFFFFFFF;
  var DEFAULT_RESIZE_FACTOR:ResizeFactor;

  var reservoirSize:int;
  var currItemsAlloc:int;
  var itemsSeen:int;
  var rf:ResizeFactor;

  var arrDom: domain(1);
  var arr:[arrDom] T;

  var rrand : RandomStream(real);
  var irand : RandomStream(int);

  proc startingSubMultiple(lgtarget, lgrf, lgmin) {
    return if lgtarget <= lgmin then lgmin else if lgrf == 0 then lgtarget else ((lgtarget-lgmin) % (lgrf+lgmin));
  }

  proc getAdjustedSize(mxsize, resizetarget) {
    return if (mxsize - (resizetarget << 1)) < 0 then mxsize else resizetarget;
  }

  proc ReservoirSketch(type T, k:int, rf_:ResizeFactor, randseed=DEFAULT_UPDATE_SEED) {
    reservoirSize = k;
    itemsSeen = 0;
    var ceilingLgK = log2(reservoirSize ** 2);
    var initialLgSize = startingSubMultiple(ceilingLgK, rf_.lg(), MIN_LG_ARR_ITEMS);
    currItemsAlloc = getAdjustedSize(reservoirSize, 1 << initialLgSize);
    arrDom = {0..#currItemsAlloc};
    rrand = new RandomStream(real, randseed);
    irand = new RandomStream(int, randseed);
  }

  proc ReservoirSketch(type T, data:[]T, itemsseen:int, rf_:ResizeFactor, k:int, randseed=DEFAULT_UPDATE_SEED) {
    reservoirSize = k;
    currItemsAlloc = data.domain.high;
    itemsSeen = itemsseen;
    rf = rf_;
    arrDom = {data.domain.low..data.domain.high};
    arr = data;
    rrand = new RandomStream(real, randseed);
    irand = new RandomStream(int, randseed);
  }

  proc numsamples() { return min(reservoirSize, itemsSeen):int; }

  proc update(item:T) {
    if itemsSeen == MAX_ITEMS_SEEN {
      return false;
    }

    if itemsSeen < reservoirSize {
      if itemsSeen >= currItemsAlloc {
        growReservoir();
      }

      arr(itemsSeen) = item;
      itemsSeen +=1;
    }
    else {
      itemsSeen+=1;
      if (rrand.getNext():int * itemsSeen) < reservoirSize {
        var val = irand.getNext();
        val *= if val < 0 then -1 else 1;
        var newSlot = val % reservoirSize;
        newSlot *= if newSlot < 0 then -1 else 1;
        arr(newSlot) = item;
      }
    }

    return true;
  }

  proc reset() {
    var ceilingLgK = log2(pow2(reservoirSize));
    var initialLgSize = startingSubMultiple(ceilingLgK, rf.lg(), MIN_LG_ARR_ITEMS);
    currItemsAlloc = getAdjustedSize(reservoirSize, 1 << initialLgSize);
    arrDom = {0..#currItemsAlloc};
    itemsSeen = 0;
  }

  proc downSampledCopy(maxK) {
    var ris = new ReservoirSketch(T, maxK, rf);
    for item in arr {
      ris.update(item);
    }

    if ris.itemsSeen < itemsSeen {
      ris.itemsSeen += itemsSeen - ris.itemsSeen;
    }

    return ris;
  }

  proc growReservoir() {
    currItemsAlloc = getAdjustedSize(reservoirSize, currItemsAlloc << rf.lg());
    if arrDom.high < (currItemsAlloc-1) {
      arrDom = {arrDom.low..#currItemsAlloc};
    }
  }

  proc samples() {
    return arr;
  }

  proc implicitSampleWeight() {
    return if itemsSeen < reservoirSize then 1.0 else ((1.0 * itemsSeen:real) / reservoirSize:real);
  }

  proc this(pos) { return arr(pos); }

  proc put(value:T, pos:int) {
    arr(pos) = value;
  }

  iter these() {
    for a in arr {
      yield a;
    }
  }
}

/*
proc main() {
  var rf = new ResizeFactor(10);
  var rs = new ReservoirSketch(int, 100, rf);

  var dataDom = {0..#100};
  var data : [dataDom] int;
  forall i in dataDom {
    data(i) = i;
  }

  for i in data {
    rs.update(i);
  }

  for i in rs {
    writeln(i);
  }

}
*/

