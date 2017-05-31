#!/bin/bash

# THIS SCRIPT SHOULD BE EXECUTED EACH DAY, AFTER THE 'backup_database.sh' is run in the container
# THIS SCRIPT SHOULD BE RUN FROM THE HOST (via crontab)
# See cron_daily.sh for more info

# Variables
_dayofweek="$(date +'%A')"
_jsondump_filename="database_backup.${_dayofweek}.json"

# SET BELOW TO THE PATH OF A MOUNTED NETWORK SHARE, e.g. "/mnt/Bullfrog"
_path_to_backup_dir="{YOUR_BACKUP_PATH}"
# SET BELOW TO THE PATH OF THE DOCKER CONTAINER SOURCE, e.g. "/srv/bullfrog"
_path_to_source_dir="{YOUR_PATH_TO_DOCKER_CONTAINER_SOURCE}"

# Timestamp function
timestamp(){
  date +"%Y-%m-%d_%H:%M:%S"
}

#start
timestamp && echo "backup_copy_to_remote.sh script started."

# Copy to backup location
echo "Copy $_path_to_source_dir/$_jsondump_filename to $_path_to_backup_dir/$_jsondump_filename"
cp ${_path_to_source_dir}/${_jsondump_filename} ${_path_to_backup_dir}/${_jsondump_filename}

# Done
timestamp && echo "backup_copy_to_remote.sh script done (success unknown)"
