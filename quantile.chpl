use BitOps;
use Sort;
use Random;

enum OptionState {
  EMPTY,
  FULL
}

record Option {

  type T;
  var state:OptionState;
  var value:T;

  proc Option(type T, state=OptionState.EMPTY) {
  }

  proc Option(type T, value:T, state=OptionState.FULL) {
  }

}

/*proc type Option.none(type T) {
  return new Option(T);
}

proc type Option.some(value_:?T) {
  return new Option(T, value_);
}*/

proc comp_basebufferitems(k, n) {
  return (n%(2*k)):int;
}

proc twos_comp(val_, bits) {
  var val = val_;
  if (val & (1 << (bits - 1))) != 0 {
    val = val - (1 << bits);
  }

  return val;
}

proc compute_validlevels(const bp) {
  return popcount(twos_comp(bp, 0xFFFFFFFF));
}

proc comp_bitpattern(k, n) {
  return (n/(2*k)):int;
}

proc retained(k, n) {
  var bbcnt = comp_basebufferitems(k, n);
  var bp = comp_bitpattern(k, n);
  var vl = compute_validlevels(bp);
  return (bbcnt + vl * k)-1;
}

proc posOfPhi(phi:real, n:int) {
  var pos = floor(phi:int * n);
  return if (pos == n) then n-1 else pos;
}

proc searchForChunkContainingPos(arr, pos, l, r) :int {
  if (l+1 != r) {
    var m = 1 + (r-1) / 2;
    if(arr(m) <= pos) {
      return searchForChunkContainingPos(arr, pos, m, r);
    }
    else {
      return searchForChunkContainingPos(arr, pos, l, m);
    }
  }

  return l;
}

proc chunkContainingPos(arr, pos) {
  var len = arr.domain.high - 1;
  var n = arr(len);
  var l = 0;
  var r = len;
  return searchForChunkContainingPos(arr, pos, l, r);
}

record QSAux {
  type T;
  var n:int;
  var Darr : domain(1);
  var arr:[Darr] T;
  var Dwtarr : domain(1);
  var wtarr:[Dwtarr] int;

  proc QSAux(type T, s:QuantileSketch) {
    var k = s.k;
    var n_ = s.n;
    var bitpattern = s.bitpattern;
    var combinedbuffer = s.combinedbuffer;
    var buffercount = s.basebuffercount;
    var nsamples = retained(s.k, s.n);
    Darr = {0..nsamples};
    Dwtarr = {0..(nsamples+1)};
    populateFromSketch(k, n_, bitpattern, combinedbuffer, buffercount, nsamples, arr, wtarr, s.comp);
    blockyTandemMergeSort(arr, wtarr, nsamples, k, s.comp);

    var subtot = 0:int;
    for i in 0..#nsamples {
      var newsubtot = subtot + wtarr(i);
      wtarr(i) = subtot;
      subtot = newsubtot;
    }

    n = n_;
  }

  proc quantile(phi:real) {
    //if !(0.0 <= phi) { return Option.none(T); }
    //if !(phi <= 1.0) { return Option.none(T); }
    //if(n <= 0) { return Option.none(T); }
    var pos = posOfPhi(phi, n);
    return approxAnswerPosQuery(pos);
  }

  proc approxAnswerPosQuery(pos) {
    if !(0 <= pos) { return new Option(T); }
    if !(pos < n) { return new Option(T); }
    var idx = chunkContainingPos(wtarr, pos);
    return new Option(T, arr(idx));
    //return arr(idx);
  }

  proc blockyTandemMergeSortRecur(ksrc, vsrc, kdst, vdst, grpstart, grplen, blksize, arrlim, comp) {
    if(grplen == 1) then return;

    var grplen1 = grplen/2;
    var grplen2 = grplen - grplen1;
    var grpstart1 = grpstart;
    var grpstart2 = grpstart + grplen1;
    blockyTandemMergeSortRecur(kdst, vdst, ksrc, vsrc, grpstart1, grplen1, blksize, arrlim, comp);
    blockyTandemMergeSortRecur(kdst, vdst, ksrc, vsrc, grpstart2, grplen2, blksize, arrlim, comp);
    var arrstart1 = grpstart1*blksize;
    var arrstart2 = grpstart2*blksize;
    var arrlen1 = grplen1 * blksize;
    var arrlen2 = grplen2 * blksize;

    if(arrstart2 + arrlen2 > arrlim) {
      arrlen2 = arrlim - arrstart2;
    }
    tandemMerge(ksrc, vsrc, arrstart1, arrlen1, arrstart2, arrlen2, kdst, vdst, arrstart1, comp);
  }

  proc tandemMerge(ksrc, vsrc, arrst1, arrlen1, arrst2, arrlen2, kdst, vdst, arrst3, comp) {
      var arrstop1 = arrst1 + arrlen1;
      var arrstop2 = arrst2 + arrlen2;
      var i1 = arrst1;
      var i2 = arrst2;
      var i3 = arrst3;
      while(i1 < arrst1 && i2 < arrst2) {
        if(comp(ksrc(i2), ksrc(i1)) < 0) {
          kdst(i3) = ksrc(i2);
          vdst(i3) = vsrc(i2);
          i3+=1; i2+=1;
        }
        else {
          kdst(i3) = ksrc(i1);
          vdst(i3) = vsrc(i1);
          i3+=1; i1+=1;
        }
      }

      if(i1 < arrstop1) {
        ksrc(i1..(i3+(arrstop1-i1))) = kdst(i3..(i3+(arrstop1-i1)));
        vsrc(i1..(i3+(arrstop1-i1))) = vdst(i3..(i3+(arrstop1-i1)));
      }
      else {
        ksrc(i2..(i3+(arrstop1-i1))) = kdst(i3..(i3+(arrstop1-i2)));
        vsrc(i2..(i3+(arrstop1-i1))) = vdst(i3..(i3+(arrstop1-i2)));
      }
  }

  proc blockyTandemMergeSort(arr, wtarr, nsamples, k, comp) {
    if !(k >= 1) then return;
    if nsamples <= k then return;
    var nblks = nsamples/k;
    if(nblks * nsamples < k) {
      nblks+=1;
    }

    var arrtmp = arr;
    var wtarrtmp = wtarr;
    blockyTandemMergeSortRecur(arrtmp, wtarrtmp, arr, wtarr, 0, nblks, k, nsamples, comp);
  }

  proc populateFromSketch(k, n, bitpattern, buffer, buffercount, nsamples, arr, wtarr, comp) {
    var weight = 1;
    var nxt = 0;
    var bits = bitpattern;
    var lvl = 0;
    while bits != 0 {
      weight *= 2;
      if (bits & 1) > 0 {
        var offset = (2+lvl)*k;
        for i in 0..#k {
          arr(nxt) = buffer(i+offset);
          wtarr(nxt) = weight;
          nxt+=1;
        }
      }
      bits = bits >> 1;
    }

    weight = 1;
    var startofbasebufferblock = nxt;
    for i in 0..#buffercount {
      arr(nxt) = buffer(i);
      wtarr(nxt) = weight;
      nxt+=1;
    }

    var c = new QSComparator(T, comp);
    sort(arr(startofbasebufferblock..startofbasebufferblock+nsamples), c);
    wtarr(nsamples) = 0;
  }

}

record QSComparator {
  type T;
  var comp : func(T, T, int);
  proc QSComparator(T, comp) {
  }
}

proc QSComparator.compare(a, b) {
  return comp(a,b);
}

record QuantileSketch {
  type T;
  var comp : func(T, T, int);
  var k, n:int;
  var minval, maxval:T;
  var combinedbuffercapacity, basebuffercount, bitpattern:int;

  var bufDom : domain(1);
  var combinedbuffer:[bufDom] T;

  proc QuantileSketch(type T, _comp, _k) {
    comp = _comp;
    k = _k;
    n = 0;
    var bufalloc = 2 * min(2, k);
    bufDom = {0..#bufalloc};
  }

  proc growBaseBuffer() {
    var oldsize = bufDom.high;
    bufDom = {0..max(min(2*k:int, 2*oldsize), 1)};
    combinedbuffercapacity = bufDom.high:int;
  }

  proc hiBitPos(num) {
    return 63 - clz(num);
  }

  proc computeNumLevelsNeeded() {
    return 1 + hiBitPos(n/2*k);
  }

  proc maybeGrowLevels() {
    var numlvlsneeded = computeNumLevelsNeeded();
    if(numlvlsneeded == 0) {
      return;
    }

    var spaceneeded = (2+numlvlsneeded)*k;
    if(spaceneeded <= combinedbuffercapacity) {
      return;
    }

    bufDom = {0..#spaceneeded};
    combinedbuffercapacity=spaceneeded;
  }

  proc lowestZeroBitStartingAt(bits, pos_) {
    var pos = pos_ & 0X3F;
    var mybits = bits >> pos;
    while ( (mybits & 1) != 0 ) {
      mybits = mybits >> 1;
      pos+=1;
    }

    return pos;
  }

  proc mergeTwoSizeKBuffers(src1, src1pos, src2, src2pos, dst, dstpos, k, comp) {
    var arr1stop = src1pos+k;
    var arr2stop = src1pos+k;
    var i1 = src1pos;
    var i2 = src2pos;
    var i3 = dstpos;
    while (i1 < arr1stop && i2 < arr2stop) {
      if (comp(src2(i2), src1(i1)) < 0) {
        i3+=1; i2+=1;
        dst(i3) = src2(i2);
      }
      else {
        i3+=1; i1+=1;
        dst(i3) = src1(i1);
      }
    }

    if(i1 < arr1stop) {
      src1(i1..i1+(arr1stop-i1)) = dst(i3..i3+(arr1stop-i1));
    }
    else {
      src1(i2..i2+(arr2stop-i2)) = dst(i3..i3+(arr2stop-i2));
    }

  }

  proc inPlacePropagateCarry(startinglevel, /*abuf, abufpos,*/ bbuf, bbufpos) { //, update) {
    var endinglevel = lowestZeroBitStartingAt(bitpattern, startinglevel);
    /*if(!update) {
      abuf(abufpos..abufpos+k) = combinedbuffer( ((2+endinglevel)*k)..(((2+endinglevel)*k)+k) );
    }*/

    for lvl in startinglevel..endinglevel {
      mergeTwoSizeKBuffers(combinedbuffer, (2+lvl)*k:int, combinedbuffer, (2+endinglevel)*k:int, bbuf, bbufpos, k:int, comp);
      zipSize2KBuffer(bbuf, bbufpos, combinedbuffer, (2+lvl)*k:int, k:int);
    }
    bitpattern = bitpattern + (1 << startinglevel):int;
  }

  proc zipSize2KBuffer(bufA, sA, bufB, sB, k) {
    var randv = makeRandomStream(bool, 0);
    var roff = randv.getNext();
    var limb = sB + k;
    var a = sA + roff;
    for b in sB..limb {
      bufB(b) = bufA(a);
      a+=2;
    }
  }

  proc processFullBaseBuffer() {
    maybeGrowLevels();
    var c = new QSComparator(T, comp);
    sort(combinedbuffer, c);
    inPlacePropagateCarry(0, /*nil, 0,*/ combinedbuffer, 0); //, true);
    basebuffercount = 0;
  }

  proc update(di:T) {
    if(comp(di, maxval)  > 0) {
      maxval = di;
    }
    else if(comp(di, minval) < 0) {
      minval = di;
    }

    if(basebuffercount+1 > combinedbuffercapacity) {
      growBaseBuffer();
    }

    combinedbuffer(basebuffercount:int) = di;
    basebuffercount+=1;
    n+=1;
    if(basebuffercount == 2*k) {
      processFullBaseBuffer();
    }
  }

  proc quantile(fraction:real) : Option(T) {
    if fraction < 0.0 || fraction > 1.0 {
      return new Option(T);
    }
    else if fraction == 0.0 {
      return new Option(T, minval); //Option.some(minval);
    }
    else if fraction == 1.0 {
      return new Option(T, maxval); //Option.some(maxval);
    }

    var aux = new QSAux(T, this);
    return aux.quantile(fraction);
  }

  proc compare(a, b) {
    return comp(a,b);
  }

}

proc createQuantileSketch(type T, cmpfnc:func(T, T, int), k:int, values:[?Dvalues] T) {
  var qs = new QuantileSketch(T, cmpfnc, k);
  for val in values {
    qs.update(val);
  }

  return qs;
}

/*
proc main() {

  const uintcmp : func(int, int, int) = lambda(x:int, y:int) : int { return if(x == y) then 0 else if(x < y) then -1 else 1; };
  var qs = new QuantileSketch(int, uintcmp, 100:int);

  for i in 0..1000 {
    qs.update(i:int);
  }

  var values : [0..#100] int;
  forall i in values.domain {
    values(i) = i:int;
  }

  const qsc = createQuantileSketch(int, uintcmp, 100, values);

  const q75 = qsc.quantile(0.75:real);
  writeln(q75);
  const q25 = qsc.quantile(0.25:real);
  writeln(q25);
  const q10 = qsc.quantile(0.10:real);
  writeln(q10);

}
*/

