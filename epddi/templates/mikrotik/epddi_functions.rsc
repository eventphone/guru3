:global getEpddiFolderPath do={
	:if ( [/file find name=flash] ) do={
		return "flash/epddi"
	} else={
		return "epddi"
	}
}

:global removeEpddiFolder do={
	:global getEpddiFolderPath
	:local epddiFolderPath [$getEpddiFolderPath]
	:if ( [/file find name=$epddiFolderPath]) do={
		/file remove $epddiFolderPath
	}
}

:global waitForFile do={
	while ([/file find name=$filename] = "") do={
		:delay 1s
	}
}

:global waitForDhcpLease do={
	while ([/ip dhcp-client get value-name=status number=[/ip dhcp-client find comment=epddi]] != "bound") do={
		:delay 1s
	}
}

:global createEpddiClientCertificate do={
	:global waitForFile

	/certificate add common-name="{{ object.client.hostname }}" country=DE days-valid=365 name=cert_template state=NRW unit=IT organization=eventphone key-usage=digital-signature,key-encipherment,data-encipherment,tls-client
	/certificate create-certificate-request template=cert_template key-passphrase=-
	# Wait for generation to finish
	$waitForFile filename=certificate-request.pem

	:local csr [/file get certificate-request.pem contents]
	/tool fetch "https://{{ request.get_host }}{% url "mikrotik.cert_enroll" token=object.token %}" http-method=post http-data="$csr" dst-path="epddi_cert"
	# Wait for download to finish
	$waitForFile filename=epddi_cert

	# Remove unsigned cert and import signed version
	/certificate remove [/certificate find name="cert_template"]
	/certificate import name=epddi-client-cert file-name=epddi_cert passphrase=-
	/certificate import name=epddi-client-cert file-name=certificate-request_key.pem passphrase=-

	# Cleanup
	/file remove "certificate-request.pem"
	/file remove "certificate-request_key.pem"
	/file remove "epddi_cert"
}

:global installEpddiVpnServerCaCertificate do={
	:global waitForFile

	/tool fetch "{{ EPDDI_VPN_CONCENTRATOR_SERVER_CA_CERT_URL }}" output=file dst-path="epddi-vpn-server-ca.crt"
	$waitForFile filename="epddi-vpn-server-ca.crt"
	/certificate import name=epddi-vpn-server-ca file-name="epddi-vpn-server-ca.crt" passphrase=-
	/file remove "epddi-vpn-server-ca.crt"
}

:global clearFirewallConfiguration do={
	if ([ /ip firewall filter find action!=passthrough ]!="") do={
		/ip firewall filter remove [/ip firewall filter find action!=passthrough]
	}
}

:global configureDectVpnClient do={
	/ppp profile add name=dect
	/interface ovpn-client add certificate=epddi-client-cert cipher=aes256 connect-to={{ EPDDI_VPN_CONCENTRATOR_SERVER_HOSTNAME }} name=poc-dect profile=dect verify-server-certificate=yes user=mikrotikneedsausersoweputonehere
}

:global configureFirewall do={
	:local ommAddress {{ EPDDI_OMM_ADDRESS }}
	:local vpnConcentratorAddress {{ EPDDI_VPN_CONCENTRATOR_ADDRESS }}
	:local antennaeNet {{ EPDDI_NETWORK }}
	:local yateRtpAddress {{ EPDDI_YATE_RTP_ADDRESS }}
	:local yateRtpPortRangeStart {{ EPDDI_ANTENNAE_RTP_PORT_RANGE_START }}
	:local yateRtpPortRangeEnd {{ EPDDI_ANTENNAE_RTP_PORT_RANGE_END }}
	:local antennaeRtpPortRangeStart {{ EPDDI_ANTENNAE_RTP_PORT_RANGE_START }}
	:local antennaeRtpPortRangeEnd {{ EPDDI_ANTENNAE_RTP_PORT_RANGE_END }}
	:local localNet {{ object.client.dect_network.network_address }}/{{ object.client.dect_network.network_mask }}
	:local myIP {{ object.client.dect_network.get_router_ip }}

	:global clearFirewallConfiguration
	$clearFirewallConfiguration

	/ip firewall filter {
		add action=fasttrack-connection chain=forward comment="fasttrack" connection-state=established,related
		add action=accept chain=forward comment="accept established,related, untracked" connection-state=established,related,untracked
		add action=drop chain=forward comment="drop invalid" connection-state=invalid
		add action=accept chain=forward comment="ICMP epddi -> antennae net" in-interface=poc-dect out-interface=bridge protocol=icmp
		add action=accept chain=forward comment="ICMP antennae net -> epddi" in-interface=bridge out-interface=poc-dect protocol=icmp
		add action=accept chain=forward comment="TFTP antennae -> OMM" dst-address=$ommAddress dst-port=69 in-interface=bridge out-interface=poc-dect protocol=udp src-address=$localNet
		add action=accept chain=forward comment="SYSLOG antennae -> OMM" dst-address=$ommAddress dst-port=514 in-interface=bridge out-interface=poc-dect protocol=udp src-address=$localNet
		add action=accept chain=forward comment="OMM Protokoll A antennae -> OMM" dst-address=$ommAddress dst-port=16321 in-interface=bridge out-interface=poc-dect protocol=tcp src-address=$localNet
		add action=accept chain=forward comment="OMM Protokoll B antennae -> OMM" dst-address=$ommAddress dst-port=16322 in-interface=bridge out-interface=poc-dect protocol=tcp src-address=$localNet
		add action=accept chain=forward comment="RTP local antennae -> other antennae" dst-address=$antennaeNet dst-port="$antennaeRtpPortRangeStart-$antennaeRtpPortRangeEnd" in-interface=bridge out-interface=poc-dect protocol=udp src-address=$localNet
		add action=accept chain=forward comment="RTP other antennae -> local antennae" dst-address=$localNet dst-port="$antennaeRtpPortRangeStart-$antennaeRtpPortRangeEnd" in-interface=poc-dect out-interface=bridge protocol=udp src-address=$antennaeNet
		add action=accept chain=forward comment="RTP antennae -> yate" dst-address=$yateRtpAddress dst-port="$yateRtpPortRangeStart-$yateRtpPortRangeEnd" in-interface=bridge out-interface=poc-dect protocol=udp src-address=$localNet
		add action=accept chain=forward comment="RTP yate -> antennae" dst-address=$localNet dst-port="$antennaeRtpPortRangeStart-$antennaeRtpPortRangeEnd" in-interface=poc-dect out-interface=bridge protocol=udp src-address=$yateRtpAddress
		add action=drop chain=forward comment="DROP everything else for FORWARD"
		add action=accept chain=input comment="accept established,related,untracked" connection-state=established,related,untracked
		add action=drop chain=input comment="drop invalid" connection-state=invalid
		add action=accept chain=input comment="accept ICMP * -> Mikrotik" protocol=icmp
		add action=accept chain=input comment="DHCP antennae -> Mikrotik" dst-port=67 in-interface=bridge protocol=udp
		add action=accept chain=input comment="DHCP EPDDI VPN Concentrator -> Mikrotik" dst-address=$myIP dst-port=67 in-interface=poc-dect protocol=udp src-address=$vpnConcentratorAddress
		add action=accept chain=input comment="SSH EPDDI VPN Concentrator -> Mikrotik" dst-port=22 in-interface=poc-dect protocol=tcp src-address=$vpnConcentratorAddress
		add action=accept chain=input comment="HTTP local antennae net -> Mikrotik" dst-address=$myIP dst-port=80 in-interface=bridge protocol=tcp src-address=$localNet
		add action=drop chain=input comment="DROP everything else for INPUT"
	}
}

:global configureDectNetwork do={
	:local vpnConcentratorAddress {{ EPDDI_VPN_CONCENTRATOR_ADDRESS }}

	/ip address add address={{ object.client.dect_network.get_router_ip }}/{{ object.client.dect_network.network_mask }} interface=bridge network={{ object.client.dect_network.network_address }}
	/ip dhcp-relay add dhcp-server=$vpnConcentratorAddress disabled=no interface=bridge local-address={{ object.client.dect_network.get_router_ip }} name=epddi-relay
}

:global configureServices do={
	/ip service {
		set telnet disabled=yes
		set ftp disabled=yes
		set www disabled=no
		set ssh disabled=no
		set www-ssl disabled=yes
		set api disabled=yes
		set winbox disabled=yes
		set api-ssl disabled=yes
	}
}
