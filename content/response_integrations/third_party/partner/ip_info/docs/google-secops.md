# IPinfo integration for Google Security Operations (SecOps)

The IPinfo integration for Google Security Operations enriches IP-based entities in SecOps SOAR cases and playbooks with data from the [IPinfo API](https://ipinfo.io/developers/). It supports the full set of IPinfo product tiers (Lite, Core, Plus, Max) and the specialised detection APIs (Privacy, Privacy Extended, Residential Proxy, ASN, Hosted Domains, Abuse Contact).

Source code: [chronicle/content-hub on GitHub](https://github.com/chronicle/content-hub/tree/main/content/response_integrations/third_party/partner/ip_info).

## Prerequisites

- An IPinfo account and API token. [Sign up for free](https://ipinfo.io/signup) or [view plans](https://ipinfo.io/pricing).
- Access to Google Security Operations (Chronicle SOAR / SIEM).
- Network connectivity from your SecOps environment to `https://api.ipinfo.io/`.

The free tier supports the Lite API and a baseline of Core requests. Plus, Max, Privacy Extended, Residential Proxy, and Hosted Domains require a paid plan; check the [pricing page](https://ipinfo.io/pricing) for current entitlements.

## Installation

1. Open Google Security Operations.
2. Navigate to **Response > Integrations > Marketplace**.
3. Search for **IPInfo** and install the integration.
4. Configure the integration with your IPinfo API token (see below).

## Configuration parameters

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| API Root | URL | Yes | `https://api.ipinfo.io/` | IPinfo API root URL. Override only for IPv4-only or IPv6-only endpoints (e.g. `https://v4.api.ipinfo.io/`). |
| Token | Password | Yes | — | IPinfo API access token. |
| Verify SSL | Boolean | Yes | `true` | Verify the IPinfo API SSL certificate. Leave enabled in production. |

After configuring, run the **Ping** action to validate the token.

## Actions

All IP-enrichment actions operate on `ADDRESS` entities. The ASN action takes an explicit `ASN` parameter. The Get Domain Information action takes an `ADDRESS` entity (it is a reverse-IP lookup despite the legacy name).

### Tier actions

| Action | Endpoint | Purpose |
|---|---|---|
| Get Lite Information | `/lite/{ip}` | Country, continent, ASN. Best for high-volume enrichment. |
| Get Core Information | `/lookup/{ip}` | City-level geolocation, ASN, classification flags (anycast, hosting, mobile, satellite). |
| Get Plus Information | `/plus/{ip}` | Core + mobile carrier (MCC/MNC) + anonymity detection (VPN, proxy, Tor, relay). |
| Get Max Information | `/max/{ip}` | Plus + residential proxy detection, activity window, consolidated `is_anonymous` flag. |

### Specialised actions

| Action | Endpoint | Purpose |
|---|---|---|
| Get Privacy Information | `/{ip}/privacy` | VPN, proxy, Tor, relay, hosting flags and service provider name. |
| Get Privacy Extended Information | `/{ip}/privacy_extended` | Privacy flags plus methodology metadata (`confidence`, `coverage`, `census`, `device_activity`, `inferred`, `vpn_config`, `whois`, `first_seen`, `last_seen`). |
| Get Residential Proxy Information | `/{ip}/resproxy` | Residential proxy service name, last seen date, percent days seen. |
| Get ASN Information | `/AS{asn}` | ASN details: prefixes, peers, upstreams, downstreams. Takes `ASN` parameter. |
| Get Domain Information | `/domains/{ip}` | Domains hosted on an IP (reverse-IP). Supports `Page` and `Limit` parameters. |
| Get Abuse Contact | `/{ip}/abuse` | Abuse contact for the network that owns the IP. |

### Connectivity action

| Action | Endpoint | Purpose |
|---|---|---|
| Ping | `/me` | Validate the API token and connectivity. |

### Backwards compatibility

The legacy `Get IP Information` action is retained in v8.0 and now calls the Core endpoint. Existing playbooks continue to work without modification. New playbooks should call the explicit tier action (Lite, Core, Plus, or Max) for clarity around cost and field coverage.

## Response schemas

Each action returns the full JSON payload from IPinfo. The widget templates are schema-agnostic and render every field returned. The authoritative schema for each endpoint is published in the [IPinfo OpenAPI specification](https://ipinfo.io/developers/openapi.yaml). Selected highlights:

**Lite** (`/lite/{ip}`): `ip`, `asn`, `as_name`, `as_domain`, `country_code`, `country`, `continent_code`, `continent`.

**Core** (`/lookup/{ip}`): `ip`, `hostname`, nested `geo` (city, region, region_code, country, country_code, continent, continent_code, latitude, longitude, timezone, postal_code), nested `as` (asn, name, domain, type), top-level `is_anonymous`, `is_anycast`, `is_hosting`, `is_mobile`, `is_satellite`.

**Plus** (`/plus/{ip}`): Core plus nested `mobile` (name, mcc, mnc), `anonymous` (name, is_proxy, is_relay, is_tor, is_vpn), and `geo.dma_code`, `geo.geoname_id`, `geo.radius`, `geo.last_changed`.

**Max** (`/max/{ip}`): Plus plus `anonymous.last_seen`, `anonymous.percent_days_seen`, `anonymous.is_res_proxy`.

**Privacy Standard** (`/{ip}/privacy`): `vpn`, `proxy`, `tor`, `hosting`, `relay`, `service`.

**Privacy Extended** (`/{ip}/privacy_extended`): Standard fields plus `confidence` (1-3), `coverage` (0-1), `census`, `census_ports`, `device_activity`, `inferred`, `vpn_config`, `whois`, `first_seen`, `last_seen`.

**Residential Proxy** (`/{ip}/resproxy`): `ip`, `last_seen`, `percent_days_seen`, `service`.

**ASN** (`/AS{asn}`): `asn`, `name`, `country`, `allocated`, `registry`, `domain`, `num_ips`, `route`, `type`, `prefixes`, `prefixes6`, `peers`, `upstreams`, `downstreams`.

**Hosted Domains** (`/domains/{ip}`): `ip`, `page`, `total`, `domains` (array).

**Abuse** (`/{ip}/abuse`): `address`, `country`, `email`, `name`, `network`, `phone`.

## Errors and rate limits

The integration raises typed errors for the common IPinfo response codes:

- `403 Forbidden`: token missing or invalid. The error message echoes the IPinfo message and points to support resources.
- `429 Too Many Requests`: rate limit reached for the token's plan. See [pricing](https://ipinfo.io/pricing) to increase limits.
- `400 Bad Request` / `404 Not Found`: surfaced to the action as a failed lookup with the field-level message preserved.

Errors are written to the action output message and the SecOps log; successful entities are still updated when other entities in the same action fail.

## Migrating from v7.0 (and earlier)

| v7.0 behaviour | v8.0 behaviour |
|---|---|
| `Get IP Information` called `/{ip}` and assumed the legacy enrichment schema. | `Get IP Information` is retained and now calls `/lookup/{ip}`. New playbooks should use `Get Core Information` (or another tier action) explicitly. |
| `Get Domain Information` called `/domains/{hostname}`. | `Get Domain Information` calls `/domains/{ip}` (reverse-IP). The action expects an `ADDRESS` entity instead of a hostname. |
| `Ping` called `/{TEST_IP}`. | `Ping` calls `/me`. |
| No support for Privacy, Privacy Extended, Residential Proxy, Plus, Max, ASN, or Abuse APIs. | Added as first-class actions. |
| Error validation matched the substring `"error"` anywhere in the response body. | Error validation parses the IPinfo error envelope and raises typed exceptions. |

When upgrading existing playbooks:

1. Run `Ping` after upgrade to confirm the token is still valid.
2. Replace any `Get Domain Information` step that expected a hostname entity with a reverse-IP lookup against an `ADDRESS` entity, or remove the step if it is no longer needed.
3. Consider replacing `Get IP Information` with the explicit tier action that fits your investigation (Lite for triage, Core for standard enrichment, Plus or Max for threat hunting).

## Support

- IPinfo Developer Portal: [https://ipinfo.io/developers](https://ipinfo.io/developers)
- IPinfo Community: [https://community.ipinfo.io/](https://community.ipinfo.io/)
- IPinfo Support: [support@ipinfo.io](mailto:support@ipinfo.io)
- Source code and issues: [chronicle/content-hub on GitHub](https://github.com/chronicle/content-hub/tree/main/content/response_integrations/third_party/partner/ip_info)
