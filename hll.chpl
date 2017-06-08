module hll {

/*
 * HyperLogLog implementation for Chapel
 * author: ct.clmsn
 *
 */

use IO;
use Sort;
use BitOps;
use Random;

proc murmur32(str:string, seed:uint(32)=0) {
   var membufstyle : iostyle;
   membufstyle.binary = 1;

   var membuf = openmem(style=membufstyle);
   var w = membuf.writer();
   w.writef("%s", str);
   w.close();


   var len = if membuf.length() < 4 then 4:uint(32) else membuf.length():uint(32);
   var bytes : [0..#len] uint(8) = 0;

   var r = membuf.reader();
   r.read(bytes);
   r.close();

   membuf.close();

   proc rot32(x, y) {
     return ((x << y) | (x >> (32 - y))):uint(32);
   }

   var c1 : uint(32) = 0xcc9e2d51;
   var c2 : uint(32) = 0x1b873593;
   var r1 : uint(32) = 15;
   var r2 : uint(32) = 13;
   var m : uint(32) = 5;
   var n : uint(32) = 0xe6546b64;

   var hash : uint(32) = seed;
   var nblocks : uint(32) = (len / 4):uint(32);
   ref blocks = bytes;

   var k : uint(32) = 0:uint(32);
   for i in {0..#nblocks} {
     var i4 = i*4;
     k = (blocks(i4+0):uint(32) & 0xff) + ((blocks(i4+1):uint(32) & 0xff) << 8) + ((blocks(i4+2):uint(32) & 0xff) << 16) + ((blocks(i4+3):uint(32) & 0xff) << 24);
     k *= c1;
     k = rot32(k, r1);
     k *= c2;
     hash ^= k;
     hash = rot32(hash, r2) * m + n;
   }

   var tailDom = (nblocks-1)*4;
   var tail = (blocks[tailDom..tailDom+3]);
   var k1 : uint(32) = 0;

   select(len & 3) {
     when 3 {
       k1 ^= tail(tailDom+3) << 16;
     }
     when 2 {
       k1 ^= tail(tailDom+2) << 8;
     }
     when 1 {
       k1 ^= tail(tailDom+1);
       k1 *= c1;
       k1 = rot32(k1, r1);
       k1 *= c2;
       hash ^= k1;
     }
   }

   hash ^= len;
   hash ^= (hash >> 16);
   hash *= 0x85ebca6b;
   hash ^= (hash >> 13);
   hash ^= 0xc2b2ae35;
   hash ^= (hash >> 16);

   return hash;
}

record HyperLogLog {
  var alpha:real;
  var p:int;
  var m:int;
  var domM : domain(1) = {0..0};
  var M: [domM] int;

  proc bit_length(x:?T) {
    if T == uint(64) {
      return 64;
    }
    if T == uint(32) {
      return 32;
    }
    if T == uint(8) {
      return 8;
    }
    if T == int(64) {
      return 64;
    }
    if T == int(32) {
      return 32;
    }
    if T == int(8){
      return 8;
    }

    assert(false, "bit length unknown");
    return -1;
  }

  proc get_alpha(p:int) {
    assert(4 <= p && p <= 16, "p=" + p + " should be in range {4..16}");
    if p == 4 {
      return 0.673;
    }
    if p == 5 {
      return 0.697;
    }
    if p == 6 {
      return 0.709;
    }

    return 0.7213 / (1.0 + 1.079 / ((1 << p):real) );
  }

  //proc get_threshold(p) {
  //}

  proc _Ep() {
    var E = this.alpha * (m ** 2):real / (+ reduce [ i in this.M ] pow(2.0, -i:real));
    return if E <= (5*this.m):real then (E - estimate_bias(E, this.p)) else E;
  }

  proc get_rho(w, mx_width) {
    var rho = mx_width - bit_length(w) + 1;
    if rho <= 0 {
      assert(false, "overflow!");
    }

    return rho;
  }

  proc add(val:string) {
    var x = murmur32(val, 0);
    var j = x & (this.m - 1);
    var w = x >> this.p;
    this.M(j) = max(this.M(j), get_rho(w, 64-this.p));
  }

  proc merge(hll:HyperLogLog) {
    assert(this.m == hll.m, "counter precision not equal");

    proc bitconvert(hll_) {
      var hllbits : uint(32);
      for (i, m) in zip(hll_.domM, hll_.M) {
        hllbits += (( m:uint(32) & 0xff ) << if i < 1 then 0 else (8**i));
      }
      return hllbits;
    }

    var hllM = bitconvert(hll);
    var selfM = bitconvert(this);

    this.M = if max(hllM, selfM) == hllM then hll.M else this.M;
  }

  proc linearcounting(e) {
    return this.m:real * log(this.m:real/e);
  }

  proc lagrange_correction(e) {
    return -(1<<32):real * log(1.0-e/(1<<32):real);
  }

  proc card() {
    var e = this.alpha * (this.m ** 2):real / (+ reduce [ m in this.M ] 2.0 ** -m );
    if e <= (5.0/2.0) * this.m:real {
      var num_zero = this.m:real - (+ reduce ([ m in this.M ] if m == 0 then 1 else 0));
      return linearcounting(num_zero);
    }
    if e <= (1.0/30.0) * (1<<32):real {
      return e;
    }

    return lagrange_correction(e);
  }

  proc this() {
    return card();
  }

  proc HyperLogLog(error_rate:real) {
    const p = ceil(log(1.04/error_rate)):int;
    this.alpha = get_alpha(p);
    this.p = p;
    this.m = 1 << p;
    this.domM = {0..#m};
    this.M = 0;
  }

} // hyperloglog class terminate

proc +=(ref lhs:HyperLogLog, rhs:string) {
   lhs.add(rhs);
}

proc +(ref lhs:HyperLogLog, rhs:HyperLogLog) {
   lhs.merge(rhs);
   return lhs;
}

proc +=(ref lhs:HyperLogLog, rhs:HyperLogLog) {
   lhs.merge(rhs);
}

} // hll module termination

/*
use hll;

proc main() {
  var hll = new HyperLogLog(0.05);
  var dataDom = {0..#100};
  var data:[dataDom] int;

   for i in data.domain {
     hll.add(data(i):string);
   }
}
*/

