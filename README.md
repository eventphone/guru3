# GURU3 (GenericUserRegistrationUtility v3)

[GURU3](https://guru3.eventphone.de) is our new and shiny self registration interface for our phone infrastructure at all eventphone events.

Please do not open issues for general support requests. If you have a problem with your extension or device just visit us at the PoC Helpdesk during an event or use our [ticket system](https://guru3.eventphone.de/support/).

## General Information & Disclaimer

Please note that this repository contains just a history-less dump of Eventphone's Guru3 User Registration Utility.
We decided to publish the current state of the code due to multiple requests. We are aware that the general state of
this codebase with mixed coding styles and just a bare minimum amount of tests isn't the best. Moreover, documentation
isn't really existing.

The main purpose of publishing this code-base is to provide some (code) reference for people who either want to know
the details about how the Eventphone system works or that want to be compatible with it. We discourage setting up this
tool on your own (due to the inherent complexity) and will probably not provide any guide or How-To any time soon.

If you want to use Guru3 as user front-end for your event with your telephony system, we recommend implementing the
messaging wire protocol (see core/messaging.py). We offer using the official Guru3 instance at
https://guru3.eventphone.de also for smaller (non-profit) events. If you're interested here, contact us at
support@eventphone.de.

## Contributing

Please note that we do not plan to accept contributions here. Given the overall complexity and the interplay of Guru3
with the rest of Eventphone's telephony system, we feel that providing isolated contributions here isn't the best way
to improve the state of Guru3. We may make exceptions for smaller isolated changes if clarified upfront. However, if you
want to contribute to the state of Eventphone's telephony system, please get in touch with us either via our regular
support channels (https://guru3.eventphone.de/support/) or at some of the events directly at our PoC desk.

## Licensing

The code published here is released under AGPL. This DOES NOT apply to the contents of the static folder. Libraries
are published under their respective licenses and the Eventphone artwork is only provided for reference and
without any permission to use it for your own purposes.

## Security
Please contact us via our [ticket system](https://guru3.eventphone.de/support/) if you've found a security issue impacting either our infrastructure or the users or if you don't want to submit your request publicly.