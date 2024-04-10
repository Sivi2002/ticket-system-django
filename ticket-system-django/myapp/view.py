from django.http import HttpResponse , JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.template import loader
from myapp.models import Ticket
from django.conf import settings  
from django.core.serializers import serialize  # include this
import json# include this
from myapp.forms import AppForm


def check_session(view_func):
    def wrapped_view(request, *args, **kwargs):
        # Perform session checking logic here
        print()
        # if not request.session.get('username'):
        if 'username' not in request.COOKIES:
            # return HttpResponseForbidden("Session not valid. Please log in.")
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wrapped_view


@require_http_methods(['POST'])
@csrf_exempt
@check_session
def ticket(request):
    try: 
        # Access form data from POST request
        form_data = request.POST
        # Access uploaded files from POST request
        files_data = request.FILES

        # Do something with the form data and files
        # For example, you can access form fields by name:
        subject = form_data.get('subject')
        discription = form_data.get('discription')
        ticket_type = form_data.get('ticket_type')
        comment = form_data.get('comment')
        active = form_data.get('active')
        file = files_data.get('file')
        if active == 'on':
            active = True
        else: 
            active = False
            
        mem = Ticket(subject = subject,discription = discription, ticket_type=ticket_type, comment=comment, active= active, file=file)
        mem.full_clean()
        mem.save()
        return JsonResponse({'message' : 'context'}, status = 200)
    except Exception as e :
        print(e)
        return JsonResponse({'message' : 'ERROR in updatedelete'}, safe=False, status = 500)  
    

@require_http_methods(['POST','GET'])
@csrf_exempt
@check_session 
def edit_view(request,pk):
    instance = Ticket.objects.get(pk=pk)
    if request.method == 'POST':
        form = AppForm(request.POST, instance=instance)
        files_data = request.FILES
        print(files_data)
        if form.is_valid():
            # Extract form data
            subject = form.cleaned_data['subject']
            discription = form.cleaned_data['discription']
            ticket_type = form.cleaned_data['ticket_type']
            comment = form.cleaned_data['comment']
            active = form.cleaned_data['active']
            file = files_data.get('file')

            # Update instance with form data
            instance.subject = subject
            instance.discription = discription
            instance.ticket_type = ticket_type
            instance.comment = comment
            instance.active = active
            instance.file = file
            instance.save()  # Save the updated instance
            
            return JsonResponse({'message': 'Data updated successfully'}, status=200)
    else:
        form = AppForm(instance=instance)
    return render(request, 'edit.html', {'form': form, 'url':'/api/load_edit_form/'+pk+'/'})