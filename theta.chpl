// port of HeapQuickSelectSketch.java in Yahoo's DataSketches library
//
use BitOps;
use Math;

require "limits.h";

extern var INT_MAX:int;

enum ResizeFactorEnum {
  X1 = 0,
  X2 = 1,
  X4 = 2,
  X8 = 3,
}

record ResizeFactor {
  var _lg:int;

  proc ResizeFactor(lg_) {
    _lg = lg_;
  }

  proc lg() { return _lg; }

  proc rf(lg_) {
    select lg_ {
      when ResizeFactorEnum.X1 do return ResizeFactorEnum.X1;
      when ResizeFactorEnum.X2 do return ResizeFactorEnum.X2;
      when ResizeFactorEnum.X4 do return ResizeFactorEnum.X4;
    }

    return ResizeFactorEnum.X8;
  }

  proc getValue() {
    return 1 << _lg;
  }
}

record QuickSelect {}

  proc type QuickSelect.partition(arr, lo, hi) {
      var i = lo;
      var j = hi+1;
      var v = arr(lo);
      while(true) {
        while(arr(i) < v) {
          if i == hi {
            break;
          }

          i+=1;
        }

        while v < arr(j) {
          if j == lo {
            break;
          }
        }

        if i >= j {
          break;
        }

       var x = arr(i);
       arr(i) = arr(j);
       arr(j) = x;
    }

    var x = arr(lo);
    arr(lo) = arr(j);
    arr(j) = x;
    return j;
  }

proc type QuickSelect.pick(arr, lo_, hi_, pivot) {
    var hi = hi_;
    var lo = lo_;
    while hi > lo {
      var j = QuickSelect.partition(arr, lo, hi);
      if j == pivot {
        return arr(pivot);
      }

      if j > pivot {
        hi = j - 1;
      }
      else {
        lo = j + 1;
      }
    }

    return arr(pivot);
  }

proc type QuickSelect.selectExcludingZeros(arr, nonZeros, pivot) {
  if (pivot > nonZeros) {
    return 0:int;
  }

  var arrSize = arr.domain.high;
  var zeros = arrSize - nonZeros;
  var adjK = (pivot + zeros) - 1;
  return QuickSelect.pick(arr, 0, arrSize - 1, adjK);
}

record HashOperations {
}

proc type HashOperations.continueCondition(thetalong, hash) {
  return (( (hash - 1:int) | (thetalong - hash - 1:int)) < 0:int );
}

proc type HashOperations.hashArrayInsert(srcarr, hashtable, lgarrlongs, thetalong) {
  var count = 0;
  var arrLen = srcarr.domain.high;
  for i in 0..#arrLen {
    var h = srcarr(i);
    if HashOperations.continueCondition(thetalong, h) {
      continue;
    }
    if HashOperations.hashSearchOrInsert(hashtable, lgarrlongs, h) < 0 {
      count+=1;
    }
  }

  return count;
}

const STRIDE_HASH_BITS = 7;
const STRIDE_MASK = (1 << STRIDE_HASH_BITS) - 1;

proc type HashOperations.stride(hash, lgArrLongs) { return (2 * ((hash >> (lgArrLongs)) & STRIDE_MASK)):int + 1; }

proc type HashOperations.hashSearchOrInsert(hashTable, lgArrLongs, hash) {
  var arraymask = (1<<lgArrLongs)-1;
  var stride = HashOperations.stride(hash, lgArrLongs);
  var curProbe = (hash & arraymask):int;

  while (hashTable(curProbe) != 0) {
    if hashTable(curProbe) == hash { return curProbe; }
      curProbe = (curProbe + stride) & arraymask;
    }

  hashTable(curProbe) = hash;
  return ~curProbe;
}

const MIN_LG_ARR_LONGS = 5;
const MIN_LG_NOM_LONGS = 4;
const RESIZE_THRESHOLD = 0.5;
const REBUILD_THRESHOLD = 15.0 / 16.0;
const DEFAULT_NOMINAL_ENTRIES = 4096;
const DEFAULT_UPDATE_SEED = 9001:int;
const MAX_THETA_LONG_AS_DOUBLE = INT_MAX:real;

record ThetaSketch {
  type T;

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

  proc startingSubMultiple(lgtarget, lgrf, lgmin) {
    return if lgtarget <= lgmin then lgmin else if lgrf == 0 then lgtarget else ((lgtarget-lgmin) % (lgrf+lgmin));
  }

  proc setHashTableThreshold(lgnomlongs, lgarrlongs) {
    return floor((if (lgarrlongs <= lgnomlongs) then RESIZE_THRESHOLD else REBUILD_THRESHOLD) * (1 << lgarrlongs)):int;
  }

  proc ThetaSketch(type T, hf:func(T, int, int), p_:real=1.0, rf_:ResizeFactor, preamblelongs=3, lgnomlongs=DEFAULT_NOMINAL_ENTRIES, seed_=DEFAULT_UPDATE_SEED) {
    hashfunc = hf;
    lgNomLongs = max(lgnomlongs, MIN_LG_NOM_LONGS);
    seed = seed_;
    p = p_;
    rf = rf_;
    preambleLongs = preamblelongs;
    lgArrLongs = startingSubMultiple(lgNomLongs+1, rf.lg(), MIN_LG_ARR_LONGS);
    hashtableThreshold = setHashTableThreshold(lgNomLongs, lgArrLongs);
    curCount = 0;
    thetaLong = (p*MAX_THETA_LONG_AS_DOUBLE):int;
    empty = true;
    cacheDom = {0..#(1 << lgArrLongs)};
  }

  proc retained() { return curCount; }

  /*proc quickSelectAndRebuild() {
    var arrLongs = 1 << lgArrLongs;

    var pivot = (1 << lgNomLongs) + 1; // pivot for QS

    thetaLong = QuickSelect.selectExcludingZeros(cache, curCount, pivot); //messes up the cache_

    var tgtArr : [0..#arrLongs] int;
    curCount = HashOperations.hashArrayInsert(cache, tgtArr, lgArrLongs, thetaLong);
    cache = tgtArr;
  }*/

  proc rebuild() {
    if retained() > (1<<lgNomLongs) {
      quickSelectAndRebuild();
    }
  }

  proc reset() {
    var lgArrLongsSM = startingSubMultiple(lgNomLongs + 1, rf, MIN_LG_ARR_LONGS);
    if (lgArrLongsSM == lgArrLongs) {
      cache = 0;
    }
    else {
      cacheDom = {0..#(1 << lgArrLongsSM)};
      lgArrLongs = lgArrLongsSM;
    }

    hashtableThreshold = setHashTableThreshold(lgNomLongs, lgArrLongs);
    empty = true;
    curCount = 0;
    thetaLong = (p * MAX_THETA_LONG_AS_DOUBLE):int;
  }

  proc dirty() { return false; }

  proc hashUpdate(hash) {
    empty = false;

    if (HashOperations.continueCondition(thetaLong, hash)) {
      return false;
    }

    if (HashOperations.hashSearchOrInsert(cache, lgArrLongs, hash) >= 0) {
      return false;
    }

    curCount+=1;

    if curCount > hashtableThreshold {
      if lgArrLongs <= lgNomLongs {
        resizeCache();
      }
      else {
        quickSelectAndRebuild();
      }
    }

    return true;
  }

  proc update(datum:T) {
    var hfv = hashfunc(datum, seed);
    return hashUpdate(hfv >> 1);
  }

  proc resizeCache() {
    var lgTgtLongs = lgNomLongs + 1;
    var lgDeltaLongs = lgTgtLongs - lgArrLongs;
    var lgResizeFactor = max(min(rf.lg(), lgDeltaLongs), 1);
    lgArrLongs += lgResizeFactor; // new tgt size
    var tgtArr : [0..(1<<lgArrLongs)] int;
    var newCount = HashOperations.hashArrayInsert(cache, tgtArr, lgArrLongs, thetaLong);;
    curCount = newCount;
    cacheDom = {tgtArr.domain.low..tgtArr.domain.high};
    cache = tgtArr;
    hashtableThreshold = setHashTableThreshold(lgNomLongs, lgArrLongs);
  }

  proc quickSelectAndRebuild() {
    var arrLongs = 1 << lgArrLongs;
    var pivot = (1 << lgNomLongs) + 1;
    thetaLong = QuickSelect.selectExcludingZeros(cache, curCount, pivot);
    var tgtArr : [0..#arrLongs] int;
    curCount = HashOperations.hashArrayInsert(cache, tgtArr, lgArrLongs, thetaLong);
    cache = tgtArr;
  }

  proc estMode(thetalong, empty) {
    return (thetalong < INT_MAX) && !empty;
  }

  proc estimate(thetalong, curcount, empty) {
    if (estMode(thetalong, empty)) {
      var theta = thetaLong / MAX_THETA_LONG_AS_DOUBLE;
      return curcount / theta;
    }

    return curcount;
  }

  proc estimate() {
    return estimate(thetaLong, retained(), empty);
  }

  proc merge(ts:ThetaSketch(T)) {
    var uthetalong = min(thetaLong, ts.thetaLong);
    var curCountIn = retained();
    var cacheIn = ts.cache;
    var arrLongs = cacheIn.domain.high;
    var c = 0;
    for i in 0..#arrLongs {
      if c < curCountIn { break; }
      var hashIn = cacheIn(i);
      if ((hashIn <= 0:int) || (hashIn >= uthetalong)) { continue; }
      hashUpdate(hashIn);
      c+=1;
    }
  }

}

proc createThetaSketch(type T, hf_:func(T, int, int), k_:int, p_:real = 1.0) {
  //hf:func(T, int), p_:real=1.0, rf_:ResizeFactor=ResizeFactor.X8, preamblelongs=3, lgnomlongs=DEFAULT_NOMINAL_ENTRIES, seed_=DEFAULT_UPDATE_SEED
  var rf = new ResizeFactor(ResizeFactorEnum.X8);
  return new ThetaSketch(T, hf=hf_, rf_=rf, p_=p_, lgnomlongs=ctz(ceil(k_**2):int));
}

proc +(a:ThetaSketch(?T), b:ThetaSketch(T)) {
  a.merge(b);
  return a;
}

/*
proc main() {

  var uintcmp : func(int, int, int) = lambda(x:int, seed:int) : int { return x; };

  var k = 512;
  var u = k;
  var seed = 0;
  var ts =  createThetaSketch(int, uintcmp, k);

  for i in 0..#u {
    ts.update(i);
  }

  writeln((ts.estimate(), u, 0.0:real));

}
*/

