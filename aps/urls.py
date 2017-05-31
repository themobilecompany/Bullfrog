from django.conf.urls import url
from django.contrib import admin
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    url(r'^all/$',                              views.Index.as_view(),              name='index'),
    url(r'^$',                                  views.MeView.as_view(),             name='me'),
    url(r'^people/$',                           views.PeopleView.as_view(),         name='people'),
    url(r'^people/(?P<pk>\d+)/$',               views.PersonDetailView.as_view(),   name='person_detail'),
    url(r'^people/update/(?P<pk>\d+)/$',        views.PersonUpdate.as_view(),       name='person_update'),
    url(r'^people/delete/(?P<pk>\d+)/$',        views.PersonDelete.as_view(),       name='person_delete'),
    url(r'^circles/$',                          views.CirclesView.as_view(),        name='circles'),
    url(r'^circles/(?P<pk>\d+)/$',              views.CircleDetailView.as_view(),   name='circle_detail'),
    url(r'^circles/update/(?P<pk>\d+)/$',       views.CircleUpdate.as_view(),       name='circle_update'),
    url(r'^circles/delete/(?P<pk>\d+)/$',       views.CircleDelete.as_view(),       name='circle_delete'),
    url(r'^roles/$',                            views.RolesView.as_view(),          name='roles'),
    url(r'^role/delete/(?P<pk>\d+)/$',          views.RoleDelete.as_view(),         name='role_delete'),
    url(r'^rolefillers/$',                      views.RoleFillersView.as_view(),    name='rolefillers'),
    url(r'^rolefillers/update/(?P<pk>\d+)/$',   views.RoleFillerUpdate.as_view(),   name='rolefiller_update'),
    url(r'^rolefillers/delete/(?P<pk>\d+)/$',   views.RoleFillerDelete.as_view(),   name='rolefiller_delete'),
    url(r'^import/',                            views.DoImport.as_view(),           name='import'),

    url(r'^login/',                  auth_views.login,  {'template_name': 'login.html'}, name='login'),
    url(r'^logout/',                 auth_views.logout, {'next_page': '/login'},         name='logout'),
    url(r'^password_change/',      auth_views.password_change, {'template_name': 'password_change_form.html'}, name='password_change'),
    url(r'^password_change_done/', auth_views.password_change_done, {'template_name': 'password_change_done.html'}, name='password_change_done'),

    url(r'^about/', views.AboutView.as_view(), name='about'),

    url(r'^admin/', admin.site.urls, name='admin'),
]
