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

"""Get Domain Information action.

The action name is preserved for backwards compatibility with existing
playbooks. It now lists the domains hosted on an IP address (reverse-IP
lookup) using the IPinfo Hosted Domains API: GET /domains/{ip}.
"""
from __future__ import annotations

from soar_sdk.SiemplifyAction import SiemplifyAction
from soar_sdk.SiemplifyUtils import (
    add_prefix_to_dict,
    convert_dict_to_json_result_dict,
    dict_to_flat,
    flat_dict_to_csv,
    output_handler,
)

from ._common import ADDRESS, INTEGRATION_PREFIX, build_manager

ACTION_NAME = "IPInfo Get_Domain_Information"

DEFAULT_LIMIT = 100
MAX_LIMIT = 1000


def _parse_int_param(value: str | None, name: str) -> int | None:
    if value is None or str(value).strip() == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Invalid integer value for '{name}': {value}") from exc


@output_handler
def main():
    siemplify = SiemplifyAction()
    siemplify.script_name = ACTION_NAME

    try:
        page = _parse_int_param(
            siemplify.extract_action_param(param_name="Page", is_mandatory=False, print_value=True),
            "Page",
        )
        limit_raw = _parse_int_param(
            siemplify.extract_action_param(param_name="Limit", is_mandatory=False, print_value=True),
            "Limit",
        )
        limit = limit_raw if limit_raw is not None else DEFAULT_LIMIT
        if limit < 1 or limit > MAX_LIMIT:
            raise ValueError(f"'Limit' must be between 1 and {MAX_LIMIT}.")
    except ValueError as exc:
        siemplify.end(str(exc), False)
        return

    manager = build_manager(siemplify)

    success_entities = []
    errors: list[str] = []
    json_results = {}
    result_value = False

    ip_entities = [
        entity for entity in siemplify.target_entities if entity.entity_type == ADDRESS
    ]

    for entity in ip_entities:
        try:
            data = manager.get_hosted_domains(entity.identifier, page=page, limit=limit)
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
        except Exception as err:  # noqa: BLE001
            error_message = (
                f"Failed fetching hosted-domains information for {entity.identifier}, "
                f"ERROR: {err}"
            )
            siemplify.LOGGER.error(error_message)
            siemplify.LOGGER.exception(err)
            errors.append(error_message)

    siemplify.update_entities(success_entities)

    if success_entities:
        identifiers = ", ".join(entity.identifier for entity in success_entities)
        output_message = f"Fetched hosted-domains information for: {identifiers}"
    else:
        output_message = "No hosted-domains information fetched for target entities."

    if errors:
        output_message = "{0}\n\nErrors:\n{1}".format(output_message, "\n".join(errors))

    siemplify.result.add_result_json(convert_dict_to_json_result_dict(json_results))
    siemplify.end(output_message, result_value)


if __name__ == "__main__":
    main()
