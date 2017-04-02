# Simulation Report

## {{ title }}

### 1. Introduction

**Goal**: {{ goal }}
{% if notes %}
{{ notes }}
{% endif %}
### 2. Configuration

#### Wireless Sensor Network

The simulation lasts {{ duration }} seconds and is {% if repeat == 1 %}not repeated{% else %}is repeated {{ n - 1 }} times{% endif %}.

The WSN contains:
- 1 root node of type {{ mtype_root }} built upon a {{ target }}
- {{ n }} sensors of type {{ mtype_sensor }} built upon a {{ target }}
- 1 malicious mote of type {{ mtype_malicious }} built upon a {{ malicious_target }}

The sensors are spread across an area of {{ area_side }} meters side and centered around the root node at a minimum distance of {{ min_range }} meters and a maximum distance of {{ max_range }} meters. They have a maximum transmission range of {{ tx_range }} meters and a maximum interference range of {{ int_range }} meters. The WSN configuration is depicted in the following figure:

![](without-malicious/results/wsn-without-malicious_start.png "WSN configuration without the malicious mote before starting the simulation")

#### Attack Description

The attack is composed of the following building blocks:
{% for block in blocks %}- {{ block}}{% endfor %}
{% if ext_lib %}
The malicious mote is built with a custom RPL library located at {{ ext_lib }}.
{% endif %}
The WSN configuration including the malicious mote is depicted in the following figure:

![](with-malicious/results/wsn-with-malicious_start.png "WSN configuration with the malicious mote before starting the simulation")

### 3. Results

In this section, the pictures on the left side corresponds to the results for the simulation without the malicious mote. These on the left are for the simulation with the malicious mote.

#### Resulting DODAG

The resulting Destination Oriented Directed Acyclic Graph (DODAG) is depicted in the following pictures:

<table border="0">
<tr>
<td>![](without-malicious/results/dodag.png "Final DODAG for the simulation without the malicious mote")</td>
<td>![](with-malicious/results/dodag.png "Final DODAG for the simulation with the malicious mote")</td>
</tr>
</table>

> **Important note**: The resulting DODAG's could be not representative if the duration is not long enough. Ensure that it is set appropriately.

#### Power Tracking Analysis

The power tracking is depicted in the following pictures:

<table border="0">
<tr>
<td>![](without-malicious/results/powertracking.png "Power tracking histogram for the simulation without the malicious mote")</td>
<td>![](with-malicious/results/powertracking.png "Power tracking histogram for the simulation with the malicious mote")</td>
</tr>
</table>
