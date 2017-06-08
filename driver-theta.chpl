use Time;
use Random;
use theta;

proc randfill(data, sz) {
  //var r = new RandomStream(int, sz);
  //r.fill(data);
  fillRandom(data);
  return data;
}

proc hf(x:int, seed:int) :int {
  return x;
}

proc main() {

  var k = 1024;
  var sketch = createThetaSketch(int, hf, k);

  var dataDom = {0..100000};
  var data : [dataDom] int;

  var numOps = 0;

  var time_constraint = true;
  var FIVE_MINUTES = 5.0;
  var aggregatetime = 0.0;

  while( time_constraint ) {

    data = randfill(data, dataDom.high);
    var timer = new Timer();
    timer.start();
    for i in data {
      sketch.update(i);
    }
    timer.stop();

    aggregatetime += timer.elapsed(); //(ops_stop - ops_start);
    numOps+=1;
    var m = (aggregatetime/60.0);
    var s = (((aggregatetime-60.0)*(aggregatetime/60.0)));
    //writeln( (m,s) );

    time_constraint = (m <= FIVE_MINUTES);
    //writeln(numOps, (m,s), time_constraint, aggregatetime);
  }

  writeln((numOps, aggregatetime));
}
