# Assignment 1 report - Olgierd Kasprowicz

## SBB completion

Working commit hash: `94a4f22bff3cfd7395fc15eddf8f043690d8b9e7`

![](./start.png)
![](./more-blocks.png)

## Blocktime calculations

Working commit hash: `6a94bb55619b9b0048b0971c2815abf2198af93d`

I had to make some tweaks in order to automate the testing -> see `run-timing-test`

The target is average block time of 10 seconds for 20 blocks, so 200s for total.
There is 0.5% error margin because of the measuring interval (I'm sampling the blocks every 1 second, because otherwise most of the CPU is tied in the busy-loop)

### Results

| #zeros |   time   | Δtarget |
|:------:|:--------:|:-------:|
|    2   |   2.5s   |  ~197s  |
|    3   |  9.505s  |  ~190s  |
|    4   |  87.612s |  ~112s  |
|    5   | 1653.36s |  ~1453s |

### Conclusion

Since the target_delta function has two intervals, one monotoincially decreasing and the other monotoincially increasing I conclude that no further tests are required, global minimum was found and the final parameters are:
- 4 zeros 
- 4381ms per block on average
