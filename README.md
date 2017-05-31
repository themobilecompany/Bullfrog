# Bullfrog v.0.2 alpha
For organisations that have implemented Holocracy, an *Attention Point Management System* with Glassfrog integration, based on [The Mobile Company's](https://themobilecompany.com/?utm_source=bullfrog) Attention Points System Policy and implementation.

### More info
This tool connects to the [Glassfrog Api](https://github.com/holacracyone/glassfrog-api/tree/API_v3) to download all People, Circles and Roles, and their connections.
These are imported into a local database, and values are updated when imported again (either manually via the web interface, or via a scheduled cronjob).
The web interface allows logged in users (credentials to be created via the /admin interface) to administer and review Attention Points per RoleFiller and Sub-Circle.
The assigned Attention Points of RoleFillers in nested circles propagate up the parent circle, showing as "assigned attention points" of the sub-circles.

### Dependencies and Requirements
- Docker
- Docker-compose
- Glassfrog Api Version 3 Api Key (get one here: https://app.glassfrog.com/api_keys)
- Some basic knowledge in Docker, Django, Python, bash

### To do:
 - Randomise password generation for new users (GlassfrogImporter.py)
 - Set up SMTP mail to email new users when an account is created for them (GlassfrogImporter.py)

---

## Pre-setup instructions
1. Download the source code and host it in on your Git servers.
2. In the file `backup_copy_to_remote.sh`, update the values for `_path_to_backup_dir` and `_path_to_source_dir`.
3. In the file `GlassfrogApi/GlassfrogExporter.py`, insert your Glassfrog API key into `API_KEY`

## Set up instructions for the server
We're assuming you've set up in a Linux environment. In our case, we used CentOS7 virtual server (where **Docker is already installed**)
1. Install [Docker-compose](https://docs.docker.com/compose/install/)

    ```
    sudo yum install epel-release
    sudo yum install -y python-pip
    sudo pip install docker-compose
    sudo yum upgrade python*
    sudo yum install git
    ```
2. Clone the git repository you set up in the pre-setup instructions
    ```
    git clone https://{PATH_TO_YOUR_GIT}/bullfrog.git /srv
    ```
3. For our Docker installation, it expects `Dockerfile` instead of `DockerFile`
    ```
    cp /srv/DockerFile /srv/Dockerfile
    ```
4. Setup a mounted file share for automatic backups

    ```
    yum install samba-client samba-common cifs-utils
    mkdir /mnt/{YOUR_BACKUP_DIR}
    nano /etc/fstab
    ```
5. Auto-start the Docker Daemon: 
    ```
    sudo chkconfig docker on
    ```
6. Mount the network share for backups by adding this following to `/etc/fstab`: 
    ```
    //{YOUR_SERVER_IP}/{YOUR_BACKUP_DIR} /mnt/{YOUR_BACKUP_DIR} cifs {YOUR_GIT_USER_CREDENTIALS},users,auto,user_$
    ```
    
    Then run `mount -a`.
7. Set up Contab jobs for auto importing and backup:
    ```
    sudo crontab -e
    ```
    
    Then:
    ```
    @reboot mount -a
    0 20 * * * /bin/bash /srv/bullfrog/cron_daily.sh
    */10 * * * * /bin/bash /srv/bullfrog/cron_10_minutely.sh
    #empty line needed
    ```
8. Now that your server environment is ready, you'll need to set up the application. See the `Set up instructions for Development` below.

## Set up instructions for Development
If you are setting up on the server, skip step 1 and 2 (since you have already done that by following `Set up instructions for the server`)

1. Download and install Docker for your environment. E.g. [Docker for Mac](https://docs.docker.com/engine/installation/mac/)
2. Clone the git repository to your local machine
3. Rename `/bullfrog/local_settings.py.empty` to `/bullfrog/local_settings.py` and edit it to set the correct variables.
    - At a minimum, the file should contain the following:
        ```
        DEBUG = True
        ALLOWED_HOSTS = [
            '127.0.0.1', 'localhost', '0.0.0.0'  # set to local ip of production server
        ]
        DEFAULT_PASSWORD = 'test'  # set a default password for new users. they will need to change it on first use
        ```
4. Open terminal from the `bullfrog` directory and do the following:
    - Build the containers with: `docker-compose build`
    - Expose the ports and run the containers with: `docker-compose up`
    - *For some reason, when doing this the first time, the DB doesn't respond to the webserver, so we need to CTRL+C and run `docker-compose up` again*
5. Run the migration script and create a root user:
    - EASY MODE (on a Mac):
        - Go to the Docker icon in your status bar (top right), select 'Open Kitematic'
        - Select the webserver (probably named 'bullfrog_web_1'), select the 'EXEC' button next to the Stop and Restart buttons.
        - This should open a bash session in your container
        - Enter `python manage.py migrate`
        - Enter `python manage.py createsuperuser`
    - HARD MODE (everywhere else, including on your server):
        - In terminal, `$~> docker ps` ==> Note the "CONTAINER ID" of the "bullfrogdocker_web" container
        - Login to the web container:`$>docker exec -i -t <Container ID> /bin/bash
        - Run database migration: `root/code# python manage.py migrate`
        - Create superuser, to be able to login to the admin panel: `root:/code# python manage.py createsuperuser`
6. Run the initial import by going to [http://localhost:8000/import](http://localhost:8000/import) if on your own machine. If setting up on your server, then replace `localhost` with your server's hostname.
    - Login with the root user you created
    - You may receive an error of some sort. **We'll resolve this in the future.**
    For now, go back to [http://localhost:8000](http://localhost:8000/import) and you should see that the import completed successfully
    - If setting up on your Mac with Kitematic, you'll see the import logs in the Kitematic container log.
7. Alternatively, import an already existing database with `python manage.py loaddata BACKUP_FILENAME.json `
  - To copy the latest backup files from production, open terminal on your local computer, login and enter the following ()where `DAY` is the day of the week you want to copy and `/bullfrog` is your local directory):
      ```
      scp root@192.168.112.21:/srv/bullfrog/database_backup.DAY.json /bullfrog
      ```

>If you receive a **'Bad Request (400)'** error, try quitting the server (CTRL-C) and running 'docker-compose up' again, or restart the web container.
This could be due the DB container completing its startup procedure after the web container starts up, resulting in an invalid connection to the database container.

>If you receive a **500 error**, ensure you have run `python manage.py migrate` from the web container

#### Docker for Mac known issues:
 - If you set DEBUG = False in local_settings.py, the server doesn't work... TBD

### Development - Windows (or Docker Toolbox)
Besides some intricacies, the "Development - Mac" guide can be used.
- If your Windows version does not support 'Docker for Windows', than use 'Docker Toolbox'.
- You might need an `.env` file in the project root with this line in it `COMPOSE_CONVERT_WINDOWS_PATHS=1`.

## Making changes in Development

### Changing database schemas
When you make changes to the data models in `models.py`, you have to migrate the database:
- In the docker web container, run `python manage.py makemigrations`
- Followed by `python manage.py migrate`
The 'makemigrations' command will create migration files that need to be committed to git, so they can be run on production during deployment.
*Note*: these migration instructions are sequential, take care when changing the models while working in multiple Git branches!

### Adding static files (\*.js, \*.png, etc)
When adding, editing, or removing static files in the APS app directory, you will need to regenerate the static files for Django via WhiteNoise. You can do this with `python manage.py collectstatic` in the Docker web container. This will run through the entire app and collect + compress the relevant static files.
Note: You may also need to restart your Django web server after running `collectstatic`

---

# Production

##### SSH into production server  
You should be able to SSH into your production server using the following (after logging in):
```
ssh {YOUR_SERVERS_IP}
root@localhost:~ $ cd /srv/bullfrog
root@localhost:~/srv/bullfrog $
```

### Deploying to production
- Merge changes to `master` branch
- SSH into production server, and navigate to codebase directory (see "SSH into production sever")
- Make sure you are on a clean master branch: `git status`
- Run `git pull`. Use the same root password.
- If new database schema, run: `docker exec bullfrog_web_1 python manage.py migrate`
- If new static files (javascript, css images, etc), run: `docker exec bullfrog_web_1 python manage.py collectstatic` (should probably have been done by developer before committing to master)

### Starting the containers in the background
- Initially do: `docker-compose up`
- Stop once: `ctrl-c`
- Start again in background thread: `docker-compose up &` (***NOTE*** the '&' in the end!)
- Check if webserver runs: Open your browser and enter your server's IP address
    - If not, stop server via `docker-compose down`, and repeat process
- Run migrations on the database: `docker exec bullfrog_web_1 python manage.py migrate`
- Follow the *'Restoring a database backup'* steps below. (`exit` to leave the container shell)
- Check if everything works and all data is restored
- Reboot the server: `reboot` (give the server some time to come back up)
- Check again if the website works properly.

### Restoring a database backup
- SSH into bullfrog docker host (see "SSH into production server")
- Copy the backup file into the web container, e.g.:
  `$>docker cp /mnt/{YOUR_REPO_PATH}/database_backup.Saturday.json bullfrog_web_1:/code/`
  Note: The path should be a mounted network share, as setup outside of the docker host.
- Login to the web container
    - via container name, e.g.:
    `$>docker exec -it bullfrog_web_1 bash`
    - _OR_ via container ID (obtain via `docker ps`):
    `$>docker exec -it <Container ID> /bin/bash`
- Export the current database, just to be sure
    - Default method (includes everything but might be hard to restore):
      `root:/code# python manage.py dumpdata > backup.json`
    - _AND_ Fancy method (excludes some stuff but might work better for restoring):
      `root:/code# python manage.py dumpdata --natural-primary --natural-foreign --indent=4 -e sessions -e admin -e contenttypes > backup_natural_keys.json`
- Flush (empty) the current database:
  `root:/code# python manage.py flush`
- Load backup into database, e.g.:
  `root:/code# python manage.py loaddata database_backup.Saturday.json`

### Troubleshooting
Check the mail file for logs from the cronjob processes, that might help understand any problems:
`$> cat /var/spool/mail/root`

If you can't isolate the problem, try re-building the whole container from scratch.
- Stop the containers: `docker-compose down`
- Remove all persistent volumes (DATA WILL BE LOST, NO WAY BACK!):
    - Find container names with: `docker volume ls`
    - Remove one by one with: `docker volume rm <name>`, e.g. `docker volume rm bullfrog_bullfrog-db-volume`
    - Also remove the 'local' ones, with random hash names, e.g. `docker volume rm ea3f55c439320876e278cb5230164601d6271fea9d11720ebb153b96ac67d64c`
    - Check that all are gone: `docker volume ls`
- Rebuild the containers: `docker-compose build`
- Start containers: see *'Starting containers in the background'*
