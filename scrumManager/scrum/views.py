from datetime import datetime
import re
import uuid
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from .forms import RegisterForm
from django.contrib import messages
from scrum.models import Notification, Project, User, Company, CompanyUsers, ProjectUsers, TaskGroup, Task, SubTask, TaskType, TaskTable, TaskGroupVariable, tokenInvitation
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.template import Context, Template
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
import json

def index(request):
    user = request.user
    if user.is_authenticated:
        username = user.username
        project_attributes = getCompanies(user)
        
        def parse_task_details(task_details):
            details_dict = {}
            task_details = task_details.rstrip("\\|/")
            parts = task_details.split("\\|/")
            for part in parts:
                if ':' in part:
                    key, value = part.split(':', 1)
                    capitalized_key = key.strip().capitalize()
                    details_dict[capitalized_key] = value.strip()
            return details_dict
        
        tasksAsigned = Task.objects.filter(user=user)
        tasksNames = []
        tasksNamesFinal = []
        for i in tasksAsigned:
            task_name = i.name
            task_name = parse_task_details(task_name)
            tasksNames.append(task_name)
        for i in tasksNames:
            if 'Tarea' in i and 'Taskgroup' in i:
                tarea = i['Tarea']
                task_group_id = i['Taskgroup']
                task_group = TaskGroup.objects.get(id=task_group_id)
                project = task_group.project
                tareaF = f"{project.name} - {tarea}"
                tasksNamesFinal.append({'tarea': tareaF, 'id': project.id})            
        notifications = Notification.objects.filter(user=user)

        return render(request, 'index.html', {'user': user, 'projects': project_attributes, 'tasksAsigned': tasksNamesFinal, 'notifications': notifications})
    else:
        return render(request, 'index.html')

def login_view(request):
    if request.user.is_authenticated:
        return redirect('index')
    
    if request.method == 'POST':
        try:
            form = AuthenticationForm(request, request.POST)
            if form.is_valid():
                email = form.cleaned_data.get('username')
                password = form.cleaned_data.get('password')
                user = authenticate(request, email=email, password=password)
                if user is not None:
                    login(request, user)
                    return JsonResponse({'status': 'success', 'message': '¡Inicio de sesión correcto!'})
                else:
                    return JsonResponse({'status': 'error', 'message': 'El correo o la contraseña son incorrectos'})
            else:
                return JsonResponse({'status': 'error', 'message': 'El correo o la contraseña son incorrectos'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': 'Error: ' + str(e)})
    else:
        form = AuthenticationForm()
    
    return render(request, 'login/index.html', {'form': form})

def register(request):
    if request.method == 'POST':
        try:
            form = RegisterForm(request.POST)
            if form.is_valid():
                user = User.objects.create_user(
                    email=form.cleaned_data['email'],
                    username=form.cleaned_data['username'],
                    password=form.cleaned_data['password1']
                )
                return JsonResponse({'status': 'success', 'message': 'Bienvenido! Accede al dashboard para entrar a proyectos.'})
            else:
                if form.errors.get('email'):
                    return JsonResponse({'status': 'error', 'message': 'El correo ya existe'})
                elif form.errors.get('password2'):
                    return JsonResponse({'status': 'error', 'message': 'Las contraseñas no coinciden'})
                else:
                    return JsonResponse({'status': 'error', 'message': 'Error al registrar el usuario'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': 'Error: ' + str(e)})
    else:
        form = RegisterForm()
    return render(request, 'register/index.html', {'form': form})

def logout_view(request):
    if request.user.is_authenticated:
        logout(request)
    return JsonResponse({'status': 'success', 'message': '¡Hasta luego!'})

def scrum(request):
    return render(request, 'scrum/index.html')

@login_required
def dashboard(request):
    user = request.user
    company_users = CompanyUsers.objects.filter(user=user)
    company_ids = [company.company.id for company in company_users]
    projects_attributes = getCompanies(user)
    
    def parse_task_details(task_details):
        details_dict = {}
        task_details = task_details.rstrip("\\|/")
        parts = task_details.split("\\|/")
        for part in parts:
            if ':' in part:
                key, value = part.split(':', 1)
                capitalized_key = key.strip().capitalize()
                details_dict[capitalized_key] = value.strip()
        return details_dict
            
    tasksAsigned = Task.objects.filter(user=user)
    tasksNames = []
    tasksNamesFinal = []
    for i in tasksAsigned:
        task_name = i.name
        task_name = parse_task_details(task_name)
        tasksNames.append(task_name)
    for i in tasksNames:
        if 'Tarea' in i and 'Taskgroup' in i:
            tarea = i['Tarea']
            task_group_id = i['Taskgroup']
            task_group = TaskGroup.objects.get(id=task_group_id)
            project = task_group.project
            tareaF = f"{project.name} - {tarea}"
            tasksNamesFinal.append({'tarea': tareaF, 'id': project.id})  

    if request.method == 'POST':
        if 'project-name' in request.POST:
            try:
                project_name = request.POST.get('project-name')
                poject_start_date = request.POST.get('start-date')
                project_end_date = request.POST.get('end-date')
                if project_end_date == '':
                    project_end_date = None
                project = Project(
                    name=project_name,
                    company_id=company_ids[0],
                    start_date=poject_start_date,
                    end_date=project_end_date
                )
                project.save()
                project_user = ProjectUsers(user=user, project=project)
                project_user.save()
                
                task_group = TaskGroup(name='Completado', project=project)
                task_group.save()
                
                task_group_variables = [
                    TaskGroupVariable(name='Fecha', value='date', project=project),
                    TaskGroupVariable(name='Asignado', value='selectable', project=project),
                    TaskGroupVariable(name='Estado', value='selectable', project=project),
                    TaskGroupVariable(name='Horas', value='int', project=project),
                    TaskGroupVariable(name='Minutos', value='int', project=project),
                    TaskGroupVariable(name='Notas', value='string', project=project),
                ]
                TaskGroupVariable.objects.bulk_create(task_group_variables)
                
                task = Task(name='Tarea:Tu primera tarea completada\\|/Fecha:\\|/Asignado:\\|/Estado:Completado\\|/Horas:\\|/Minutos:\\|/Notas:', task_group=task_group, user=user)
                task.save()
                task.name = f"TaskGroup:{task_group.id}\\|/Id:{task.id}\\|/Tarea:Tu primera tarea completada\\|/Fecha:\\|/Asignado:\\|/Estado:Completado\\|/Horas:\\|/Minutos:\\|/Notas:"
                task.save()
                
                task_group = TaskGroup(name='En Progreso', project=project)
                task_group.save()
                
                task = Task(name='Tarea:Tu primera tarea en progreso\\|/Fecha:\\|/Asignado:\\|/Estado:En proceso\\|/Horas:\\|/Minutos:\\|/Notas:', task_group=task_group, user=user)
                task.save()       
                task.name = f"TaskGroup:{task_group.id}\\|/Id:{task.id}\\|/Tarea:Tu primera tarea en progreso\\|/Fecha:\\|/Asignado:\\|/Estado:En proceso\\|/Horas:\\|/Minutos:\\|/Notas:"
                task.save()                
                
                return JsonResponse({'status': 'success', 'message': '¡Proyecto creado correctamente!'})
            except Exception as e:
                return JsonResponse({'status': 'error', 'message': 'Error al crear el proyecto...' + str(e)})
        elif 'access-code' in request.POST:
            try:
                group_name = request.POST.get('group-name')
                access_code = request.POST.get('access-code')
                company = Company.objects.get(name=group_name, access_code=access_code)
                company_user = CompanyUsers(user=user, company=company)
                company_user.save()
                return JsonResponse({'status': 'success', 'message': '¡Te has unido al grupo correctamente!'})
            except Exception as e:
                return JsonResponse({'status': 'error', 'message': 'Error al unirse al grupo. Verifica el código de acceso o el nombre del grupo.'})
    
    notifications = Notification.objects.filter(user=user)

    return render(request, 'dashboard/index.html', {'companies': company_ids, 'projects': projects_attributes, 'tasksAsigned': tasksNamesFinal, 'user': user, 'notifications': notifications})

def create_company(request):
    if request.method == 'POST':
        try:
            company_name = request.POST.get('name-company')
            access_code = request.POST.get('access-code')
            company = Company(name=company_name, access_code=access_code)
            company.save()
            
            company_user = CompanyUsers(user=request.user, company=company)
            company_user.save()
            
            return JsonResponse({'status': 'success', 'message': '¡Grupo creado correctamente!'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': 'Error al crear el grupo...'})
    return render(request, 'dashboard/create_company.html')

def getCompanies(user):
    company_users = CompanyUsers.objects.filter(user=user)
    company_ids = [company.company.id for company in company_users]
    projects = Project.objects.filter(company__id__in=company_ids, projectusers__user=user)
    projects_attributes = []
    for project in projects:
        projects_attributes.append({
            'id': project.id,
            'name': project.name,
            'company': project.company.name,
            'start_date': project.start_date,
            'end_date': project.end_date
        })
    return projects_attributes

def project(request, project_id):
    if request.GET.get('token'):
        token = request.GET.get('token')
        try:
            token_invitation = tokenInvitation.objects.get(token=token)
            user = token_invitation.user
            project = token_invitation.project
            project_user = ProjectUsers(user=user, project=project)
            project_user.save()
            token_invitation.delete()
            
            company_user = CompanyUsers(user=user, company=project.company)
            company_user.save()
            
            return JsonResponse({'status': 'success', 'message': '¡Te has unido al proyecto correctamente!'})
        except tokenInvitation.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Error al unirse al proyecto. Verifica el token de invitación.'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': 'Error al unirse al proyecto. Verifica el token de invitación.'})
    
    project = get_object_or_404(Project, id=project_id)
    try:
        task_groups = TaskGroup.objects.filter(project=project)
        if task_groups.filter(name='Completado').exists():
            completed_group = task_groups.get(name='Completado')
            task_groups = task_groups.exclude(name='Completado')
            task_groups = list(task_groups)
            task_groups.append(completed_group)
        else:
            task_groups = list(task_groups)

        task_groups_attributes = {}

        for task_group in task_groups:
            tasks = Task.objects.filter(task_group=task_group)
            tasks_attributes = []

            for task in tasks:
                sub_tasks = SubTask.objects.filter(task=task)
                sub_tasks_attributes = []

                for sub_task in sub_tasks:
                    sub_tasks_attributes.append({
                        'id': sub_task.id,
                        'name': sub_task.name
                    })

                tasks_attributes.append({
                    'id': task.id,
                    'name': task.name,
                    'sub_tasks': sub_tasks_attributes
                })

            task_groups_attributes[task_group.id] = {
                'name': task_group.name,
                'tasks': tasks_attributes
            }

        def parse_task_details(task_details):
            details_dict = {}
            task_details = task_details.rstrip("\\|/")
            parts = task_details.split("\\|/")
            for part in parts:
                if ':' in part:
                    key, value = part.split(':', 1)
                    capitalized_key = key.strip().capitalize()
                    details_dict[capitalized_key] = value.strip()
            return details_dict

        for group_id, group in task_groups_attributes.items():
            for task in group['tasks']:
                task_name = task['name']
                task['details'] = parse_task_details(task_name)
                del task['name']

        task_groups_attributes = dict(sorted(task_groups_attributes.items(), key=lambda x: x[1]['name']))
        
        if 'Completado' in task_groups_attributes:
            completed_group = task_groups_attributes.pop('Completado')
            task_groups_attributes['Completado'] = completed_group
        
        task_groups_attributes = json.dumps(task_groups_attributes)
    except Exception as e:
        task_groups_attributes = []
        task_groups = []

    user = request.user
    project_users = ProjectUsers.objects.filter(project=project)
    usersIds = [user.user.id for user in project_users]
    tasksgroup_variables = TaskGroupVariable.objects.filter(project=project)
            
    tasksAsigned = Task.objects.filter(user=user)
    tasksNames = []
    tasksNamesFinal = []
    for i in tasksAsigned:
        task_name = i.name
        task_name = parse_task_details(task_name)
        tasksNames.append(task_name)
    for i in tasksNames:
        if 'Tarea' in i and 'Taskgroup' in i:
            tarea = i['Tarea']
            task_group_id = i['Taskgroup']
            task_group = TaskGroup.objects.get(id=task_group_id)
            projectX = task_group.project
            tareaF = f"{projectX.name} - {tarea}"
            tasksNamesFinal.append({'tarea': tareaF, 'id': projectX.id})  
    if not project_users:
        return HttpResponse('No tienes permisos para acceder a este proyecto')
    
    def parse_task_details(task_details):
        details_dict = {}
        task_details = task_details.rstrip("\\|/")
        parts = task_details.split("\\|/")
        for part in parts:
            if ':' in part:
                key, value = part.split(':', 1)
                capitalized_key = key.strip().capitalize()
                details_dict[capitalized_key] = value.strip()
        return details_dict

    task_groups_attributes2 = json.loads(task_groups_attributes)
    for group_id, group in task_groups_attributes2.items():
        for task in group['tasks']:
            for i in task['details']:
                if i[0].islower():
                    task['details'][i[0].upper() + i[1:]] = task['details'].pop(i)
                if task['details'][i] in ['nulo', 'none', 'undefined', 'null', 'None', 'Undefined', 'Null', 'Nulo']:
                    task['details'][i] = ''
    
    usersIdsAndNames = []
    for i in usersIds:
        user = User.objects.get(id=i)
        usersIdsAndNames.append({'id': i, 'name': user.username})
    
    notifications = Notification.objects.filter(user=user)

    return render(request, 'project/index.html', {
        'project': project,
        'task_groups': task_groups,
        'task_groups_attributes': task_groups_attributes,
        'tasksgroup_variables': tasksgroup_variables,
        'project_users': project_users,
        'projects': getCompanies(user),
        'usersIds': usersIds,
        'tasksAsigned': tasksAsigned,
        'usersIdsAndNames': usersIdsAndNames,
        'notifications': notifications,
    })
    
def profile(request):
    user = request.user
    return render(request, 'profile/index.html', {'user': user})
    
@csrf_exempt
def update_task(request, task_id):
    if request.method == 'POST':
        task = get_object_or_404(Task, pk=task_id)
        task_data = request.POST.get('task_data', '')
        details = parse_task_details(task_data)
        task_name = details['Tarea']
        
        user_id = request.POST.get('user_id', '')
        if user_id != '0':
            user2 = User.objects.get(id=user_id)
            date = datetime.now().strftime("%d de %B de %Y a las %H:%M").replace("June", "Junio")
            notification = Notification.objects.create(
                user = user2,
                message = f"Has sido asignado a la tarea {task_name} en el proyecto {task.task_group.project.name}",
                date = date
            )
            notification.save()
            task.user = user2

        task.name = task_data
        task.save()
        
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'failed'}, status=400)

def create_task(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        formatted_data = data.get('formatted_data')
        task_group_id = data.get('task_group_id')

        try:
            task_group = TaskGroup.objects.get(id=task_group_id)
            
            new_task = Task.objects.create(
                name="Nombre temporal",
                task_group=task_group,
                user=request.user
            )

            name = (
                f"TaskGroup:{task_group_id}\\|/"
                f"Id:{new_task.id}\\|/"
                f"{formatted_data}"
            )

            new_task.name = name
            new_task.save()
            
            return JsonResponse({'status': 'success', 'task_id': new_task.id})

        except TaskGroup.DoesNotExist:
            return JsonResponse({'status': 'error', 'error': 'Task group not found'}, status=404)
        except Exception as e:
            return JsonResponse({'status': 'error', 'error': str(e)}, status=500)

    else:
        return JsonResponse({'status': 'error', 'error': 'Method not allowed'}, status=405)
    
@require_http_methods(["DELETE"])
def delete_task(request, task_id):
    try:
        task = Task.objects.get(id=task_id)
        task.delete()
        return JsonResponse({'status': 'success', 'message': '¡Tarea eliminada correctamente!'})
    except Task.DoesNotExist:
        return JsonResponse({'status': 'error', 'error': 'Task not found'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'error': str(e)}, status=500)

def create_taskgroup(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        project_id = data.get('project_id')
        task_group_name = data.get('name')
        try:
            project = Project.objects.get(id=project_id)
            task_group = TaskGroup.objects.create(
                name=task_group_name,
                project=project
            )
            return JsonResponse({'status': 'success', 'message': '¡Grupo creado correctamente!', 'task_group_id': task_group.id})
        except Project.DoesNotExist:
            return JsonResponse({'status': 'error', 'error': 'Project not found'}, status=404)
        except Exception as e:
            return JsonResponse({'status': 'error', 'error': str(e)}, status=500)
    else:
        return JsonResponse({'status': 'error', 'error': 'Method not allowed'}, status=405)
     
@csrf_exempt
def update_task_group(request, task_id):
    if request.method == 'POST':
        data = json.loads(request.body)
        new_task_group_id = data.get('new_task_group_id')

        if not new_task_group_id:
            return JsonResponse({'status': 'error', 'message': 'new_task_group_id not provided'})

        try:
            task_group = TaskGroup.objects.get(pk=new_task_group_id)
        except TaskGroup.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Task group not found'})

        try:
            task = Task.objects.get(pk=task_id)
            
            task.name = task.name.replace(f'TaskGroup:{task.task_group.id}', f'Taskgroup:{new_task_group_id}')
            task.name = task.name.replace(f'taskgroup:{task.task_group.id}', f'Taskgroup:{new_task_group_id}')
            task.name = task.name.replace(f'Taskgroup:{task.task_group.id}', f'Taskgroup:{new_task_group_id}')

            task.task_group = task_group  
            task.save()
            return JsonResponse({'status': 'success', 'message': '¡Tarea actualizada correctamente!'})
        except Task.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Task not found'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})

    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

@csrf_exempt
def update_border_color(request, groupId):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            border_color = data.get('border_color')
            if not border_color:
                return JsonResponse({'status': 'error', 'error': 'No color provided'}, status=400)

            task_group = TaskGroup.objects.get(id=groupId)
            task_group.color = border_color
            task_group.save()
            redirect_url = f'/proyecto/{task_group.project.id}'
            
            return JsonResponse({'status': 'success', 'message': '¡Color actualizado correctamente!'})
        except TaskGroup.DoesNotExist:
            
            return JsonResponse({'status': 'error', 'error': 'Task group not found'}, status=404)
        except Exception as e:
            return JsonResponse({'status': 'error', 'error': str(e)}, status=500)
    else:
        return JsonResponse({'status': 'error', 'error': 'Method not allowed'}, status=405)
    
@csrf_exempt
def create_taskgroup_variable(request, projectId):
    if request.method == 'POST':
        data = json.loads(request.body)
        name = data.get('name')
        name = name[0].upper() + name[1:]
        value = data.get('value')
        try:
            project = Project.objects.get(id=projectId)
            task_group_variable = TaskGroupVariable.objects.create(
                name=name,
                value=value,
                project=project
            )
            
            task_groups = TaskGroup.objects.filter(project=project)
            for task_group in task_groups:
                tasks = Task.objects.filter(task_group=task_group)
                for task in tasks:
                    task_name = task.name
                    task_name += f"\\|/{name}:"
                    task.name = task_name
                    task.save()
            return JsonResponse({'status': 'success', 'message': '¡Variable creada correctamente!', 'task_group_variable_id': task_group_variable.id})
        except Project.DoesNotExist:
            return JsonResponse({'status': 'error', 'error': 'Project not found'}, status=404)
        except TaskGroup.DoesNotExist:
            return JsonResponse({'status': 'error', 'error': 'Task group not found'}, status=404)
        except Exception as e:
            return JsonResponse({'status': 'error', 'error': str(e)}, status=500)
    else:
        return JsonResponse({'status': 'error', 'error': 'Method not allowed'}, status=405)
    
@require_http_methods(["DELETE"])
def delete_taskgroup(request, groupId):
    try:
        task_group = TaskGroup.objects.get(id=groupId)
        task_group.delete()
        return JsonResponse({'status': 'success', 'message': '¡Grupo eliminado correctamente!'})
    except TaskGroup.DoesNotExist:
        return JsonResponse({'status': 'error', 'error': 'Task group not found'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'error': str(e)}, status=500)
    
def add_project_user(request, projectId):
    if request.method == 'POST':
        data = json.loads(request.body)
        email = data.get('email')
        try:
            user = User.objects.get(email=email)
            project = Project.objects.get(id=projectId)
            send_invitation_project_email(request, projectId, user.id, email)
            return JsonResponse({'status': 'success', 'message': '¡Invitación enviada correctamente!'})
        except User.DoesNotExist:
            return JsonResponse({'status': 'error', 'error': 'User not found'}, status=404)
        except Project.DoesNotExist:
            return JsonResponse({'status': 'error', 'error': 'Project not found'}, status=404)
        except Exception as e:
            return JsonResponse({'status': 'error', 'error': str(e)}, status=500)
    else:
        return JsonResponse({'status': 'error', 'error': 'Method not allowed'}, status=405)  
        
def send_invitation_project_email(request, projectId, userId, email):
    project = Project.objects.get(id=projectId)
    user = User.objects.get(id=userId)
    subject = 'Invitación al proyecto ' + project.name
    from_email = 'jbernabeucaballero.cf@iesesteveterradas.cat'
    to_email = email
    
    if ProjectUsers.objects.filter(user=user, project=project).exists():
        return HttpResponse('Este usuario ya está en el proyecto.')
    elif tokenInvitation.objects.filter(user=user, project=project).exists():
        return HttpResponse('Ya se ha enviado una invitación a este usuario.')
    else:
        token = tokenInvitation.objects.create(token=uuid.uuid4().hex, project=project, user=user)
        
        context = {
            'username': user.username,
            'email': to_email,
            'project_name': project.name,
            'token': token.token,
            'projectId': projectId,
        }

        html_content = render_to_string('emails/addUserEmailTemplate.html', context)
        text_content = strip_tags(html_content)

        msg = EmailMultiAlternatives(subject, text_content, from_email, [to_email])
        msg.attach_alternative(html_content, "text/html")
        try:
            msg.send()
            return HttpResponse('Correo enviado exitosamente.')
        except Exception as e:
            return HttpResponse(f'Error al enviar el correo: {e}')
    
@require_http_methods(["DELETE"])
def delete_project_user(request, projectId, userId):
    try:
        user = User.objects.get(id=userId)
        project = Project.objects.get(id=projectId)
        project_user = ProjectUsers.objects.get(user=user, project=project)
        project_user.delete()
        return JsonResponse({'status': 'success', 'message': '¡Usuario eliminado correctamente!'})
    except ProjectUsers.DoesNotExist:
        return JsonResponse({'status': 'error', 'error': 'Project user not found'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'error': str(e)}, status=500)
    
def delete_taskgroup_variable(request, variableId):
    try:
        task_group_variable = TaskGroupVariable.objects.get(id=variableId)
        task_group_variable.delete()
        project = task_group_variable.project
        task_groups = TaskGroup.objects.filter(project=project)
        for task_group in task_groups:
            tasks = Task.objects.filter(task_group=task_group)
            for task in tasks:
                task_name = task.name
                task_name = re.sub(r'\\\|/' + re.escape(task_group_variable.name) + r':.*?(?=\\\|/|$)', '', task_name)
                task.name = task_name
                task.save()
            
        return JsonResponse({'status': 'success', 'message': '¡Variable eliminada correctamente!'})
    except TaskGroupVariable.DoesNotExist:
        return JsonResponse({'status': 'error', 'error': 'Task group variable not found'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'error': str(e)}, status=500)
    
@require_http_methods(["DELETE"])
def delete_project(request, projectId):
    try:
        project = Project.objects.get(id=projectId)
        project.delete()
        return JsonResponse({'status': 'success', 'message': '¡Proyecto eliminado correctamente!'})
    except Project.DoesNotExist:
        return JsonResponse({'status': 'error', 'error': 'Project not found'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'error': str(e)}, status=500)

def mark_as_read(request, notificationId):
    try:
        notification = Notification.objects.get(id=notificationId)
        notification.delete()
        return JsonResponse({'status': 'success', 'message': '¡Notificación marcada como leída!'})
    except Notification.DoesNotExist:
        return JsonResponse({'status': 'error', 'error': 'Notification not found'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'error': str(e)}, status=500)

def parse_task_details(task_details):
    details_dict = {}
    task_details = task_details.rstrip("\\|/")
    parts = task_details.split("\\|/")
    for part in parts:
        if ':' in part:
            key, value = part.split(':', 1)
            capitalized_key = key.strip().capitalize()
            details_dict[capitalized_key] = value.strip()
    return details_dict
