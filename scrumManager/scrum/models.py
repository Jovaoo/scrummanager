from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin

class Company(models.Model):
    name = models.CharField(max_length=50)
    access_code = models.CharField(max_length=50, null=True, blank=True)

    def __str__(self):
        return self.name
    
class CompanyUsers(models.Model):
    user = models.ForeignKey('User', on_delete=models.CASCADE)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    

class Project(models.Model):
    name = models.CharField(max_length=50)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='projects')
    start_date = models.DateField(default=None, null=True, blank=True)
    end_date = models.DateField(default=None, null=True, blank=True)

    def __str__(self):
        return self.name
    
class ProjectUsers(models.Model):
    user = models.ForeignKey('User', on_delete=models.CASCADE)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    def __str__(self):
        return self.user.username

class TaskGroup(models.Model):
    name = models.CharField(max_length=50)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='task_groups')
    color = models.CharField(max_length=50, default='#1a73e8', null=True, blank=True)

    def __str__(self):
        return self.name
    
class TaskGroupVariable(models.Model):
    name = models.CharField(max_length=50)
    value = models.CharField(max_length=50)
    #task_group = models.ForeignKey(TaskGroup, on_delete=models.CASCADE, related_name='variables')
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='variables', null=True, blank=True)

    def __str__(self):
        return self.name

class tokenInvitation(models.Model):
    token = models.CharField(max_length=50)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    user = models.ForeignKey('User', on_delete=models.CASCADE)

    def __str__(self):
        return self.token

class Task(models.Model):
    name = models.CharField(max_length=2000)
    task_group = models.ForeignKey(TaskGroup, on_delete=models.CASCADE, related_name='tasks')
    user = models.ForeignKey('User', on_delete=models.CASCADE, related_name='tasks')

    def __str__(self):
        return self.name

class SubTask(models.Model):
    name = models.CharField(max_length=50)
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='sub_tasks')

    def __str__(self):
        return self.name

class TaskType(models.Model):
    name = models.CharField(max_length=50)
    # Category solo podra ser: int, str, bool, date
    category = models.CharField(max_length=50)

    def __str__(self):
        return self.name
    
class selectableTaskType(models.Model):
    task_type = models.ForeignKey(TaskType, on_delete=models.CASCADE)
    items = models.CharField(max_length=50)

class TaskTable(models.Model):
    name = models.CharField(max_length=50)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='task_tables')
    task_type = models.ForeignKey(TaskType, on_delete=models.CASCADE, related_name='task_tables')

    def __str__(self):
        return self.name
    
class Notification(models.Model):
    user = models.ForeignKey('User', on_delete=models.CASCADE)
    message = models.CharField(max_length=500)
    date = models.CharField(max_length=50)
     
    def __str__(self):
        return self.message

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=50, default='')
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)
    verified = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email
