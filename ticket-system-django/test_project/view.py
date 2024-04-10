from datetime import datetime, timedelta
from django.http import HttpResponse, HttpResponseForbidden , JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.template import loader
from myapp.models import Ticket, LoginDetails
from django.conf import settings  
from django.core.serializers import serialize  # include this
import json# include this
from myapp.forms import AppForm, LoginForm
from myapp.authenticate import ModelBackend
from django.core.mail import EmailMessage, send_mail, send_mass_mail



def check_session(view_func):
    def wrapped_view(request, *args, **kwargs):
        # Perform session checking logic here
        # if not request.session.get('username'):
        if 'username' not in request.COOKIES:
            # return HttpResponseForbidden("Session not valid. Please log in.")
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wrapped_view

@require_http_methods(['POST','GET'])
@csrf_exempt
def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = ModelBackend.authenticate(request=request, username=username, password=password)
            if user is not None:
                response = redirect('index')
                expiry_time = datetime.now() + timedelta(hours=1)
                response.set_cookie('username', user['username'], expires=expiry_time)
                # Redirect to a success page or home page
                return response
            else:
                # Authentication failed
                return render(request, 'login.html', {'form': form, 'error_message': 'Invalid username or password'})
    else:
        form = LoginForm()
    return render(request, 'login.html', {'form': form})


@require_http_methods(['POST'])
@csrf_exempt
@check_session
def userdata(request):
    try: 
        body  = json.loads(request.body.decode('utf-8'))
        subject_data =  body['message']['subject']
        discription_data =  body['message']['discription']
        type =  body['message']['type']
        mem = Ticket(subject = subject_data,discription = discription_data, ticket_type=type, comment="Comment")
        mem.full_clean()
        mem.save()
        TICKET_RESPONSE = Ticket.objects.all()
        # html_data = loader.render_to_string('sendmail.html',{'context':'values'})
        # send_mail(
        #     '<h1>Hello</h1>',
        #     'discription_data',
        #     settings.EMAIL_HOST_USER,
        #     ['vineetr.tiwari@outlook.com']
        #     ,fail_silently=False,
        #     html_message=html_data
        # )
        # email = EmailMessage(
        #     'subject data',
        #     'discription_data',
        #     settings.EMAIL_HOST_USER,
        #     ['vineet.tiwari@myyahoo.com'],
        # )
        # # Attach the file
        # file_path = 'public/file.txt'  # Specify the path to the file
        # with open(file_path, 'rb') as file:
        #     email.attach('file.txt', file.read(), 'text/plain')
        # email.send()
        
        # email_subject = 'Subject of the Email'
        # email_body = 'Body of the Email'
        # from_email = settings.EMAIL_HOST_USER
        # recipient_list = ['vineet.tiwari@myyahoo.com', 'tiwarivineet112@gmail.com']
        
        # # Prepare the list of email tuples
        # email_messages = [
        #     (email_subject, email_body, from_email, [recipient])
        #     for recipient in recipient_list
        # ]
        # send_mass_mail(email_messages, fail_silently=False)
        context  = serialize("json", TICKET_RESPONSE)
        context = json.loads(context) 
        return JsonResponse({'message' : context}, status = 200)
    except Exception as e :
        print(e)
        return JsonResponse({'message' : 'ERROR'}, safe=False, status = 500)
    
@require_http_methods(['POST'])
@csrf_exempt
def updateDelete(request):
    try: 
        body  = json.loads(request.body.decode('utf-8'))
        id =  body['message']['id']
        mem = Ticket.objects.all()[id]
        if body['status'] == "update":
            discription_data =  body['message']['discription']
            mem_newvar = mem   
            mem_newvar.discription = discription_data
            mem_newvar.save()
        elif body['status'] == "delete":
            mem.delete()
        TICKET_RESPONSE = Ticket.objects.all()
        context  = serialize("json", TICKET_RESPONSE)
        context = json.loads(context) 
        return JsonResponse({'message' : context}, status = 200)
    except Exception as e :
        print(e)
        return JsonResponse({'message' : 'ERROR in updatedelete'}, safe=False, status = 500)   

    

@require_http_methods(['GET'])
@csrf_exempt
@check_session
def index(request):
    ticket_list = Ticket.objects.all().values()
    ticket_list = list(ticket_list)
    form = AppForm()
    template = loader.get_template('index.html')
    context = {
        'ticket' : ticket_list,
        'form': form
    }
    return HttpResponse(template.render(context, request))

@require_http_methods(['GET'])
@csrf_exempt
def index_new(request):
    form = AppForm()
    return render(request, 'upload_form.html', {'form': form})


@require_http_methods(['POST'])
@csrf_exempt
def ticket_list(request):
    ticket_list = Ticket.objects.all().values()
    ticket_list = list(ticket_list)
    # context  = serialize("json", ticket_list)
    # context = json.loads(context)
    return JsonResponse({'message' : ticket_list}, status = 200)