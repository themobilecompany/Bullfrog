from django.contrib import admin

from .models import Person
from .models import Circle
from .models import Role
from .models import RoleFiller

admin.site.register(Person)
admin.site.register(Circle)
admin.site.register(Role)
admin.site.register(RoleFiller)