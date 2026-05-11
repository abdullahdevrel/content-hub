# IPInfo integration for Google Security Operations

This directory contains the IPinfo response integration for Google Security Operations (Chronicle SOAR). It is published in the SecOps Marketplace via the [chronicle/content-hub](https://github.com/chronicle/content-hub) repository.

## Current version: 8.0

Version 8.0 migrates the integration to the modern [IPinfo API](https://ipinfo.io/developers/openapi.yaml). See `release_notes.yaml` for the full change log and `docs/google-secops.md` for the partner-hosted documentation page.

## Layout

```
.
├── actions/                 Action scripts and YAML manifests
├── core/                    IPInfoManager API client
├── docs/                    Partner-hosted documentation source
├── resources/               Example JSON, AI descriptions, logo, image
│   └── ai/                  AI action descriptions
├── tests/                   Test scaffold (uses Chronicle integration-testing)
├── widgets/                 Widget HTML and YAML manifests
├── definition.yaml          Integration manifest
├── pyproject.toml           Python project metadata
└── release_notes.yaml       Version history
```

## Actions

- **Ping** — validates the token via `/me`.
- **Get Lite Information** — `/lite/{ip}`
- **Get Core Information** — `/lookup/{ip}`
- **Get Plus Information** — `/plus/{ip}`
- **Get Max Information** — `/max/{ip}`
- **Get Privacy Information** — `/{ip}/privacy`
- **Get Privacy Extended Information** — `/{ip}/privacy_extended`
- **Get Residential Proxy Information** — `/{ip}/resproxy`
- **Get ASN Information** — `/AS{asn}` (takes `ASN` parameter)
- **Get Domain Information** — `/domains/{ip}` (reverse-IP; supports `Page`, `Limit`)
- **Get Abuse Contact** — `/{ip}/abuse`
- **Get IP Information** — retained for backwards compatibility; now calls Core.

## Development

The integration depends on the Chronicle SOAR SDK (`soar-sdk`) and uses the same packaging conventions as other partner integrations in this repository. See the [Build Partner Content Guide](https://cloud.google.com/chronicle/docs/soar/partners) for the developer license workflow.
