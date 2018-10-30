This section explains how to generate a simulation report and how to fine-tune it.


## Process

**1. Run the experiment/campaign**

With the interactive console:
 
```shell-session
user@instant-contiki:rpl-attacks>> run_all sample-attacks
```

Or with Fabric:

```shell-session
rpl-attacks$ fab run_all:test-campaign
```

When the processing will be done, a first PDF report will be generated and available in each related experiment folder.

**2. Fine-tune the report(s)**

In each experiment folder, edit `report.md`. Especially,

- Insert your comments for each result in the text areas provided for this purpose
- Mix Markdown and HTML to improve the layout as desired

When done, re-generate the report in the interactive console:

```shell-session
user@instant-contiki:rpl-attacks>> report my-experiment
```

Or with Fabric:

```shell-session
rpl-attacks$ fab report:my-experiment
```

