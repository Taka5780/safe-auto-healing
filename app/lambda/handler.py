import time
import traceback
import urllib.error
import urllib.request

import boto3
from utils.slack import send_slack

ssm = boto3.client("ssm")
ec2 = boto3.client("ec2")


def lambda_handler(event, context):
    print("Received event:", event)

    try:
        alarm_data = event.get("alarmData", {})
        state = alarm_data.get("state", {})
        current_value = state.get("value")

        if current_value != "ALARM":
            print(f"Skipping: Alarm state is {current_value}")
            return

        alarm_name = alarm_data.get("alarmName", "Unknown Alarm")
        configuration = alarm_data.get("configuration", {})
        metrics = configuration.get("metrics", [{}])
        dimensions = (
            metrics[0].get("metricStat", {}).get("metric", {}).get("dimensions", {})
        )
        instance_id = dimensions.get("InstanceId")

        if not instance_id:
            raise Exception(
                f"InstanceId not found. Event structure: {list(event.keys())}"
            )

        ec2_resp = ec2.describe_instances(InstanceIds=[instance_id])
        reservations = ec2_resp.get("Reservations", [])
        if not reservations:
            raise Exception(f"No reservations found for {instance_id}")
        instances = reservations[0].get("Instances", [])
        if not instances:
            raise Exception(f"No instances found for {instance_id}")

        target_instance = instances[0]
        tags = target_instance.get("Tags", [])

        is_target = any(
            t.get("Key") == "auto-healing" and str(t.get("Value", "")).lower() == "true"
            for t in tags
        )

        if not is_target:
            print(f"Skipping: Instance {instance_id} is not tagged for auto-healing.")
            return

        ssm_resp = ssm.send_command(
            InstanceIds=[instance_id],
            DocumentName="AWS-RunShellScript",
            Parameters={"commands": ["sudo systemctl restart nginx"]},
            Comment="Auto-healing by Lambda",
        )
        command_id = ssm_resp.get("Command", {}).get("CommandId")
        if not command_id:
            raise Exception("Failed to get CommandId from SSM response.")

        status_result = "NG"
        instance_ip = target_instance.get("PublicIpAddress") or target_instance.get(
            "PrivateIpAddress"
        )

        for i in range(5):
            print(f"Checking recovery status... attempt {i + 1}")
            time.sleep(3)

            try:
                invocation = ssm.get_command_invocation(
                    CommandId=command_id, InstanceId=instance_id
                )
                ssm_status = invocation.get("Status")

                if ssm_status in ["Pending", "InProgress"]:
                    continue

                if ssm_status == "Success":
                    if instance_ip:
                        try:
                            req = urllib.request.Request(
                                f"http://{instance_ip}",
                                headers={"User-Agent": "AutoHealingCheck"},
                            )
                            with urllib.request.urlopen(req, timeout=2) as res:
                                if res.getcode() == 200:
                                    status_result = "OK"
                                    break
                        except (urllib.error.URLError, urllib.error.HTTPError) as e:
                            print(f"Health check failed: {e}")
                elif ssm_status in ["Failed", "Cancelled", "TimedOut"]:
                    break
            except Exception as e:
                print(f"Waiting for command invocation: {e}")

        now = time.strftime("%Y-%m-%d %H:%M:%S")
        emoji = "✅" if status_result == "OK" else "🚨"

        message = (
            f"{emoji} *[Auto-Healing {'SUCCESS' if status_result == 'OK' else 'FAIL'}]*\n\n"
            f"*Time:* `{now}`\n"
            f"*Instance:* `{instance_id}`\n"
            f"*Alarm:* `{alarm_name}`\n"
            f"*Action:* Nginx Restart\n"
            f"*Result:* `{status_result}`"
        )
        if status_result == "NG":
            message += "\n\n→ *Manual intervention is required.*"

        send_slack(message)

    except Exception:
        error_trace = traceback.format_exc()
        print(error_trace)
        send_slack(f"❌ *Auto-healing System Error*\n```\n{error_trace}\n```")

    return {"statusCode": 200}
