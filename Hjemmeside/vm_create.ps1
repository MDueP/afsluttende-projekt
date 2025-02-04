
Connect-AzAccount
            
#Azure Account - Info
$resourcegroup = 'rg-itm8'
$location = 'westeurope'
            
#VM Account - Info
$adminUsername = "LocalAdmin"
$adminPassword = ConvertTo-SecureString "LocalAdmin1!" -AsPlainText -Force
$credential = New-Object System.Management.Automation.PSCredential ($adminUsername, $adminPassword)
            
#VM - Info
$vmName = "vm-itm8"

$imagepub = "MicrosoftWindowsServer"
$imageoffer = "WindowsServer"
$imagesku = "2022-Datacenter"
            
#Networking
$subnet_name = 'subnet'
$vnet_name = 'vnet'

#Resource Group
New-AzResourceGroup -Name $resourcegroup -Location $location

#Vnet
$subnet = New-AzVirtualNetworkSubnetConfig `
    -Name $subnet_name `
    -AddressPrefix "10.0.0.0/24" 

New-AzVirtualNetwork -Name $vnet_name `
    -ResourceGroupName $resourcegroup `
    -Location $location `
    -AddressPrefix "10.0.0.0/16" `
    -Subnet $subnet
    
$Subnet = Get-AzVirtualNetwork -Name $vnet_name -ResourceGroupName $resourcegroup

$publicIP = New-AzPublicIPAddress `
    -Name "$vmName-ip" `
    -ResourceGroupName $resourcegroup `
    -Location $location `
    -AllocationMethod Static `
    -Sku Standard

$nic = New-AzNetworkInterface `
    -Name "$vmName-nic" `
    -ResourceGroupName $resourcegroup `
    -Location $location `
    -SubnetId $Subnet.Subnets[0].Id `
    -PublicIpAddressId $publicIp.Id
    
#Config of the virtual machine -VMSize has to be changed to v5. We only have access to deploy up to v4
$vm_config = New-AzVMConfig `
    -VMName $vmName `
    -VMSize "Standard_D2ds_v4" `
    -SecurityType "Standard" `
    -IdentityType "SystemAssigned"

$vm_config = Set-AzVMOperatingSystem `
    -VM $vm_config `
    -ComputerName $vmName `
    -Credential $credential `
    

$vm_config = Set-AzVMSourceImage `
    -VM $vm_config `
    -PublisherName "$imagepub" `
    -Offer "$imageoffer" `
    -Skus "$imagesku" `
    -Version "latest"
    
    
#Adds the networkinterface to the VM
$vm_config = Add-AzVMNetworkInterface `
    -VM $vm_config `
    -Id $nic.Id

$vm_config = Add-AzVMDataDisk `
    -VM $vm_config `
    -Name "disk1" `
    -DiskSizeInGB 256 `
    -CreateOption "Empty" `
    -DeleteOption "Delete" `
    -Lun 1

New-AzVM `
    -ResourceGroupName $resourcegroup `
    -Location $location `
    -VM $vm_config 
