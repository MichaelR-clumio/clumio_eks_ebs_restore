# Copyright 2024, Clumio Inc.

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#    http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from botocore.exceptions import ClientError
from clumio_sdk_v9 import DynamoDBBackupList, RestoreDDN, ClumioConnectAccount, AWSOrgAccount, ListEC2Instance, \
    EnvironmentId, RestoreEC2, EC2BackupList, EBSBackupList, RestoreEBS, OnDemandBackupEC2, RetrieveTask


def lambda_handler(events, context):
    bear = events.get('bear', None)
    source_account = events.get('source_account', None)
    source_region = events.get('source_region', None)
    search_direction = events.get('search_direction', None)
    search_day_offset_input = events.get('search_day_offset', None)
    debug_input = events.get('debug', None)
    velero_manifest_dict = events.get("velero_manifest", None)

    source_volume_id = velero_manifest_dict.get("spec", {}).get("providerVolumeID")

    inputs = {
        'record': [],
    }

    # Validate inputs
    try:
        search_day_offset = int(search_day_offset_input)
    except ValueError as e:
        error = f"invalid task id: {e}"
        return {"status": 401, "msg": f"failed {error}", "inputs": inputs}
    try:
        debug = int(debug_input)
    except ValueError as e:
        error = f"invalid debug: {e}"
        return {"status": 402, "msg": f"failed {error}", "inputs": inputs}

    # Initiate API and configure
    ebs_backup_list_api = EBSBackupList()
    ebs_backup_list_api.set_token(bear)
    ebs_backup_list_api.set_debug(debug)

    # Set search parameters
    ebs_backup_list_api.set_search_start_day(search_day_offset)
    ebs_backup_list_api.set_search_time_frame_before_after(search_direction)
    ebs_backup_list_api.set_aws_account_id(source_account)
    ebs_backup_list_api.set_aws_region(source_region)

    # Run search
    ebs_backup_list_api.run_all()

    # Parse and return results
    result_dict = ebs_backup_list_api.ebs_parse_results("restore")

    records = result_dict.get("records", [])
    # print(f"EBS records {records}")
    found_vol = False
    if not len(records) > 1:
        return {"status": 403, "msg": "no records found", "inputs": inputs}
    inputs = {
        'record': records,
    }
    for record in records:
        # print(f"source {source_volume_id} and {record.get("volume_id", None)}")
        if record.get("volume_id", None) == source_volume_id:
            found_vol = True
            inputs = {
                'record': [record],
            }
            return {"status": 200, "msg": "record found", "inputs": inputs}
    return {"status": 404,"msg": f"volume {source_volume_id} not found in backup records", "inputs": inputs}