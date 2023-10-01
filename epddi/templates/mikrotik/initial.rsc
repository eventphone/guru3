{% include 'mikrotik/epddi_functions.rsc' %}

:global waitForInterfaces do={
	:local count 0
	:while ([/interface ethernet find] = "") do={
		:if ($count = 30) do={
			:log warning "Initial Configuration: Unable to find ethernet interfaces"
			/quit
		}
		:delay 1s
		:set count ($count +1)
	}
}

:global configureBridge do={
	/interface bridge add name=bridge disabled=no auto-mac=yes protocol-mode=rstp comment="epddi"
	:global bMACIsSet 0
	:foreach k in=[/interface find where !(slave=yes || name="ether1" || name~"bridge")] do={
		:global tmpPortName [/interface get $k name]
		:log info "port: $tmpPortName"
		:if ($bMACIsSet = 0) do={
			:if ([/interface get $k type] = "ether") do={
				/interface bridge set "bridge" auto-mac=no admin-mac=[/interface ethernet get $tmpPortName mac-address]
				:set bMACIsSet 1
			}
		}
		/interface bridge port add bridge=bridge interface=$tmpPortName comment="epddi"
	}
}

$waitForInterfaces
/user set admin password="{{ object.admin_password }}"
$configureServices
$configureBridge

# IP CONFIGURATION WAN SIDE
/ip dhcp-client add interface=ether1 disabled=no comment="epddi"

$waitForDhcpLease

$createEpddiClientCertificate
$installEpddiVpnServerCaCertificate
$configureDectVpnClient
$configureDectNetwork
$configureFirewall
/system identity set name={{ object.client.hostname }}

/system script add name=get_config_scheduled source={
	:local model [/system routerboard get model]
	:local serial [/system routerboard get serial]
	:local currentfw [/system routerboard get current-firmware]
	:local factoryfw [/system routerboard get factory-firmware]
	:local upgradefw [/system routerboard get upgrade-firmware]
	:local httpData "{\"model\":\"$model\",\"serial\":\"$serial\",\"currentfw\":\"$currentfw\",\"factoryfw\":\"$factoryfw\",\"upgradefw\":\"$upgradefw\"}"
	:local httpUrl "https://{{ request.get_host }}{% url "mikrotik.deploy_config" token=object.token %}"
	:local execute true
	:do {
		/tool fetch http-method=post http-data=$httpData url=$httpUrl output=file dst-path=autoconfig.rsc
	} on-error={
		:set execute false
	}
	:if (execute) do={
		:do {
			import autoconfig.rsc
		} on-error={
			:log info "Download error no execute"
		}
	}
	/file remove [find name=autoconfig.rsc]
}

/sys scheduler add name=autoconfig interval=1m on-event=get_config_scheduled

/system package update set channel=long-term
/system package update install
