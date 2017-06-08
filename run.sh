#!/bin/bash
#make -f makefile

echo "chapel"
for i in `seq 1 5`; 
do
	echo "hh"
	./driver-hh
	echo "hll"
	./driver-hll
	echo "quant"
	./driver-quant
	echo "sampling"
	./driver-sampling
	echo "theta"
	./driver-theta
	echo "end"
done

echo "chapel fast"
for i in `seq 1 5`; 
do
	echo "fhh"
	./driver-hh-fast
	echo "fhll"
	./driver-hll-fast
	echo "fquant"
	./driver-quant-fast
	echo "fsampling"
	./driver-sampling-fast
	echo "ftheta"
	./driver-theta-fast
	echo "end"
done

echo "python"
for i in `seq 1 5`; 
do
	echo "pyhll"
	python2.7 driver-hll.py
	echo "pyhh"
	python2.7 driver-hh.py
	echo "pyquant"
	python2.7 driver-quant.py
	echo "pysampling"
	python2.7 driver-sampling.py
	echo "pytheta"
	python2.7 driver-theta.py
	echo "end"
done

