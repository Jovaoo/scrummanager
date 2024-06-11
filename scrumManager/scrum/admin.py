from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group
from .models import Company, Project, TaskGroup, Task, SubTask, TaskType, TaskTable, User

admin.site.register(Company)
admin.site.register(Project)
admin.site.register(TaskGroup)
admin.site.register(Task)
admin.site.register(SubTask)
admin.site.register(TaskType)
admin.site.register(TaskTable)

class UserAdmin(BaseUserAdmin):
    list_display = ('email', 'username', 'is_staff')
    search_fields = ('email', 'username')
    ordering = ('email',)

    fieldsets = (
        (None, {'fields': ('username', 'email', 'password')}),
        ('Permissions', {'fields': ('is_staff', 'is_active', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'verified')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2'),
        }),
    )

try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    pass

admin.site.register(User, UserAdmin)
admin.site.unregister(Group)