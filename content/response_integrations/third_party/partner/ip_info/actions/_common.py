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

"""Shared helpers for IPinfo SecOps actions.

Centralises the entity enrichment loop so each action file stays small and
focused on its endpoint-specific concerns.
"""
from __future__ import annotations

from collections.abc import Callable
from typing import Any

from soar_sdk.SiemplifyAction import SiemplifyAction
from soar_sdk.SiemplifyDataModel import EntityTypes
from soar_sdk.SiemplifyUtils import (
    add_prefix_to_dict,
    convert_dict_to_json_result_dict,
    dict_to_flat,
    flat_dict_to_csv,
)

from ..core.IPInfoManager import IPInfoManager

PROVIDER = "IPInfo"
INTEGRATION_PREFIX = "IPInfo"


def build_manager(siemplify: SiemplifyAction) -> IPInfoManager:
    """Read integration config and return a configured IPInfoManager."""
    conf = siemplify.get_configuration(PROVIDER)
    verify_ssl = str(conf.get("Verify SSL", "true")).lower() == "true"
    return IPInfoManager(conf.get("API Root"), conf["Token"], verify_ssl)


def enrich_entities(
    siemplify: SiemplifyAction,
    entity_type: str,
    lookup: Callable[[str], dict[str, Any]],
    *,
    label: str,
) -> None:
    """Enrich all matching entities, populate the SecOps UI, and end the action.

    Args:
        siemplify: The action context.
        entity_type: Entity type to filter on (e.g. EntityTypes.ADDRESS).
        lookup: Callable that takes an entity identifier and returns the
            decoded JSON payload from IPinfo.
        label: Human-readable label used in the output message (e.g. "Lite",
            "Privacy", "Hosted Domains").
    """
    success_entities = []
    errors: list[str] = []
    json_results: dict[str, Any] = {}
    result_value = False

    matching_entities = [
        entity for entity in siemplify.target_entities if entity.entity_type == entity_type
    ]

    for entity in matching_entities:
        try:
            data = lookup(entity.identifier)
            if not data:
                continue

            json_results[entity.identifier] = data
            flat_info = dict_to_flat(data)
            entity.additional_properties.update(
                add_prefix_to_dict(flat_info, INTEGRATION_PREFIX)
            )
            entity.is_enriched = True
            siemplify.result.add_entity_table(entity.identifier, flat_dict_to_csv(flat_info))
            success_entities.append(entity)
            result_value = True
        except Exception as err:  # noqa: BLE001 - we want to surface every failure.
            error_message = (
                f"Failed fetching {label} information for {entity.identifier}, ERROR: {err}"
            )
            siemplify.LOGGER.error(error_message)
            siemplify.LOGGER.exception(err)
            errors.append(error_message)

    siemplify.update_entities(success_entities)

    if success_entities:
        identifiers = ", ".join(entity.identifier for entity in success_entities)
        output_message = f"Fetched {label} information for: {identifiers}"
    else:
        output_message = f"No {label} information fetched for target entities."

    if errors:
        output_message = "{0}\n\nErrors:\n{1}".format(output_message, "\n".join(errors))

    siemplify.result.add_result_json(convert_dict_to_json_result_dict(json_results))
    siemplify.end(output_message, result_value)


# Re-exported for action modules.
ADDRESS = EntityTypes.ADDRESS
