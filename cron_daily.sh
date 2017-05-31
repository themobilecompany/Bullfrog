# THIS FILE SHOULD BE RUN DAILY, via a cronjob
# IT RUNS THE BACKUP SCRIPT INSIDE THE DOCKER CONTAINER
# AND COPIES THE BACKUP TO A REMOTE LOCATION
#
# Content of the crontab (edit with `sudo crontab -e`):
# @reboot mount -a
# 0 20 * * * /bin/bash /srv/bullfrog/cron_daily.sh
#

# note that the container name 'bullfrog_web_1' could be different on other host systems
docker exec bullfrog_web_1 /bin/bash backup_database.sh

# use absolute path to bullfrog source
bash /srv/bullfrog/backup_copy_to_remote.sh
