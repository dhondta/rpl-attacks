<p align="center"><img src="https://github.com/dhondta/rpl-attacks/raw/master/doc/imgs/logo.png"></p>
<h1 align="center">RPL Attacks Framework <a href="https://twitter.com/intent/tweet?text=RPL%20Attacks%20Framework%20-%20Framework%20for%20simulating%20WSN%20with%20a%20malicious%20mote%20based%20on%20Contiki%20for%20attacking%20the%20RPL%20protocol.%0D%0Ahttps%3a%2f%2fgithub%2ecom%2fdhondta%2frpl-attacks%0D%0A&hashtags=python,simulation,framework,contiki,rpl,wsn,sensors"><img src="https://img.shields.io/badge/Tweet--lightgrey?logo=twitter&style=social" alt="Tweet" height="20"/></a></h1>
<h3 align="center">Make simulations of a WSN with a malicious mote for attacking the RPL protocol.</h3>

[![Read The Docs](https://readthedocs.org/projects/rpl-attacks/badge/?version=latest)](https://rpl-attacks.readthedocs.io/en/latest/?badge=latest)
[![Build Status](https://travis-ci.com/dhondta/rpl-attacks.svg?branch=master)](https://travis-ci.com/dhondta/rpl-attacks)
[![Requirements Status](https://requires.io/github/dhondta/rpl-attacks/requirements.svg?branch=master)](https://requires.io/github/dhondta/rpl-attacks/requirements/?branch=master)
[![Known Vulnerabilities](https://snyk.io/test/github/dhondta/rpl-attacks/badge.svg?targetFile=requirements.txt)](https://snyk.io/test/github/dhondta/rpl-attacks?targetFile=requirements.txt)
[![DOI](https://zenodo.org/badge/22624/dhondta/rpl-attacks.svg)](https://zenodo.org/badge/latestdoi/22624/dhondta/rpl-attacks)
[![Black Hat Arsenal Europe 2018](https://img.shields.io/badge/Black%20Hat%20Arsenal-EU%202018-blue.svg)](https://www.blackhat.com/eu-18/arsenal/schedule/index.html#rpl-attacks-framework-attacking-rpl-in-wsns-12671)
[![Vagrant](https://img.shields.io/badge/vagrant-1.0.0-blue.svg)](https://app.vagrantup.com/dhondta/boxes/rpl-attacks)
[![License](https://img.shields.io/badge/license-AGPLv3-lightgrey)](https://github.com/dhondta/rpl-attacks/blob/master/LICENSE)
[![Beerpay](https://img.shields.io/beerpay/hashdog/scrapfy-chrome-extension.svg)](https://beerpay.io/dhondta/rpl-attacks)
[![Donate](https://img.shields.io/badge/donate-paypal-orange.svg)](https://www.paypal.me/dhondta)


This project aims to provide a simple and convenient interface relying on [Contiki OS](https://github.com/contiki-os/contiki) to generate [Cooja simulations](https://anrg.usc.edu/contiki/index.php/Cooja_Simulator) and deploy malicious motes for a [Wireless Sensor Network (WSN)](https://en.wikipedia.org/wiki/Wireless_sensor_network) that uses [Routing Protocol for Low-power and lossy devices (RPL)](https://www.ietf.org/proceedings/94/slides/slides-94-rtgarea-2.pdf) ([RFC 6550](https://tools.ietf.org/html/rfc6550)) as its network layer.

With this framework, it is possible to easily define campaign of simulations (in JSON format) either redefining RPL configuration constants, modifying single lines from the [ContikiRPL library](https://github.com/contiki-os/contiki/tree/master/core/net/rpl) or using an own external RPL library. Moreover, experiments in a campaign can be generated either based on a same or a randomized topology for each simulation.

See the [Wiki](https://github.com/dhondta/rpl-attacks/wiki) for additional documentation.

### A few test cases made with the framework:

#### Test case 1: flooding attack

The malicious mote has 3, 7, 10 in its range                               |  Power tracking without the malicious mote                                                |  Power tracking with the malicious mote
:-------------------------------------------------------------------------:|:-----------------------------------------------------------------------------------------:|:------------------------------------------------------------------------------------:
![The malicious mote has 3, 7, 10 in its range](https://github.com/dhondta/rpl-attacks/raw/master/doc/imgs/flooding-dag.png) | ![Power tracking without the malicious mote](https://github.com/dhondta/rpl-attacks/raw/master/doc/imgs/flooding-powertracking-without.png) | ![Power tracking with the malicious mote](https://github.com/dhondta/rpl-attacks/raw/master/doc/imgs/flooding-powertracking-with.png)

#### Test case 2: versioning attack

Legitimate DODAG                                         |  Versioning attack in action (global repair)
:-------------------------------------------------------:|:-----------------------------------------------------:
![Legitimate DODAG](https://github.com/dhondta/rpl-attacks/raw/master/doc/imgs/versioning-dag-without.png) | ![Versioning attack](https://github.com/dhondta/rpl-attacks/raw/master/doc/imgs/versioning-dag-with.png)

Power tracking without the malicious mote                          |  Power tracking with the malicious mote
:-----------------------------------------------------------------:|:---------------------------------------------------------------:
![Power tracking without the malicious mote](https://github.com/dhondta/rpl-attacks/raw/master/doc/imgs/versioning-powertracking-without.png) | ![Power tracking with the malicious mote](https://github.com/dhondta/rpl-attacks/raw/master/doc/imgs/versioning-powertracking-with.png)

#### Test case 3a: blackhole attack

Legitimate DODAG                                               |  Blackhole attack in action
:-------------------------------------------------------------:|:-----------------------------------------------------------:
![Legitimate DODAG](https://github.com/dhondta/rpl-attacks/raw/master/doc/imgs/blackhole-attack-ex1-without.png) | ![Blackhole attack](https://github.com/dhondta/rpl-attacks/raw/master/doc/imgs/blackhole-attack-ex1-with.png)

#### Test case 3b: blackhole attack

Legitimate DODAG                                               |  Blackhole attack in action
:-------------------------------------------------------------:|:-----------------------------------------------------------:
![Legitimate DODAG](https://github.com/dhondta/rpl-attacks/raw/master/doc/imgs/blackhole-attack-ex2-without.png) | ![Blackhole attack](https://github.com/dhondta/rpl-attacks/raw/master/doc/imgs/blackhole-attack-ex2-with.png)


## :cd: Installation

1. Clone this repository

 ```
 $ git clone https://github.com/dhondta/rpl-attacks.git
 ```
 
 > **Behind a proxy ?**
 > 
 > Setting: `git config --global http.proxy http://[user]:[pwd]@[host]:[port]`
 > 
 > Unsetting: `git config --global --unset http.proxy`
 > 
 > Getting: `git config --global --get http.proxy`

2. Create the VM

 ```
 $ vagrant login
 [...]
 $ vagrant up
 ```
 
 > **Important notes**
 > 
 > The downloads of the Vagrant box may take a while, please be patient...
 > 
 > Also, after the creation of the VM, Vagrant may complain that the *SSH connection was unexpectedly closed by the remote end*. In practice, this does not affect the creation and operation of the box.
 
 > **Behind a proxy ?**
 > 
 > Install the plugin: `vagrant plugin install vagrant-proxyconf`
 > 
 > Configure Vagrant: Uncomment the lines starting with `config.proxy` in the `Vagrantfile`

 > **Troubleshooting**:
 > 
 > - Ensure the latest version of Vagrant is installed
 > - If using `virtualbox` provider, ensure Oracle Extension Pack is installed (see [Oracle website](https://www.google.be/#q=virtualbox+oracle+extension+pack+install))

 > **Using Instant Contiki or another distribution**:
 > 
 > The full manual installation procedure is available [here](https://rpl-attacks.readthedocs.io/en/latest/install/#manual-installation) and mentions [InstantContiki](https://sourceforge.net/projects/contiki/files/Instant%20Contiki/) but it is advised to use the [Vagrant box](https://app.vagrantup.com/dhondta/boxes/rpl-attacks) as it was fully tested.


## :sunglasses: Demonstration

This will make 3 complete examples of attacks : hello flood, version number and blackhole.

Open the console like before and type:

 ```
 user@instant-contiki:rpl-attacks>> demo
 ```

Or simply launch the `demo` command with Fabric:

 ```
 ./rpl-attacks$ fab demo
 ```


## :fast_forward: Quick Start

1. Open the console (you should see something like in the following screenshot)

 ```
 ./rpl-attacks$ python main.py
 ```

 or

 ```
 ./rpl-attacks$ fab console
 ```
 
 <p align="center"><img src="https://github.com/dhondta/rpl-attacks/raw/master/doc/imgs/rpl-attacks.png"></p>

2. Create a campaign of simulations

 ```
 user@instant-contiki:rpl-attacks>> prepare sample-attacks
 ```

3. Go to your experiments folder (default: `~/Experiments`) and edit your new `sample-attacks.json` to suit your needs

  See [*How to create a campaign of simulations ?*](https://github.com/dhondta/rpl-attacks/blob/master/doc/campaigns.md) for more information.

4. Make the simulations

 ```
 user@instant-contiki:rpl-attacks>> make_all sample-attacks
 ```

5. Run the simulations (multi-processed)

 ```
 user@instant-contiki:rpl-attacks>> run_all sample-attacks
 ```

  **Hint** : You can type ``status`` during ``make_all`` and ``run_all`` processing for getting the status of pending tasks.

6. Once tasks are in status ``SUCCESS`` in the status tables (visible by typing ``status``), just go to the experiment's ``results`` folders to get pictures and logs of the simulations. The related paths are the followings :

 ``[EXPERIMENTS_FOLDER]/[experiment_name]/without-malicious/results/``
 ``[EXPERIMENTS_FOLDER]/[experiment_name]/with-malicious/results/``

 
## :grimacing: Issues management

In case of bug, there should be a **crash report generated in the folder of the experiment** that the framework was processing. By convention, this is named **`crash-report-[...].txt`**. Please copy its content (without the title) in a [new Issue](https://github.com/dhondta/rpl-attacks/issues/new).
 
For contributions or suggestions, please [open an Issue](https://github.com/dhondta/rpl-attacks/issues/new) and clearly explain, using an example or a use case if appropriate.

If you want to build new RPL attacks, please refer to the [*How to make new building blocks ?*](https://github.com/dhondta/rpl-attacks/blob/master/doc/building-blocks.md) section. In this case, please submit your new attack through a Pull Request.


## :clap:  Supporters

[![Stargazers repo roster for @dhondta/rpl-attacks](https://reporoster.com/stars/dark/dhondta/rpl-attacks)](https://github.com/dhondta/rpl-attacks/stargazers)

[![Forkers repo roster for @dhondta/rpl-attacks](https://reporoster.com/forks/dark/dhondta/rpl-attacks)](https://github.com/dhondta/rpl-attacks/network/members)

<p align="center"><a href="#"><img src="https://img.shields.io/badge/Back%20to%20top--lightgrey?style=social" alt="Back to top" height="20"/></a></p>
