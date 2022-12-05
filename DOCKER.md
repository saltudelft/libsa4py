# Docker instructions for libsa4py process (with pyre option)


This README file includes the instructions for libsapy data prepocessing process for pyre option

[//]: # (> [name= Lang Feng])

[//]: # (> [time=Wed, Nov 16, 2022 9:51 AM])


## docker build
```
docker build -t libsa4py .
```

## docker run
```
docker run --platform linux/amd64 -it -v [source]:/data/source -v [result]:/data/results libsa4py bash 
```
> `[source]` refers the location for the dataset in the local machine
> 
> `[result]` refers the location for the dataset in the local machine

[//]: # ()
[//]: # (### cd to data folder and start pyre && watchman)

[//]: # (```)

[//]: # (cd data && ls)

[//]: # (```)

[//]: # (the output should be `results  source`)

[//]: # (#### pyre init )

[//]: # (```)

[//]: # (pyre init)

[//]: # (```)

[//]: # (**--interations:**)

[//]: # (##### Also initialize watchman in the current directory? [Y/n] `Y`)

[//]: # (##### Unable to locate typeshed, please enter its root:  `/pyre-check/stubs/typeshed/typeshed-master`)

[//]: # (##### Which directory&#40;ies&#41; should pyre analyze? &#40;Default: `.`&#41;:  `.`)

[//]: # ()
[//]: # (#### start pyre)

[//]: # (```)

[//]: # (pyre)

[//]: # (```)



<!-- docker run --platform linux/amd64 -it -v /Users/fenglang/Desktop/libsa4py/dataset:/data/source -v /Users/fenglang/Desktop/libsa4py/processedprojects:/data/results libsa4py bash  -->

[//]: # (### make changes to the libsapy `pipiline` as well as `pyre utils`)

[//]: # (```)

[//]: # (cd /libsa4py/libsa4py)

[//]: # (```)

[//]: # (#### modify `cst_pipeline`)

[//]: # ()
[//]: # ()
[//]: # (#### modify `pyre.py`)


## run libsa4py with pyre options
```
cd data
libsa4py process --p source --o results --pyre
```
