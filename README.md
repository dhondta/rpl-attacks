RPL Attacks Framework
=====================

This project is aimed to provide a simple and convenient way to generate simulations and deploy malicious motes for a Wireless Sensor Network (WSN) that uses Routing Protocol for Low-power and lossy devices (RPL) as its network layer. With this framework, it is possible to easily define campaign of simulations either redefining RPL configuration constants or using an own external RPL library.


Installation
------------

1. Clone this repository

 ```
 git clone https://github.com/dhondta/rpl-attacks.git
 ```

2. Install system requirements

 ```
 sudo apt-get install gcc-msp430 libcairo2-dev libffi-dev
 ```

3. Install Python requirements

 ```
 sudo pip install -r requirements.txt
 ```

 or

 ```
 sudo pip3 install -r requirements.txt
 ```

4. Setup Cooja

 ```
 ../rpl-attacks$ fab setup
 ```


Configuration
-------------

**This section only applies if you want to tune Contiki's source folder and/or your experiments folder.**

Create a default configuration file

 ```
 ../rpl-attacks$ fab config
 ```

or create a configuration file with your own parameters (respectively, *contiki_folder* and *experiments_folder*)

 ```
 ../rpl-attacks$ fab config:/opt/contiki,~/simulations
 ```

Parameters :

- `contiki_folder`: the path to your contiki installation

>  [default: ~/contiki]

- `experiments_fodler`: the path to your experiments folder

>  [default: ~/Experiments]

These parameters can be later tuned by editing ``~/.rpl-attacks.conf``. These are written in a section named "RPL Attacks Framework Configuration".

Example configuration file :

```
[RPL Attacks Framework Configuration]
contiki_folder = /opt/contiki
experiments_folder = ~/simulations
```


Quick Start
-----------

1. Create a simulation campaign file from the template

 ```
 ../rpl-attacks$ fab prepare
 ```

or create a simulation campaign file with a custom name

 ```
 ../rpl-attacks$ fab prepare:test-campaign
 ```

2. Edit the simulation campaign file to suit your needs

3. Create the simulations

 ```
 ../rpl-attacks$ fab make_all:test-campaign
 ```



Commands
--------

Commands are used by typing **``fab [command here]``** (e.g. ``fab launch:hello-flood``).

- **`clean`**`:name`

> This will clean the simulation directory named 'name'.

- **`config`**`[:contiki_folder, experiments_folder`]

> This will create a configuration file with the given parameters at `~/.rpl-attacks.conf`.
>
>  `contiki_folder`: path to Contiki installation [default: ~/contiki]
>
>  `experiments_folder`: path to your experiments [default: Experiments]

- **`cooja`**`:name[, with-malicious-mote]`

> This will open Cooja and load simulation named 'name' in its version with or without the malicious mote.
>
>  `with-malicious-mote`: flag for starting the simulation with/without the malicious mote [default: false]

- **`make`**`:name[, n, mtype, max_range, blocks, ext_lib, duration, title, goal, notes, target]`

> This will create a simulation named 'name' with specified parameters and also build all firmwares from ``root.c``, ``sensor.c`` and ``malicious.c`` templates with the specified target mote type. This can alternatively make the malicious mote with an external library by providing its path.
>
>  `n`: number of sensors (excluding the root and malicious motes) [default: 10]
>
>  `mtype`: malicious mote type (`root` or `sensor`) [default: `sensor`]
>
>  `max_range`: malicious mote's maximum range from the root [default:
>
>  `blocks`: building blocks for building the malicious mote, as defined in `./templates/building-blocks.json` [default: empty]
>
>  `ext_lib`: external RPL library for building the malicious mote [default empty]
>
>  `duration`: simulation duration in seconds [default: 300]
>
>  `title`: simulation title [default: empty]
>
>  `goal`: simulation goal (displayed in the Notes pane) [default: empty]
>
>  `notes`: simulation notes (appended behind the goal in the Notes pane) [default: empty]

- **`make_all`**`:simulation-campaign-json-file`

> This will generate a campaign of simulations from a JSON file formatted and execute the chain `clean`|`new`|`make` for each simulation. See ``./templates/experiments.json`` for simulation campaign JSON format.

- **`run`**`:name`

> This will execute the the given simulation, parse log files and generate the results.

- **`run_all`**`:simulation-campaign-json-file`

> This will the simulation campaign. See ``./templates/experiments.json`` for simulation campaign JSON format.

- **`setup`**

> This will setup Contiki and Cooja for RPL Attacks.


Simulation campaign
-------------------

Example JSON :

```
{
  "sinkhole": {
    "simulation": {
      "title": "Sinkhole Attack",
      "goal": "Show that the malicious node is creating another\n DODAG, preventing some motes from joining legitimate\n root's DODAG",
      "notes": "The malicious mote will use the same prefix as the\n root and prevent sensors from joining the legitimate\n DODAG",
      "number_motes": 10,
      "target": "z1",
      "duration": 120,
      "debug": true
    },
    "malicious": {
      "type": "sensor",
      "constants": {
        "RPL_CONF_MIN_HOPRANKINC": 128
      }
    }
  }
}
```

