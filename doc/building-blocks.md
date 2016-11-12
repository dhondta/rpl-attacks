# How to make new building blocks ?

## 1. Making building blocks

Building blocks are made in the JSON file located at `[RPL_ATTACKS_FRAMEWORK]/templates/building-blocks.json`.

The sample JSON provided in `[RPL_ATTACKS_FRAMEWORK]/templates/experiments.json` is already documented but some principles should be kept in mind, especially the "*levels of complexity*" that should be considered to get a building block work.

* The building blocks are only applicable to **malicious motes** (`malicious-root.c` and `malicious-sensor.c` source files can be found in `[RPL_ATTACKS_FRAMEWORK]/experiment/motes/` but are not aimed to be directly edited as it is performed by the framework through the building blocks).
* Always keep in mind that Contiki is a build system, thus relying on C code and Makefile's. When writing a mote and altering its working at the RPL-level, some settings can be made directly in the mote's C file but some settings/changes can also be made directly in the Contiki sources themselves. Hence, there are several ways to create building blocks such that malicious motes can be built with different features.

> Both altering a mote file or altering Contiki are possible in an automated way with this framework. This simply performs moves of code files or replacements in source files before compiling, then restoring Contiki state after the motes are compiled. Unless there is a bug, RPL Attacks Framework does modify Contiki while making motes but restores it afterwards.
> 
> Note that using an alternative ContikiRPL library is done through an `ext_lib` parameter in a JSON of an experiment, not in building blocks.

### Altering constants

This is about altering **RPL configuration constants** and therefore, if choosing this way to make a building block, the altered constant **MUST** start with `RPL_CONF_...` like in the example below.

 ```
 "...": {
   "RPL_CONF_DIO_INTERVAL_MIN": 1
 }
 ```

Configurable constants can be found in `~/Contiki/core/net/rpl/rpl-conf.h` :

 **Constant** | **Default Value** | **Description**
 --- | --- | ---
 `RPL_CONF_STATS` | `0` | Enable RPL statistics
 `RPL_CONF_DAG_MC` | `0` | DAG Metric Container Object Type
 `RPL_CONF_DEFAULT_INSTANCE` | `0x1e` | DAG instance in which the WSN should participate by default
 `RPL_CONF_LEAF_ONLY` | `0` | Indicates if the mote must stay as a leaf or not
 `RPL_CONF_MAX_INSTANCES` | `1` | Maximum of concurrent RPL instances
 `RPL_CONF_MAX_DAG_PER_INSTANCE` | `2` | Maximum number of DAGs within an instance
 `RPL_CONF_DAO_SPECIFY_DAG` | `1` | Default DAG that should be advertised in DAO messages (depends on `RPL_MAX_DAG_PER_INSTANCE`)
 `RPL_CONF_DEFAULT_ROUTE_INFINITE_LIFETIME` | `0` | RPL Default route lifetime
 `RPL_CONF_DIO_INTERVAL_MIN` | `12` | DIO interval (n) ; 2^n ms
 `RPL_CONF_DIO_INTERVAL_DOUBLINGS` | `8` | Maximum amount of timer doublings (default gives 2^(12+8) ms = 1048.576 s)
 `RPL_CONF_DIO_REDUNDANCY` | `10` | DIO redundancy
 `RPL_CONF_DEFAULT_LIFETIME_UNIT` | `0xffff` | Granularity of time used in RPL lifetime value in seconds
 `RPL_CONF_DEFAULT_LIFETIME` | `0xff` | Default route lifetime as a multiple of the lifetime unit
 `RPL_CONF_PREFERENCE` | `0` | DAG preference field
 `RPL_CONF_INSERT_HBH_OPTION` | `1` | RPL Hop-by-Hop extension header into packets originating from the mote
 `RPL_CONF_WITH_PROBING` | `1` | Enable RPL probing
 `RPL_CONF_PROBING_INTERVAL` | `120 * CLOCK_SECOND` | RPL probing interval
 `RPL_CONF_PROBING_EXPIRATION_TIME` | `600 * CLOCK_SECOND` | RPL probing expiration time
 `RPL_CONF_OF` | ETX (see `rpl-mrhof.c`) | Name of an rpl_of object linked into the system image, e.g., `rpl_of0`
 `RPL_CONF_INIT_LINK_METRIC` | `2` | Initial metric attributed to a link when the ETX is unknown
 `RPL_CONF_PROBING_SELECT_FUNC` | `get_probing_target(dag)` (see `rpl-timers.c`) | Function used to select the next parent to be probed
 `RPL_CONF_PROBING_SEND_FUNC` | With DIO | Function used to send RPL probes (with DIO or DIS)
 `RPL_CONF_PROBING_DELAY_FUNC` | `RPL_PROBING_INTERVAL/2 + random_rand() % RPL_PROBING_INTERVAL` | Function used to calculate next RPL probing interval

**RFC References**: 6206, 6550

### Altering code

Another way to tune a mote is to perform a **line replacement**, like in the example below. Just use the targeted file as the key and a tuple with the old and the new line.

 ```
 "...": {
   "rpl-icmp6.c": ["dag->version;", "dag->version++;"]
 }
 ```

If you want to **replace several lines for a same source file**, use a list, like in the example below.

 ```
 "...": {
   "rpl-private.h": [
      ["#define RPL_MAX_RANKINC             (7 * RPL_MIN_HOPRANKINC)", "#define RPL_MAX_RANKINC 0"],
      ["#define INFINITE_RANK                   0xffff", "#define INFINITE_RANK 256"]
    ],
 }
 ```

If you want to **remove a line**, use `null` as the new line, like in the example below.

 ```
 "...": {
   "rpl-timers.c": ["rpl_recalculate_ranks();", null]
 }
 ```

The possible keys are :
- `rpl.c`
- `rpl.h`
- `rpl-conf.h`
- `rpl-dag.c`
- `rpl-dag-root.c`
- `rpl-dag-root.h`
- `rpl-ext-header.c`
- `rpl-icmp6.c`
- `rpl-mrhof.c`
- `rpl-of0.c`
- `rpl-private.h`
- `rpl-timers.c`

> Note that the line to be replaced (in the example above: `"dag->version;"`) could be a regular expression.
> 
> Beware that if the line to be replaced appears several times, it will be replaced for each found instance.

## 2. Real Examples

### Increased Version

This attack can be simply simulated by using a malicious mote that increases the DAG version when receiving a DIO message and then sends a new (poisoned) DIO message to its neighbours, forcing a DAG recomputation. By this mechanism, it is easy to find the line with `dag->version;` in `rpl-icmp6.c` such that simply adding a `++` will increase the DAG version by 1 and thus implement the attack.

The building block is then :

 ```
 ...
   "increased-version": {
     "rpl-icmp6.c": ["dag->version;", "dag->version++;"]
   }
 ...
 ```

### Hello Flood

This attack consists in repeatedly sending DIS messages to neighbours such that they will consume their power. The malicious could then immediately start sending DIS messages with a short interval of time, hence some RPL configuration constants, `RPL_CONF_DIS_START_DELAY` and `RPL_CONF_DIS_INTERVAL`, could be set to a low value. There only remains to find the place where DIS messages are triggered, that is, `rpl-timers.c`, and to add the triggering of a bunch of DIS messages.

The building block can for example be the following :

 ```
 ...
   "hello-flood": {
     "RPL_CONF_DIS_INTERVAL": 0,
     "RPL_CONF_DIS_START_DELAY": 0,
     "rpl-timers.c": ["next_dis++;", "next_dis++; int i=0; while (i<20) {i++; dis_output(NULL);}"]
   }
 ...
 ```


## 3. Building your own blocks - Methodology

Building blocks nearly always contain a mix of several ways to alter the code. Creating a build block can always be processed according to the following steps :

### 1. Select/Build an attack

### 2. Decompose the attack according to ContikiRPL

### 3. Identify constants to be tuned

### 4. Identify the workflow and find lines to be replaced

### 5. Write the building block

### 6. Test the building block
