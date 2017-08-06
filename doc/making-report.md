# How to make and fine-tune a simulation report ?

## 1. Run the experiment/campaign

With the interactive console:
 
 ```
 user@instant-contiki:rpl-attacks>> run_all sample-attacks
 ```

Or with Fabric:

 ```
 ../rpl-attacks$ fab run_all:test-campaign
 ```
 
 When the processing will be done, a first PDF report will be generated and available in each related experiment folder.

## 2. Fine-tune the report(s)

In each experiment folder, edit `report.md`. Especially,

- Insert your comments for each result in the text areas provided for this purpose
- Mix Markdown and HTML to improve the layout as desired

When done, re-generate the report in the interactive console:

 ```
 user@instant-contiki:rpl-attacks>> report my-experiment
 ```

Or with Fabric:

 ```
 ../rpl-attacks$ fab report:my-experiment
 ```

