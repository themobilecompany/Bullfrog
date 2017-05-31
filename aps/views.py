from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.views.generic.edit import UpdateView
from django.views.generic.edit import DeleteView
from django.views.generic.detail import DetailView
from django.views.generic import TemplateView
from django.views.generic.base import  TemplateResponseMixin

from django.db.models import Sum
from django.db.models import Count
from django.db.models import Case, When, Value, IntegerField
from django.urls import reverse_lazy
from django.utils import timezone
from django.shortcuts import render, redirect

from aps.models import Person
from aps.models import Circle
from aps.models import Role
from aps.models import RoleFiller



# Helper methods ########################################################################################

def getObjectsNotInGlassfrog(modelObject, orderBy='name'):
    # get newest import date in db table (as last date of import)
    last_import_date = getLastImportedDate(modelObject)
    object_list = modelObject.objects.filter(last_imported__lt=last_import_date).order_by(orderBy).annotate(is_deleted_in_glassfrog=Value(1, IntegerField()))
    return object_list


def getLastImportedDate(modelObject):
    last_imported_objects = modelObject.objects.order_by('-last_imported')
    if last_imported_objects.exists():
        last_imported_object = last_imported_objects[0]
        last_import_date = last_imported_object.last_imported
    else:
        last_import_date = timezone.now()
    return last_import_date


def sumField(object_list, field_to_sum):
    return round(object_list.aggregate(Sum(field_to_sum))[field_to_sum + '__sum'], 1)


def prepareObjectListContext(object_list, field_to_sum):
    total = 0.0
    if object_list.exists():
        total = sumField(object_list, field_to_sum)
    context = {
        'total': total,
        'object_list': object_list
    }
    return context


def preparePersonListContext(object_list):
    # get generic additional context
    context = prepareObjectListContext(object_list, 'contract_fte')
    # add person specific additional context
    try:  # can only count/sum when the object_list has related items (i.e. rolefillers) in the query result set. That is not always the case, depending on the query done.
        context['total_roles'] = sumField(object_list, 'rolefiller__count')
        context['total_attention_points'] = sumField(object_list, 'rolefiller__attention_points__sum')
        context['total_utilisation'] = Person.calculate_expected_utilisation_percentage(
            context['total_attention_points'], context['total'])
    except:
        pass  # dont worry, if we don't have the totals, we dont show them
    return context


def getAnnotatedPersons():
    return Person.objects.annotate(
        Count('rolefiller'),
        # todo: add Round() function to get rid of rounding errors in the sum function
        # docs: https://docs.djangoproject.com/es/1.10/ref/models/expressions/#func-expressions
        Sum('rolefiller__attention_points'),
        Count('rolefiller__role__circle', distinct=True)
        # only count each circle once, when someone has more than one role in a circle
    )

def getPersonDetailAdditionalContext(person_object):
    additional_context = {}
    # get data related to this person
    annotated_person_object = getAnnotatedPersons().get(id=person_object.id)
    circles = Circle.objects.filter(roles__rolefiller__person__id=person_object.id).distinct().order_by('name')
    leadlink_roles = RoleFiller.objects.all().filter(role__name="Lead Link").filter(person__id=person_object.id)
    leadlink_circles = []

    for circle in circles:
        # get all roles this person has in this circle
        circle.person_roles = RoleFiller.objects.filter(role__circle__id=circle.id, person__id=person_object.id).order_by('role')
        circle.total_attention_points = 0
        for rolefill in circle.person_roles:
            circle.total_attention_points += rolefill.attention_points

        circle.total_attention_points = round(circle.total_attention_points, 2) # python can be weird with floats

        # if this person is Lead Link of this circle, store this circle in his leadlink_circles list
        if leadlink_roles.filter(role__circle=circle):
            circle.additional_context = prepareSubCircleListContextRecursive(circle_object=circle)
            leadlink_circles.append(circle)

    # add data to the additional_context, before it is passed to the template
    additional_context['circle_count'] = annotated_person_object.rolefiller__role__circle__count
    additional_context['rolefiller_count'] = annotated_person_object.rolefiller__count
    additional_context['attention_points_sum'] = annotated_person_object.rolefiller__attention_points__sum
    additional_context['circles'] = circles
    additional_context['circles_leadlink'] = leadlink_circles

    return additional_context

def getCircleDetailAdditionalContext(circle__object):
    last_import_date_rolefiller = getLastImportedDate(RoleFiller)
    additional_context = {}
    # add a breadcrumb list of parent circles
    additional_context['breadcrumbs'] = getBreadCrumbList(circle__object)
    # add data to the additional_context, before it is passed to the template
    # store sub-circles, and their total granted and assigned attention points
    additional_context['circles'] = prepareSubCircleListContextRecursive(circle__object)
    # store rolefillers and their total assigned attention points
    additional_context['rolefillers'] = prepareObjectListContext(
        RoleFiller.objects.filter(role__circle__pk=circle__object.pk).order_by("person__name", "role__name").annotate(
               is_deleted_in_glassfrog=Case(When(last_imported__lt=last_import_date_rolefiller,then=Value(1)),default=Value(0),output_field=IntegerField())),
        field_to_sum='attention_points')
    # store total granted, assigned attention points
    additional_context['attention_points_granted']  = circle__object.attention_points  # just an alias of the objects property value
    additional_context['attention_points_assigned'] = round(additional_context['circles']['attention_points_assigned'] + additional_context['rolefillers']['total'], 1)
    additional_context['attention_points_balance']  = round(additional_context['attention_points_granted'] - additional_context['attention_points_assigned'], 1)
    # add Unassigned Roles to additional_context
    additional_context['unassigned_roles'] = Role.objects.filter(circle__pk=circle__object.pk, rolefiller__isnull=True)
    return additional_context


def prepareSubCircleListContextRecursive(circle_object=None, circle_list=None, field_to_sum='attention_points', subcircle_list=None):
    last_import_date_circle = getLastImportedDate(Circle)
    if subcircle_list != None:
        sub_circle_list = subcircle_list
    elif circle_object == None:
        if circle_list == None:
            circle_object = getRootCircle()  # needed to get attention points
            sub_circle_list = Circle.objects.all().annotate(is_deleted_in_glassfrog=Case(When(last_imported__lt=last_import_date_circle,then=Value(1)),default=Value(0),output_field=IntegerField()))
        else:
            sub_circle_list = circle_list
    else:
        sub_circle_list = circle_object.sub_circles.all().annotate(is_deleted_in_glassfrog=Case(When(last_imported__lt=last_import_date_circle,then=Value(1)),default=Value(0),output_field=IntegerField()))

    context = {
        'total': 0,
        'object_list': sub_circle_list
    }
    # get total assigned attention points within subcircles (recursive)
    total_assigned = 0.0
    for sub_circle in sub_circle_list:
        assigned_in_sub_circle = 0.0
        # add this sub_circles rolefiller assigned points
        circle_rolefiller_list = RoleFiller.objects.filter(role__circle__pk=sub_circle.pk)
        if circle_rolefiller_list.exists():
            assigned_in_sub_circle += sumField(circle_rolefiller_list, field_to_sum)
        else:
            assigned_in_sub_circle += 0
        # add this circles sub-circles assigned points (recursive)
        list_context = prepareSubCircleListContextRecursive(sub_circle, None, field_to_sum)
        assigned_in_sub_circle += list_context['attention_points_assigned']
        total_assigned += assigned_in_sub_circle
        # store values in the sub_circle object, to be retrieved in the template
        sub_circle.attention_points_granted  = round(sub_circle.attention_points, 1)  # alias
        sub_circle.attention_points_assigned = round(assigned_in_sub_circle, 1)
        sub_circle.attention_points_balance  = round(sub_circle.attention_points_granted - sub_circle.attention_points_assigned, 1)
    # Add additional circle list specific data to the circle object, to retrieve in the template
    context['attention_points_granted']  = round(context['total'], 1)  # alias for conveneance
    context['attention_points_assigned'] = round(total_assigned, 1)
    context['attention_points_balance']  = round(context['total'] - total_assigned, 1)
    # context['total_assigned'] = total_assigned
    # context['total_balance']  = circle_object.attention_points - total_assigned
    return context


def getRootCircle():
    # query all circles without a super-circle. These could also be deleted     circles
    # therefore we inverse order by glassfrog ID, as the root circle has PROBABLY the lowest glassfrog ID.
    root_circle = Circle.objects.filter(super_circle__isnull=True).order_by('glassfrog_id').first()
    return root_circle


def getBreadCrumbList(circle_object, bread_crumb_list=None):
    if not bread_crumb_list:
        bread_crumb_list = []
    parent = circle_object.super_circle
    if parent:
        bread_crumb_list.append(parent)
        bread_crumb_list = getBreadCrumbList(parent, bread_crumb_list)
    return bread_crumb_list


def debug(ctx):
    try:
        fail
    except:
        raise Exception(ctx)
    pass

def getLeadLinkDetails(self, filter_to_use, include_GCC = False):
    # Check if the current user is a leadlink of any circles, and pass the details of the sub-circles to the view
    person = Person.objects.get(user=self.request.user.id)
    leadlink_role_of_circles = RoleFiller.objects.filter(person=person).filter(role__name="Lead Link")
    if leadlink_role_of_circles.exists():
        circles = []
        for rolefiller in leadlink_role_of_circles:
            # Find all the sub-circles where they are a leadlink
            if filter_to_use == "super_circle":
                filter = Circle.objects.filter(super_circle__name=rolefiller.role.circle)
            elif filter_to_use == "rolefiller":
                filter = Circle.objects.filter(name=rolefiller.role.circle)
            else:
                filter = None

            circles_to_add = filter
            for circle in circles_to_add:
                circles.append(circle)

            if include_GCC:
                # Special case for GCC - GCC LL should be able to set GCC points
                if rolefiller.role.circle.name == "General Company Circle":
                    circles.append(Circle.objects.get(name=rolefiller.role.circle))

        return circles
    else:
        return None

def getLeadlinkCircleDetails(self):
    return getLeadLinkDetails(self, "super_circle", True)

def getLeadLinkRolefillerDetails(self):
    return getLeadLinkDetails(self, "rolefiller")

# VIEW CLASSES #########################################################################################################

# List View Classes #############################
class BullfrogListView(LoginRequiredMixin, View):
    context = {}
    login_url = reverse_lazy('login')
    template_name = '' # should override in subclasses

    def get_template_names(self):
        # get and validate requested output format
        output = self.request.GET.get('output') \
            if self.request.GET.get('output') in ['html','json'] \
            else 'html'
        # change default template to requested output version
        template_name = self.template_name.rsplit( ".", 1 )[ 0 ] + "." + output
        return [template_name]

    def render(self, request):
        if RoleFiller.objects.filter(role__name="Lead Link", person__user=self.request.user.id):
            self.context['is_leadlink'] = True
        else:
            self.context['is_leadlink'] = False

        return render(request, self.get_template_names()[0], self.context)


class Index(BullfrogListView):
    template_name = 'index.html'

    def get(self, request):

        # If the user still has the default password he has to change it
        if request.user.check_password(settings.DEFAULT_PASSWORD):
            return redirect('password_change')


        # select PEOPLE that have no fte set (usually because the were recently imported from Glassfrog)
        object_list = Person.objects.filter(contract_fte=0).order_by('name')
        self.context['persons_without_fte'] = preparePersonListContext(object_list)

        # select CIRCLES that have no attention points set (usually because they were recently imported from Glassfrog)
        object_list = Circle.objects.filter(attention_points=0).order_by('name')
        # self.context['circles_without_attention_points'] = prepareCircleListContext(object_list, field_to_sum='attention_points')
        self.context['circles_without_attention_points'] = prepareSubCircleListContextRecursive(None, object_list)

        # select ROLEFILLERS that have no attention points set (usually because they were recently imported from Glassfrog)
        object_list = RoleFiller.objects.filter(attention_points=0).order_by('role')
        self.context['rolefillers_without_attention_points'] = prepareObjectListContext(object_list, field_to_sum='attention_points')

        # select PEOPLE that are no longer in Glassfrog
        object_list = getObjectsNotInGlassfrog(Person)
        self.context['persons_not_in_glassfrog'] = preparePersonListContext(object_list)

        # select CIRCLES that are no longer in Glassfrog
        object_list = getObjectsNotInGlassfrog(Circle)
        self.context['circles_not_in_glassfrog'] = prepareObjectListContext(object_list,
                                                                            field_to_sum='attention_points')

        # select ROLEFILLER that are no longer in Glassfrog
        object_list = getObjectsNotInGlassfrog(RoleFiller, orderBy='role')
        self.context['rolefillers_not_in_glassfrog'] = prepareObjectListContext(object_list,
                                                                                field_to_sum='attention_points')

        # select ROLES that are no longer in Glassfrog
        object_list = getObjectsNotInGlassfrog(Role)
        self.context['roles_not_in_glassfrog'] = prepareObjectListContext(object_list,
                                                                          field_to_sum='glassfrog_id')  # summing up glassfrog_id is a 'hack'. it wont be used, but makes it possible to reuse the generic method

        # get information relevant for lead links
        self.context['leadlink_subcircles'] = getLeadlinkCircleDetails(self)
        self.context['leadlink_circle_rolefillers'] = getLeadLinkRolefillerDetails(self)

        return self.render(request)


class PeopleView(BullfrogListView):
    template_name = 'people.html'
    def get(self, request):
        last_import_date_person = getLastImportedDate(Person)
        object_list = getAnnotatedPersons().order_by('name').annotate(
               is_deleted_in_glassfrog=Case(When(last_imported__lt=last_import_date_person,then=Value(1)),default=Value(0),output_field=IntegerField()))
        self.context['persons'] = preparePersonListContext(object_list)

        return self.render(request)


class CirclesView(BullfrogListView):
    template_name = 'circles.html'
    def get(self, request):
        last_import_date_circle = getLastImportedDate(Circle)
        object_list = Circle.objects.order_by('name').annotate(
               is_deleted_in_glassfrog=Case(When(last_imported__lt=last_import_date_circle,then=Value(1)),default=Value(0),output_field=IntegerField()))
        self.context['circles'] = prepareSubCircleListContextRecursive(None, object_list)
        self.context['leadlink_subcircles'] = getLeadlinkCircleDetails(self)

        return self.render(request)



class RoleFillersView(BullfrogListView):
    template_name = 'rolefillers.html'
    def get(self, request):
        last_import_date_rolefiller = getLastImportedDate(RoleFiller)
        object_list = RoleFiller.objects.order_by('role__name', 'person__name').annotate(
               is_deleted_in_glassfrog=Case(When(last_imported__lt=last_import_date_rolefiller,then=Value(1)),default=Value(0),output_field=IntegerField()))
        self.context['rolefillers'] = prepareObjectListContext(object_list, 'attention_points')
        self.context['leadlink_circle_rolefillers'] = getLeadLinkRolefillerDetails(self)

        return self.render(request)


class RolesView(BullfrogListView):
    template_name = 'roles.html'
    def get(self, request):
        last_import_date_role = getLastImportedDate(Role)
        object_list = Role.objects.order_by('circle', 'name').annotate(
               is_deleted_in_glassfrog=Case(When(last_imported__lt=last_import_date_role,then=Value(1)),default=Value(0),output_field=IntegerField()))
        self.context['roles'] = prepareObjectListContext(object_list, 'glassfrog_id')  # hack: will create an unused sum of glassfrog_id's, to be able to reuse the generic method.
        return self.render(request)


# Update View Classes ###################################
class BullfrogUpdateView(LoginRequiredMixin, UpdateView):
    login_url = reverse_lazy('login')
    template_name = 'generic_update_form.html'
    fields = ['attention_points']  # default, should be overridden by subclass if you want something else
    delete_url = '_delete'  # placeholder, should be overridden by subclass with something like 'person_delete'
    success_url = reverse_lazy(
        'index')  # where to return after update, can be overridden by subclass, or by passing a ?next= url parameter

    def get_success_url(self):
        # look in the url for the ?next= paramater, and use that to redirect on success, or default to whatever the base class returns
        return self.request.GET.get('next', super(UpdateView, self).get_success_url())


class PersonUpdate(BullfrogUpdateView):
    model = Person
    delete_url = 'person_delete'
    fields = ['contract_fte']


class CircleUpdate(BullfrogUpdateView):
    model = Circle
    delete_url = 'circle_delete'


class RoleFillerUpdate(BullfrogUpdateView):
    model = RoleFiller
    delete_url = 'rolefiller_delete'


class RoleUpdate(BullfrogUpdateView):
    model = Role
    delete_url = 'role_delete'
    success_url = reverse_lazy('roles')
    fields = []  # overriding the default


# Delete View Classes ###################################
class BullfrogDeleteView(LoginRequiredMixin, DeleteView):
    login_url = reverse_lazy('login')
    template_name = 'generic_delete_form.html'
    success_url = reverse_lazy('index')


class PersonDelete(BullfrogDeleteView):
    model = Person


class CircleDelete(BullfrogDeleteView):
    model = Circle


class RoleFillerDelete(BullfrogDeleteView):
    model = RoleFiller


class RoleDelete(BullfrogDeleteView):
    model = Role


# Detail View Classes #############################
class BullfrogDetailView(LoginRequiredMixin, DetailView):
    login_url = reverse_lazy('login')
    template_name = '' # should override in subclasses

    def get_template_names(self):
        # get and validate requested output format
        output = self.request.GET.get('output') \
            if self.request.GET.get('output') in ['html','json'] \
            else 'html'
        # change default template to requested output version
        template_name = self.template_name.rsplit( ".", 1 )[ 0 ] + "." + output
        return [template_name]


class PersonDetailView(BullfrogDetailView):
    model = Person
    template_name = "person.html"

    def get_context_data(self, **kwargs):
        # get the context for this object that the super class auto generates (object details)
        context = super(PersonDetailView, self).get_context_data(**kwargs)
        # add additional data to the context, before it is passed to the template
        context['additional_context'] = getPersonDetailAdditionalContext(self.object)

        return context


class CircleDetailView(BullfrogDetailView):
    model = Circle
    template_name = "circle.html"

    def get_context_data(self, **kwargs):
        # get the context for this object that the super class auto generates (object details)
        context = super(CircleDetailView, self).get_context_data(**kwargs)
        # add additional data to the context, before it is passed to the template
        context['additional_context'] = getCircleDetailAdditionalContext(self.object)
        context['leadlink_subcircles'] = getLeadlinkCircleDetails(self)
        context['leadlink_circle_rolefillers'] = getLeadLinkRolefillerDetails(self)


        rolefillers = context['additional_context']['rolefillers']['object_list']
        personRolesList = []
        people = []
        for obj in rolefillers:
            if not obj.person.pk in people:
                people.append(obj.person.pk)
                personRoles = rolefillers.filter(person__pk=obj.person.pk)
                personRolesList.append(prepareObjectListContext(personRoles,'attention_points'))

        context['additional_context']['roles_per_person'] = personRolesList

        return context


class MeView(PersonDetailView):
    template_name = "me.html"

    def get(self, request):
        # If the user still has the default password he has to change it
        if request.user.check_password(settings.DEFAULT_PASSWORD):
            return redirect('password_change')
        return super(MeView, self).get(request)

    # Get the Person object belonging to the logged in user as the object for this view (instead of passing an object via url, like is the default for a detail view)
    def get_object(self):
        return Person.objects.get(user=self.request.user.id)

    def get_context_data(self, **kwargs):
        # get the context for this object that the super class auto generates (object details)
        context = super(MeView, self).get_context_data(**kwargs)
        # add additional data to the context, before it is passed to the template
        context['additional_context'] = getPersonDetailAdditionalContext(self.object)

        # get information relevant for lead links
        if RoleFiller.objects.filter(role__name="Lead Link", person__user=self.request.user.id):
            context['is_leadlink'] = True
            leadlink_of_circles = context['additional_context']['circles_leadlink']

            def get_object_from_leadlinks_circles(object, role_or_circle):
                relevant_objects = []

                for circle in leadlink_of_circles:
                    try:
                        if role_or_circle == "role":
                            circle_objects = object.filter(role__circle=circle)
                        elif role_or_circle == "supercircle":
                            circle_objects = object.filter(super_circle=circle)
                        else:
                            circle_objects = object.filter(circle=circle)

                        for circle_object in circle_objects:
                            relevant_objects.append(circle_object)
                    except:
                        pass

                return relevant_objects

            # show roles not in glassfrog
            roles_not_in_gf = getObjectsNotInGlassfrog(Role)
            context['roles_not_in_glassfrog'] = get_object_from_leadlinks_circles(roles_not_in_gf, "circle")

            # show rolefillers that have no attention points
            roles_with_no_ap = RoleFiller.objects.filter(attention_points=0).order_by('role')
            context['rolefillers_without_attention_points'] = get_object_from_leadlinks_circles(roles_with_no_ap, "role")

            # select rolefillers that are no longer in Glassfrog
            rolefillers_not_in_gf = getObjectsNotInGlassfrog(RoleFiller, orderBy='role')
            context['rolefillers_not_in_glassfrog'] = get_object_from_leadlinks_circles(rolefillers_not_in_gf, "role")

            # show circles that are no longer in Glassfrog
            circles_not_in_gf = getObjectsNotInGlassfrog(Circle)
            context['circles_not_in_glassfrog'] = get_object_from_leadlinks_circles(circles_not_in_gf, "circle")

            # show circles that have no attention points
            circles_with_no_ap = Circle.objects.filter(attention_points=0).order_by('name')
            relevant_circles_with_no_ap = get_object_from_leadlinks_circles(circles_with_no_ap, "supercircle")
            circle_list_prepared = prepareSubCircleListContextRecursive(subcircle_list=relevant_circles_with_no_ap)
            context['circles_without_attention_points'] = circle_list_prepared

            # get details of the circles that they are lead link
            leadlink_circles_list = prepareSubCircleListContextRecursive(subcircle_list=leadlink_of_circles)
            context['leadlink_circles'] = leadlink_circles_list

            context['leadlink_subcircles'] = getLeadlinkCircleDetails(self)
            context['leadlink_circle_rolefillers'] = getLeadLinkRolefillerDetails(self)

        return context


# IMPORT VIEW ##########################################################################################################

from aps.utils.GlassfrogImporter import GlassfrogImporter

class DoImport(LoginRequiredMixin, View):
    login_url = reverse_lazy('login')

    def get(self, request):
        imp = GlassfrogImporter()
        imp.doImport()

        numPeopleInGlassfrog = len(imp.people)
        numPeopleInBullfrog = len(Person.objects.all())
        successPeople = True if numPeopleInGlassfrog <= numPeopleInBullfrog else False

        numCirclesInGlassfrog = len(imp.circles)
        numCirclesInBullfrog = len(Circle.objects.all())
        successCircles = True if numCirclesInGlassfrog <= numCirclesInBullfrog else False

        numRolesInGlassfrog = len(imp.roles)
        numRolesInBullfrog = len(Role.objects.all())
        successRoles = True if numRolesInGlassfrog <= numRolesInBullfrog else False

        numRoleFillersInGlassfrog = len(imp.rolefillers)
        numRoleFillersInBullfrog = len(RoleFiller.objects.all())
        successRoleFillers = True if numRoleFillersInGlassfrog <= numRoleFillersInBullfrog else False

        messages = [
            'People Import successful:' + str(successPeople),
            'Number of people in Glassfrog:' + str(numPeopleInGlassfrog),
            'Number of people in Bullfrog:' + str(numPeopleInBullfrog),
            '',
            'Circles Import successful:' + str(successCircles),
            'Number of circles in Glassfrog:' + str(numCirclesInGlassfrog),
            'Number of circles in Bullfrog:' + str(numCirclesInBullfrog),
            '',
            'Roles Import successful:' + str(successRoles),
            'Number of roles in Glassfrog:' + str(numRolesInGlassfrog),
            'Number of roles in Bullfrog:' + str(numRolesInBullfrog),
            '',
            'Role Fillers Import successful:' + str(successRoleFillers),
            'Number of role fillers in Glassfrog:' + str(numRoleFillersInGlassfrog),
            'Number of role fillers in Bullfrog:' + str(numRoleFillersInBullfrog),
        ]

        return render(request, 'import.html', {'messages': messages})

# ABOUT VIEW ##########################################################################################################

class AboutView(TemplateView):
    context = {}
    template_name = "about.html"
