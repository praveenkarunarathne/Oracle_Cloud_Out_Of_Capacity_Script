import oci
import logging
import time
import sys
import telebot
import datetime
from dotenv import load_dotenv
import os

# ============================ CONFIGURATION ============================ #

load_dotenv()

availabilityDomains = os.getenv("AVAILABILITY_DOMAINS").split(",")
displayName = os.getenv("DISPLAY_NAME")
compartmentId = os.getenv("COMPARTMENT_ID")
subnetId = os.getenv("SUBNET_ID")
ssh_authorized_keys = os.getenv("SSH_AUTHORIZED_KEYS")

imageId = os.getenv("IMAGE_ID")
boot_volume_size_in_gbs = os.getenv("BOOT_VOLUME_SIZE_IN_GBS")
boot_volume_id = os.getenv("BOOT_VOLUME_ID")

bot_token = os.getenv("BOT_TOKEN")
uid = os.getenv("UID")

ocpus = int(os.getenv("OCPUS"))
memory_in_gbs = int(os.getenv("MEMORY_IN_GBS"))
minimum_time_interval = int(os.getenv("MINIMUM_TIME_INTERVAL"))

# ============================ LOGGING SETUP ============================ #

LOG_FORMAT = "[%(levelname)s] %(asctime)s - %(message)s"
logging.basicConfig(
    level=logging.INFO,
    format=LOG_FORMAT,
    handlers=[logging.StreamHandler(sys.stdout)]
)

logging.info("#####################################################")
logging.info("Script to spawn VM.Standard.E2.1.Micro instance")

# ============================ INITIAL SETUP ============================ #

if not bot_token == "xxxx" :
    bot = telebot.TeleBot(bot_token)
message = f"Start spawning instance VM.Standard.E2.1.Micro - {ocpus} ocpus - {memory_in_gbs} GB"
logging.info(message)

logging.info("Loading OCI config")
config = oci.config.from_file(file_location="./config")

logging.info("Initialize OCI service clients")
compute_client = oci.core.ComputeClient(config)
identity_client = oci.identity.IdentityClient(config)
vcn_client = oci.core.VirtualNetworkClient(config)
volume_client = oci.core.BlockstorageClient(config)

cloud_name = identity_client.get_tenancy(tenancy_id=compartmentId).data.name
email = identity_client.list_users(compartment_id=compartmentId).data[0].email

# ============================ STORAGE CHECK ============================ #

logging.info("Checking available storage in account")
total_volume_size = 0

if imageId != "xxxx":
    try:
        list_volumes = volume_client.list_volumes(compartment_id=compartmentId).data
    except Exception as e:
        logging.error(f"{e.status} - {e.code} - {e.message}")
        logging.error("Error detected. Check config and credentials. **SCRIPT STOPPED**")
        sys.exit()

    # Sum all active block and boot volumes
    for volume in list_volumes:
        if volume.lifecycle_state not in ("TERMINATING", "TERMINATED"):
            total_volume_size += volume.size_in_gbs

    for ad in availabilityDomains:
        boot_volumes = volume_client.list_boot_volumes(
            availability_domain=ad, compartment_id=compartmentId
        ).data
        for bvol in boot_volumes:
            if bvol.lifecycle_state not in ("TERMINATING", "TERMINATED"):
                total_volume_size += bvol.size_in_gbs

    free_storage = 200 - total_volume_size
    required_storage = (
        47 if boot_volume_size_in_gbs == "xxxx" else int(boot_volume_size_in_gbs)
    )

    if free_storage < required_storage:
        logging.critical(
            f"Only {free_storage} GB free out of 200 GB. "
            f"{required_storage} GB needed. **SCRIPT STOPPED**"
        )
        sys.exit()

# ============================ INSTANCE CHECK ============================ #

logging.info("Checking current instances")
instances = compute_client.list_instances(compartment_id=compartmentId).data

total_ocpus = total_memory = active_E2_instances = 0
instance_names = []

if instances:
    logging.info(f"{len(instances)} instance(s) found!")
    for instance in instances:
        logging.info(
            f"{instance.display_name} - {instance.shape} - "
            f"{int(instance.shape_config.ocpus)} ocpus - "
            f"{instance.shape_config.memory_in_gbs} GB | State: {instance.lifecycle_state}"
        )
        instance_names.append(instance.display_name)
        if instance.shape == "VM.Standard.E2.1.Micro" and instance.lifecycle_state not in ("TERMINATING", "TERMINATED"):
            active_E2_instances += 1
            total_ocpus += int(instance.shape_config.ocpus)
            total_memory += int(instance.shape_config.memory_in_gbs)
else:
    logging.info("No instances found!")

logging.info(
    f"Total ocpus: {total_ocpus} | Total memory: {total_memory} GB || "
    f"Free: {2 - total_ocpus} ocpus, {2 - total_memory} GB memory"
)

# Free-tier resource check
if total_ocpus + ocpus > 2 or total_memory + memory_in_gbs > 2:
    logging.critical("Free-tier resource limit exceeded (2 OCPUs / 2 GB max). **SCRIPT STOPPED**")
    sys.exit()

if displayName in instance_names:
    logging.critical(f"Duplicate display name '{displayName}' detected. **SCRIPT STOPPED**")
    sys.exit()

logging.info(f"Precheck passed! Ready to create instance: {ocpus} ocpus, {memory_in_gbs} GB")

# ============================ INSTANCE LAUNCH ============================ #

# Determine source details
if imageId != "xxxx":
    if boot_volume_size_in_gbs == "xxxx":
        source_details = oci.core.models.InstanceSourceViaImageDetails(
            source_type="image", image_id=imageId
        )
    else:
        source_details = oci.core.models.InstanceSourceViaImageDetails(
            source_type="image",
            image_id=imageId,
            boot_volume_size_in_gbs=boot_volume_size_in_gbs
        )
elif boot_volume_id != "xxxx":
    source_details = oci.core.models.InstanceSourceViaBootVolumeDetails(
        source_type="bootVolume", boot_volume_id=boot_volume_id
    )
else:
    logging.critical("No image or boot volume specified. **SCRIPT STOPPED**")
    sys.exit()

# Telegram status message
if bot_token != "xxxx" and uid != "xxxx":
    try:
        msg = (
            f"Cloud Account: {cloud_name}\n"
            f"Email: {email}\n"
            f"Number of Retry: 0\n"
            f"Bot Status: Running\n"
            f"Last Checked (UTC): {datetime.datetime.now(datetime.timezone.utc):%Y-%m-%d %H:%M:%S}"
        )
        msg_id = bot.send_message(uid, msg).id
    except Exception:
        msg_id = None

# ============================ RETRY LOOP ============================ #

wait_s_for_retry = 1
total_count = j_count = tc = oc = 0

while True:
    for ad in availabilityDomains:
        instance_detail = oci.core.models.LaunchInstanceDetails(
            metadata={"ssh_authorized_keys": ssh_authorized_keys},
            availability_domain=ad,
            shape="VM.Standard.E2.1.Micro",
            compartment_id=compartmentId,
            display_name=displayName,
            is_pv_encryption_in_transit_enabled=True,
            source_details=source_details,
            create_vnic_details=oci.core.models.CreateVnicDetails(
                assign_public_ip=True, subnet_id=subnetId
            ),
            shape_config=oci.core.models.LaunchInstanceShapeConfigDetails(
                ocpus=ocpus, memory_in_gbs=memory_in_gbs
            )
        )

        try:
            # Attempt to create instance
            launch_resp = compute_client.launch_instance(instance_detail)
            time.sleep(60)

            # Get public IP
            vnic_attachments = compute_client.list_vnic_attachments(
                compartment_id=compartmentId, instance_id=launch_resp.data.id
            ).data
            private_ips = vcn_client.list_private_ips(
                subnet_id=subnetId, vnic_id=vnic_attachments[0].vnic_id
            ).data
            public_ip = vcn_client.get_public_ip_by_private_ip_id(
                oci.core.models.GetPublicIpByPrivateIpIdDetails(private_ip_id=private_ips[0].id)
            ).data.ip_address

            total_count += 1
            logging.info(
                f'"{displayName}" VPS created successfully! IP: {public_ip}, '
                f"Retries: {total_count}, Cloud: {cloud_name}, Email: {email}"
            )

            # Telegram success message
            if bot_token != "xxxx" and uid != "xxxx" and msg_id:
                while True:
                    try:
                        bot.delete_message(uid, msg_id)
                        bot.send_message(
                            uid,
                            f'"{displayName}" VPS created successfully!\n'
                            f"Cloud Account: {cloud_name}\n"
                            f"Email: {email}\n"
                            f"Number of Retry: {total_count}\n"
                            f"VPS IP: {public_ip}"
                        )
                        break
                    except Exception:
                        time.sleep(5)

            sys.exit()

        except oci.exceptions.ServiceError as e:
            total_count += 1
            j_count += 1

            if j_count == 10:
                j_count = 0
                if bot_token != "xxxx" and uid != "xxxx" and msg_id:
                    try:
                        msg = (
                            f"Cloud Account: {cloud_name}\n"
                            f"Email: {email}\n"
                            f"Number of Retry: {total_count}\n"
                            f"Bot Status: Running\n"
                            f"Last Checked (UTC): {datetime.datetime.now(datetime.timezone.utc):%Y-%m-%d %H:%M:%S}"
                        )
                        bot.edit_message_text(msg, uid, msg_id)
                    except Exception:
                        pass

            # Handle throttling and other errors
            if e.status == 429:
                oc = 0
                tc += 1
                if tc == 2:
                    wait_s_for_retry += 1
                    tc = 0
            else:
                tc = 0
                if wait_s_for_retry > minimum_time_interval:
                    oc += 1
                if oc == 2:
                    wait_s_for_retry -= 1
                    oc = 0

            logging.info(
                f"{e.status} - {e.code} - {e.message}. Retrying after {wait_s_for_retry}s. "
                f"Retry count: {total_count}"
            )
            time.sleep(wait_s_for_retry)

        except Exception as e:
            total_count += 1
            j_count += 1
            if j_count == 10:
                j_count = 0
                if bot_token != "xxxx" and uid != "xxxx" and msg_id:
                    try:
                        msg = (
                            f"Cloud Account: {cloud_name}\n"
                            f"Email: {email}\n"
                            f"Number of Retry: {total_count}\n"
                            f"Bot Status: Running\n"
                            f"Last Checked (UTC): {datetime.datetime.now(datetime.timezone.utc):%Y-%m-%d %H:%M:%S}"
                        )
                        bot.edit_message_text(msg, uid, msg_id)
                    except Exception:
                        pass

            logging.info(f"{e}. Retrying after {wait_s_for_retry}s. Retry count: {total_count}")
            time.sleep(wait_s_for_retry)

        except KeyboardInterrupt:
            sys.exit()
