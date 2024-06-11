from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('scrum/', views.scrum, name='scrum'),
    path('crear_grupo/', views.create_company, name='crear_grupo'),
    path('proyecto/<int:project_id>/', views.project, name='proyecto'),
    path('perfil/', views.profile, name='perfil'),

    
    path('create_task/', views.create_task, name='create_task'),
    path('update_task/<int:task_id>/', views.update_task, name='update_task'),
    path('delete_task/<int:task_id>/', views.delete_task, name='delete_task'),
    path('create_taskgroup/', views.create_taskgroup, name='create_taskgroup'),
    path('delete_taskgroup/<int:groupId>/', views.delete_taskgroup, name='delete_taskgroup'),
    path('update_task_group/<int:task_id>/', views.update_task_group, name='update_task_group'),
    path('update_border_color/<int:groupId>/', views.update_border_color, name='update_border_color'),
    path('create_taskgroup_variable/<int:projectId>/', views.create_taskgroup_variable, name='create_taskgroup_variable'),
    path('add_project_user/<int:projectId>/', views.add_project_user, name='add_project_user'),
    path('delete_project_user/<int:projectId>/<int:userId>/', views.delete_project_user, name='delete_project_user'),
    path('delete_taskgroup_variable/<int:variableId>/', views.delete_taskgroup_variable, name='delete_taskgroup_variable'),
    path('delete_project/<int:projectId>/', views.delete_project, name='delete_project'),
    path('mark_as_read/<int:notificationId>/', views.mark_as_read, name='mark_as_read'),
]