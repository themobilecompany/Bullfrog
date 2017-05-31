__author__ = 'Erie'

from GlassfrogApi.GlassfrogExporter import GlassfrogExporter
from django.utils import timezone
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings

from aps.models import Person
from aps.models import Circle
from aps.models import Role
from aps.models import RoleFiller

class GlassfrogImporter(GlassfrogExporter):

    def __init__(self):
        super(GlassfrogImporter, self).__init__()

    def doImport(self):
        # get data from glassfrog
        self.doExport()
        # reconstruct / enrich the Glassfrog api results
        # glassfrog api does not return enriched data, only referenced id's
        self.enrichData()
        # create list of all rolefillers (role + person combo's)
        self.buildRoleFillers()

        #store values in database
        self.updateDatabaseCoreObjects(Person,     importedObjects=self.people,      glassfrogUrlStub="people")
        self.updateDatabaseCoreObjects(Circle,     importedObjects=self.circles,     glassfrogUrlStub="circles")
        self.updateDatabaseCoreObjects(Role,       importedObjects=self.roles,       glassfrogUrlStub="roles")
        self.updateDatabaseRoleFillers(importedObjects=self.rolefillers)

    def updateDatabaseCoreObjects(self, modelObject, importedObjects, glassfrogUrlStub):
        now = timezone.now()
        for importedObject in importedObjects:
            values = {
                "name":          importedObject['name'],
                "glassfrog_id":  importedObject['id'],
                "glassfrog_url": "https://app.glassfrog.com/"+glassfrogUrlStub+"/"+str(importedObject['id']),
                "last_imported": now
            }

            # For Roles, we have to find the linked Circle that should already be in the database
            # If the linked circle is NOT found, the role is STILL imported/updated, with Null as default value
            if modelObject==Role:
                try:
                    values['circle'] = Circle.objects.get(glassfrog_id=importedObject['links']['circle'])
                except Circle.DoesNotExist:
                    values['circle'] = None
                    pass
                # We also have to check if this role represents a sub-circle (that circle should already be in the database, otherwise this will not work)
                try:
                    values['supporting_circle'] = Circle.objects.get(glassfrog_id=importedObject['links']['supporting_circle'])
                except Circle.DoesNotExist:
                    values['supporting_circle'] = None
                    pass

            # For Circles, we have to find the parent Circle (that hopefully already exists in the database)
            # If the linked circle is NOT found, the Circle is STILL imported/updated, without a super-circle set.
            if modelObject==Circle:
                try:
                    values['super_circle'] = Circle.objects.get(glassfrog_id=importedObject['links']['super_circle'])
                except Circle.DoesNotExist:
                    # Circle is NOT found in the database, default to null
                    values['super_circle'] = None
                    pass

            obj, created = modelObject.objects.update_or_create(
                glassfrog_id=values['glassfrog_id'], # search for this value, if found, update with 'values', otherwise insert new row with 'values'
                defaults=values
            )

            # For People, also create a bullfrog user that they can login with (if none is linked yet)
            # and send him temp credentials via email
            if modelObject==Person and not obj.user:
                username = importedObject['email'].split("@")[0] # grab the username from the email address
                names = username.split('.') # split username in parts, separated by dot (.)
                password = settings.DEFAULT_PASSWORD # TODO: change to: ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(8))
                email = importedObject['email']

                # Check if the User object already exist, and only create if it doesn't. This fixes a bug which occured when an import previous failed, and the user object was already created
                if not User.objects.filter(username=username).exists():
                    user = User.objects.create_user(
                        username=username,
                        email=email,
                        password=password,
                        first_name = names[0].title(),
                        last_name = ' '.join(names[1:]).title()
                    )
                    obj.user = user
                    obj.save()

                    #Todo: setup smtp email server. Currently emails are written to the console because of the setting in settings.py
                    send_mail(
                        'Bullfrog account created',
                        'A Bullfrog account has been created for you. Username: '+username+' Password: '+password,
                        'bullfrog@themobilecompany.com',
                        [email],
                        fail_silently=False,
                    )

    def updateDatabaseRoleFillers(self, importedObjects):
        now = timezone.now()
        for importedObject in importedObjects:
            values = {
                "last_imported": now
            }
            try:
                values['role'] =    Role.objects.get(glassfrog_id=importedObject['roleId'])
                values['person'] =  Person.objects.get(glassfrog_id=importedObject['personId'])
                obj, created = RoleFiller.objects.update_or_create(
                    role=values['role'],     # search for this value, if found, update with 'values', otherwise insert new row with 'values'
                    person=values['person'], # dito
                    defaults=values
                )
            except Role.DoesNotExist:
                # Role is NOT found in the database, skip import of this rolefiller
                pass
            except Person.DoesNotExist:
                # Person is NOT found in the database, skip import of this rolefiller
                pass

    def logToFile(self, obj):
        pathToLogFile = "~/projects/Bullfrog/logs.txt"
        with open(pathToLogFile, 'w') as outfile:
            outfile.write(obj)