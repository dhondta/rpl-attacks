# -*- mode: ruby -*-
# vi: set ft=ruby :

# IMPORTANT :
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
  config.vm.provider "virtualbox" do |v|
    config.vm.box = "ubuntu/bionic64"
    # config.vm.box = "ubuntu/xenial64"
    v.gui = true
    v.name = "RPL Attacks Framework"
    v.memory = 2048
    v.cpus = 2
    v.customize ["modifyvm", :id, "--usb", "on"]
    v.customize ["modifyvm", :id, "--usbehci", "on"]
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
