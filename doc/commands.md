This section explains each command included in the console of the framework.

Commands are used by typing **``fab [command here]``** (e.g. ``fab launch:hello-flood``) or in the framework's console (e.g. ``launch hello-flood``).

## Maintenance

- **`config`**`[contiki_folder, experiments_folder`]

> This will create a configuration file with the given parameters at `~/.rpl-attacks.conf`.
>
>  `contiki_folder`: path to Contiki installation [default: ~/contiki]
>
>  `experiments_folder`: path to your experiments [default: Experiments]

- **`list`**`type-of-item`

> This will list all existing items of the specified type from the experiment folder.
>
>  `type-of-item`: `experiments` or `campaigns`

- **`setup`**

> This will setup Contiki, Cooja and upgrade `msp430-gcc` for RPL Attacks.

- **`status`**

> This will show the status of current multi-processed tasks.

- **`test`**

> This will test the framework.

- **`update`**

> This will attempt to update Git repositories of Contiki-OS and RPL Attacks Framework.

- **`versions`**

> This will display the versions of Contiki-OS and RPL Attacks Framework.


## Simulation

- **`clean`**`name`

> This will clean the simulation directory named 'name'.

- **`cooja`**`name[, with-malicious-mote]`

> This will open Cooja and load simulation named 'name' in its version with or without the malicious mote.
>
>  `with-malicious-mote`: flag for starting the simulation with/without the malicious mote [default: false]

- **`make`**`name[, n, ...]`

> This will create a simulation named 'name' with specified parameters and also build all firmwares from ``root.c``, ``sensor.c`` and ``malicious.c`` templates with the specified target mote type. This can alternatively make the malicious mote with an external library by providing its path.
>
>  `n`: number of sensors (excluding the root and malicious motes)
>
>  `duration`: simulation duration in seconds
>
>  `title`: simulation title
>
>  `goal`: simulation goal (displayed in the Notes pane)
>
>  `notes`: simulation notes (appended behind the goal in the Notes pane)
>
>  `min_range`: malicious mote's maximum range from the root
>
>  `tx_range`: transmission range
>
>  `int_range`: interference range
>
>  `area_side`: side of the square area of the WSN
>
>  `mtype_root`: root mote type
>
>  `mtype_sensor`: sensor mote type
>
>  `mtype_malicious`: malicious mote type
>
>  `malicious_target`: external RPL library for building the malicious mote
>
>  `blocks`: building blocks for building the malicious mote, as defined in `./templates/building-blocks.json`
>
>  `ext_lib`: external RPL library for building the malicious mote
>
>  `wsn_gen_algo`: WSN topology generation algorithm

- **`report`**`name[, theme]`

> This will make a PDF report from the `report.md` template contained in an experiment.
>
>  `theme`: CSS file for generating the PDF report (with Weasyprint) ; this can be an absolute path or one of the CSS files available in the templates folder in the `report` subfolder.

- **`run`**`name`

> This will execute the given simulation, parse log files, generate the results and finally generate a PDF report based on the default CSS theme (GitHub).


## Campaign

- **`demo`**

> This will process (copy, `make_all` then `run_all`) the campaign file named 'rpl-attacks.json' contained in the 'examples' folder of the framework.

- **`drop`**`simulation-campaign-json-file`

> This will remove the campaign file named 'simulation-campaign-json-file'.

- **`make_all`**`simulation-campaign-json-file`

> This will generate a campaign of simulations from a JSON file.

- **`prepare`**`simulation-campaign-json-file`

> This will generate a campaign JSON file from the template located at `./templates/experiments.json`.

- **`remake_all`**`simulation-campaign-json-file`

> This will re-generate malicious motes for a campaign of simulations from the selected malicious mote template (which can then be modified to refine only the malicious mote without re-generating the entire campaign).

- **`run_all`**`simulation-campaign-json-file`

> This will run the entire simulation campaign.


## Build

- **`build`**`name`

> This will the malicious mote from the simulation directory named 'name' and upload it to the target hardware.

