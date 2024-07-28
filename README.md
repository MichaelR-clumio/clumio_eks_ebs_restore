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

# FOR EXAMPLE PURPOSES ONLY

#
# Requirements: 
#  Secure account to deploy resources for scanning 
#  Local account to install lambdas and step function
#  Role in secure account that can descibe and delete EC2 scanned resources and initiate guardduty scans
#  Role in local account that can assume role in secure account
#  
#  S3 bucket in same region where stepfunction/lambdas are to be deployed 
#
# Upload lambda zip file "clumio_scan_restore_guardduty.zip" into S3 bucket
# Modify the lambda deployment cft "clumio_restore_and_scan_guardduty_lambda_deploy_cft.yaml" to include your S3 bucket name and modify key name to include prefix if lambda zip is not in root of the bucket
# Run the lambda deployment CFT
# Modify step function json "clumio_restore_and_scan_state_machine.json" to point to your lambda functions (6 in total).  Note:  name will be the same but aws account id an region will be different.
# Create a new step function.  select on the code option in the builder.  copy and paste code from your modified step function json file.
#
# Modify inputs json "example_step_function_inputs.json" to include your data
#  - "source_account"  account where data was backed up from
#  - "source_region"     region where data was backed up from
#
#   NEXT Two values determine which backups (by time) you want to use
#  - "search_day_offset":   - Point in time to use as a reference for the search.  0 means start with most recent backups, 1 means start with backup from 1 day ago, etc      
#  - "search_direction":   - direction to search.  before or after - before searches for dates at or older then the point of reference.  after searches for dates newer then the point of reference

# Target values are configuraiton or infrastuructor values in the secure account

#  - "target_account": 
#  "target_region": 
#  "target_az": 
#  "target_iam_instance_profile_name": 
#  "target_key_pair_name": 
#  "target_security_group_native_ids": 
#  "target_subnet_native_id":
#  "target_vpc_native_id": 
#  "target_kms_key_native_id": 
#  "target_role_arn": role in secure account that can be assumeed by local/lambda role,
#
# Execute the step function passing it the contents of the modified inputs json.
#
# Lambda function code
#
# aws_guardduty_check_scan_status.py - checks if scan has completed
# aws_guardduty_scan_response.py - does final processing after scan completes
# aws_guardduty_start_scan.py - starts guardduty scan
# clumio_ec2_list_backups.py - generates a list of records for all backups that are to be scanned
# clumio_ec2_restore_guardduty.py - restores an ec2 instnace in the secure account
# clumio_retrieve_task.py - waits for restore to finish

# clumio_sdk_v9.py - the "helper" sdk
