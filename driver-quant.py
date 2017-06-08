from time import time
from random import sample

from heavyhitter import *

def randfill(data):
  return sample(list(range(len(data))), len(data))

def hf(x):
  return x

if __name__ == "__main__":
  sketch = HeavyHitter(1024, hf)

  dataDom = xrange(100000)
  data = [ 0 for i in dataDom ]

  numOps = 0

  time_constraint = True
  FIVE_MINUTES = 5
  aggregatetime = 0

  while( time_constraint ):

    data = randfill(data)
    ops_start = time()

    [ sketch.update(i, 1) for i in data ]

    ops_stop = time()
    aggregatetime += (ops_stop - ops_start);
    numOps+=1;
    (m, s) = (int(aggregatetime/60), int(aggregatetime-60*(aggregatetime/60)))
    time_constraint = (m <= FIVE_MINUTES)
    #print aggregatetime, (m, s), FIVE_MINUTES

  print(numOps, (m, s))

