CHIUW2017

# chpl-sketching
Sketching algorithms implemented in Chapel

[Sketch Origins](https://datasketches.github.io/docs/SketchOrigins.html):

Sketching is a relatively recent development in the theoretical field of
Stochastic Streaming Algorithms, which deals with algorithms that can extract
information from a stream of data in a single pass (sometimes called
“one-touch” processing) using various randomization techniques.

## HyperLogLog


[HyperLogLog on Wikipedia](https://en.wikipedia.org/wiki/HyperLogLog):

HyperLogLog is an algorithm for the count-distinct problem, approximating the
number of distinct elements in a multiset
...
The HyperLogLog algorithm can estimate cardinalities well beyond 10^9 with a
relative accuracy (standard error) of 2% while only using 1.5kb of memory.

[count-distinct problem on Wikipedia](https://en.wikipedia.org/wiki/Count-distinct_problem):

count-distinct problem (also known in applied mathematics as the cardinality
estimation problem) is the problem of finding the number of distinct elements
in a data stream with repeated elements.

[Cardinality Estimation for Big Data](http://druid.io/blog/2012/05/04/fast-cheap-and-98-right-cardinality-estimation-for-big-data.html):

HyperLogLog takes advantage of the randomized distribution of bits from hashing
functions in order to estimate how many things you would’ve needed to see in
order to experience a specific phenomenon.
