# scalastrap


A harness for testing, debugging and profiling the Scala compiler.

Setup:

```
cd <WORKSPACE>
git clone https://github.com/VirtusLab/scalastrap.git
git clone -b 2.13.x-parallelize https://github.com/rorygraves/scalac_perf.git

cd <WORKSPACE>/scalac_perf
sbt dist/mkPack
```

Usage:

```
cd <WORKSPACE>/scalastrap
./run.py -s <WORKSPACE>/scalac_perf/build/pack/ -f dump.jfr -- -Ystatistics
```

Also `./run.py -h` gives information about additional possible parameters.
