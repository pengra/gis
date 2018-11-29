# Initial Builder

A simple tool to build initial graphs for walking.

![command](https://imgur.com/mDXu8y2.png)

![example](https://imgur.com/mkP2DqI.png)

Running `buildmap/ -h` will return the following output:

```txt
usage: [-h] [-pieces PIECES] [-v V] state {block,county,precinct} output

A tool that takes in a state and splits it up into n pieces. Piece granularity
is defined by the user. VERSION: 0.01

positional arguments:
  state                 A state code (such as 53_WASHINGTON).
  {block,county,precinct}
                        How large the initial chunks should be.
  output                Name of file to output.

optional arguments:
  -h, --help            show this help message and exit
  -pieces PIECES        Number of pieces to split the state into. Pass nothing
                        to maintain pieces defined by state set.
  -v V                  Execute with output
```

## Note: Tool as a Service

I noticed that when on a non-unix OS, setting up an environment so that `GeoPandas`, `fiona`, etc can run is actually quite tedious.
On top that, the process can take a while on slower computers (and any laptop).
For this reason, I've made this tool into a service that can be used @ [data.pengra.io/state_gis](https://data.pengra.io/state_gis/).
Pass in the parameters listed in the `help` listed above as `GET` data.