== General ==

The certificate here (snom-phone-ca.pem) is the CA certificate
that issues the Snom phone client certificates. It needs to be
entered as client cert CA in your main web server.

For nginx you use the `ssl_client_certificate` option together
with `ssl_verify_client optional` to enable opportunistic
TLS client certificate validation.

The validation result needs to be passed on to the server
that runs django. With nginx you can use:
```
proxy_set_header X-Forwarded-Client-Cert-I-DN $ssl_client_i_dn;
proxy_set_header X-Forwarded-Client-Cert-S-DN $ssl_client_s_dn;
```
This forwards the issuer DN and the subject DN for django to
inspect. The snom module uses this to verify the identify of
a connecting phone.
