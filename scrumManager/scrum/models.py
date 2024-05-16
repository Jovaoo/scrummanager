from django.db import models

# Create your models here.
class Company(models.Model):
    name = models.CharField(max_length=50)
    email = models.EmailField()
    
    def __str__(self):
        return self.name
    
class Project(models.Model):
    name = models.CharField(max_length=50)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    
    def __str__(self):
        return self.name
    
class TaskGroup(models.Model):
    name = models.CharField(max_length=50)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    
    def __str__(self):
        return self.name
    
class Task(models.Model):
    name = models.CharField(max_length=50)
    task_group = models.ForeignKey(TaskGroup, on_delete=models.CASCADE)
    
    def __str__(self):
        return self.name
    
class subTask(models.Model):
    name = models.CharField(max_length=50)
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    
    def __str__(self):
        return self.name
    
class TaskTable(models.Model):
    name = models.CharField(max_length=50)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    task_type = models.ForeignKey('taskType', on_delete=models.CASCADE)
    
    def __str__(self):
        return self.name
    
class taskType(models.Model):
    name = models.CharField(max_length=50)
    type = models.CharField(max_length=50)
    
    def __str__(self):
        return self.name