# -*- mode: ruby -*-
# vi: set ft=ruby :

# IMPORTANT :
#  Don't forget to run the following commands to get the provider plugin installed !
#  $ vagrant plugin install vagrant-vmware-workstation
#  $ vagrant plugin license vagrant-vmware-workstation /path/to/license.lic
#  If you want to get the VMs installed in a specific directory, type:
#  Not working: $ export VAGRANT_VMWARE_CLONE_DIRECTORY=/path/to/your/vm/library
#  $ mkdir .vagrant && cd .vagrant
#  $ sudo ln -s /path/to/vm/library machines && cd ..

# Vagrantfile API/syntax version. Don't touch unless you know what you're doing!
VAGRANTFILE_API_VERSION = "2"

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
# Beware that the following lines require Vagrant proxy plugin to be installed ;
#  this can be done by executing 'vagrant plugin install vagrant-proxyconf'
#
#  config.proxy.http     = "http://yourproxy:8080"
#  config.proxy.https    = "http://yourproxy:8080"
#  config.proxy.no_proxy = "localhost,127.0.0.1"

  config.vm.box = "bento/ubuntu-16.04"
  config.vm.network :private_network, ip: "192.168.27.100"
  config.vm.host_name = "rpl-attacks-framework"

  # customize VM
  #  when --provider virtualbox
  config.vm.provider "virtualbox" do |v|
    config.vm.box_url = "https://atlas.hashicorp.com/bento/boxes/ubuntu-16.04/versions/2.3.4/providers/virtualbox.box"
    v.gui = true
    v.name = "RPL Attacks Framework"
    v.memory = 2048
    v.cpus = 2
    v.customize ["modifyvm", :id, "--usb", "on"]
    v.customize ["modifyvm", :id, "--usbehci", "on"]
  end
  #  when --provider vmware_workstation
  config.vm.provider "vmware_workstation" do |v|
    config.vm.box_url = "https://atlas.hashicorp.com/bento/boxes/ubuntu-16.04/versions/2.3.4/providers/vmware_desktop.box"
    v.gui = true
    v.vmx["displayName"] = "RPL Attacks Framework"
    v.vmx["name"] = "rpl-attacks-framework"
    v.vmx["memsize"] = 2048
    v.vmx["numvcpus"] = 2
    v.vmx["usb.vbluetooth.startConnected"] = false # disable BlueTooth
  end

  # baseline provisioning
  config.vm.provision "ansible" do |ansible|
    ansible.playbook = "provisioning/rpl-attacks.yml"
    ansible.inventory_path = "provisioning/ansible_hosts"
    ansible.limit = "all"
    ansible.host_key_checking = false
    ansible.verbose = "v"
  end

  config.vm.synced_folder '.', '/vagrant', disabled: true
end
