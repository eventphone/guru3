/tool fetch url="https://{{ request.get_host }}{% url "mikrotik.download_provision_runscript" token=object.token %}" dst-path=epddi_provision.rsc
:while ([/file find name=epddi_provision.rsc] = "") do={ :delay 1s }
:import epddi_provision.rsc
