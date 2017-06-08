all:
	chpl driver-hh.chpl -o driver-hh
	chpl driver-hll.chpl -o driver-hll
	chpl driver-quant.chpl -o driver-quant
	chpl driver-sampling.chpl -o driver-sampling
	chpl driver-theta.chpl -o driver-theta
	chpl --fast driver-hh.chpl -o driver-hh-fast
	chpl --fast driver-hll.chpl -o driver-hll-fast
	chpl --fast driver-quant.chpl -o driver-quant-fast
	chpl --fast driver-sampling.chpl -o driver-sampling-fast
	chpl --fast driver-theta.chpl -o driver-theta-fast

