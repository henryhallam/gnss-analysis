# gnss-analysis

Tools for analyzing libswiftnav filters on stored GNSS data.

# Setup and install

First, you need to install [libswiftnav-python](https://github.com/swift-nav/libswiftnav-python/),
[libswiftnav](https://github.com/swift-nav/libswiftnav/), and
[pyNEX](https://github.com/swift-nav/pynex) installed. You will also probably
want [sbp_log_analysis](https://github.com/swift-nav/sbp_log_analysis) but you
really just need some of the files it creates with the `--write-hdf5` option.
These may be installed by following the directions on their respective pages.

Then you will need some more dependencies for this library. These can be
installed with

```shell
sudo pip install numpy tables pandas
```

Then the library can be installed with

```shell
sudo python setup.py install
```

# Usage

Given a JSON log file generated by `piksi_tools`, you can generate an
HDF5 file of observations, ephemerides, and single-point/RTK
solutions:

```shell
python gnss_analysis/hdf5.py -o my_file.hdf5 data/serial_link_log_20150314-190228_dl_sat_fail_test1.log.json.dat
```

```
usage: hdf5.py [-h] [-o OUTPUT] [-n NUM_RECORDS] file

Swift Nav SBP log parser.

positional arguments:
  file                  Specify the log file to use.

optional arguments:
  -h, --help            show this help message and exit
  -o OUTPUT, --output OUTPUT
                        Test results output filename.
  -n NUM_RECORDS, --num_records NUM_RECORDS
                        Number or SBP records to process.
```

With the HDF5 file, this library runs tests using the currently
installed RTK filters from the `libswiftnav` library. You can run it
with

```shell
python runner.py NAME_OF_HDF5_FILE
```

You may want to change some of the arguments in `runner.py` so that the keys
to your tables in the HDF5 file have the correct names. These will eventually
be command line arguments.

To add new analyses, write new classes whose super classes are `Analysis` and
`Report`, as detailed below. Then, before the `tester.compute()` step of
runner.py, add `tester.add_report(Foo())` if your new `Report` is `Foo`.

# Structure and Development

## Structure

This library is constructed from a few basic building blocks in
`gnss_analysis/abstract_analysis`. They are `Report`, `Analysis`, and `SITL`.
In general consider `SITL` as a function to manage a directed acyclic graph
(DAG) of analyses and reports. `Report` and `Analysis` are nodes in this graph
whose parents are `Analysis` nodes. A `Report` cannot depend on a
`Report`. `Analysis` nodes have `compute` methods their children depend on.
`Report` nodes have `report` that is spit out at the end.

Their dependencies are specified in via a `set` passed intothe `parents`
argument of their constructors.

### Analysis

`Analysis` nodes have multiple types. They can be either a summary or
(a map and/or a fold). It can be a map and a fold, but not a map and a summary,
nor a fold and a summary. (Eventually, if speed/storage is an issue and we run
out of gains to make elsewhere, I'll add a new type of `Analysis` for unstored
intermediate computations.)

Each `Analysis` must have a unique key. If two analyses share the same key, when
the second is added, it's storage settings (`keep_as_fold`, `keep_as_map`, and
`is_summary`) will be merged (via or), but the compute function will be that of the
first one added under that key.

- **Folds:**
  - A fold node is an `Analysis` with `keep_as_fold=True` in the contructor.
This flag indicates that the result of its `compute` should be stored in the
dictionary of current fold results, to be passed back in at the next data
point. It can also be stored as a map via `keep_as_map=True`.
  - A fold's `compute` function takes as arguments a data point, the
result of the `compute` function of its dependencies, the result of its
own `compute` function on the previous data point, and some `parameters`
from the `SITL`.
  - In its constructor, it takes an initial "previous result."
  - A fold can depend on other folds and maps.
  - You could do everything in a fold node, but don't. It's bad and you should
feel bad.
- **Maps:**
  - A map node is an `Analysis` with `keep_as_map=True` in the constructor.
This flag indicates that the result of its `compute` function should be stored
separately for each data point. It can also be stored as a fold via
`keep_as_fold=True`.
  - A maps's `compute` function takes as arguments a data point, the result
of the `compute` function of its dependencies, and some `parameters`
from the `SITL`. These dependencies will be input in the `current_analyses`
 argument. (It also takes the previous folds, just to have a common type
 signature, but should not use them)
  - A map can depend on folds and other maps.
- **Summaries:**
  - A summary node is an `Analysis` with `is_summary=True` in the constructor.
  - The results of a summary node's `compute` function cannot also be stored
as a map or fold.
  - A summary's `compute` function takes as arguments the whole data set,
the result of the `compute` functions of its dependencies, and some `parameters`
from the `SITL`. The map and summary dependencies will be input via the
`current_analyses` argument, and the folds will be input via the fold argument.
  - A summary can depend on folds, maps and other summaries.
  - You could do everything in a single summary node, but don't. It's bad and
you should feel bad.

### Report

`Report` nodes are the final nodes in the DAG. They act much like summary nodes,
but instead of a compute function, they have a report function.

Each `Report` must have a unique key. If two reports share the same key, only
the second will be used, but all the dependencies of the original will be
executed.

- `report` takes the same arguments as the `compute` of a summary `Analysis`
node, and some `parameters` from the `SITL`.
- `report` should return a string. This will be output from the program.
- A report can can depend on folds, maps, and summaries.

## SITL

`SITL` is the class that manages the DAG of `Report` and `Analysis`
dependencies and computations. You initialize it with a data set, an update
step which will be executed before any of the computations on each data point,
and some object to be passed to all the `Report` and `Analysis` functions. It
serves as extra parameters. The update function is useful for updating any
global states.

You add the reports you want computed to the `SITL` object via `.add_report`
and it will add any analyses necessary to compute the report. The reports are
computed via the `.compute` function.

## Development

If you want to write new reports and analyses, simply write the `Report` and
`Analysis` as desired (detailed in the "Structure" section of the README)
and add the new report to your existing `SITL` object via `.add_report(Foo())`
before the `SITL`'s `.compute()` is called. That part is intended to be nice
and simple.
