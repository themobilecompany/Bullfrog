#!/bin/bash

# Define a timestamp function
timestamp() {
  date +"%Y-%m-%d_%H:%M:%S"
}

timestamp && echo "Importing from Glassfrog..."
docker exec bullfrog_web_1 python manage.py import_glassfrog
timestamp && echo "Done importing."
