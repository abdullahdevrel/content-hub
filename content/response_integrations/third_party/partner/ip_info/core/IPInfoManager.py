# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# ==============================================================================
# IPInfoManager.py
# IPinfo API client for the Google SecOps response integration.
# Targets the IPinfo OpenAPI specification:
# https://ipinfo.io/developers/openapi.yaml
# ==============================================================================
from __future__ import annotations

import copy
import urllib.parse
from typing import Any

import requests

# =====================================
#               CONSTS                #
# =====================================
DEFAULT_API_ROOT = "https://api.ipinfo.io/"
DEFAULT_TIMEOUT_SECONDS = 30

HEADERS = {
    "Authorization": "Bearer {0}",
    "Accept": "application/json",
}

# Endpoint paths.
ME_PATH = "me"
LITE_PATH = "lite/{ip}"
CORE_PATH = "lookup/{ip}"
PLUS_PATH = "plus/{ip}"
MAX_PATH = "max/{ip}"
PRIVACY_PATH = "{ip}/privacy"
PRIVACY_EXTENDED_PATH = "{ip}/privacy_extended"
RESPROXY_PATH = "{ip}/resproxy"
ASN_PATH = "AS{asn}"
HOSTED_DOMAINS_PATH = "domains/{ip}"
ABUSE_PATH = "{ip}/abuse"

API_LIMIT_STATUS_CODE = 429


# =====================================
#              CLASSES                #
# =====================================
class IPInfoManagerError(Exception):
    """Raised when the IPinfo API returns an error or is unreachable."""


class IPInfoRateLimitError(IPInfoManagerError):
    """Raised when the IPinfo API returns 429 Too Many Requests."""


class IPInfoForbiddenError(IPInfoManagerError):
    """Raised when the IPinfo API returns 403 Forbidden (invalid token)."""


class IPInfoManager:
    """Thin client for the IPinfo API.

    The manager intentionally returns the raw decoded JSON from each endpoint so
    that downstream SecOps actions and widgets can render the full payload.
    """

    def __init__(
        self,
        api_root: str | None,
        token: str,
        verify_ssl: bool = True,
        timeout: int = DEFAULT_TIMEOUT_SECONDS,
    ) -> None:
        if not token:
            raise IPInfoManagerError("An IPinfo API token is required.")

        resolved_root = api_root or DEFAULT_API_ROOT
        self.api_root = resolved_root if resolved_root.endswith("/") else resolved_root + "/"
        self.timeout = timeout
        self.session = requests.session()
        self.session.verify = verify_ssl
        self.session.headers = copy.deepcopy(HEADERS)
        self.session.headers["Authorization"] = self.session.headers["Authorization"].format(token)

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------
    def _build_url(self, path: str) -> str:
        return urllib.parse.urljoin(self.api_root, path.lstrip("/"))

    def _get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        response = self.session.get(self._build_url(path), params=params, timeout=self.timeout)
        return self._validate_response(response)

    @staticmethod
    def _extract_error_message(payload: Any, fallback: str) -> str:
        """Pulls a human-readable message out of an IPinfo error payload.

        The spec uses several error shapes (Error400, Error403, Error404,
        Error429 with title/message; Error404ASN / Lite errors with a single
        `error` string). This helper handles all of them.
        """
        if isinstance(payload, dict):
            error = payload.get("error")
            if isinstance(error, dict):
                title = error.get("title")
                message = error.get("message")
                if title and message:
                    return f"{title}: {message}"
                return message or title or fallback
            if isinstance(error, str):
                return error
            title = payload.get("title")
            message = payload.get("message")
            if title and message:
                return f"{title}: {message}"
            if message:
                return message
            if title:
                return title
        if isinstance(payload, str) and payload:
            return payload
        return fallback

    @classmethod
    def _validate_response(cls, response: requests.Response) -> Any:
        """Validate an HTTP response and return the decoded body.

        Returns parsed JSON when the response declares `application/json`,
        otherwise returns the raw text. Raises a typed exception on errors.
        """
        # Try to decode the body once for both success and error paths.
        body: Any
        content_type = (response.headers.get("Content-Type") or "").lower()
        try:
            body = response.json() if "application/json" in content_type else response.text
        except ValueError:
            body = response.text

        if response.status_code == API_LIMIT_STATUS_CODE:
            message = cls._extract_error_message(body, "IPinfo API rate limit exceeded.")
            raise IPInfoRateLimitError(message)

        if response.status_code == 403:
            message = cls._extract_error_message(body, "IPinfo API token is invalid or forbidden.")
            raise IPInfoForbiddenError(message)

        if not response.ok:
            message = cls._extract_error_message(
                body, f"IPinfo API request failed with status {response.status_code}.",
            )
            raise IPInfoManagerError(message)

        return body

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def ping(self) -> bool:
        """Validate the token by calling the `/me` endpoint.

        Returns True on success. Raises IPInfoForbiddenError when the token
        is invalid and IPInfoManagerError for other failures.
        """
        self._get(ME_PATH)
        return True

    def get_me(self) -> dict[str, Any]:
        """Return token metadata (plan limits, feature flags)."""
        return self._get(ME_PATH)

    def get_lite_information(self, ip_address: str) -> dict[str, Any]:
        """IPinfo Lite: country and ASN information."""
        return self._get(LITE_PATH.format(ip=ip_address))

    def get_core_information(self, ip_address: str) -> dict[str, Any]:
        """IPinfo Core: city-level geolocation, ASN, classification flags."""
        return self._get(CORE_PATH.format(ip=ip_address))

    def get_plus_information(self, ip_address: str) -> dict[str, Any]:
        """IPinfo Plus: Core + mobile carrier and anonymity detection."""
        return self._get(PLUS_PATH.format(ip=ip_address))

    def get_max_information(self, ip_address: str) -> dict[str, Any]:
        """IPinfo Max: full intelligence including residential proxy detection."""
        return self._get(MAX_PATH.format(ip=ip_address))

    def get_privacy_information(self, ip_address: str) -> dict[str, Any]:
        """Privacy Detection Standard: VPN/proxy/Tor/relay/hosting flags."""
        return self._get(PRIVACY_PATH.format(ip=ip_address))

    def get_privacy_extended_information(self, ip_address: str) -> dict[str, Any]:
        """Privacy Detection Extended: methodology, confidence, coverage."""
        return self._get(PRIVACY_EXTENDED_PATH.format(ip=ip_address))

    def get_residential_proxy_information(self, ip_address: str) -> dict[str, Any]:
        """Residential Proxy Detection: activity window and provider name."""
        return self._get(RESPROXY_PATH.format(ip=ip_address))

    def get_asn_information(self, asn: str) -> dict[str, Any]:
        """ASN lookup. Accepts `AS15169`, `as15169` or `15169`."""
        normalised = str(asn).strip().upper()
        if normalised.startswith("AS"):
            normalised = normalised[2:]
        if not normalised.isdigit():
            raise IPInfoManagerError(
                f"Invalid ASN value: {asn}. Provide a numeric ASN such as 15169 or AS15169."
            )
        return self._get(ASN_PATH.format(asn=normalised))

    def get_hosted_domains(
        self,
        ip_address: str,
        page: int | None = None,
        limit: int | None = None,
    ) -> dict[str, Any]:
        """Hosted Domains (reverse-IP): list of domains hosted on the IP."""
        params: dict[str, Any] = {}
        if page is not None:
            params["page"] = page
        if limit is not None:
            params["limit"] = limit
        return self._get(HOSTED_DOMAINS_PATH.format(ip=ip_address), params=params or None)

    def get_abuse_contact(self, ip_address: str) -> dict[str, Any]:
        """Abuse contact information for the IP's network owner."""
        return self._get(ABUSE_PATH.format(ip=ip_address))
