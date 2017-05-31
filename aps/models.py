from django.db import models
from django.db.models import Sum
from django.contrib.auth.models import User

class GlassfrogEntity(models.Model):
    name            = models.CharField(max_length=200)
    glassfrog_id    = models.IntegerField(unique=True)
    glassfrog_url   = models.CharField(max_length=200)
    last_imported   = models.DateTimeField()

    def __str__(self):
        return self.name

    class Meta:
        abstract = True

class Person(GlassfrogEntity):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True, related_name='person')
    contract_fte = models.FloatField(default=1.0)

    # Define an extra property of this model, that is calculated with existing model properties
    # Expected Utilisation is the percentage of total attention points, compared to contract hours (fte*40)
    def _get_expected_utilisation(self):
        return Person.calculate_expected_utilisation_percentage(self.rolefiller_set.aggregate(Sum('attention_points'))['attention_points__sum'], self.contract_fte)
    expected_utilisation = property(_get_expected_utilisation)

    @staticmethod
    def calculate_expected_utilisation_percentage(attention_points, contract_fte):
        utilisation_percentage = 0
        if contract_fte != 0:
            utilisation_percentage = round(attention_points / contract_fte )
        return utilisation_percentage

class Circle(GlassfrogEntity):
    super_circle = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name="sub_circles")
    attention_points = models.FloatField(default=0)
    # actual_hours = models.FloatField()
    # actual_hours_modified = models.DateTimeField()

class Role(GlassfrogEntity):
    circle            = models.ForeignKey(Circle, on_delete=models.CASCADE, null=True, unique=False, related_name="roles")
    supporting_circle = models.ForeignKey(Circle, on_delete=models.CASCADE, null=True, blank=True, unique=False, related_name="supported_role") # for roles that represent a sub-circle, this links to that circle
    def __str__(self):
        if self.supporting_circle: #if this role represent a Circle, than this is the LeadLink of that Circle
            return self.name+' (Lead Link) - Delete'
        else:
            return self.name

class RoleFiller(models.Model):
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    attention_points = models.FloatField(default=0)
    last_imported   = models.DateTimeField()

    def __str__(self):
        return str(self.role) + " : " + str(self.person)

