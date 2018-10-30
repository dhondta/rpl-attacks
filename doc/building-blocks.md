This section details how to build new building blocks for making attacks (by defining the building blocks to be used in the simulations).

!!! info "New building blocks"
    
    Do not hesitate to submit your new building blocks via a Pull Request for integration in *RPL Attacks Framework* !

-----

## Basics

Building blocks are made in the JSON file located at `[RPL_ATTACKS_FRAMEWORK]/templates/building-blocks.json`.

The sample JSON provided in `[RPL_ATTACKS_FRAMEWORK]/templates/experiments.json` is already documented but some principles should be kept in mind, especially the "*levels of complexity*" that should be considered to get a building block work.

* The building blocks are only applicable to **malicious motes** (`malicious-root.c` and `malicious-sensor.c` source files can be found in `[RPL_ATTACKS_FRAMEWORK]/experiment/motes/` but are not aimed to be directly edited as it is performed by the framework through the building blocks).
* Always keep in mind that Contiki is a build system, thus relying on C code and Makefile's. When writing a mote and altering its working at the RPL-level, some settings can be made directly in the mote's C file but some settings/changes can also be made directly in the Contiki sources themselves. Hence, there are several ways to create building blocks such that malicious motes can be built with different features.

!!! warning "Contiki code change/restore"
        
    Both altering a mote file or altering Contiki are possible in an automated way with this framework. This simply performs moves of code files or replacements in source files before compiling, then restoring Contiki state after the motes are compiled. Unless there is a bug, RPL Attacks Framework does modify Contiki while making motes but restores it afterwards.

!!! tip "Using an external `rpl` library"
    
    Note that using an alternative ContikiRPL library is done through an `ext_lib` parameter in a JSON of an experiment, not in building blocks.

**RPL-related RFC References**: 6206, 6550

-----

## Tuning

**Altering constants**

This is about altering **RPL configuration constants** and therefore, if choosing this way to make a building block, the altered constant **MUST** start with `RPL_CONF_...` like in the example below.

```json
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

**Altering code**

Another way to tune a mote is to perform a **line replacement**, like in the example below. Just use the targeted file as the key and a tuple with the old and the new line.

```json
"...": {
 "rpl-icmp6.c": ["dag->version;", "dag->version++;"]
}
```

If you want to **replace several lines for a same source file**, use a list, like in the example below.

```json
"...": {
 "rpl-private.h": [
    ["#define RPL_MAX_RANKINC             (7 * RPL_MIN_HOPRANKINC)", "#define RPL_MAX_RANKINC 0"],
    ["#define INFINITE_RANK                   0xffff", "#define INFINITE_RANK 256"]
  ],
}
```

If you want to **remove a line**, use `null` as the new line, like in the example below.

```json
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

!!! tip "Line replacement based on regex"

    The line to be replaced (in the example above: `"dag->version;"`) could be a regular expression.
    
    Beware that if the line to be replaced appears several times, it will be replaced for each found instance.

-----

## Creation Process

Building blocks will often contain a mix of several ways to alter the code.

Creating a building block can always be processed according to the following process:

![Building-block Creation Process](imgs/bb-creation-process.png)

The tarting point is the **attack** you want to implement. This could be either a new or existent attack.

The ending point is then the new **building block**, that is, the key-value pair to be added to the `building-blocks.json`.

**1. Decompose**

Decompose your attack according to ContikiRPL, that is, identifying where the attack should impact the workflow of the particular implementation of RPL in Contiki.

**2. Identify**

Identify the constants to be tuned (as shown in section *1. Making building blocks -- Altering constants*) and the lines of code to be replaced (as shown in section *1. Making building blocks -- Altering code*).

**3. Write**

Write the building block in the JSON format like presented in the examples provided in section *2. Real Examples*.

**4. Test**

Test your new building block by running multiple simulations and reviewing the results to determine if it provides what is expected.

-----

## Real Examples

**Increased Version**

This attack can be simply simulated by using a malicious mote that increases the DAG version when receiving a DIO message and then sends a new (poisoned) DIO message to its neighbours, forcing a DAG recomputation. By this mechanism, it is easy to find the line with `dag->version;` in `rpl-icmp6.c` such that simply adding a `++` will increase the DAG version by 1 and thus implement the attack.

The building block is then :

```json
...
  "increased-version": {
    "rpl-icmp6.c": ["dag->version;", "dag->version++;"]
  }
...
```

**Hello Flood**

This attack consists in repeatedly sending DIS messages to neighbours such that they will consume their power. The malicious could then immediately start sending DIS messages with a short interval of time, hence some RPL configuration constants, `RPL_CONF_DIS_START_DELAY` and `RPL_CONF_DIS_INTERVAL`, could be set to a low value. There only remains to find the place where DIS messages are triggered, that is, `rpl-timers.c`, and to add the triggering of a bunch of DIS messages.

For example, the building block can be the following :

```json
...
  "hello-flood": {
    "RPL_CONF_DIS_INTERVAL": 0,
    "RPL_CONF_DIS_START_DELAY": 0,
    "rpl-timers.c": ["next_dis++;", "next_dis++; int i=0; while (i<20) {i++; dis_output(NULL);}"]
  }
...
```
 
**Decreased Rank**

> **Credit**: Many thanks to [Nicolas Müller](https://github.com/mueller91), for documenting this building block and also providing a few improvements to some core modules of the framework.

This attack consists of attracting traffic by advertising a low rank. This building block is made the following way:
- Set `RPL_CONF_MIN_HOPRANKINC` to 0. MinHopRankIncrease is the minimum increase in Rank between a node and any of its DODAG parents.
- Set `RPL_MAX_RANKINC` to 0, instead of `7 * RPL_MIN_HOPRANKINC`. Thus, our malicious node will now advertise the parent's rank, incremented by any value between the min and max rank increase values, both of which we just set to 0. Thus, it'll advertise the same rank as its parent.
- Set `INFINITE_RANK` to 256, which will limit the node's rank to no more than 256 (which is comparatively low).
- Remove the function call to `rpl_recalculate_ranks`, which normally is called periodically and is responsible to remove parents whose rank is lower than you own. Since we artificially limit our rank to 256, we must make sure not to drop parents with a larger rank, since this would isolate us.
 

```json
...
"decreased-rank": {
    "RPL_CONF_MIN_HOPRANKINC": 0,
    "rpl-private.h": [
      ["#define RPL_MAX_RANKINC             (7 * RPL_MIN_HOPRANKINC)", "#define RPL_MAX_RANKINC 0"],
      ["#define INFINITE_RANK                   0xffff", "#define INFINITE_RANK 256"]
    ],
    "rpl-timers.c": ["rpl_recalculate_ranks();", null]
  }
...
```

