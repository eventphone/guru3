{% include 'mikrotik/epddi_functions.rsc' %}

# Cleanup old epddi stuff that might be within flash
$removeEpddiFolder

:global epddiFolder [$getEpddiFolderPath]
:global epddiInitialConfigurationFilename "$epddiFolder/epddi_initial.rsc"
/tool fetch http-method=get url="https://{{ request.get_host }}{% url "mikrotik.download_inital" token=object.token %}" output=file dst-path=$epddiInitialConfigurationFilename
$waitForFile filename=$epddiInitialConfigurationFilename
/system reset-configuration no-defaults=yes skip-backup=yes run-after-reset=$epddiInitialConfigurationFilename
