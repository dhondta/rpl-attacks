This section explains how to install the framework and how to tune its configuration.

-----

## System Requirements

This framework was tested on an **InstantContiki** appliance (that is, an Ubuntu 14.04).

It was tested with **Python 2 and 3**.

-----

## Manual Installation

**This section only applies if did not followed the previous section.**

!!! warning "Important Note"

    For more ease, it is advised to download and deploy [InstantContiki at Sourceforge.net](https://sourceforge.net/projects/contiki/files/Instant%20Contiki/)

**1. Clone the repository**

```shell-session
$ git clone https://github.com/dhondta/rpl-attacks.git
```
 
If not using InstantContiki appliance, also clone the [repository of Contiki](https://github.com/contiki-os/contiki) :

```shell-session
$ git clone https://github.com/contiki-os/contiki.git
```
     
!!! tip "Behind a proxy ?"
    
    Setting: `git config --global http.proxy http://[user]:[pwd]@[host]:[port]`
    
    Unsetting: `git config --global --unset http.proxy`
    
    Getting: `git config --global --get http.proxy`

**2. Install system requirements**

```shell-session
$ sudo apt-get install gfortran libopenblas-dev liblapack-dev
$ sudo apt-get install build-essential python-dev libffi-dev libssl-dev
$ sudo apt-get install python-numpy python-scipy
$ sudo apt-get install libxml2-dev libxslt1-dev libjpeg8-dev zlib1g-dev
$ sudo apt-get install imagemagick libcairo2-dev libffi-dev
```

If not using InstantContiki appliance, also install :

```shell-session
$ sudo apt-get install binutils-msp430 gcc-msp430 msp430-libc msp430mcu mspdebug
$ sudo apt-get install binutils-avr gcc-avr gdb-avr avr-libc avrdude
$ sudo apt-get install openjdk-7-jdk openjdk-7-jre ant
$ sudo apt-get install libncurses5-dev lib32ncurses5
```

!!! tip "Behind a proxy ?"

    Do not forget to configure your Network system settings (or manually edit `/etc/apt/apt.conf`).

**3. Install Python requirements**

```shell-session
$ cd rpl-attacks
rpl-attacks$ sudo apt-get install python-pip
rpl-attacks$ sudo pip install -r requirements.txt
```

or

```shell-session
$ cd rpl-attacks
rpl-attacks$ sudo apt-get install python3-pip
rpl-attacks$ sudo pip3 install -r requirements.txt
```

!!! tip "Behind a proxy ?"

    Do not forget to add option `--proxy=http://[user]:[pwd]@[host]:[port]` to your pip command.
     
**4. Setup dependencies and test the framework**

```shell-session
rpl-attacks$ fab setup
rpl-attacks$ fab test
```

-----

## Non-Standard Configuration

**This section only applies if you want to tune Contiki's source folder and/or your experiments folder.**

Create a default configuration file

```shell-session
rpl-attacks$ fab config
```

or create a configuration file with your own parameters (respectively, *contiki_folder* and *experiments_folder*)

```shell-session
rpl-attacks$ fab config:/opt/contiki,~/simulations
```

Parameters :

- `contiki_folder`: the path to your contiki installation

>  [default: `~/contiki`]

- `experiments_folder`: the path to your experiments folder

>  [default: `~/Experiments`]

These parameters can be later tuned by editing ``~/.rpl-attacks.conf``. These are written in a section named "RPL Attacks Framework Configuration".

Example configuration file :

```cfg
[RPL Attacks Framework Configuration]
contiki_folder = /opt/contiki
experiments_folder = ~/simulations
```
