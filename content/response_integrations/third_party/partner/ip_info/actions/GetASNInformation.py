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

from __future__ import annotations

from soar_sdk.SiemplifyAction import SiemplifyAction
from soar_sdk.SiemplifyUtils import (
    convert_dict_to_json_result_dict,
    dict_to_flat,
    flat_dict_to_csv,
    output_handler,
)

from ._common import build_manager

ACTION_NAME = "IPInfo Get_ASN_Information"


@output_handler
def main():
    siemplify = SiemplifyAction()
    siemplify.script_name = ACTION_NAME

    asn_param = siemplify.extract_action_param(param_name="ASN", is_mandatory=True, print_value=True)

    manager = build_manager(siemplify)
    json_results = {}
    result_value = False
    output_message = ""

    try:
        data = manager.get_asn_information(asn_param)
        if data:
            json_results[asn_param] = data
            flat_info = dict_to_flat(data)
            siemplify.result.add_data_table(asn_param, flat_dict_to_csv(flat_info))
            result_value = True
            output_message = f"Fetched ASN information for: {asn_param}"
        else:
            output_message = f"No ASN information returned for {asn_param}."
    except Exception as err:  # noqa: BLE001
        error_message = f"Failed fetching ASN information for {asn_param}, ERROR: {err}"
        siemplify.LOGGER.error(error_message)
        siemplify.LOGGER.exception(err)
        output_message = error_message

    siemplify.result.add_result_json(convert_dict_to_json_result_dict(json_results))
    siemplify.end(output_message, result_value)


if __name__ == "__main__":
    main()
