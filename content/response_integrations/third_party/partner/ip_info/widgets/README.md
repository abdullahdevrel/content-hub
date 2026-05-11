# Widget HTML files

This directory contains the YAML widget manifests for each action. The two
HTML widget templates `GetIPInformation.html` and `GetDomainInformation.html`
are intentionally not modified in v8.0.

Both templates are schema-agnostic: they flatten any JSON payload via
`flattenKeys` and render it as a key-value list, with auto-generated tables
for any array of objects. They continue to render correctly against the new
endpoint payloads (Lite, Core, Plus, Max, Privacy, Privacy Extended,
Residential Proxy, ASN, Hosted Domains, Abuse).

When merging v8.0, keep the existing HTML files in place and replace only the
YAML manifests with the versions in this directory.
