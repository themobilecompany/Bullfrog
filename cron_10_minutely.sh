# THIS FILE SHOULD BE RUN EACH 10 MINUTES, via a cronjob
# OR AS OFTEN AS YOU WANT TO IMPORT FROM GLASSFROG
# Content of the crontab (edit with `sudo crontab -e`):
# */10 * * * * /bin/bash /srv/bullfrog/cron_10_minutely.sh

# use absolute path to bullfrog source
bash /srv/bullfrog/import_from_glassfrog.sh
