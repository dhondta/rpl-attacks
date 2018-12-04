<center> <h1>Simulation Report</h1> </center>

## {{ title }}

### 1. Introduction

**Goal**: {{ goal if goal|trim != '' else '<span class="red">Not mentioned</span>' }}
{% if notes %}{{ notes }}{% endif %}

### 2. Configuration

#### Wireless Sensor Network

The simulation lasts {{ duration }} seconds and is {% if repeat == 1 %}not repeated{% else %}is repeated {{ n - 1 }} times{% endif %}.

The WSN contains:

- 1 root node of type *{{ mtype_root }}* built upon a *{{ target|upper }}*
- {{ n }} sensors of type *{{ mtype_sensor }}* built upon a *{{ target|upper }}*
- 1 malicious mote of type *{{ mtype_malicious }}* built upon a *{{ malicious_target|upper }}*

The sensors are spread across an area of {{ area_side }} meters side and centered around the root node at a minimum distance of {{ min_range }} meters and a maximum distance of {{ max_range }} meters. They have a maximum transmission range of {{ tx_range }} meters and a maximum interference range of {{ int_range }} meters.

The WSN configuration is depicted in Figures 1 and 2:

<div class="left">
  <figure>
    <img src="without-malicious/results/wsn-without-malicious_start.png" alt="ERROR">
    <figcaption>Fig 1 - WSN configuration without the malicious mote before starting the simulation.</figcaption>
  </figure> 
</div>
<div class="right">
  <figure>
    <img src="with-malicious/results/wsn-with-malicious_start.png" alt="ERROR">
    <figcaption>Fig 2 - WSN configuration with the malicious mote before starting the simulation.</figcaption>
  </figure> 
</div>

#### Attack

The attack is composed of the following building blocks:
{% if blocks|length > 0 %}
{% for block in blocks %}
- {{ block}}{% endfor %}
{% else %}
<span class="red">No building block specified.</span>
{% endif %}
{% if ext_lib %}
The malicious mote is built with a custom RPL library located at {{ ext_lib }}.
{% endif %}

### 3. Results

In this section, the pictures on the left side corresponds to the results for the simulation without the malicious mote. These on the left are for the simulation with the malicious mote.

#### Resulting DODAG

The resulting Destination Oriented Directed Acyclic Graph (DODAG) is depicted in the following pictures:

<div class="left">
  <figure>
    <img src="without-malicious/results/dodag.png" alt="ERROR">
    <figcaption>Fig 3 - Final DODAG for the simulation without the malicious mote.</figcaption>
  </figure> 
</div><div class="right">
  <figure>
    <img src="with-malicious/results/dodag.png" alt="ERROR">
    <figcaption>Fig 4 - Final DODAG for the simulation with the malicious mote.</figcaption>
  </figure> 
</div>

<p class="textbox">
Insert your comments here.
</p>

> **Important note**: The resulting DODAG's could be not representative if the duration is not long enough. Ensure that it is set appropriately.

#### Power Tracking Analysis

The power tracking is depicted in the following pictures:

<div class="left">
  <figure>
    <img src="without-malicious/results/powertracking.png" alt="ERROR">
    <figcaption>Fig 5 - Power tracking histogram for the simulation without the malicious mote.</figcaption>
  </figure> 
</div>
<div class="right">
  <figure>
    <img src="with-malicious/results/powertracking.png" alt="ERROR">
    <figcaption>Fig 6 - Power tracking histogram for the simulation with the malicious mote.</figcaption>
  </figure> 
</div>

<p class="textbox">
Insert your comments here.
</p>

