This section explains how to install the framework and how to tune its configuration.

-----

## System & Software Requirements

This framework was tested on an [**InstantContiki**](https://sourceforge.net/projects/contiki/files/Instant%20Contiki/) appliance (that is, an Ubuntu 14.04 ; the latest version is 3.0). Also, the Vagrant box is based on Ubuntu 16.04. It was tested with **Python 2 and 3**.

!!! danger "Using InstantContiki"
    
    This appliance relies on Ubuntu 14.04, that is, an outdated version of Ubuntu. As a consequence, it has many known vulnerabilities that won't be fixed that make such a system a great target for hackers. So, it is advised to keep it network-connected only during the installation procedure and then to disable network interfaces in the settings of the virtual machine. Alos, it is strongly advised not to use it for any other purpose than research with RPL Attacks Framework and not to set an account password already used on another system.

As it can be seen in the [*Manual Installation*](#manual-installation) hereafter, the following software products are prerequisites (non-exhaustive list) for running the framework:

- [Contiki OS](https://github.com/contiki-os/contiki)
- [OpenJDK](https://openjdk.java.net/install/)
- [GCC Compiler for MSP430 Microcontrollers](https://www.ti.com/tool/MSP430-GCC-OPENSOURCE)
- [Python Numpy](https://numpy.org/)
- [Python Scipy](https://www.scipy.org/)
- Various other Unix libraries

!!! warning "Manual Installation"
    
    If you plan not to use the provided [Vagrant box](https://app.vagrantup.com/dhondta/boxes/rpl-attacks) (e.g. if you would like to use the project on Google Colab), please carefully read the [*Manual Installation*](#manual-installation) procedure hereafter. Otherwise, you may experience various errors due to missing components/files.
    
    Also, if you manually install [Contiki OS](https://github.com/contiki-os/contiki) in a folder other than "`~/contiki`", do not forget to follow the steps of the [*Non-Standard Configuration*](#non-standard-configuration) section.

-----

## Manual Installation

**This section only applies if you do not use the Vagrant box.**

**1. Clone the repository**

```shell-session
$ git clone https://github.com/dhondta/rpl-attacks.git
```
 
If not using [InstantContiki](https://sourceforge.net/projects/contiki/files/Instant%20Contiki/) appliance, also clone the [repository of Contiki](https://github.com/contiki-os/contiki) :

```shell-session
$ git clone https://github.com/contiki-os/contiki.git
```
     
!!! tip "Behind a proxy ?"
    
    Setting: `git config --global http.proxy http://[user]:[pwd]@[host]:[port]`
    
    Unsetting: `git config --global --unset http.proxy`
    
    Getting: `git config --global --get http.proxy`

**2. Install prerequisite software**

```shell-session
$ sudo apt-get install gfortran libopenblas-dev liblapack-dev
$ sudo apt-get install build-essential python-dev libffi-dev libssl-dev
$ sudo apt-get install libxml2-dev libxslt1-dev libjpeg8-dev zlib1g-dev
$ sudo apt-get install imagemagick libcairo2-dev libffi-dev
```

If not using [InstantContiki](https://sourceforge.net/projects/contiki/files/Instant%20Contiki/) appliance, also install :

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
rpl-attacks$ sudo apt-get install python-pip python-numpy python-scipy
rpl-attacks$ sudo pip install -r requirements.txt
```

or

```shell-session
$ cd rpl-attacks
rpl-attacks$ sudo apt-get install python3-pip python3-numpy python3-scipy
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

