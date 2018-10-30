This section shows how to use the framework for making simulations and campaigns of simulation.

## Quick Start (using the console)

1. Open the console (you should see something like in the following screenshot)

        rpl-attacks$ fab console

    or

        rpl-attacks$ python main.py

    or

        rpl-attacks$ python3 main.py

    ![RPL Attacks Framework console](imgs/rpl-attacks.png)

2. Create a campaign of simulations

        user@instant-contiki:rpl-attacks>> prepare sample-attacks

3. Go to your experiments folder (default: `~/Experiments`) and edit your new `sample-attacks.json` to suit your needs

    See [*How to create a campaign of simulations ?*](campaigns.md) for more information.

4. Make the simulations

        user@instant-contiki:rpl-attacks>> make_all sample-attacks

5. Run the simulations (multi-processed)

        user@instant-contiki:rpl-attacks>> run_all sample-attacks

    !!! tip "Behind a proxy ?"

        You can type ``status`` during ``make_all`` and ``run_all`` processing for getting the status of pending tasks.

6. Once tasks are in status ``SUCCESS`` in the status tables (visible by typing ``status``), just go to the experiment's ``results`` folders to get pictures and logs of the simulations. The related paths are the followings :

        [EXPERIMENTS_FOLDER]/[experiment_name]/without-malicious/results/
        [EXPERIMENTS_FOLDER]/[experiment_name]/with-malicious/results/


## Quick Start (using `fabric`)

1. Create a simulation campaign file from the template

        rpl-attacks$ fab prepare:test-campaign

2. Edit the simulation campaign file to suit your needs

3. Create the simulations

        rpl-attacks$ fab make_all:test-campaign

4. Run the simulations (not multi-processed)

        rpl-attacks$ fab run_all:test-campaign

5. Once done, just go to the experiment's ``results`` folders to get pictures and logs of the simulations. The related paths are the followings :

        [EXPERIMENTS_FOLDER]/[experiment_name]/without-malicious/results/
        [EXPERIMENTS_FOLDER]/[experiment_name]/with-malicious/results/


## Demonstration

Open the console like before and type:

        user@instant-contiki:rpl-attacks>> demo

Or simply launch the `demo` command with Fabric:

        rpl-attacks$ fab demo

