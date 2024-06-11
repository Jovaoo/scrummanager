from datetime import datetime
import re
import uuid
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from .forms import RegisterForm
from django.contrib import messages
from scrum.models import Notification, Project, User, Company, CompanyUsers, ProjectUsers, TaskGroup, Task, SubTask, TaskType, TaskTable, TaskGroupVariable, tokenInvitation
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.template import Context, Template
from django.http import JsonResponse
import json
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import send_mail
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.http import HttpResponse

def index(request):
    user = request.user
    if user.is_authenticated:
        username = user.username
        project_attributes = getCompanies(user)
        
            # separa name de task por \\|/ y lo convierte en un diccionario
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
            # Recorrer todas las tareas con parse_task_details y cambiar las que tengan algun item con la primera letra en minuscula a la primera en mayuscula
            
        tasksAsigned = Task.objects.filter(user=user)
        tasksNames = []
        tasksNamesFinal = []
        for i in tasksAsigned:
            task_name = i.name
            task_name = parse_task_details(task_name)
            tasksNames.append(task_name)
        for i in tasksNames:
            # Guardar solo el "Tarea:" y el nombre de la tarea
            if 'Tarea' in i and 'Taskgroup' in i:
                tarea = i['Tarea']
                # conseguir el proyecto de la tarea a partir del id del task group
                task_group_id = i['Taskgroup']
                task_group = TaskGroup.objects.get(id=task_group_id)
                project = task_group.project
                tareaF = f"{project.name} - {tarea}"
                # añadir a la lista final tambien el id del proyecto
                tasksNamesFinal.append({'tarea': tareaF, 'id': project.id})            
        notifications = Notification.objects.filter(user=user)

        return render(request, 'index.html', {'user': user, 'projects': project_attributes, 'tasksAsigned': tasksNamesFinal, 'notifications': notifications})
    else:
        return render(request, 'index.html')

def login_view(request):
    # verificar si el usuario ya esta logueado
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
                    messages.success(request, '¡Inicio de sesión correcto!')
                    return redirect('index')
                else:
                    messages.error(request, 'El correo o la contraseña son incorrectos')
            else:
                messages.error(request, 'El correo o la contraseña son incorrectos')
        except Exception as e:
            return HttpResponse('Error:' + str(e))
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
                messages.success(request, 'Bienvenido! Accede al dashboard para entrar a proyectos.')
                return redirect('index')
            else:
                if form.errors.get('email'):
                    messages.error(request, 'El correo ya existe')
                elif form.errors.get('password2'):
                    messages.error(request, 'Las contraseñas no coinciden')
                else:
                    messages.error(request, 'Error al registrar el usuario')
        except Exception as e:
            return HttpResponse('Error:' + str(e))
    else:
        form = RegisterForm()
    return render(request, 'register/index.html', {'form': form})

def logout_view(request):
    if request.user.is_authenticated:
        messages.info(request, '¡Hasta luego!')
        logout(request)
    return redirect('index')

def scrum(request):
    return render(request, 'scrum/index.html')

@login_required
def dashboard(request):
    # Obtener los IDs de las empresas del usuario
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
            # Recorrer todas las tareas con parse_task_details y cambiar las que tengan algun item con la primera letra en minuscula a la primera en mayuscula
            
    tasksAsigned = Task.objects.filter(user=user)
    tasksNames = []
    tasksNamesFinal = []
    for i in tasksAsigned:
        task_name = i.name
        task_name = parse_task_details(task_name)
        tasksNames.append(task_name)
    for i in tasksNames:
        # Guardar solo el "Tarea:" y el nombre de la tarea
        if 'Tarea' in i and 'Taskgroup' in i:
            tarea = i['Tarea']
            # conseguir el proyecto de la tarea a partir del id del task group
            task_group_id = i['Taskgroup']
            task_group = TaskGroup.objects.get(id=task_group_id)
            project = task_group.project
            tareaF = f"{project.name} - {tarea}"
            # añadir a la lista final tambien el id del proyecto
            tasksNamesFinal.append({'tarea': tareaF, 'id': project.id})  

    # Crear un nuevo proyecto
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
                # Asignar el proyecto al usuario
                project_user = ProjectUsers(user=user, project=project)
                project_user.save()
                
                # Crear un nuevo task group para el proyecto 
                task_group = TaskGroup(name='Completado', project=project)
                task_group.save()
                
                # Añadir a TaskGroupVariable las variables por defecto
                task_group_variables = [
                    TaskGroupVariable(name='Fecha', value='date', project=project),
                    TaskGroupVariable(name='Asignado', value='selectable', project=project),
                    TaskGroupVariable(name='Estado', value='selectable', project=project),
                    TaskGroupVariable(name='Horas', value='int', project=project),
                    TaskGroupVariable(name='Minutos', value='int', project=project),
                    TaskGroupVariable(name='Notas', value='string', project=project),
                ]
                task_group_variables = TaskGroupVariable.objects.bulk_create(task_group_variables)
                
                # Crear la primera tarea para el task group
                task = Task(name='Tarea:Tu primera tarea completada\\|/Fecha:\\|/Asignado:\\|/Estado:Completado\\|/Horas:\\|/Minutos:\\|/Notas:', task_group=task_group, user=user)
                task.save()
                # Añadir el id al name de la tarea creada
                task.name = f"TaskGroup:{task_group.id}\\|/Id:{task.id}\\|/Tarea:Tu primera tarea completada\\|/Fecha:\\|/Asignado:\\|/Estado:Completado\\|/Horas:\\|/Minutos:\\|/Notas:"
                task.save()
                
                # Crear grupo de "En Progreso"
                task_group = TaskGroup(name='En Progreso', project=project)
                task_group.save()
                
                # Crear la primera tarea para el task group
                task = Task(name='Tarea:Tu primera tarea en progreso\\|/Fecha:\\|/Asignado:\\|/Estado:En proceso\\|/Horas:\\|/Minutos:\\|/Notas:', task_group=task_group, user=user)
                task.save()       
                # Añadir el id al name de la tarea creada
                task.name = f"TaskGroup:{task_group.id}\\|/Id:{task.id}\\|/Tarea:Tu primera tarea en progreso\\|/Fecha:\\|/Asignado:\\|/Estado:En proceso\\|/Horas:\\|/Minutos:\\|/Notas:"
                task.save()                
                
                messages.success(request, '¡Proyecto creado correctamente!')
                return redirect('dashboard')
            except Exception as e:
                print(e)
                messages.error(request, 'Error al crear el proyecto...')
        elif 'access-code' in request.POST:
            try:
                group_name = request.POST.get('group-name')
                access_code = request.POST.get('access-code')
                company = Company.objects.get(name=group_name, access_code=access_code)
                company_user = CompanyUsers(user=user, company=company)
                company_user.save()
                messages.success(request, '¡Te has unido al grupo correctamente!')
                return redirect('dashboard')
            except Exception as e:
                print("error: ", e)
                messages.error(request, 'Error al unirse al grupo. Verifica el código de acceso o el nombre del grupo.')
    notifications = Notification.objects.filter(user=user)

    return render(request, 'dashboard/index.html', {'companies': company_ids, 'projects': projects_attributes, 'tasksAsigned': tasksNamesFinal, 'user': user, 'notifications': notifications})

def create_company(request):
    if request.method == 'POST':
        try:
            company_name = request.POST.get('name-company')
            access_code = request.POST.get('access-code')
            company = Company(name=company_name, access_code=access_code)
            company.save()
            
            # Asignar la empresa al usuario
            company_user = CompanyUsers(user=request.user, company=company)
            company_user.save()
            
            messages.success(request, '¡Grupo creado correctamente!')
            return redirect('dashboard')
        except Exception as e:
            messages.error(request, 'Error al crear el grupo...')
    return render(request, 'dashboard/create_company.html')

# Función para obtener los proyectos de las empresas del usuario
def getCompanies(user):
    company_users = CompanyUsers.objects.filter(user=user)
    company_ids = [company.company.id for company in company_users]
    # obtener los proyectos de las empresas del usuario en las que también está incluido
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
    
    # comprobar si hay un get en la url
    if request.GET.get('token'):
        token = request.GET.get('token')
        try:
            token_invitation = tokenInvitation.objects.get(token=token)
            user = token_invitation.user
            project = token_invitation.project
            project_user = ProjectUsers(user=user, project=project)
            project_user.save()
            token_invitation.delete()
            
            # Unirlo a la comañia del proyecto
            company_user = CompanyUsers(user=user, company=project.company)
            company_user.save()
            
            messages.success(request, '¡Te has unido al proyecto correctamente!')
        except tokenInvitation.DoesNotExist:
            messages.error(request, 'Error al unirse al proyecto. Verifica el token de invitación.')
        except Exception as e:
            messages.error(request, 'Error al unirse al proyecto. Verifica el token de invitación.')
    
    
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
        print(e)
        task_groups_attributes = []
        task_groups = []

    user = request.user
    project_users = ProjectUsers.objects.filter(project=project)
    usersIds = [user.user.id for user in project_users]
    print('usersId:', usersIds)
    tasksgroup_variables = TaskGroupVariable.objects.filter(project=project)
            
    tasksAsigned = Task.objects.filter(user=user)
    tasksNames = []
    tasksNamesFinal = []
    for i in tasksAsigned:
        task_name = i.name
        task_name = parse_task_details(task_name)
        tasksNames.append(task_name)
    for i in tasksNames:
        # Guardar solo el "Tarea:" y el nombre de la tarea
        if 'Tarea' in i and 'Taskgroup' in i:
            tarea = i['Tarea']
            # conseguir el proyecto de la tarea a partir del id del task group
            task_group_id = i['Taskgroup']
            task_group = TaskGroup.objects.get(id=task_group_id)
            projectX = task_group.project
            tareaF = f"{projectX.name} - {tarea}"
            # añadir a la lista final tambien el id del proyecto
            tasksNamesFinal.append({'tarea': tareaF, 'id': projectX.id})  
    if not project_users:
        return HttpResponse('No tienes permisos para acceder a este proyecto')
    
    # separa name de task por \\|/ y lo convierte en un diccionario
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
    # Recorrer todas las tareas con parse_task_details y cambiar las que tengan algun item con la primera letra en minuscula a la primera en mayuscula
    task_groups_attributes2 = json.loads(task_groups_attributes)
    for group_id, group in task_groups_attributes2.items():
        for task in group['tasks']:
            for i in task['details']:
                if i[0].islower():
                    task['details'][i[0].upper() + i[1:]] = task['details'].pop(i)
                    # actualiza el nombre de la tarea
                    task_name = task['details']
                    task['details'] = task_name
                # verificar que no hayan valores repetidos, si los hay busca que no se repita y si se repite elimina el repetido con valor nulo/none/undefined
                if task['details'][i] == 'nulo' or task['details'][i] == 'none' or task['details'][i] == 'undefined' or task['details'][i] == 'null' or task['details'][i] == 'None' or task['details'][i] == 'Undefined' or task['details'][i] == 'Null' or task['details'][i] == 'Nulo':
                    task['details'][i] = ''
    for i in task_groups:
        # imprimir todos los valores de task_group
        print(i.id, i.name, i.project_id)
        
    usersIdsAndNames = []
    for i in usersIds:
        user = User.objects.get(id=i)
        usersIdsAndNames.append({'id': i, 'name': user.username})
    print('usersIdsAndNames:', usersIdsAndNames)
    
    # Sacar las notificaciones del usuario
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
        # sacar solo el "Tarea:" y el nombre de la tarea
        task_name = details['Tarea']
        
        user_id = request.POST.get('user_id', '')
        print('user_id:', user_id)
        if user_id != '0':
            user2 = User.objects.get(id=user_id)
            # Nueva notificación
            # Crear notificación
            # parse the date to a string format like "13 de enero de 2021 a las 12:00"
            date = datetime.now().strftime("%d de %B de %Y a las %H:%M").replace("June", "Junio")
            print('date:', date)
            notification = Notification.objects.create(
                user = user2,
                message = f"Has sido asignado a la tarea {task_name} en el proyecto {task.task_group.project.name}",
                date = date
            )
            notification.save()
            task.user = user2


        # Actualizar el campo name
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
        messages.success(request, '¡Tarea eliminada correctamente!')
        return JsonResponse({'status': 'success'})
    except Task.DoesNotExist:
        messages.error(request, 'Error al eliminar la tarea...')
        return JsonResponse({'status': 'error', 'error': 'Task not found'}, status=404)
    except Exception as e:
        messages.error(request, 'Error al eliminar la tarea...')
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
            messages.success(request, '¡Grupo creado correctamente!')
            return JsonResponse({'status': 'success', 'task_group_id': task_group.id})
        except Project.DoesNotExist:
            messages.error(request, 'Error al crear el grupo...')
            return JsonResponse({'status': 'error', 'error': 'Project not found'}, status=404)
        except Exception as e:
            messages.error(request, 'Error al crear el grupo...')
            return JsonResponse({'status': 'error', 'error': str(e)}, status=500)
    else:
        messages.error(request, 'Error al crear el grupo...')
        return JsonResponse({'status': 'error', 'error': 'Method not allowed'}, status=405)
     
@csrf_exempt
def update_task_group(request, task_id):
    if request.method == 'POST':
        data = json.loads(request.body)
        new_task_group_id = data.get('new_task_group_id')

        if not new_task_group_id:
            messages.error(request, 'Error al actualizar la tarea...')
            return JsonResponse({'status': 'error', 'message': 'new_task_group_id not provided'})

        try:
            task_group = TaskGroup.objects.get(pk=new_task_group_id)
        except TaskGroup.DoesNotExist:
            messages.error(request, 'Error al actualizar la tarea...')
            return JsonResponse({'status': 'error', 'message': 'Task group not found'})

        try:
            task = Task.objects.get(pk=task_id)
            
            task.name = task.name.replace(f'TaskGroup:{task.task_group.id}', f'Taskgroup:{new_task_group_id}')
            task.name = task.name.replace(f'taskgroup:{task.task_group.id}', f'Taskgroup:{new_task_group_id}')
            task.name = task.name.replace(f'Taskgroup:{task.task_group.id}', f'Taskgroup:{new_task_group_id}')

            task.task_group = task_group  
            task.save()
            messages.success(request, '¡Tarea actualizada correctamente!')
            return JsonResponse({'status': 'success'})
        except Task.DoesNotExist:
            messages.error(request, 'Error al actualizar la tarea...')
            return JsonResponse({'status': 'error', 'message': 'Task not found'})
        except Exception as e:
            messages.error(request, 'Error al actualizar la tarea...')
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
            messages.success(request, '¡Color actualizado correctamente!')
            return JsonResponse({'status': 'success'})
        except TaskGroup.DoesNotExist:
            messages.error(request, 'Error al actualizar el color...')
            return JsonResponse({'status': 'error', 'error': 'Task group not found'}, status=404)
        except Exception as e:
            messages.error(request, 'Error al actualizar el color...')
            return JsonResponse({'status': 'error', 'error': str(e)}, status=500)
    else:
        messages.error(request, 'Error al actualizar el color...')
        return JsonResponse({'status': 'error', 'error': 'Method not allowed'}, status=405)

@csrf_exempt
def create_taskgroup_variable(request, projectId):
    if request.method == 'POST':
        data = json.loads(request.body)
        name = data.get('name')
        # poner la primera letra en mayuscula
        name = name[0].upper() + name[1:]
        value = data.get('value')
        try:
            project = Project.objects.get(id=projectId)
            task_group_variable = TaskGroupVariable.objects.create(
                name=name,
                value=value,
                project=project
            )
            
            # Actualizar todas las tareas con la nueva variable creada
            task_groups = TaskGroup.objects.filter(project=project)
            for task_group in task_groups:
                tasks = Task.objects.filter(task_group=task_group)
                for task in tasks:
                    task_name = task.name
                    task_name += f"\\|/{name}:"
                    task.name = task_name
                    task.save()
            messages.success(request, '¡Variable creada correctamente!')
            return JsonResponse({'status': 'success', 'task_group_variable_id': task_group_variable.id})
        except Project.DoesNotExist:
            messages.error(request, 'Error al crear la variable...')
            return JsonResponse({'status': 'error', 'error': 'Project not found'}, status=404)
        except TaskGroup.DoesNotExist:
            messages.error(request, 'Error al crear la variable...')
            return JsonResponse({'status': 'error', 'error': 'Task group not found'}, status=404)
        except Exception as e:
            messages.error(request, 'Error al crear la variable...')
            return JsonResponse({'status': 'error', 'error': str(e)}, status=500)
    else:
        messages.error(request, 'Error al crear la variable...')
        return JsonResponse({'status': 'error', 'error': 'Method not allowed'}, status=405)
    
@require_http_methods(["DELETE"])
def delete_taskgroup(request, groupId):
    try:
        task_group = TaskGroup.objects.get(id=groupId)
        task_group.delete()
        # enviar mensaje de exito
        messages.success(request, '¡Grupo eliminado correctamente!')
        return JsonResponse({'status': 'success'})
    except TaskGroup.DoesNotExist:
        messages.error(request, 'Error al eliminar el grupo...')
        return JsonResponse({'status': 'error', 'error': 'Task group not found'}, status=404)
    except Exception as e:
        messages.error(request, 'Error al eliminar el grupo...')
        return JsonResponse({'status': 'error', 'error': str(e)}, status=500)
    
def add_project_user(request, projectId):
    if request.method == 'POST':
        data = json.loads(request.body)
        email = data.get('email')
        try:
            user = User.objects.get(email=email)
            project = Project.objects.get(id=projectId)
            #project_user = ProjectUsers.objects.create(user=user, project=project)
            send_invitation_project_email(request, projectId, user.id, email)
            messages.success(request, '¡Invitación enviada correctamente!')
            return JsonResponse({'status': 'success'         ''', 'project_user_id': project_user.id'''               })
        except User.DoesNotExist:
            messages.error(request, 'Este usuario no existe...')
            return JsonResponse({'status': 'error', 'error': 'User not found'}, status=404)
        except Project.DoesNotExist:
            messages.error(request, 'Error al añadir el usuario...')
            return JsonResponse({'status': 'error', 'error': 'Project not found'}, status=404)
        except Exception as e:
            messages.error(request, 'Error al añadir el usuario...')
            return JsonResponse({'status': 'error', 'error': str(e)}, status=500)
    else:
        messages.error(request, 'Error al añadir el usuario...')
        return JsonResponse({'status': 'error', 'error': 'Method not allowed'}, status=405)  
        
def send_invitation_project_email(request, projectId, userId, email):
    project = Project.objects.get(id=projectId)
    user = User.objects.get(id=userId)
    subject = 'Invitación al proyecto ' + project.name
    from_email = 'jbernabeucaballero.cf@iesesteveterradas.cat'
    to_email = email
    
    # comprobar que no exista ya una invitación para el usuario o que el usuario ya este en el proyecto
    if ProjectUsers.objects.filter(user=user, project=project).exists():
        messages.error(request, 'Este usuario ya está en el proyecto.')
        return HttpResponse('Este usuario ya está en el proyecto.')
    elif tokenInvitation.objects.filter(user=user, project=project).exists():
        messages.error(request, 'Ya se ha enviado una invitación a este usuario.')
        return HttpResponse('Ya se ha enviado una invitación a este usuario.')
    else:
        token = tokenInvitation.objects.create(token=uuid.uuid4().hex, project=project, user=user)
        
        context = {
            'username': user.username,
            'email': to_email,
            'project_name': project.name,
            'token': token.token,
        }

        html_content = render_to_string('emails/addUserEmailTemplate.html', context)
        text_content = strip_tags(html_content)  # Strip the HTML tags for the plain text version

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
        messages.success(request, '¡Usuario eliminado correctamente!')
        return JsonResponse({'status': 'success'})
    except ProjectUsers.DoesNotExist:
        messages.error(request, 'Error al eliminar el usuario...')
        return JsonResponse({'status': 'error', 'error': 'Project user not found'}, status=404)
    except Exception as e:
        messages.error(request, 'Error al eliminar el usuario...')
        return JsonResponse({'status': 'error', 'error': str(e)}, status=500)
    
def delete_taskgroup_variable(request, variableId):
    try:
        task_group_variable = TaskGroupVariable.objects.get(id=variableId)
        task_group_variable.delete()
        # eliminar la variable de todas las tareas del proyecto
        project = task_group_variable.project
        task_groups = TaskGroup.objects.filter(project=project)
        for task_group in task_groups:
            tasks = Task.objects.filter(task_group=task_group)
            for task in tasks:
                task_name = task.name
                # eliminar la variable de la tarea si existe hasta el siguiente \\|/
                task_name = re.sub(r'\\\|/' + re.escape(task_group_variable.name) + r':.*?(?=\\\|/|$)', '', task_name)
                task.name = task_name
                task.save()
            
        messages.success(request, '¡Variable eliminada correctamente!')
        return JsonResponse({'status': 'success'})
    except TaskGroupVariable.DoesNotExist:
        messages.error(request, 'Error al eliminar la variable...')
        return JsonResponse({'status': 'error', 'error': 'Task group variable not found'}, status=404)
    except Exception as e:
        messages.error(request, 'Error al eliminar la variable...')
        return JsonResponse({'status': 'error', 'error': str(e)}, status=500)
    
@require_http_methods(["DELETE"])
def delete_project(request, projectId):
    try:
        project = Project.objects.get(id=projectId)
        project.delete()
        messages.success(request, '¡Proyecto eliminado correctamente!')
        return JsonResponse({'status': 'success'})
    except Project.DoesNotExist:
        messages.error(request, 'Error al eliminar el proyecto...')
        return JsonResponse({'status': 'error', 'error': 'Project not found'}, status=404)
    except Exception as e:
        messages.error(request, 'Error al eliminar el proyecto...')
        return JsonResponse({'status': 'error', 'error': str(e)}, status=500)

def mark_as_read(request, notificationId):
    try:
        notification = Notification.objects.get(id=notificationId)
        # Eliminar la notificación
        notification.delete()
        messages.success(request, '¡Notificación marcada como leída!')
        return JsonResponse({'status': 'success'})
    except Notification.DoesNotExist:
        messages.error(request, 'Error al marcar la notificación como leída...')
        return JsonResponse({'status': 'error', 'error': 'Notification not found'}, status=404)
    except Exception as e:
        messages.error(request, 'Error al marcar la notificación como leída...')
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
    