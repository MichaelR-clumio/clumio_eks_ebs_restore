# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from botocore.exceptions import ClientError
import boto3
from clumio_sdk_v9 import DynamoDBBackupList, RestoreDDN, ClumioConnectAccount, AWSOrgAccount, ListEC2Instance, \
    EnvironmentId, RestoreEC2, EC2BackupList, EBSBackupList, RestoreEBS, OnDemandBackupEC2, RetrieveTask


def lambda_handler(events, context):
    debug = events.get('debug', None)
    target_region = events.get('target_region', None)
    target_account = events.get('target_account', None)
    target_role_arn = events.get('target_role_arn', None)
    source_backup_id = events.get('inputs', {}).get('source_backup_id',None)
    velero_manifest_dict = events.get("velero_manifest", None)

    source_volume_id = velero_manifest_dict.get("spec", {}).get("providerVolumeID")

    aws_account_mng = AWSOrgAccount()
    aws_account_mng.set_debug(debug)
    volume_deleted = False
    [status, msg, cred] = aws_account_mng.connect_assume_role("boto3", target_role_arn, 'a')
    if not status:
        return {"status": 401, "msg": msg, "manifest": {}, "volume_deleted": volume_deleted}

    aws_access_key_id = cred.get("AccessKeyId", None)
    aws_secret_access_key = cred.get('SecretAccessKey', None)
    aws_session_token = cred.get('SessionToken', None)
    region = target_region

    try:
        aws_session1 = boto3.Session(
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            aws_session_token=aws_session_token,
            region_name=region
        )
    except ClientError as e:
        error = e.response['Error']['Code']
        error_msg = f"failed to initiate session {error}"
        # print("in DataDump 03")
        payload = error_msg
        return {"status": 402, "msg": error_msg, "manifest": {}, "volume_deleted": volume_deleted}
    client_ebs = aws_session1.client('ec2')

    if debug > 5: print(f"aws_create_volume_snapshot: looking for tag with value of {source_volume_id}")
    try:
        desc_volume = client_ebs.describe_volumes(
            Filters=[
                {
                    'Name': 'tag:source_backup_id',
                    'Values': [source_backup_id]
                },
            ],
        )
    except ClientError as e:
        error = e.response['Error']['Code']
        error_msg = f"Describe Volume failed - {error}"
        payload = error_msg
        return {"status": 403, "msg": error_msg, "manifest": {}, "volume_deleted": volume_deleted}
    if len(desc_volume.get('Volumes', [])) == 0:
        return {"status": 404, "msg": f"no volumes found {desc_volume}", "manifest": {}, "volume_deleted": volume_deleted}
    new_volume = desc_volume.get('Volumes', [])[0].get('VolumeId', None)
    try:
        create_snap = client_ebs.create_snapshot(
            Description='created by eks_clumio restore process',
            VolumeId=new_volume,
            TagSpecifications=[
                {
                    'ResourceType': 'snapshot',
                    'Tags': [
                        {
                            'Key': 'original_volume',
                            'Value': source_volume_id
                        },
                        {
                            'Key': 'original_backup_id',
                            'Value': source_backup_id
                        },
                    ]
                },
            ],
            DryRun=False
        )
    except ClientError as e:
        error = e.response['Error']['Code']
        error_msg = f"Create snapshot failed - {error}"
        payload = error_msg
        return {"status": 405, "msg": error_msg, "manifest": {}, "volume_deleted": volume_deleted}
    new_snapshot_id = create_snap.get('SnapshotId', None)
    if debug > 5: print(f"aws_create_volume_snapshot: new snapshot id {new_snapshot_id}")
    # Wait until snapshot creation as started before deleting volume
    time.sleep(30)
    try:
        del_vol = client_ebs.delete_volume(
            VolumeId=new_volume,
        )
        volume_deleted = True
    except ClientError as e:
        error = e.response['Error']['Code']
        error_msg = f"- {error}"
        if debug > 1: print(f"aws_create_volume_snapshot: delete of {new_volume} failed {error_msg}")
    new_velero_manifest_dict = dict(velero_manifest_dict)
    new_velero_manifest_dict["status"]["providerSnapshotID"] = new_snapshot_id

    return {"status": 200, "msg": "done", "manifest": new_velero_manifest_dict, "volume_deleted": volume_deleted}