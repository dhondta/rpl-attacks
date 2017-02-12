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
  config.vm.box = "bento/ubuntu-16.04"
#  config.vm.box_url = "https://atlas.hashicorp.com/boxcutter/boxes/ubuntu1404/versions/2.0.10/providers/vmware_desktop.box"
  config.vm.box_url = "https://oss-binaries.phusionpassenger.com/vagrant/boxes/latest/ubuntu-14.04-amd64-vmwarefusion.box"

  config.vm.network "private_network", type: "dhcp"

  # customize VM
  server.vm.hostname = "rpl-attacks-framework"
  config.vm.provider :vmware_workstation do |vmware|
    vmware.gui = true
    vmware.vmx["name"] = "rpl-attacks-framework"
    vmware.vmx["displayName"] = "RPL Attacks Framework"
    vmware.vmx["memsize"] = 2048
    vmware.vmx["numvcpus"] = 2
    vmware.vmx["usb.vbluetooth.startConnected"] = false # disable BlueTooth
  end

  # baseline provisioning
  config.vm.provision "ansible" do |ansible|
    ansible.playbook = "provisioning/rpl-attacks.yml"
    ansible.host_key_checking = false
    ansible.verbose = "v"
  end
end

