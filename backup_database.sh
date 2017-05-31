#!/bin/bash

# THIS SCRIPT SHOULD BE EXECUTED EACH DAY
# FROM INSIDE THE DOCKER CONTAINER
# It can however be invoked FROM the host (crontab) via:
# docker exec bullfrog_web_1 /bin/bash backup_database.sh
# See cron_daily.sh for more info

# FOR COPYING THE BACKUP FILE TO A REMOTE LOCATION
# THE HOST SHOULD RUN THE 'backup_copy_to_remote.sh' SCRIPT
# See cron_daily.sh for more info


# Variables
_dayofweek="$(date +'%A')"
_jsondump_filename="database_backup.${_dayofweek}.json"

# Timestamp function
timestamp(){
  date +"%Y-%m-%d_%H:%M:%S"
}

#start
timestamp && echo "backup_database.sh script started."

# Dump database data
echo "Dump database data to $_jsondump_filename"
python manage.py dumpdata --natural-primary --natural-foreign --indent=4 -e sessions -e admin -e contenttypes > ${_jsondump_filename}

# Done
timestamp && echo "backup_database.sh script done (success unknown)"
