import time
import traceback
import urllib.request
from datetime import datetime, timedelta, timezone

import boto3
from utils.slack import send_slack

ssm = boto3.client("ssm")
ec2 = boto3.client("ec2")

JST = timezone(timedelta(hours=+9), "JST")


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
        instance_state = target_instance.get("State", {}).get("Name", "unknown")
        instance_name = next(
            (t.get("Value") for t in tags if t.get("Key") == "Name"), instance_id
        )

        is_target = any(
            t.get("Key") == "auto-healing" and str(t.get("Value", "")).lower() == "true"
            for t in tags
        )
        if not is_target:
            print(f"Skipping: Instance {instance_id} is not tagged for auto-healing.")
            return

        now_jst = datetime.now(JST).strftime("%Y-%m-%d %H:%M:%S")

        # Scenario 1: Auto-Healing (Nginx down)
        if "auto-healing" in alarm_name:
            action_name = "Nginx Restart (L1)"
            status_result, detail_info = execute_auto_healing(
                instance_id, target_instance
            )

            emoji = "✅" if status_result == "OK" else "🚨"
            message = (
                f"{emoji} *[Auto-Healing {'SUCCESS' if status_result == 'OK' else 'FAIL'}]*\n\n"
                f"*Time:* `{now_jst}` (JST)\n"
                f"*Instance:* `{instance_name}` ({instance_id})\n"
                f"*Alarm:* `{alarm_name}`\n"
                f"*Action:* `{action_name}`\n"
                f"*Result:* `{status_result}`\n"
                f"*Detail:* {detail_info}"
            )

        # Scenario 2: Human Decision (CPU High)
        elif "human-decision" in alarm_name:
            action_name = "Process Investigation (L2)"
            status_result, detail_info = execute_investigation(instance_id)

            message = (
                "🚨 *[ALERT] Service Impact Suspected*\n\n"
                f"*Instance:* `{instance_name}` ({instance_id})\n"
                f"*Alarm:* `CPU High`\n"
                f"*Value:* `Over 30%` (As detected)\n\n"
                "*Additional Info:*\n"
                f"- Current status: `{instance_state}`\n"
                f"- Triggered at: `{now_jst}` (JST)\n"
                "- Recovery action: `None (Investigation only)`\n\n"
                "*Suggested Actions:*\n"
                "1. Check the process list below\n"
                "2. Reboot instance if necessary\n"
                "3. Check application logs\n\n"
                "*Status:* `[UNRESOLVED]`\n"
                "---\n"
                f"*Current Top Processes:*\n```\n{detail_info}\n```"
            )

        else:
            print(f"No matching scenario for alarm: {alarm_name}")
            return

        if status_result == "NG" and "human-decision" not in alarm_name:
            message += "\n\n→ *Manual intervention is required.*"

        send_slack(message)

    except Exception:
        error_trace = traceback.format_exc()
        print(error_trace)
        send_slack(f"❌ *System Error*\n```\n{error_trace}\n```")

    return {"statusCode": 200}


def execute_auto_healing(instance_id, target_instance):
    ssm.send_command(
        InstanceIds=[instance_id],
        DocumentName="AWS-RunShellScript",
        Parameters={"commands": ["sudo systemctl restart nginx"]},
    )

    instance_ip = target_instance.get("PublicIpAddress") or target_instance.get(
        "PrivateIpAddress"
    )
    time.sleep(5)

    try:
        req = urllib.request.Request(
            f"http://{instance_ip}", headers={"User-Agent": "AutoHealingCheck"}
        )
        with urllib.request.urlopen(req, timeout=2) as res:
            if res.getcode() == 200:
                return "OK", "Nginx is back online and responding to HTTP 200."
    except Exception as e:
        print(f"Health check failed: {e}")

    return "NG", "Nginx failed to recover or health check timed out."


def execute_investigation(instance_id):
    cmd = "ps -eo pid,user,%cpu,command --sort=-%cpu | head -n 10"
    ssm_resp = ssm.send_command(
        InstanceIds=[instance_id],
        DocumentName="AWS-RunShellScript",
        Parameters={"commands": [cmd]},
    )
    command_id = ssm_resp["Command"]["CommandId"]

    time.sleep(3)
    try:
        invocation = ssm.get_command_invocation(
            CommandId=command_id, InstanceId=instance_id
        )
        if invocation["Status"] == "Success":
            return "OK", invocation.get(
                "StandardOutputContent", "No output from command."
            )
        return "NG", f"SSM Command Status: {invocation['Status']}"
    except Exception as e:
        return "NG", f"Failed to get command output: {str(e)}"
