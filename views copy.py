######################EXTRA FUNCTION IMPORT##################################
import re
import os
import csv 
import json
import uuid
import hmac
import time
import magic
import base64
import asyncio
import hashlib
import requests
import websocket
import threading
import phonenumbers
import mysql.connector
from copy import deepcopy
from decimal import Decimal
from datetime import datetime, timedelta
from io import BytesIO
import secrets
########################EXTRA DJANGO IMPORT###################################
from django.http import HttpResponse,JsonResponse
from django.core.mail import send_mail
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q, F, Count, Sum, Value, CharField, Subquery, OuterRef
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db import connection, transaction
from django.utils import timezone
from django.core.serializers import serialize
from django.forms.models import model_to_dict
from django.db.models.functions import Concat
from django.core.files.base import ContentFile
from django.conf import settings
from django.utils.timezone import make_aware
from django.core.files.uploadedfile import InMemoryUploadedFile
#######################REST_FRAMEWORK IMPORT#####################################
from rest_framework.decorators import *
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import AllowAny,IsAuthenticated
from rest_framework import status
##########################IMPORT MODELS###########################################
from talk2xircls.models import LinkTracking,Integration_details,CampaignFlowReport,CustomerFlowReport,WhatsappCampaign,CustomerFlowLog,OptSettings,MessageContext,PlanSubscriptionsLog,WhatsappWalletTransaction,WhatsappWallet,MessageRelation,BusinessDetails, ProjectDetails,TemplateDetails,Contacts,ContactsGroup,MessageLog,WhatsappCampaign,TriggerEvent,CarouselCard,quickreply,CustomerTagsNotes,Tags,PlanSubscription,ChildTransactions,MembershipPlan,widgets_data,WhatsAppFlowForm
from outlets.models import outlet_details
#from .models import widgets_data
#from subcriptions.models import plan_subscription,membership_plan
from auth_merchant.models import OutletTimeline
from talk2xircls.tasks import unblock_found_scheduled,scheduled_flow,scheduled_conditional_flow
#########################SERIALIZER IMPORT#########################################
from talk2xircls.serializers import CampaignFlowReportSerializers,GETProjectSerializer,OutletSerializer,CustomerReportSerializers,TemplateDetailsSerializer,MembershipPlanDepthSerializer,PlanSubcriptionSerializer,OptSettingsSerializer,ProjectSerializer,Contactserializer,MessageSerializer,WhatsappCampaginSerializer,TriggerEventsSerializer,QuickReplySerializer,TagsSerializer,MembershipPlanSerializer,WhatsappWalletSerializer,WhatsAppFlowFormSerializer
#########################FUNCTION IMPORT#########################################
from utility.views import api_post_request,hash_password,get_access_token_all,dictfetchall,add_webhook,remove_webhook
#########################SETTINGS IMPORT#########################################
from xircls.settings import XIRCLS_DOMAIN,API_DB_NAME,API_USER_NAME,API_DB_PASSWORD,SHOPIFY_API_YEAR,ADMIN_EMAIL,APP_DOMAIN
#########################THREADING IMPORT#########################################
import concurrent.futures
#########################RAZORPAY IMPORT#########################################
import razorpay
#########################FIRE BASE#########################################
from firebase_admin import messaging
#########################API KEYS IMPORT#########################################
from dotenv import load_dotenv
# from celery import shared_task
from shopify.models import ShopifyXirclsApp
#from mailapp.tasks import send_messages_scheduled
from integration_hub.models import EventFlow
# Provided by AiSensy
load_dotenv()
apikey              = os.environ.get("APISENSY_API_KEY")
partner_id          = os.environ.get("APISENSY_PARTNER_ID")
shared_secret       = os.environ.get('APISENSY_SHARED_SECRET')
partner_server      = os.environ.get('AISENSY_PARTNER_SERVER')
direct_server       = os.environ.get('AISENSY_DIRECT_SERVER')
RAZORPAY_API_KEY    = os.environ.get('RAZORPAY_TEST_API_KEY')
RAZORPAY_SECRET_KEY = os.environ.get('RAZORPAY_TEST_SECRET_KEY')

# ##############################################################################################################################################
# Section: BUSINESS
# ##############################################################################################################################################     

#Create Business
@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
@csrf_exempt
def business_view(request):
    if request.method == "POST":
        postdata            = request.data.copy()
        try:
           outlet_obj          = outlet_details.objects.get(api_key = request.META.get('HTTP_API_KEY'))
        except (outlet_details.DoesNotExist, outlet_details.MultipleObjectsReturned):
            return JsonResponse({'error': 'Invalid API Key'}, status=400)
        try:
            BusinessDetails.objects.get(outlet=outlet_obj)    
            response = {'message' : "Business Already exists."}
            return JsonResponse(response, status=400, safe=False)
        except:
            password            = postdata.get('password')
            url                 = f'{partner_server}/partner/{partner_id}/business'
            headers = {
                'X-AiSensy-Partner-API-Key': apikey,
                'Content-Type': 'application/json',
            }
            payload = json.dumps({
                "display_name"  : postdata.get('company'),
                "email"         : postdata.get('email'),
                "company"       : postdata.get('company'),
                "contact"       : postdata.get('phone_code') + postdata.get('contact'),
                "timezone"      : postdata.get('timezone'),
                "currency"      : postdata.get('preferredBillingCurrency'),
                "company_size"  : postdata.get('companySize'),
                "password"      : password,
            })
            try:
                response = requests.request("POST", url, headers=headers, data=payload).json()
                if response.get("business_id"):
                    postdata['business_id'] = response.get("business_id")
                    postdata['password']    = password 
                    postdata['phone_code']  = postdata["countryCode"]
                    del postdata["countryCode"]
                    del postdata["preferredBillingCurrency"]
                    additional  = {
                        'outlet':outlet_obj
                    }
                    postdata.update(additional)
                    BusinessDetails.objects.create(**postdata)
                    timeline_update(outlet_obj,outlet_obj.web_url,'is_business',True)
                    return JsonResponse({"success": 'business created successfully'})
                else:
                    return JsonResponse(response, status=400, safe=False)
            except Exception as e:
                
                response = f"Something went wrong : {e}"
                return JsonResponse(response, status=400, safe=False)

#Get business Profile
@csrf_exempt
@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def get_business_profile(request):
    if request.method == "GET":
        try:
            outlet_obj  = outlet_details.objects.get(api_key = request.META.get('HTTP_API_KEY'))
            business    = BusinessDetails.objects.get(outlet=outlet_obj)
            business_id = business.business_id
            url = f"{partner_server}/partner/{partner_id}/business/{business_id}"
            headers = {
                'X-AiSensy-Partner-API-Key': apikey
            }
            response = requests.request("GET", url, headers=headers).json()
            return JsonResponse(response)
        except (outlet_details.DoesNotExist, outlet_details.MultipleObjectsReturned,BusinessDetails.DoesNotExist, BusinessDetails.MultipleObjectsReturned) as e:
            if isinstance(e, outlet_details.DoesNotExist):
                return JsonResponse({'error': 'Invalid API Key outlet details not found'}, status=404)
            elif isinstance(e, outlet_details.MultipleObjectsReturned):
                return JsonResponse({'error': 'Multiple outlets found with the same API Key'}, status=400)
            elif isinstance(e, BusinessDetails.DoesNotExist):
                return JsonResponse({'error': 'Business details not found'}, status=404)
            elif isinstance(e, BusinessDetails.MultipleObjectsReturned):
                return JsonResponse({'error': 'Multiple Business found with the outlet'}, status=400)
        except Exception as e:
            return JsonResponse({'error': 'An unexpected error occurred: ' + str(e)}, status=500)
    
@csrf_exempt
@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def updating_business_detail(request):
    try:
        outlet_obj   = outlet_details.objects.get(api_key = request.META.get('HTTP_API_KEY'))
        business_obj = BusinessDetails.objects.filter(outlet=outlet_obj).first()

        token = request.data.get("fcm_token")

        if not business_obj or not token:
            return JsonResponse({"error": "Missing business or registration_token"}, status=400)

        if not isinstance(business_obj.fcm_token, list):
            business_obj.fcm_token = []
        valid_tokens = []
        device  = request.POST.get("device_name",None)
        message = messaging.MulticastMessage(
            notification = messaging.Notification(
                title = "New Login",
                body  = f"Your acccount is logged in device {device}",
                ),data  = { "title": "New Login",
                      "body" : f"Your acccount is logged in device {device}",
                    },
            tokens = business_obj.fcm_token
            )
        response = messaging.send_multicast(message)
        print(f'Push notifications sent successfully: {response.success_count} successful, {response.failure_count} failed')
        
        for idx, resp in enumerate(response.responses):
            if resp.success:
                valid_tokens.append(business_obj.fcm_token[idx])
            if not resp.success:
                print(f'Error sending notification to {business_obj.fcm_token[idx]}: {resp.exception}')
        print(f'Push notification sent successfully: {response}')
        business_obj.fcm_token = valid_tokens
        print(token)
        if token not in business_obj.fcm_token:
            business_obj.fcm_token.append(token)
            business_obj.save()
        return JsonResponse({"success": "Business detail updated successfully"}, status=200)
    except (outlet_details.DoesNotExist, outlet_details.MultipleObjectsReturned,BusinessDetails.DoesNotExist, BusinessDetails.MultipleObjectsReturned) as e:
            if isinstance(e, outlet_details.DoesNotExist):
                return JsonResponse({'error': 'Invalid API Key outlet details not found'}, status=404)
            elif isinstance(e, outlet_details.MultipleObjectsReturned):
                return JsonResponse({'error': 'Multiple outlets found with the same API Key'}, status=400)
            elif isinstance(e, BusinessDetails.DoesNotExist):
                return JsonResponse({'error': 'Business details not found'}, status=404)
            elif isinstance(e, BusinessDetails.MultipleObjectsReturned):
                return JsonResponse({'error': 'Multiple Business found with the outlet'}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

# ##############################################################################################################################################
# Section: PROJECT
# ##############################################################################################################################################     

#Create Project
@csrf_exempt
@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def project_creation(request):
    try:
        project_key = secrets.token_urlsafe(32)
        name        = request.POST.get('projectName')
        phone_code  = request.POST.get('phone_code')
        phone_no    = request.POST.get('phone_no')
        outlet_obj  = outlet_details.objects.get(api_key = request.META.get('HTTP_API_KEY'))
        business    = BusinessDetails.objects.get(outlet=outlet_obj)
        business_id = business.business_id
        url         = f"{partner_server}/partner/{partner_id}/business/{business_id}/project"
        headers     = {
            'X-AiSensy-Partner-API-Key': apikey,
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        payload = {
        "name": f"{name}"
        }
        response = requests.post(url=url, data = json.dumps(payload), headers=headers).json()
        print(response,"===========146===========")
        if 'message' in response:
            response['success'] = False
            return JsonResponse(response, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            username        = business.email
            password        = business.password
            project_id         = response["id"]
            token_string    = f"{username}:{password}:{project_id}"
            encoded_bytes   = base64.b64encode(token_string.encode('utf-8'))
            token           = encoded_bytes.decode('utf-8')
            url             = f'{direct_server}/users/regenrate-token'
            headers         = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            }
            data = {
                'direct_api' : True
            }
            payload
            response        = requests.post(url, headers=headers,data=json.dumps(payload)).json()
            print(response,'========================webhook')
            try:
                token           = response['users'][0]['token']
            except:
                return JsonResponse(response,status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            # url             = f'{direct_server}/settings/update-webhook'
            # headers         = {
            #     "Authorization": f"Bearer {token}",
            #     "Content-Type": "application/json",
            # }
            # payload = {
            #     'webhook' : {
            #         'url' : f'{XIRCLS_DOMAIN}/talk/waba/webhook_handler/'
            #     }
            # }
            # response = requests.patch(url, headers=headers, json=payload).json()
            try:
                project_instance = ProjectDetails.objects.filter(outlet=outlet_obj,business=business).update(is_default=False)
            except:
                pass
            project_instace = ProjectDetails.objects.create(is_default=True,project_id = project_id,api_key=project_key,phone_code=phone_code,phone_no=phone_no,project_name = name,outlet=outlet_obj,business=business,token=token)
            WhatsappWallet.objects.create(project = project_instace,business = business , outlet = outlet_obj)
            timeline_update(outlet_obj,outlet_obj.web_url,'is_project',True,project_key)
            response['success'] = True
            print(response,"============================response12321321")
            return JsonResponse(response,status=status.HTTP_200_OK)
    except (outlet_details.DoesNotExist, outlet_details.MultipleObjectsReturned,BusinessDetails.DoesNotExist, BusinessDetails.MultipleObjectsReturned) as e:
            if isinstance(e, outlet_details.DoesNotExist):
                return JsonResponse({'error': 'Invalid API Key outlet details not found'}, status=404)
            elif isinstance(e, outlet_details.MultipleObjectsReturned):
                return JsonResponse({'error': 'Multiple outlets found with the same API Key'}, status=400)
            elif isinstance(e, BusinessDetails.DoesNotExist):
                return JsonResponse({'error': 'Business details not found'}, status=404)
            elif isinstance(e, BusinessDetails.MultipleObjectsReturned):
                return JsonResponse({'error': 'Multiple Business found with the outlet'}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

#Get project details from database
@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def project_get(request):
    if request.method == 'GET':
        try:
            outlet_obj          = outlet_details.objects.get(api_key = request.META.get('HTTP_API_KEY'))
            project_obj         = ProjectDetails.objects.filter(outlet=outlet_obj)
            project_serializer  = ProjectSerializer(project_obj,many=True).data
            response = {
                'project_data' : project_serializer
            }
            return JsonResponse(response,  status=200)
        except (outlet_details.DoesNotExist, outlet_details.MultipleObjectsReturned) as e:
            if isinstance(e, outlet_details.DoesNotExist):
                return JsonResponse({'error': 'Invalid API Key outlet details not found'}, status=404)
            elif isinstance(e, outlet_details.MultipleObjectsReturned):
                return JsonResponse({'error': 'Multiple outlets found with the same API Key'}, status=400)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
#Get project details from aiseny
@csrf_exempt
@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def get_projects(request):
    try:
        outlet_obj  = outlet_details.objects.get(api_key = request.META.get('HTTP_API_KEY'))
        business    = BusinessDetails.objects.get(outlet=outlet_obj)
        business_id = business.business_id
        url         = f"{partner_server}/partner/{partner_id}/business/{business_id}/project"
        headers = {
            'X-AiSensy-Partner-API-Key': apikey
        }
        response = requests.request("GET", url, headers=headers).json()
        return JsonResponse(response)
    except (outlet_details.DoesNotExist, outlet_details.MultipleObjectsReturned,BusinessDetails.DoesNotExist, BusinessDetails.MultipleObjectsReturned) as e:
            if isinstance(e, outlet_details.DoesNotExist):
                return JsonResponse({'error': 'Invalid API Key outlet details not found'}, status=404)
            elif isinstance(e, outlet_details.MultipleObjectsReturned):
                return JsonResponse({'error': 'Multiple outlets found with the same API Key'}, status=400)
            elif isinstance(e, BusinessDetails.DoesNotExist):
                return JsonResponse({'error': 'Business details not found'}, status=404)
            elif isinstance(e, BusinessDetails.MultipleObjectsReturned):
                return JsonResponse({'error': 'Multiple Business found with the outlet'}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@api_view(['GET'])
@authentication_classes([])
@permission_classes([AllowAny])
def project_get_all(request):
    if request.method == 'GET':
        try:
            outlet_id = request.GET.get('outlet_id',None)
            if outlet_id is None :
                return JsonResponse({'error': 'Outlet id is missing'}, status=404)
            project_obj         = ProjectDetails.objects.filter(outlet__id=outlet_id)
            project_serializer  = GETProjectSerializer(project_obj,many=True).data
            response = {
                'project_data' : project_serializer
            }
            return JsonResponse(response,  status=200)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

# ##############################################################################################################################################
# Section: EMBEDDED SIGNUP
# ##############################################################################################################################################     

#embedded signup
@csrf_exempt
@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def embedded_signup(request):
    try:
        url         = f"{partner_server}/partner/{partner_id}/generate-waba-link"
        data        = request.POST
        outlet_obj  = outlet_details.objects.get(api_key = request.META.get('HTTP_API_KEY'))
        business    = BusinessDetails.objects.get(outlet=outlet_obj)
        assistantId = ProjectDetails.objects.filter(business=business,api_key=request.META.get('HTTP_WHATSAPP_PROJECT_KEY')).values_list('project_id', flat=True).first()
        # assistantId is the projectId
        payload = json.dumps({
            "businessId": business.business_id,
            "assistantId": assistantId,
            "setup": {
                "business": {
                    "name": business.name,
                    "email": business.email,
                    "phone": {
                        "code": business.phone_code,
                        "number": business.contact
                    },
                    "website": business.website,
                    "address": {
                        "streetAddress1": business.address,
                        "city": business.city,
                        "state": business.state,
                        "zipPostal": business.postal_code,
                        "country": business.country
                    },
                    "timezone": "UTC-800"
                },
                "phone": {
                    "displayName": business.company,
                    "category": business.industry,
                    "description": business.description
                }
            }
        })

        headers = {
            'Content-Type': 'application/json',
            'X-AiSensy-Partner-API-Key': apikey
        }
        response = requests.request("POST", url, headers=headers, data=payload).json()
        return JsonResponse(response)
    except (outlet_details.DoesNotExist, outlet_details.MultipleObjectsReturned,BusinessDetails.DoesNotExist, BusinessDetails.MultipleObjectsReturned) as e:
            if isinstance(e, outlet_details.DoesNotExist):
                return JsonResponse({'error': 'Invalid API Key outlet details not found'}, status=404)
            elif isinstance(e, outlet_details.MultipleObjectsReturned):
                return JsonResponse({'error': 'Multiple outlets found with the same API Key'}, status=400)
            elif isinstance(e, BusinessDetails.DoesNotExist):
                return JsonResponse({'error': 'Business details not found'}, status=404)
            elif isinstance(e, BusinessDetails.MultipleObjectsReturned):
                return JsonResponse({'error': 'Multiple Business found with the outlet'}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
#fb status for checking whatsapp verification 
@api_view(['POST'])   
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
@csrf_exempt
def fbStatus(request):
    try:
        outlet_obj      = outlet_details.objects.get(api_key = request.META.get('HTTP_API_KEY'))
        business        = BusinessDetails.objects.get(outlet=outlet_obj)
        project_instance =  ProjectDetails.objects.get(business=business,project_name=request.POST.get('project_name'))
        username        = business.email
        password        = business.password
        projectId       = project_instance.project_id
        # token_string    = f"{username}:{password}:{projectId}"
        # encoded_bytes   = base64.b64encode(token_string.encode('utf-8'))
        # token           = encoded_bytes.decode('utf-8')
        # url             = '{direct_server}/users/regenrate-token'
        # headers         = {
        #     "Authorization": f"Bearer {token}",
        #     "Content-Type": "application/json",
        # }
        # response        = requests.post(url, headers=headers)
        # token           = response.json()['users'][0]['token']
        token           = project_instance.token  
        url             = f'{direct_server}/fb-verification-status'
        print(url,"=============================url")
        headers         = {
            'Authorization':f'Bearer {token}'
        }
        status = requests.get(url,headers=headers).json()
        print(status,"==============================fbstatus")
        verificationStatus          = status.get('verificationStatus',None)
        if verificationStatus == 'verified':
            message='Your WhatsApp buisness account is verified....'
            fb_status_code = True
        else:
            fb_status_code = False
            message = 'Your WhatsApp buisness account is not verified....'
        project_instance.is_fb_verified = fb_status_code
        project_instance.save()
        timeline_update(outlet_obj,outlet_obj.web_url,'is_fb_verified',fb_status_code,request.META.get('HTTP_WHATSAPP_PROJECT_KEY'))
        return JsonResponse({'fb_status':fb_status_code,'message':message},status=200)
    except (outlet_details.DoesNotExist, outlet_details.MultipleObjectsReturned,BusinessDetails.DoesNotExist, BusinessDetails.MultipleObjectsReturned,ProjectDetails.DoesNotExist) as e:
            if isinstance(e, outlet_details.DoesNotExist):
                return JsonResponse({'error': 'Invalid API Key outlet details not found'}, status=404)
            elif isinstance(e, outlet_details.MultipleObjectsReturned):
                return JsonResponse({'error': 'Multiple outlets found with the same API Key'}, status=400)
            elif isinstance(e, BusinessDetails.DoesNotExist):
                return JsonResponse({'error': 'Business details not found'}, status=404)
            elif isinstance(e, BusinessDetails.MultipleObjectsReturned):
                return JsonResponse({'error': 'Multiple Business found with the outlet'}, status=400)
            elif isinstance(e, ProjectDetails.DoesNotExist):
                return JsonResponse({'error': 'Project details not found'}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

# ##############################################################################################################################################
# Section: MIGRATION
# ##############################################################################################################################################     
#Create Business

# ##############################################################################################################################################
# Section: TEMPLATE
# ##############################################################################################################################################     
  
###interactive template
@api_view(['POST','PUT','GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
@csrf_exempt
def interactive_template(request):
    try:
        if request.method == 'POST':
            payload = request.POST.get('payload')
            template_name = request.POST.get('template_name')
            print(payload,template_name,"=====================================")
            outlet_obj              = outlet_details.objects.get(api_key = request.META.get('HTTP_API_KEY'))
            project_obj             = ProjectDetails.objects.get(api_key = request.META.get('HTTP_WHATSAPP_PROJECT_KEY'))
            token                   = project_obj.token
            business_instance       = project_obj.business
            try:
                template_instance = TemplateDetails.objects.get(templateName=request.POST.get('template_name'))
                print(str(e),"============================================")
                return JsonResponse({"message":"Template Already exists", "success" : False},status=200)
            except Exception as e:
                pass
            template_instance = TemplateDetails.objects.create(
                templateName=template_name,
                project=project_obj,
                business=business_instance,
                outlet=outlet_obj,
                payload = payload,
                template_type = "INTERACTIVE",
                is_active = True
            )  
            return JsonResponse({"message":"Template Created Successfully", "success" : True},status=201)
        if request.method == 'GET':
            template_id             = request.POST.get('template_id',None)
            outlet_obj              = outlet_details.objects.get(api_key = request.META.get('HTTP_API_KEY'))
            project_obj             = ProjectDetails.objects.get(api_key = request.META.get('HTTP_WHATSAPP_PROJECT_KEY'))
            business_instance       = project_obj.business
            template_instance       = TemplateDetails.objects.filter(
                project=project_obj,
                business=business_instance,
                outlet=outlet_obj,
                template_type = "INTERACTIVE"
            )
            if template_id is not None:
                template_instance = template_instance.filter(id=template_id)
            template_serializer = TemplateDetailsSerializer(template_instance,many=True)
            return JsonResponse({"template_data":template_serializer.data, "success" : True},status=201)
        if request.method == 'PUT':
            payload                 = request.POST.get('payload')
            outlet_obj              = outlet_details.objects.get(api_key = request.META.get('HTTP_API_KEY'))
            project_obj             = ProjectDetails.objects.get(api_key = request.META.get('HTTP_WHATSAPP_PROJECT_KEY'))
            business_instance       = project_obj.business
            template_instance = TemplateDetails.objects.get(
                id=request.POST.get('template_id'),
                project=project_obj,
                business=business_instance,
                outlet=outlet_obj,
                template_type = "INTERACTIVE"
            )
            template_instance.payload = payload
            template_instance.save()
            return JsonResponse({"message":"Template Created Successfully", "success" : True},status=201)
    except (outlet_details.DoesNotExist, outlet_details.MultipleObjectsReturned,ProjectDetails.DoesNotExist) as e:
            if isinstance(e, outlet_details.DoesNotExist):
                return JsonResponse({'error': 'Invalid API Key outlet details not found'}, status=404)
            elif isinstance(e, outlet_details.MultipleObjectsReturned):
                return JsonResponse({'error': 'Multiple outlets found with the same API Key'}, status=400)
            elif isinstance(e, ProjectDetails.DoesNotExist):
                return JsonResponse({'error': 'Project details not found'}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

    #except Exception as e:
        #return JsonResponse({"message": str(e), "success": False}, safe=False) 

#Create Template
@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
@csrf_exempt
def create_template(request):
    try:
        payload                 = request.POST
        outlet_api_key          = request.META.get('HTTP_API_KEY')
        project_api_key         = request.META.get('HTTP_WHATSAPP_PROJECT_KEY')
        name                    = request.POST.get('name',None)
        category                = request.POST.get('category',None)
        language                = request.POST.get('language',None)
        is_draft                = request.POST.get('is_draft',None)
        components              = request.POST.get('components',None)
        if name is None :
            return JsonResponse({'error': 'Name is missing'}, status=404)
        if category is None :
            return JsonResponse({'error': 'Category is missing'}, status=404)
        if language is None :
            return JsonResponse({'error': 'language is missing'}, status=404)
        if components is None :
            return JsonResponse({'error': 'components is missing'}, status=404)
        if outlet_api_key is None :
            return JsonResponse({'error': 'outlet_api_key is missing'}, status=404)
        if project_api_key is None :
            return JsonResponse({'error': 'project_api_key is missing'}, status=404)
        outlet_obj              = outlet_details.objects.get(api_key = outlet_api_key)
        project_obj             = ProjectDetails.objects.get(api_key = project_api_key)
        token                   = project_obj.token
        business_instance       = project_obj.business
        components              = json.loads(components)
        payload = {
            'name'          : name,
            'category'      : category,
            'language'      : language,
            'components'    : components
        }
        file_type = request.POST.get('file_type',None)
        if request.POST.get('dynamic_media',None) is not None:
            #header_media = f"{request.POST.get("dynamic_media")}"
            #header_media_type = f"{components[0]["format"]}"
            dynamic_media = [{
                "header_media"     : request.POST.get("dynamic_media"),
                "header_media_type": components[0]['format']
            }]
        else:
            dynamic_media = [{}]
        try:
            template = TemplateDetails.objects.get(business=business_instance,templateName=name)
            response = {
                'message' : 'Template Name Already Exist'
            }
            return JsonResponse(response,safe=False)
        except:
            dynamic_link = request.POST.get('dynamic_link',None)
            template  = TemplateDetails(
                filename             = request.POST.get('filename',None),
                templateName         = name,
                business             = business_instance,
                project              = project_obj,
                outlet               = outlet_obj,
                body_variable_list   = request.POST.get('bodyVariableList',None),
                header_variable_list = request.POST.get('headerVariableList',None),
                button_variable_list = request.POST.get('buttonVariableList',None),
                file_type            = file_type.lower() if file_type else None,
                is_draft             = request.POST.get('is_draft').capitalize(),
                template_type        = category,
                template_language    = language,
                dynamic_media        = dynamic_media,
                dynamic_link         = dynamic_link,
                global_parameters    = request.POST.get('global_parameters',[])
            )
        if str(components[1]["type"]) == 'CAROUSEL':
            template.save()
            
            print('yeeeeeeeeeeeeeeeeeeeeeee')
            # cardbodyVariableList = request.POST.get('cardbodyVariableList',None)
            # cardbuttonVariableList = request.POST.get('cardbuttonVariableList',None)
            count = 0 
            for i in range(int(request.POST.get('headerUrlCount'))):
                keyword = f'headerUrl{count}'  # Use count instead of 0
                keyword_file_type = f'fileType{count}'
                mediafiles          = request.FILES.get(keyword)
                mediafile_type      = request.POST.get(keyword_file_type,'image')
                print(count,keyword,mediafiles,template,"==========================i")
                # mediatype  = request.POST.get('file_type',None,file_type=mediafile_type)
                keyword_body            = f'cardbodyVariableList{0}'.format(i)
                keyword_button          = f'cardbuttonVariableList{0}'.format(i)
                cardbodyVariableList    = request.POST.get(keyword_body,None)
                cardbuttonVariableList  = request.POST.get(keyword_button,None)
                # print(mediafiles,template,cardbodyVariableList[i],cardbuttonVariableList[i])
                carouselcard = CarouselCard.objects.create(file_data=mediafiles,file_type=mediafile_type,template_details=template,body_variable_list=cardbodyVariableList,button_variable_list=cardbuttonVariableList)
                link = f"{XIRCLS_DOMAIN}/static{carouselcard.file_data.url}"
                payload["components"][1]["cards"][count]["components"][0]["example"]["header_handle"] = [link]
                count += 1
        elif components[0]['format'] != 'TEXT':
            if request.POST.get('dynamic_media',None) is not None and request.POST.get('dynamic_media',None) != 'DEFAULT':
                media_format = 'png' if template.file_type == 'image' else 'mp4'
                file_type = template.file_type
                link = f"{XIRCLS_DOMAIN}/static/template_document/DUMMY_{file_type.upper()}.{media_format}"
            else:
                template.file_data = request.FILES.get('headerUrl')
                template.save()
                
                link = f"{XIRCLS_DOMAIN}/static{template.file_data.url}"
            print(link,"===========================link")
            payload['components'][0]['example']['header_handle'] = [link]
            
        template.payload = json.dumps(payload)
        template.save()
        print(is_draft.capitalize())
        print("<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<in temp>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
        if is_draft.capitalize() == 'False':
            print("<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<in condition>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
            response = send_template_to_aisensy(payload,token,template.id,business_instance,outlet_obj)
            response['success'] = True
            return JsonResponse(response,safe=False)
        else:
            response = {
                "message":"template saved successfully in draft"
            }
            response['success'] = True
            return JsonResponse(response,status=200)
    except (outlet_details.DoesNotExist,ProjectDetails.DoesNotExist,json.JSONDecodeError) as e:
        if isinstance(e, outlet_details.DoesNotExist):
            return JsonResponse({'error': 'Invalid API Key outlet details not found'}, status=404)
        elif isinstance(e, ProjectDetails.DoesNotExist):
            return JsonResponse({'error': 'Project details not found'}, status=404)
        elif isinstance(e, json.JSONDecodeError):
            return JsonResponse({'error': 'Invalid JSON in components'}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

    
def make_dynamic_link(template_id,payload):    
    template_instance = TemplateDetails.objects.get(id =template_id)
    payload_order_index = {ele["type"]: count for count, ele in enumerate(payload["components"])}
    print(payload_order_index,"==============================payload_order_index")
    if payload_order_index.get('BUTTONS',None) is not None:
        dynamic_link = json.loads(template_instance.dynamic_link)
        url_count = 1
        url = f'{XIRCLS_DOMAIN}/talk/'
        button_index = int(payload_order_index['BUTTONS'])
        print(payload['components'][button_index],button_index,"==============================button_index")
        for but in payload['components'][button_index]['buttons']:
            if but['type'] == "URL":
                dynamic_link[f'url_{url_count}']['url'] = but["url"]
                but["url"] = f"{url}"+ str("{{1}}")
                but["example"] = f"{url}/test"
                url_count += 1
        print(dynamic_link,"==========================================")
        print("adssadsadsd")
        template_instance.dynamic_link = json.dumps(dynamic_link)
        template_instance.save()
    return payload

    
@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
@csrf_exempt
def send_draft_to_aisensy(request):
    try:
        outlet_obj              = outlet_details.objects.get(api_key = request.META.get('HTTP_API_KEY'))
        project_obj             = ProjectDetails.objects.get(api_key = request.META.get('HTTP_WHATSAPP_PROJECT_KEY'))
        token                   = project_obj.token
        business_instance       = project_obj.business
        template_instance       = TemplateDetails.objects.get(id = request.POST.get('id'))
        if template_instance.is_draft  is False:
            return JsonResponse({"error":"template is all ready saved at whats app"},status=409)
        else:
            response = send_template_to_aisensy(json.loads(template_instance.payload),token,template_instance.id,business_instance,outlet_obj)
            if 'id' in response :
                template_instance       = TemplateDetails.objects.get(id = request.POST.get('id'))
                template_instance.is_draft = False
                template_instance.save()
                print(template_instance,"=================================================")
            else:
                pass
            return JsonResponse(response,safe=False)
    except (outlet_details.DoesNotExist,ProjectDetails.DoesNotExist,TemplateDetails.DoesNotExist) as e:
        if isinstance(e, outlet_details.DoesNotExist):
            return JsonResponse({'error': 'Invalid API Key outlet details not found'}, status=404)
        elif isinstance(e, ProjectDetails.DoesNotExist):
            return JsonResponse({'error': 'Project details not found'}, status=404)
        elif isinstance(e, TemplateDetails.DoesNotExist):
            return JsonResponse({'error': 'Template details not found'}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
        
def send_template_to_aisensy(payload,token,template_index_id,business_instance,outlet_obj):
    try:
        url                = f"{direct_server}/wa_template"
        print(payload,'============================payload')
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {token}',
        }
        print(headers)
        print(json.dumps(payload))
        payload = make_dynamic_link(template_index_id,payload)
        print("<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<,,,send_template_to_aisensy>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
        response = requests.request("POST", url, headers=headers, data= json.dumps(payload))
        try:
            print(response.text, "==============================response")
        except Exception as e:
            print(str(e))
        response = response.json()   
        if 'id' in response :
            try:
                template_id = response.get('id')
                print("<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<id_respones check>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
                template_instance = TemplateDetails.objects.get(id=template_index_id,business=business_instance)
                print(template_instance)
                template_instance.templateId=template_id
                template_instance.save()
                try:
                    timeline_update(outlet_obj,outlet_obj.web_url,'is_template',True,template_instance.project.api_key)
                except Exception as e:
                    print(str(e),"================================")
            except Exception as e:
                TemplateDetails.objects.get(id=template_index_id,business=business_instance).delete()
        else:
            TemplateDetails.objects.get(id=template_index_id,business=business_instance).delete()
        return response
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
@csrf_exempt
def create_duplicate_template(request):
    try:
        outlet_api_key          = request.META.get('HTTP_API_KEY')
        project_api_key         = request.META.get('HTTP_WHATSAPP_PROJECT_KEY')
        template_id             = request.POST.get("templateId")
        if outlet_api_key is None :
            return JsonResponse({'error': 'outlet_api_key is missing'}, status=404)
        if project_api_key is None :
            return JsonResponse({'error': 'project_api_key is missing'}, status=404)
        if template_id is None :
            return JsonResponse({'error': 'template_id is missing'}, status=404)
        outlet_obj           = outlet_details.objects.get(api_key = outlet_api_key)
        project_obj          = ProjectDetails.objects.get(api_key = project_api_key)
        template_obj         = TemplateDetails.objects.filter(id = request.POST.get("templateId"),project_id = project_obj.id,outlet_id = outlet_obj.id).first()
        if template_obj is None:
            return JsonResponse({"message":"Template is not exist"} ,status= 200)
        match      = re.match(r'^(.*?)(_copy.*)?$', template_obj.templateName)
        base_name  = match.group(1) if match else template_obj.templateName
        name_count = TemplateDetails.objects.filter(templateName__startswith = base_name,project_id = project_obj.id,outlet_id = outlet_obj.id).count()
        
        new_template_obj                     = deepcopy(template_obj)
        new_template_obj.pk                  = None
        new_template_obj.templateId          = ''
        new_template_obj.templateName        = base_name + "_copy" if name_count == 1 else base_name + f"_copy({name_count})"
        new_template_obj.is_draft            = True
        new_template_obj.template_status     = ''
        new_template_obj.template_sent       = 0
        new_template_obj.template_total_sent = 0
        new_template_obj.template_read       = 0
        new_template_obj.template_delivered  = 0
        new_template_obj.template_failed     = 0
        payload                              = json.loads(template_obj.payload)
        payload["name"]                      = base_name + "_copy" if name_count == 1 else base_name + f"_copy({name_count})"    
        new_template_obj.payload             = json.dumps(payload)
        new_template_obj.save()
        """""
        response = send_template_to_aisensy(payload,token,template_obj.id + "_copy",business_instance,outlet_obj)
        if 'id' in response :
            pass        
            #TemplateDetails.objects.create(template_obj)
        else:
            pass
        """""
        return JsonResponse({"message":"Template created successfully"} ,status= 200)
    except (outlet_details.DoesNotExist,ProjectDetails.DoesNotExist,TemplateDetails.DoesNotExist) as e:
        if isinstance(e, outlet_details.DoesNotExist):
            return JsonResponse({'error': 'Invalid API Key outlet details not found'}, status=404)
        elif isinstance(e, ProjectDetails.DoesNotExist):
            return JsonResponse({'error': 'Project details not found'}, status=404)
        elif isinstance(e, TemplateDetails.DoesNotExist):
            return JsonResponse({'error': 'Template details not found'}, status=404)
    except Exception as e:
        print(e)
        return JsonResponse({"error":e},status= 500)

@csrf_exempt
@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def template_delete(request):
    try:
        print(request.POST.get("ID"))
        outlet_api_key          = request.META.get('HTTP_API_KEY')
        project_api_key         = request.META.get('HTTP_WHATSAPP_PROJECT_KEY')
        template_id             = request.POST.get("templateId")
        if outlet_api_key is None :
            return JsonResponse({'error': 'outlet_api_key is missing'}, status=404)
        if project_api_key is None :
            return JsonResponse({'error': 'project_api_key is missing'}, status=404)
        if template_id is None :
            return JsonResponse({'error': 'template_id is missing'}, status=404)
        outlet_obj    = outlet_details.objects.get(api_key = outlet_api_key)
        project_obj   = ProjectDetails.objects.get(api_key = project_api_key)
        template_obj  = TemplateDetails.objects.get(id = template_id)
        if template_obj.is_draft:
            template_obj.is_active = False
            template_obj.is_trash = True
            template_obj.save()
        else:
            template_name = template_obj.templateName                                                                                                               
            url = f"https://backend.aisensy.com/direct-apis/t1/wa_template/{template_name}"
            headers = {
                        "Accept": "application/json",
                        'Authorization':f'Bearer {project_obj.token}'
                    }
            response = requests.delete(url, headers=headers)
            print(response,"==============================")
            if 'success' in response.json():
                template_obj.is_active = False
                template_obj.is_trash = True
                template_obj.save()
                #TemplateDetails.object.filter(business=project.business,templateName=template_name).update(status = 'Deleted')
        return JsonResponse({"message":"Delete Successfully"},status= 200)
    except (outlet_details.DoesNotExist,ProjectDetails.DoesNotExist,TemplateDetails.DoesNotExist) as e:
        if isinstance(e, outlet_details.DoesNotExist):
            return JsonResponse({'error': 'Invalid API Key outlet details not found'}, status=404)
        elif isinstance(e, ProjectDetails.DoesNotExist):
            return JsonResponse({'error': 'Project details not found'}, status=404)
        elif isinstance(e, TemplateDetails.DoesNotExist):
            return JsonResponse({'error': 'Template details not found'}, status=404)
    except Exception as e:
        print(str(e))
        print("======================== ERROR ==============================")
        return JsonResponse({"error": "Something went wrong!"}, status=500)

#Edit template
@csrf_exempt
@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def edit_template(request):
    try:
        outlet_api_key      = request.META.get('HTTP_API_KEY')
        project_api_key     = request.META.get('HTTP_WHATSAPP_PROJECT_KEY')
        name                = request.POST.get('name') 
        language            = request.POST.get('language')
        template_id         = request.POST.get('templateId')
        header_url_change   = request.POST.get('headerUrlChange')
        category            = request.POST.get('category')
        components          = request.POST.get('components',None)
        if outlet_api_key is None :
            return JsonResponse({'error': 'outlet_api_key is missing'}, status=404)
        elif project_api_key is None :
            return JsonResponse({'error': 'project_api_key is missing'}, status=404)
        elif name is None :
            return JsonResponse({'error': 'Name is missing'}, status=404)
        elif category is None :
            return JsonResponse({'error': 'Category is missing'}, status=404)
        elif language is None :
            return JsonResponse({'error': 'language is missing'}, status=404)
        elif components is None :
            return JsonResponse({'error': 'components is missing'}, status=404)
        else:
            pass
        components          = json.loads(components)
        outlet_obj          = outlet_details.objects.get(api_key = request.META.get('HTTP_API_KEY'))
        project_obj         = ProjectDetails.objects.get(api_key = request.META.get('HTTP_WHATSAPP_PROJECT_KEY'))
        template            = TemplateDetails.objects.get(id=template_id)
        
        url                 = f"{direct_server}/edit-template/{template.templateId}" 
        payload         = {
            'name'          : name,
            'category'      : category,
            'language'      : language,
            'components'    : components
        }
        edited_payload  = ({
            "category"  : category,
            "components": components
        })
        headers = {
            'Content-Type'  : 'application/json',
            'Authorization' : f'Bearer {project_obj.token}'
        }
        if request.POST.get('dynamic_media',None) is not None:
            #header_media = f"{request.POST.get("dynamic_media")}"
            #header_media_type = f"{components[0]["format"]}"
            dynamic_media = [{
                "header_media"     : request.POST.get("dynamic_media"),
                "header_media_type": components[0]['format']
            }]
        else:
            dynamic_media = [{}]
        try:
            format = payload['components'][0]['format']
            if format in ['IMAGE', 'VIDEO', 'DOCUMENT']:
                file_type = format.lower()
                if header_url_change == "1":
                    template.file_type = file_type
                    template.file_data = request.FILES.get('headerUrl')
                    template.save()
                template            = TemplateDetails.objects.get(id=template_id)
                if dynamic_media is not None and request.POST.get('dynamic_media',None) is not None and dynamic_media[0]['header_media'] != 'DEFAULT':
                    media_format = 'png' if template.file_type == 'image' else 'mp4'
                    file_type = template.file_type
                    link = f"{XIRCLS_DOMAIN}/static/template_document/DUMMY_{file_type.upper()}.{media_format}"
                else:
                    link = f"{XIRCLS_DOMAIN}/static{template.file_data.url}"
                edited_payload['components'][0]['example']['header_handle'] = [link]
                payload['components'][0]['example']['header_handle'] = [link]
            else:
                template.file_type = 'text'
                template.file_data = None
        except:
            template.file_type = 'None'
            template.file_data = None
        print("=============================================adsd")
        if template.is_draft:
            template.templateName       = name
            template.template_language  = language
        else:
            pass
        template.body_variable_list     = request.POST.get('bodyVariableList', None)
        template.header_variable_list   = request.POST.get('headerVariableList', None)
        template.button_variable_list   = request.POST.get('buttonVariableList', None)
        template.global_parameters      = request.POST.get('global_parameters',[])
        template.dynamic_link           = json.dumps(request.POST.get('dynamic_link',None)) if request.POST.get('dynamic_link',None) is not None else None
        template.dynamic_media          = dynamic_media
        template.save()
        print(template,"=====================done1111111111111111111111111")
        print(edited_payload,"==================================payload")
        print(payload,"==================================payload")
        if str(components[1]["type"]) == 'CAROUSEL':
            # cardbodyVariableList = request.POST.get('cardbodyVariableList',None)
            # cardbuttonVariableList = request.POST.get('cardbuttonVariableList',None)
            count = 0 
            carousel_obj  = CarouselCard.objects.filter(template_details=template).order_by('id')
            for i in range(int(request.POST.get('headerUrlCount'))):
                carousel_instance = CarouselCard.objects.get(id=carousel_obj[i].id)
                keyword = f'headerUrl{count}'  # Use count instead of 0
                keyword_file_type = f'fileType{count}'
                mediafiles         = request.FILES.get(keyword, None)
                print(mediafiles,"=============================mediafiles")
                if mediafiles is None:
                    mediafiles         = request.POST.get(keyword)
                else:
                    mediafile_type             = request.POST.get(keyword_file_type, carousel_instance.file_type)
                    carousel_instance.file_data  = mediafiles
                    carousel_instance.file_type  = mediafile_type
                    print(mediafiles,"========================yes")
                print(type(mediafiles),'============================================')
                print(count, keyword, mediafiles, template,"==========================i")
                # mediatype  = request.POST.get('file_type',None,file_type=mediafile_type)
                keyword_body            = f'cardbodyVariableList{0}'.format(i)
                keyword_button          = f'cardbuttonVariableList{0}'.format(i)
                cardbodyVariableList    = request.POST.get(keyword_body, carousel_instance.body_variable_list)
                cardbuttonVariableList  = request.POST.get(keyword_button, carousel_instance.button_variable_list)
                # print(mediafiles,template,cardbodyVariableList[i],cardbuttonVariableList[i])
                
                # carousel_instance.template_details=template,
                carousel_instance.body_variable_list   = cardbodyVariableList
                carousel_instance.button_variable_list = cardbuttonVariableList
                carousel_instance.save()
                print(carousel_obj)
                carousel_instance = CarouselCard.objects.get(id=carousel_instance.id)

                print({carousel_instance.file_data.url},"==============================")
                link = f"{XIRCLS_DOMAIN}/static{carousel_instance.file_data.url}"
                edited_payload["components"][1]["cards"][count]["components"][0]["example"]["header_handle"] = [link]
                payload["components"][1]["cards"][count]["components"][0]["example"]["header_handle"] = [link]
                count += 1
        if template.is_active and not template.is_draft:
            print(json.dumps(payload, indent=4),"===============================")
            response    = requests.request("POST", url, headers=headers, data=json.dumps(edited_payload))
            print(response,'==============================================')
            response = response.json()
            print(response,'=======================================response')
            if 'success' in response:
                message = {
                    "message": "Template has been edited successfully",
                    "success": True
                }
                template_instance = TemplateDetails.objects.get(id=template_id)
                template_instance.payload = json.dumps(payload)
                template_instance.save()
            else:
                error_msg = response.get('error_user_msg', "Something went wrong!")
                message = {
                    "error_msg": error_msg,
                    "message": "Something went wrong!",
                    "success": False
                }
        else:
            template_instance = TemplateDetails.objects.get(id=template_id)
            template_instance.payload = json.dumps(payload)
            template_instance.save()
            message = {
                "message": "Template has been edited successfully",
                "success": True
            }
        if request.POST.get('draft_active',None) is not None:
            if request.POST.get('draft_active').capitalize() == 'True':
                response = send_template_to_aisensy(payload,project_obj.token,template_instance.id,project_obj.business,outlet_obj)
                template_instance          = TemplateDetails.objects.get(id=template_id)
                template_instance.is_draft = False
                template_instance.save()
                response['success'] = True
                return JsonResponse(response,safe=False)
        print("=====================done")
        return JsonResponse(message, safe=False)
    except (outlet_details.DoesNotExist,ProjectDetails.DoesNotExist,json.JSONDecodeError,TemplateDetails.DoesNotExist) as e:
        if isinstance(e, outlet_details.DoesNotExist):
            return JsonResponse({"error": "Invalid API Key outlet details not found"}, status=404)
        elif isinstance(e, ProjectDetails.DoesNotExist):
            return JsonResponse({"error": "Project details not found"}, status=404)
        elif isinstance(e, json.JSONDecodeError):
            return JsonResponse({"error": "Invalid JSON in components"}, status=400)
        elif isinstance(e, TemplateDetails.DoesNotExist):
            return JsonResponse({"error": "Template details not found"}, status=404)
    except Exception as e:
        print(str(e))
        return JsonResponse({"error": "Something went wrong!"}, status=500)
    #except Exception as e:
        #return JsonResponse({"message": str(e), "success": False}, safe=False) 
       
#Get template from aisensy and active status from database
@csrf_exempt
@api_view(['GET', 'POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def getTemplates(request):
    limit = 1000
    url         = f"{direct_server}/get-templates/?limit={limit}"
    outlet_obj  = outlet_details.objects.get(api_key = request.META.get('HTTP_API_KEY'))
    project_obj = ProjectDetails.objects.get(api_key = request.META.get('HTTP_WHATSAPP_PROJECT_KEY'))
    headers     = {
        'Authorization':f'Bearer {project_obj.token}'
    }
    response    = requests.request("GET", url, headers=headers).json()
    try:
        active_id = list(TemplateDetails.objects.filter(business__outlet = outlet_obj,is_active=True).values_list("templateId", flat=True))
        if request.method == 'POST':
            searchValue = request.POST.get('searchValue', '')
            filtered_data = [
                template for template  in response.get("data", []) 
                if searchValue.lower() in template.get("name", "").lower()
            ]
            return JsonResponse({"data": filtered_data, "total": len(filtered_data), "active_id": active_id},status=200)
        elif request.method == 'GET':
            response['active_id'] =  active_id
            return JsonResponse(response, status=200)
    except Exception as e:
        print(str(e))
        return JsonResponse({"error": "Something went wrong!"}, status=500)
    
@csrf_exempt
@api_view(['GET', 'POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def get_Templates(request):
    try:
        outlet_api_key          = request.META.get('HTTP_API_KEY')
        project_api_key         = request.META.get('HTTP_WHATSAPP_PROJECT_KEY')
        if outlet_api_key is None :
            return JsonResponse({'error': 'outlet_api_key is missing'}, status=404)
        if project_api_key is None :
            return JsonResponse({'error': 'project_api_key is missing'}, status=404)
        outlet_obj       = outlet_details.objects.get(api_key = request.META.get('HTTP_API_KEY'))
        project_instance = ProjectDetails.objects.get(api_key = request.META.get('HTTP_WHATSAPP_PROJECT_KEY'))
        if request.POST.get('slug',None) == 'all':
            templates_obj = TemplateDetails.objects.filter(project=project_instance,is_trash = False)
            templates_serial = TemplateDetailsSerializer(templates_obj,many=True)
            templates_obj_count = templates_obj.count()
            message = {
                'total': templates_obj_count,
                'data': templates_serial.data
            }
            return JsonResponse(message, safe = False, status=200)
        datatables      = request.POST
        start           = int(datatables.get('page',0))
        length          = int(datatables.get('size',0))
        over_all_search = datatables.get('searchValue')
        field_mapping = {
            0: "templateId__icontains",
            1: "templateName__icontains",
            2: "template_status__icontains",
            3: "error_reason__icontains",
            4: "template_type__icontains",
            # 5: "created_at__range",
        }
        advance_filter = Q()
        for col, field in field_mapping.items():
            value = datatables.get(f"columns[{col}][search][value]", None)
            if value:
                advance_filter &= Q(**{field: value})
        if over_all_search:
            overall_search_filter = Q()
            for field in field_mapping.values():
                overall_search_filter |= Q(**{field: over_all_search})
            advance_filter |= overall_search_filter
        templates_obj = TemplateDetails.objects.filter(project=project_instance,is_trash = False).filter(advance_filter).annotate(
            Id                = F('id'),
            TemplateId        = F('templateId'),
            name              = F('templateName'),
            category          = F('template_type'),
            components        = F('payload'),
            language          = F('template_language'),
            Status            = F('template_status'),
            rejected_reason   = F('error_reason'),
            template_active   = F('is_active'),
            template_draft    = F('is_draft'),
            global_parameter  = F('global_parameters'),
            template_types    = F('template_type'),
        ).values(
            'Id',
            'TemplateId',
            'name',
            'category',
            'components',
            'template_language',
            'Status',
            'rejected_reason',
            'template_active',
            'template_draft',
            'template_types'
        ).order_by('-id')

        # Convert the payload to JSON and extract the components
        for template in templates_obj:
            if template.get('components', None):
                try:
                    payload = json.loads(template['components'])
                    template['components'] = payload.get('components', None)
                except json.JSONDecodeError as e:
                    template['components'] = None
            # if template.get('components', None):
            #     try:
            #         payload = json.loads(template['components'])
            #         template['components'] = payload.get('components') if payload.get('components',None) is not None else payload
            #     except json.JSONDecodeError as e:
            #         template['components'] = json.loads(template['components'])

        # Remove the 'language' field as it was only needed to extract components
        # for template in templates_obj:
        #     del template['language']
        
        
        templates_obj_count = templates_obj.count()
        paginator = Paginator(templates_obj, length)
        try:
            object_list = paginator.page(start).object_list
        except (PageNotAnInteger, EmptyPage):
            object_list = paginator.page(1).object_list
        message = {
            'total': templates_obj_count,
            'data': list(object_list)
        }
        return JsonResponse(message, safe = False, status=200)
    except (outlet_details.DoesNotExist,ProjectDetails.DoesNotExist) as e:
        if isinstance(e, outlet_details.DoesNotExist):
            return JsonResponse({'error': 'Invalid API Key outlet details not found'}, status=404)
        elif isinstance(e, ProjectDetails.DoesNotExist):
            return JsonResponse({'error': 'Project details not found'}, status=404)
    except Exception as e:
        print(str(e))
        return JsonResponse({"error": "Something went wrong!"}, status=500)
     
#get template by TemplateId from aisensy
@csrf_exempt
@api_view(['GET','POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def getTemplateById(request):
    try:
        outlet_api_key      = request.META.get('HTTP_API_KEY')
        project_api_key     = request.META.get('HTTP_WHATSAPP_PROJECT_KEY')
        data                = request.POST
        templateId          = data.get('templateId')
        if outlet_api_key is None :
            return JsonResponse({'error': 'outlet_api_key is missing'}, status=404)
        if project_api_key is None :
            return JsonResponse({'error': 'project_api_key is missing'}, status=404)
        if templateId is None :
            return JsonResponse({'error': 'templateId is missing'}, status=404)
        outlet_obj  = outlet_details.objects.get(api_key = request.META.get('HTTP_API_KEY'))
        project_obj = ProjectDetails.objects.get(api_key = request.META.get('HTTP_WHATSAPP_PROJECT_KEY'))
        url         = f"{direct_server}/get-template/{templateId}"
        headers     = {
            'Authorization': f'Bearer {project_obj.token}'
        }
        response = requests.request("GET", url, headers=headers).json()
        try:
            if 'message' in response:
                message     = response.get('message')
                error_msg   = {
                    'message': 'Template does not exist',
                    'success': False
                }
            return JsonResponse(error_msg, safe=False)
        except:
            return JsonResponse(response, safe=False)
    except (outlet_details.DoesNotExist,ProjectDetails.DoesNotExist) as e:
        if isinstance(e, outlet_details.DoesNotExist):
            return JsonResponse({'error': 'Invalid API Key outlet details not found'}, status=404)
        elif isinstance(e, ProjectDetails.DoesNotExist):
            return JsonResponse({'error': 'Project details not found'}, status=404)
    except Exception as e:
        print(str(e))
        return JsonResponse({"error": "Something went wrong!"}, status=500)

@csrf_exempt
@api_view(['GET','POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def get_TemplateById(request):
    try:
        outlet_api_key      = request.META.get('HTTP_API_KEY')
        project_api_key     = request.META.get('HTTP_WHATSAPP_PROJECT_KEY')
        data                = request.POST
        template_id          = data.get('templateId')
        if outlet_api_key is None :
            return JsonResponse({'error': 'outlet_api_key is missing'}, status=404)
        if project_api_key is None :
            return JsonResponse({'error': 'project_api_key is missing'}, status=404)
        if template_id is None :
            return JsonResponse({'error': 'template_id is missing'}, status=404)
        outlet_obj  = outlet_details.objects.get(api_key = request.META.get('HTTP_API_KEY'))
        project_obj = ProjectDetails.objects.get(api_key = request.META.get('HTTP_WHATSAPP_PROJECT_KEY'))
        print()
        template_instance = TemplateDetails.objects.filter(id=template_id).annotate(
            Id              = F('id'),
            TemplateId      = F('templateId'),
            name            = F('templateName'),
            category        = F('template_type'),
            components      = F('payload'),
            language        = F('template_language'),
            Status          = F('template_status'),
            rejected_reason = F('error_reason'),
            template_active = F('is_active'),
            template_draft  = F('is_draft'),
            dynamic_medias  = F('dynamic_media'),
            dynamic_links      = F('dynamic_link'),
            global_parameter = F('global_parameters')
        ).values(
            'Id',
            'TemplateId',
            'name',
            'category',
            'components',
            'language',
            'Status',
            'rejected_reason',
            'template_active',
            'template_draft',
            'dynamic_links',
            'dynamic_medias',
            'global_parameter'
        )
        if template_instance is None:
            return JsonResponse({'error': 'Template not found'}, status=404)
        for template in template_instance:
            if template.get('components',None):  # Check if language (payload) is not None
                payload = json.loads(template['components'])
                template['components'] = payload['components']
            else:
                template['components'] = None
            try:
                if template.get('dynamic_medias',None) is not None:
                    print(eval(template['dynamic_medias']))
                    template['dynamic_medias'] = eval(template['dynamic_medias'])[0]['header_media']
            except:
                pass
        response = list(template_instance)
        return JsonResponse(response, safe=False)
    except (outlet_details.DoesNotExist,ProjectDetails.DoesNotExist) as e:
        if isinstance(e, outlet_details.DoesNotExist):
            return JsonResponse({'error': 'Invalid API Key outlet details not found'}, status=404)
        elif isinstance(e, ProjectDetails.DoesNotExist):
            return JsonResponse({'error': 'Project details not found'}, status=404)
    except Exception as e:
        print(str(e))
        return JsonResponse({"error": "Something went wrong!"}, status=500)

#Template active and inactive
@csrf_exempt
@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def template_active(request):
    try: 
        outlet_api_key      = request.META.get('HTTP_API_KEY')
        project_api_key     = request.META.get('HTTP_WHATSAPP_PROJECT_KEY')
        is_active           = request.POST.get('is_active')
        id                  = request.POST.get('id')
        if outlet_api_key is None :
            return JsonResponse({'error': 'outlet_api_key is missing'}, status=404)
        if project_api_key is None :
            return JsonResponse({'error': 'project_api_key is missing'}, status=404)
        if is_active is None :
            return JsonResponse({'error': 'is_active is missing'}, status=404)
        if id is None :
            return JsonResponse({'error': 'template_id is missing'}, status=404)
        is_active.capitalize()
        project_obj = ProjectDetails.objects.get(api_key = request.META.get('HTTP_WHATSAPP_PROJECT_KEY'))
        outlet_obj  = outlet_details.objects.get(api_key = request.META.get('HTTP_API_KEY'))
        print(id)
        template_instance = TemplateDetails.objects.get(id=id,project =project_obj,outlet = outlet_obj)
        template_instance.is_active = is_active
        template_instance.save()
        return JsonResponse({"message":"Active changed successfully"},status=200)
    except (outlet_details.DoesNotExist,ProjectDetails.DoesNotExist,TemplateDetails.DoesNotExist) as e:
        if isinstance(e, outlet_details.DoesNotExist):
            return JsonResponse({"error": "Invalid API Key outlet details not found"}, status=404)
        elif isinstance(e, ProjectDetails.DoesNotExist):
            return JsonResponse({"error": "Project details not found"}, status=404)
        elif isinstance(e, TemplateDetails.DoesNotExist):
            return JsonResponse({"error": "Template details not found"}, status=404)
    except Exception as e:
        print(str(e))
        return JsonResponse({"error": "Something went wrong!"}, status=500)

# ##############################################################################################################################################
# Section: WABA WEBHOOK
# ##############################################################################################################################################     

@csrf_exempt
def waba_webhook(request):
    try:
        data = request.body
        waba_proccess_data(data)
        return HttpResponse(status=200)
    except:
        otp_message = str(request.body)
        send_mail(
            "Whatsapp Error Messaege",
            otp_message,
            ADMIN_EMAIL,
            ['sohampanchal1469@gmail.com','swapnilwork999@gmail.com'],
            fail_silently=False,
        )
        return HttpResponse(status=200)
    
def integration_process(entry,data, phone_no):
    print("===INSIDE INTEGRATION=====")
    project_instance = ProjectDetails.objects.annotate(phone_number=Concat(F('phone_code'), F('phone_no'))).filter(phone_number=phone_no).last()
    try:
        integration_obj = Integration_details.objects.get(project=project_instance.id, is_active=1)
    except Exception as e:
        print(str(e), "=============error 1382")
        integration_obj = None
    else:
        # continue_flow = ContinueFlow(entry=entry,outlet_instance=project_instance.outlet)
        # continue_flow.trigger_flow()
        try:
            response = requests.post(integration_obj.requested_url, data=data)
            print(response,"=================================response")
        except Exception as e:
            print(str(e), "=============error 1390")
            pass
    return True

def waba_proccess_data(data):
    requested_instance = json.loads(data.decode('UTF-8'))
    print("INSTANCE==============",requested_instance)
    entry = requested_instance.get('entry', [None])[0]
    time_now =  timezone.now()
    try:
        changes             = entry.get("changes", [{}])[0].get('value', {})
        contact_info        = changes.get("contacts", [{}])[0]
        customer_name       = contact_info.get("profile", {}).get("name")
        customer_number     = contact_info.get("wa_id")
        customer_message    = changes.get("messages", [{}])[0]
        phone_no            = changes.get("metadata", {}).get("display_phone_number")
        statuses            = changes.get('statuses', [{}])[0]
        event               = changes.get("event",False)
        print(event,"=======================================")
        if phone_no:
            print(len(customer_message))
            try:
                integration_process_thread = threading.Thread(target=integration_process, args=(entry,data, phone_no,))
                integration_process_thread.start()
            except Exception as e:
                print(str(e), "=================integration____error")
            if customer_name and customer_number:
                print("<<<<<<<<<<<<<<<<<<<<about to exicute update profile1>>>>>>>>>>>>>>>>>")
                update_profile_name_thread = threading.Thread(target=update_profile_name, args=(customer_name, customer_number, phone_no,))
                update_profile_name_thread.start()
            if len(customer_message) != 0:
                def recieve_message_execute(entry,customer_message, phone_no, direct_server,customer_number,time_now):
                    try:
                        print(customer_message, phone_no, direct_server,time_now)
                        handler = MessageHandler(customer_message, phone_no, direct_server,time_now)
                        handler.handle_message()
                    except Exception as e:
                        print(e, "recievemessages=======================")
                    try:
                        def trigger_continue_flow(continue_flow):
                            try:
                                if customer_message['text']['body']:
                                    project_instance = ProjectDetails.objects.annotate(phone_number=Concat(F('business__phone_code'), F('business__contact'))).filter(phone_number=phone_no).last()
                                    outlet_instance  = project_instance.outlet
                                    try:
                                        contacts_obj = Contacts.objects.annotate(phone_number=Concat(F('phone_code'), F('contact'))).filter(phone_number=customer_number,outlet=outlet_instance).last()
                                    except:
                                        phone_number = customer_number
                                        if not customer_number.startswith('+'):
                                            phone_number = '+' + customer_number
                                        parsed_number = phonenumbers.parse(phone_number)
                                        country_code  = parsed_number.country_code
                                        contact_no    = parsed_number.national_number
                                        contacts_obj = Contacts.objects.create(phone_code=country_code,contact=contact_no,outlet=outlet_instance)
                                    contacts_dict = model_to_dict(contacts_obj)
                                    print(customer_number,"==============================customer_number")
                                    flow_check = Flowcheck(trigger='start',phone=customer_number,outlet_instance=outlet_instance,customer_data=[contacts_dict])
                                    check_active_campaign =flow_check.check_active_campaign()
                                    kwargs = {
                                        'campaign_instances':check_active_campaign,
                                        'create' : True,
                                        'message_body' : customer_message['text']['body']
                                    }
                                    # flow_check.check_customer_flow_log(**kwargs)
                                    customer_flow_instance = flow_check.check_customer_flow_log(**kwargs)
                                    if customer_flow_instance is not None:
                                        print(customer_flow_instance,"========================================step3")
                                        print(customer_flow_instance[0],"========================================step3")
                                        customer_flow_instance = customer_flow_instance[0]
                                        print(customer_flow_instance,"========================================step4")
                                        flow_check.trigger_action(customer_flow_instance,None)
                            except Exception as e:
                                print(str(e),"================================asdasd")
                                continue_flow.trigger_flow()

                        project_instance = ProjectDetails.objects.annotate(phone_number=Concat(F('business__phone_code'), F('business__contact'))).filter(phone_number=phone_no).last()
                     
                        continue_flow = ContinueFlow(entry=entry,outlet_instance=project_instance.outlet)
                        trigger_continue_flow(continue_flow)
                    except Exception as e:
                        print(str(e),"<<<<<<<<<<<<<<<<<<<<continue flow error>>>>>>>>>>>>>>>>>")
                recieve_thread = threading.Thread(target=recieve_message_execute, args=(entry,customer_message, phone_no, direct_server,customer_number,time_now,))
                recieve_thread.start()
                # recieve_message_execute(entry,customer_message, phone_no, direct_server,customer_number)
                print("<<<<<<<<<<<<<<<<<<<<about to exicute recive message function1>>>>>>>>>>>>>>>>>")
            if statuses:
                print("<<<<<<<<<<<<<<<<<<<<about to exicute timestamp function>>>>>>>>>>>>>>>>>")
                mark_timestamp(time_now, statuses)
            # end_time = time.time()
            # print(f"Execution time: {end_time - start_time} seconds========================================================")
            print('asdssssasdsadasdsadasdsd')
            return HttpResponse(status=200)
        
        elif event:
            reason              = changes.get("reason")
            message_template_id = changes.get("message_template_id")
            # print("<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<in temp update>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
            if event and message_template_id:
                template_status_update(event,reason,message_template_id)
            else:
                pass
            return HttpResponse(status=200)
      
        elif customer_message["type"] == 'order':
            price = 0
            currency = "INR"
            display_contact = entry.get("changes", [{}])[0].get("value", {}).get("metadata", {}).get("display_phone_number")
            order_data = process_customer_order(customer_message,customer_name,customer_number,display_contact)
            if order_data:
                business_instance, project_instance, url, phone_no = order_data
                send_whatsapp_message(phone_no, business_instance, project_instance, url)
                shop = business_instance.outlet.web_url
                response    = get_access_token_all(shop,'whatsapp')
                create_shopify_order(shop, response)
            else:
                pass
            return HttpResponse(status=200)
        else:
            pass
    
    except:
        return HttpResponse(status=200)

# ### Subsection: UPDATE PROFILE ###
def update_profile_name(customer_name,customer_number,phone_no):
    try:
        print("Customer Name:", customer_name)
        print("Customer Number:", customer_number)
        print("Phone Number:", phone_no)
        print("#######################################   update profile #############################################")
        country_code , contact_no = get_phone_code(customer_number)
        project_details =  ProjectDetails.objects.annotate(
            phone_number=Concat(F('phone_code'), F('phone_no'))
        ).get(
            Q(phone_number=phone_no)
        )
        outlet_details   = project_details.outlet
        # print(country_code,contact_no,"============================================a")
        print(project_details)
        contact_info = Contacts.objects.filter(phone_code = country_code,contact=contact_no,outlet=outlet_details , project = project_details).last()
        print(contact_info)
        if contact_info is None:
            contact_info = Contacts.objects.create(phone_code = country_code,contact=contact_no,outlet=outlet_details,is_active=True, project = project_details)
            try:
                tags_instance = Tags.objects.get(id=8)
                # print(tags_instance,"========================================tags_instance")
                customer_tags = CustomerTagsNotes.objects.create(contact=contact_info)
                customer_tags.tags.add(tags_instance)
                customer_tags.save()
            except:
                pass
        else:
            contact_info.is_active = True
            if contact_info.first_name is None and contact_info.last_name is None :
                contact_info.first_name = customer_name
            contact_info.save()
        try:
            message_relation_instance               = MessageRelation.objects.get(receiver=customer_number,sender=phone_no)
            message_relation_instance.receiver_info = contact_info
            message_relation_instance.display_name  = customer_name
            message_relation_instance.save()
        except Exception as e:
            print(str(e),'===========================================================')
            message_relation_instance = MessageRelation.objects.create(receiver=customer_number,sender=phone_no,receiver_info=contact_info)
        print(customer_name,customer_number,phone_no)
        print(message_relation_instance)
        if isinstance(customer_name, bytes):
            message_relation_instance.display_name = customer_name.decode('utf-8')
        message_relation_instance.save()
        print(message_relation_instance)
    except Exception as e:
        print(str(e),'===========================================================')
        pass
    return True

# ### Subsection: RECEIVE MESSAGE ###
def receive_message(messages, phone_no): 
    print(messages, phone_no)
    handler = MessageHandler(messages, phone_no, direct_server)
    return handler.handle_message()

class MessageHandler:
    def __init__(self, messages, phone_no, direct_server,time_now):
        self.messages       = messages
        self.phone_no       = phone_no
        self.direct_server  = direct_server
        self.file_handler   = FileHandler(phone_no, direct_server)
        self.messages_from  = messages.get("from", "")
        self.messages_id    = messages.get("id", "")
        self.time_now       = time_now
        self.reply_context_instance, self.reply_context = self.get_reply_context()
        self.content_file   = self.file_handler.get_file(messages)
        self.project_obj    = ProjectDetails.objects.annotate(
            contact_number = Concat(F('phone_code'), F('phone_no'))
        ).select_related('business').get(contact_number=self.phone_no)
                
    def get_reply_context(self):
        try:
            context_id = self.messages.get("context", {}).get("id")
            if context_id:
                reply_context_instance = MessageContext.objects.get(message_log__message_id=context_id)
                return reply_context_instance, reply_context_instance.context
            else:
                return None, None
        except:
            return None, None
        
    def get_reaction_emoji(self):
        try:
            print(self.messages)
            message_id = self.messages.get("reaction", {}).get("message_id")
            emoji      = self.messages.get("reaction", {}).get("emoji")
            print(f"message_id is {message_id}")
            print(emoji)
            #print(MessageContext.objects.get(message_log__message_id = message_id))
            print("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")
            if message_id:
                MessageContext.objects.filter(message_log__message_id = message_id).update(reaction_reciver = emoji)
                reply_context_instance = MessageContext.objects.get(message_log__message_id = message_id)
                message_relation_instance = self.get_message_relation()
                unique_id = str(message_relation_instance.unique_id).replace("-", "")
                content = json.dumps(reply_context_instance.context)
                display_name = get_display_name(message_relation_instance)
                current_time = self.time_now.strftime("%Y-%m-%d %H:%M:%S")
                websocket_data = {
                    'type'                        :'chat.message',
                    'messages_context'            : content,
                    'messages_reply_context'      : self.reply_context,
                    'messages_sender'             : self.messages_from,
                    'messages_receiver'           : self.phone_no,
                    'messages_timestamp_sent'     : current_time,
                    'messages_timestamp_delivered': current_time,
                    'messages_messages_id'        : message_id,
                    'unique_id'                   : unique_id,
                    'reaction_reciver'            : emoji,
                }
                send_data_via_websocket('ws/chat', websocket_data, unique_id)
                content = json.loads(reply_context_instance.context)
                #body = content.get("text", {}).get("body") if content.get("type") == "text" else f"{content.get('type')}/{content.get(content.get('type'), {}).get('caption')}"
                body = content.get("text", {}).get("body") if content.get("type") == "text" else content.get(content.get('type'), {}).get('caption', None)
                print(body)
                notification_data = {
                    "display_name": display_name,
                    #"body": f"reacted {emoji} to: {body}" if body else f"reacted {emoji} to:",
                    "body": f"reacted {emoji} to: {body}" if body else f"reacted {emoji} to: ",
                    "img": content.get("image", {}).get("link") if content.get("image", {}).get("link") else None
                }
                print(websocket_data)
                print(notification_data)
                send_data_via_websocket('ws/relation', websocket_data, self.phone_no,notification_data,self.project_obj.business.fcm_token)
                #send_data_via_websocket('ws/relation', websocket_data, self.phone_no)

                print(reply_context_instance)
                return True
            else:
                return None
        except Exception as e:
            print(str(e))
            print("======================== ERROR ==============================")
            return None

    def handle_message(self):
        try:
            message_reaction = self.get_reaction_emoji()
            print(message_reaction)
            print("^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^")
            if message_reaction:
                return True
            message_relation_instance = self.get_message_relation()
            self.update_servicing_window(message_relation_instance)
            business_instance = self.project_obj.business

            message_log_instance = MessageLog.objects.create(
                project=self.project_obj, message_id=self.messages_id, business=business_instance,
                outlet=business_instance.outlet, sender=self.messages_from, reciever=self.phone_no,
                timestamp_sent=self.time_now, timestamp_delivered=self.time_now, message_type='SERVICING'
            )
            # print(message_log_instance, "================0")

            message_context = MessageContext.objects.create(
                message_log = message_log_instance, reply_context=self.reply_context_instance,
                contact_relation = message_relation_instance
            )

            self.handle_file_attachments(message_context)
            content = json.dumps(self.messages)
            message_context.context_text = self.messages.get("text", {}).get("body") if self.messages.get("text", {}).get("body") else self.messages.get("image", {}).get("caption")
            message_context.context = content
            message_context.save()

            message_relation_instance.last_message = message_context
            message_relation_instance.count += 1
            message_relation_instance.save()

            self.send_websocket_data(message_relation_instance, content, message_log_instance)
            self.send_reply()

        except Exception as e:
            print(str(e), "=======================receive_message")
        
        return True

    def get_message_relation(self):
        try:
            return MessageRelation.objects.get(sender=self.phone_no, receiver=self.messages_from)
        except MessageRelation.DoesNotExist:
            country_code, contact_no = get_phone_code(self.messages_from)

            outlet_details = self.project_obj.outlet

            contact_info, created = Contacts.objects.get_or_create(
                phone_code=country_code, contact=contact_no, outlet=outlet_details,
                defaults={'is_active': True}
            )
            if not created:
                contact_info.is_active = True
                contact_info.save()

            return MessageRelation.objects.create(sender=self.phone_no, receiver=self.messages_from, receiver_info=contact_info)

    def update_servicing_window(self, message_relation_instance):
        threshold_time = message_relation_instance.servicing_window
        if threshold_time is None or timezone.now() - threshold_time > timedelta(hours=24):
            message_relation_instance.servicing_window = timezone.now()
            message_relation_instance.chat_status = 'pending'
            message_relation_instance.save()
            

    def handle_file_attachments(self, message_context):
        if self.content_file is not None:
            if 'image' in self.messages:
                file_type = 'jpg'
                self.messages['image']['link'] = self.file_handler.save_file_and_get_link(message_context.file_data, file_type, self.content_file)
            elif 'video' in self.messages:
                file_type = 'mp4'
                self.messages['video']['link'] = self.file_handler.save_file_and_get_link(message_context.file_data, file_type, self.content_file)
            elif 'document' in self.messages:
                file_type = self.file_handler.get_document_type(self.content_file)
                self.messages['document']['link'] = self.file_handler.save_file_and_get_link(message_context.file_data, file_type, self.content_file)
            elif 'audio' in self.messages:
                file_type = 'mp3'
                self.messages['audio']['link'] = self.file_handler.save_file_and_get_link(message_context.file_data, file_type, self.content_file)

    def send_websocket_data(self, message_relation_instance, content, message_log_instance):
        unique_id = str(message_relation_instance.unique_id).replace("-", "")
        message_relation_data = model_to_dict(message_relation_instance)

        # Convert datetime fields to string format
        for key, value in message_relation_data.items():
            if isinstance(value, datetime):
                message_relation_data[key] = value.isoformat()

        last_message = message_relation_instance.last_message
        message_relation_data.update({
            'unique_id': unique_id,
            'last_message': last_message.context,
            'last_message_timestamp_sent': last_message.message_log.timestamp_sent.isoformat() if last_message.message_log.timestamp_sent else None,
            'last_message_timestamp_delivered': last_message.message_log.timestamp_delivered.isoformat() if last_message.message_log.timestamp_delivered else None,
            'last_message_timestamp_read': last_message.message_log.timestamp_read.isoformat() if last_message.message_log.timestamp_read else None
        })

        message_relation_data = {f"messages_{key}": value for key, value in message_relation_data.items()}
        message_relation_json = json.dumps(message_relation_data)

        print(message_relation_json, "--------------data")

        websocket_data = {
            'type': 'chat.message',
            'data': message_relation_json
        }

        content = json.loads(content)
        display_name = get_display_name(message_relation_instance)
        #message_relation_instance.display_name if message_relation_instance.display_name else message_relation_instance.receiver
        notification_data = {
            "display_name": display_name,
            "body": content.get("text", {}).get("body") if content.get("type") == "text" else f"{content.get('type')}/{content.get(content.get('type'), {}).get('caption')}",
            "img": content.get("image", {}).get("link") if content.get("image", {}).get("link") else None
        }
        send_data_via_websocket('ws/relation', websocket_data, self.phone_no,notification_data,self.project_obj.business.fcm_token)

        current_time = self.time_now.strftime("%Y-%m-%d %H:%M:%S")
        content = json.dumps(content)
        websocket_data = {
            'type'                        :'chat.message',
            'messages_context'            : content,
            'messages_reply_context'      : self.reply_context,
            'messages_sender'             : self.messages_from,
            'messages_receiver'           : self.phone_no,
            'messages_timestamp_sent'     : current_time,
            'messages_timestamp_delivered': current_time,
            'messages_message_id'         : message_log_instance.message_id,
            'unique_id'                   : unique_id
        }
        print(websocket_data)
        send_data_via_websocket('ws/chat', websocket_data, unique_id)

    def send_reply(self):
        try:
            reply_text = self.messages['text']['body']
            opt_class = OptSend(self.messages_from, self.phone_no, reply_text)
            opt_class.send_message_opt()
        except:
            pass

# ### Subsection: UPDATE TEMPLATE TIMEMARK ####

def mark_timestamp(time_now,statuses):
    try:
        message_id   = statuses.get('id')
        status       = statuses.get('status')
        errors        = statuses.get('errors', [{}])[0]
        error_remark  = errors.get('title') or ''
        fieldname     = f'timestamp_{status}'
        
        ############# set time in log ###################
        message_log_instance        = MessageLog.objects.get(message_id=message_id)
        message_log_instance.remark = error_remark
        
        ############ get message relation ##########################
        message_relation_instance = MessageRelation.objects.get(sender=message_log_instance.sender,receiver=message_log_instance.reciever)
        
        ############ set timestamp and transactions ##########################
        print("iiiiiiiiiiiiiiiiiiiiiiiiiiiiiinnnnnn")
        print(message_log_instance,status,"=============================status")
        if status == 'sent':
            setattr(message_log_instance, fieldname, time_now)
            message_log_instance.save()
            message_log_instance        = MessageLog.objects.get(message_id=message_id)
            message_context = MessageContext.objects.get(message_log__id=message_log_instance.id)
            mark_template_sent(message_relation_instance,message_log_instance,message_context)
        elif status == 'failed':
            message_log_instance.timestamp_sent      = None
            message_log_instance.timestamp_read      = None
            message_log_instance.timestamp_delivered = None
            message_transaction(message_log_instance,message_relation_instance,time_now,status)
        elif status == 'read':
            if message_log_instance.timestamp_read is None:
                if message_log_instance.timestamp_sent is None:
                    message_log_instance.timestamp_sent = time_now
                # print(message_log_instance.timestamp_delivered,"=======================================message_log_instance.timestamp_delivered")
                if message_log_instance.timestamp_delivered is None:
                    message_log_instance.timestamp_delivered = time_now
                    # print("=====================================trueread")
                    message_transaction(message_log_instance,message_relation_instance,time_now,status)
        elif status == 'delivered':
            # print(message_log_instance.timestamp_delivered,"=======================================message_log_instance.timestamp_delivered")
            if message_log_instance.timestamp_delivered is None:
                # print("=====================================truedeliever")
                message_transaction(message_log_instance,message_relation_instance,time_now,status)
                if message_log_instance.timestamp_sent is None:
                    message_log_instance.timestamp_sent = time_now
                    
        if message_log_instance.timestamp_failed is None:
            setattr(message_log_instance, fieldname, time_now)
            
        message_log_instance.save()

        ################ set template count########################################
        fieldname = f'template_{status}'
        campaign_fieldname = f'campaign_{status}'
        try:
            WhatsappCampaign.objects.filter(id=message_log_instance.campaign.id).update(**{campaign_fieldname: F(campaign_fieldname) + 1})
        except Exception as e:
            pass
        try:
            TemplateDetails.objects.filter(templateId=message_log_instance.templateId).update(**{fieldname: F(fieldname) + 1})
        except Exception as e:
            return True
    except Exception as e:
        # print(str(e),"errroooooooooooooooooooooooooooorrrrr")
        return True
    
def mark_template_sent(message_relation_instance,message_log_instance,message_context):
    project_obj = ProjectDetails.objects.annotate(phonenumber=Concat(F('phone_code'),F('phone_no'))).get(phonenumber=message_relation_instance.sender)
    message_relation_instance.last_message_type = message_log_instance.message_type
    message_relation_instance.last_message      = message_context
    if message_log_instance.message_type == 'SERVICING':
        message_relation_instance.chat_status = 'ongoing'
    else:
        pass
    message_relation_instance.save()
    try:
        try:
            unique_id = str(message_relation_instance.unique_id).replace("-", "")
            message_relation_data = model_to_dict(message_relation_instance)

            # Convert datetime fields to string format
            for key, value in message_relation_data.items():
                if isinstance(value, datetime):
                    message_relation_data[key] = value.isoformat()

            last_message = message_relation_instance.last_message
            message_relation_data.update({
                'unique_id': unique_id,
                'last_message': last_message.context,
                'last_message_timestamp_sent': last_message.message_log.timestamp_sent.isoformat() if last_message.message_log.timestamp_sent else None,
                'last_message_timestamp_delivered': last_message.message_log.timestamp_delivered.isoformat() if last_message.message_log.timestamp_delivered else None,
                'last_message_timestamp_read': last_message.message_log.timestamp_read.isoformat() if last_message.message_log.timestamp_read else None
            })

            message_relation_data = {f"messages_{key}": value for key, value in message_relation_data.items()}
            message_relation_json = json.dumps(message_relation_data)

            print(message_relation_json, "--------------data")

            websocket_data = {
                'type': 'chat.message',
                'data': message_relation_json
            }

            content = json.loads(message_context.context)
            if message_relation_instance.receiver_info.first_name :
                if message_relation_instance.receiver_info.first_name and message_relation_instance.receiver_info.last_name :
                    display_name = message_relation_instance.receiver_info.first_name + " " + message_relation_instance.receiver_info.last_name
                else :
                    display_name = message_relation_instance.receiver_info.first_name
            else:
                if message_relation_instance.display_name :
                    display_name = message_relation_instance.display_name
                else:
                    display_name = message_relation_instance.receiver
            #message_relation_instance.display_name if message_relation_instance.display_name else message_relation_instance.receiver
            notification_data = {
                "display_name": display_name,
                "body": content.get("text", {}).get("body") if content.get("type") == "text" else f"{content.get('type')}/{content.get(content.get('type'), {}).get('caption')}",
                "img": content.get("image", {}).get("link") if content.get("image", {}).get("link") else None
            }
            
            send_data_via_websocket('ws/relation', websocket_data, message_relation_instance.sender,notification_data,project_obj.business.fcm_token)
        except Exception as e:
            print(str(e),'kkkkkkkkkkkkkkkkkkkkkkkkkk')


        unique_id       = str(message_relation_instance.unique_id)
        unique_id       = unique_id.replace("-","")
        current_time = message_log_instance.timestamp_sent.strftime("%Y-%m-%d %H:%M:%S")
        websocket_data  = {
            'type'                          : 'chat.message',
            'messages_context'              : message_context.context,
            'messages_sender'               : message_log_instance.sender,
            'messages_receiver'             : message_log_instance.reciever, 
            'messages_message_id'           : message_log_instance.message_id, 
            'messages_timestamp_sent'       : current_time,
            # 'messages_timestamp_delivered': current_time,
            # 'messages_timestamp_read'     : current_time, 
            'unique_id'                     : unique_id,
        }
        url = 'ws/chat'
        # print(websocket_data,"========================================websocket_data")
        send_data_via_websocket(url,websocket_data,unique_id)
    except Exception as e:
        # print(str(e),"========================================marktimestamp_error")
        pass
    return True 

def message_transaction(message_log_instance, message_relation_instance, time_now, status):
    try:
        print(status, "=======================message_transactionsssssssssssssssss")
        threshold_time = timezone.now() - timedelta(hours=24)
        message_type = message_log_instance.message_type
        block_columns = {
            "MARKETING": "marketing_balance_block",
            "SERVICING": "servicing_balance_block",
            "UTILITY": "utility_balance_block",
        }
        balance_columns = {
            "MARKETING": "marketing_balance",
            "SERVICING": "servicing_balance",
            "UTILITY": "utility_balance",
        }
        total_balance_columns = {
            "MARKETING": "total_marketing_balance",
            "SERVICING": "total_servicing_balance",
            "UTILITY": "total_utility_balance",
        }
        block_column_name         = block_columns[message_type]
        balance_column_name       = balance_columns[message_type]
        total_balance_column_name = total_balance_columns[message_type]

        project_obj = ProjectDetails.objects.annotate(
            phone_number=Concat(F('phone_code'), F('phone_no'))
        ).get(Q(phone_number=message_log_instance.sender))

        if message_type == "SERVICING":
            current_month_message_log_count = MessageLog.objects.filter(
                timestamp_delivered__month=timezone.now().month,
                timestamp_delivered__year=timezone.now().year,
                message_type="SERVICING",
                is_debited=True
            ).count()
            threshold_time = message_relation_instance.servicing_window

        message_log_check = MessageLog.objects.filter(
            Q(reciever=message_log_instance.reciever) & Q(sender=message_log_instance.sender),
            is_debited=True,
            timestamp_delivered__gte=threshold_time,
            message_type=message_type
        ).first()

        wallet_obj = WhatsappWallet.objects.get(project=project_obj)
        
        if not message_log_check:
            if (message_type == 'SERVICING' and current_month_message_log_count <= 1000) or status == 'failed':
                per_message_cost = Decimal(0)
                remark = "This amount is added to your balance due to it being your {}th service message.".format(current_month_message_log_count) if status != 'failed' else "This amount is added back to your balance because the message failed to send."
            else:
                per_message_cost = wallet_obj.deduction_plan.get(message_type, Decimal(0))
                remark = "{} has been deducted from your wallet for a {} message.".format(per_message_cost, message_type)
            
            message_log_instance.is_debited = True
            message_log_instance.debited_amount = per_message_cost
            message_log_instance.save()

            if message_type != "SERVICING":
                fieldname = f'{message_type.lower()}_window'
                setattr(message_relation_instance, fieldname, time_now)
                message_relation_instance.save()
        else:
            per_message_cost = Decimal(0)
            remark = "This amount is added to your balance because the {} window is active.".format(message_type)

        balance_inst       = wallet_obj.total_balance
        block_amount_inst  = wallet_obj.is_block
        message_cost       = wallet_obj.deduction_plan.get(message_type, Decimal(0))
        check_paid_before  = WhatsappWalletTransaction.objects.filter(message_log = message_log_instance)
        check_is_unblocked = WhatsappWalletTransaction.objects.filter( block_of_unblock = message_log_instance.wallet_trans, unblocked_message__contains=[message_log_instance.id])
        # check_is_unblocked = WhatsappWalletTransaction.objects.filter(block_of_unblock = message_log_instance.wallet_trans)
        if check_paid_before.exists():
            pass
        if per_message_cost == Decimal(0) or status == 'failed':
            wllettransaction_obj = WhatsappWalletTransaction.objects.create(
                project                 = wallet_obj.project,
                message_log             = message_log_instance
                )
            update_query = f"""
                    UPDATE xl2024_wallet_whatsapp
                    SET balance = ROUND(CASE WHEN is_block >= %s THEN balance + %s ELSE balance END, 5),
                        {balance_column_name} = ROUND(CASE WHEN {block_column_name} >= %s THEN {balance_column_name} + %s ELSE {balance_column_name} END, 5),
                        {block_column_name} = ROUND(CASE WHEN {block_column_name} >= %s THEN {block_column_name} - %s ELSE {block_column_name} END, 5),
                        is_block = ROUND(CASE WHEN is_block >= %s THEN is_block - %s ELSE is_block END, 5)
                    WHERE project_id = %s
                """
            params = [
                message_cost,
                message_cost,
                message_cost,
                message_cost,
                message_cost,
                message_cost,
                message_cost,
                message_cost,
                project_obj.id
            ]
        else:
            if check_is_unblocked.exists():
                update_query = f"""
                        UPDATE xl2024_wallet_whatsapp
                        SET balance = ROUND(balance - %s,5),
                            total_balance = ROUND(total_balance - %s,5)
                        WHERE project_id = %s
                    """
                params = [
                    per_message_cost,
                    per_message_cost,
                    project_obj.id
                ]
            else:
                update_query = f"""
                        UPDATE xl2024_wallet_whatsapp
                        SET balance = ROUND(CASE WHEN is_block < %s THEN balance - %s ELSE balance END, 5),
                            {balance_column_name} = ROUND(CASE WHEN {block_column_name} < %s THEN {balance_column_name} - %s ELSE {balance_column_name} END, 5),
                            is_block = ROUND(CASE WHEN is_block >= %s THEN is_block - %s ELSE is_block END, 5),
                            {block_column_name} = ROUND(CASE WHEN {block_column_name} >= %s THEN {block_column_name} - %s ELSE {block_column_name} END, 5),
                            total_balance = ROUND(total_balance - %s, 5),
                            {total_balance_column_name} = ROUND({total_balance_column_name} - %s, 5)
                        WHERE project_id = %s
                    """
                params = [
                    per_message_cost,
                    per_message_cost,
                    per_message_cost,
                    per_message_cost,
                    per_message_cost,
                    per_message_cost,
                    per_message_cost,
                    per_message_cost,
                    per_message_cost,
                    per_message_cost,
                    project_obj.id
                ]

        with connection.cursor() as cursor:
            cursor.execute(update_query, params)

        wallet_obj_new = WhatsappWallet.objects.get(project = project_obj)
        wllettransaction_obj.transaction_no  = str(uuid.uuid4()).replace('-', '')
        wllettransaction_obj.shop            = wallet_obj.outlet.web_url
        wllettransaction_obj.payment_status  = 'Unblocked' if per_message_cost == Decimal(0) or status == 'failed' else 'Debit'
        wllettransaction_obj.reciever        = message_log_instance.reciever
        wllettransaction_obj.sender          = message_log_instance.sender
        wllettransaction_obj.message_type    = message_type
        wllettransaction_obj.payment_date    = datetime.now()
        wllettransaction_obj.original_balance_amount = balance_inst
        wllettransaction_obj.block_amount    = Decimal(block_amount_inst)
        wllettransaction_obj.balance_amount  = wallet_obj_new.total_balance
        wllettransaction_obj.amount          = message_cost if per_message_cost == Decimal(0) or status == 'failed' else per_message_cost
        wllettransaction_obj.debit_amount    = 0 if per_message_cost == Decimal(0) or status == 'failed' else per_message_cost
        wllettransaction_obj.remarks         = remark
        wllettransaction_obj.wallet          = wallet_obj
        wllettransaction_obj.business        = wallet_obj.business
        wllettransaction_obj.outlet          = wallet_obj.outlet
        wllettransaction_obj.save()

        # WhatsappWalletTransaction.objects.create(
        #     transaction_no          = str(uuid.uuid4()).replace('-', ''),
        #     shop                    = wallet_obj.outlet.web_url,
        #     wallet                  = wallet_obj,
        #     project                 = wallet_obj.project,
        #     business                = wallet_obj.business,
        #     payment_status          = 'Unblocked' if per_message_cost == Decimal(0) or status == 'failed' else 'Debit',
        #     reciever                = message_log_instance.reciever,
        #     sender                  = message_log_instance.sender,
        #     message_type            = message_type,
        #     payment_date            = datetime.now(),
        #     original_balance_amount = balance_inst,
        #     block_amount            = block_amount_inst,
        #     balance_amount          = wallet_obj.total_balance,
        #     amount                  = message_cost if per_message_cost == Decimal(0) or status == 'failed' else per_message_cost,
        #     debit_amount            = 0 if per_message_cost == Decimal(0) or status == 'failed' else per_message_cost,
        #     outlet                  = wallet_obj.outlet,
        #     remarks                 = remark,
        #     message_log             = message_log_instance
        # )

        return True
    except Exception as e:
        print(str(e), "aaaaa")

# ### Subsection: TEMPLATE STATUS UPDATE ###
def template_status_update(event,reason,message_template_id):
    try:
        TemplateDetails.objects.filter(templateId =message_template_id).update(template_status = event,error_reason =reason)
    except Exception as e:
        print(str(e))
        pass
    return True

# ### Subsection: CUSTOMER ORDER / CATLOG ORDER ###
def process_customer_order(customer_message,customer_name, customer_number,display_contact):
    customer_catalog_id = customer_message.get("order", {}).get("catalog_id")
    product_items = customer_message.get("order", {}).get("product_items", [])
    currency = "INR"
    price = sum(item.get("item_price", 0) for item in product_items)
    currency = product_items[0].get('currency', 'INR') if product_items else 'INR'
    price *= 100
    url, phone_no = process_payment(customer_name, customer_number, price, currency)
    if not display_contact or not url or not phone_no:
        return None
    business_instance = BusinessDetails.objects.filter(contact=display_contact).first()
    if not business_instance:
        return None
    project_instance = ProjectDetails.objects.filter(business=business_instance).first()
    if not project_instance:
        return None
    return business_instance, project_instance, url, phone_no

def process_payment(customer_name, customer_number, price, currency):
    client = razorpay.Client(auth=(RAZORPAY_API_KEY, RAZORPAY_SECRET_KEY))
    expiry_time_minutes=30
    response = client.payment_link.create({
        "amount": price,
        "currency": currency,
        "accept_partial": 'false',
        "expire_by": int(time.time() + (expiry_time_minutes * 60)),
        "description": "For XYZ purpose",
        "customer": {
            "name": customer_name,
            "contact": customer_number
        },
        "notify": {
            "sms": 'false',
            "email": 'false'
        },
        "reminder_enable": 'false',
        "notes": {
            "name": customer_name,
            "contact": customer_number
        },
        "callback_url": "",
        "callback_method": "get"
    })

    url = response['short_url'][17:]
    phone_no = response['notes']['contact']
    return url, phone_no

def send_whatsapp_message(phone_no, customer_name, url, project_instance):
    button_variables = [{'type': 'text', 'text': url}]
    body_variables = [{'type': 'text', 'text': customer_name}]
    data = {
        'contact': phone_no,
        'type': 'TEXT',
        'button_variables': button_variables,
        'body_variables': body_variables,
        'token': project_instance.token,
        'template_name': 'razorpay_template'
    }
    send_message(data)

def create_shopify_order(shop, response):
    shopify_url = f'https://{shop}/admin/api/2024-01/orders.json'
    headers = {
        'X-Shopify-Access-Token': response['access_token'],
        'Content-Type': 'application/json'
    }
    payload = {
        "order": {
            "line_items": [{
                "title": "Big Brown Bear Boots",
                "price": 74.99,
                "grams": "1300",
                "quantity": 3,
                "tax_lines": [{"price": 13.5, "rate": 0.06, "title": "State tax"}]
            }],
            "transactions": [{"kind": "sale", "status": "success", "amount": 238.47}],
            "total_tax": 13.5,
            "currency": "EUR"
        }
    }
    response = requests.post(shopify_url, headers=headers, json=payload).json()
    return response

####websocket############
"""""
def send_data_via_websocket(url,data,unique_id,):
    websocket_url = f"wss://api.demo.xircls.in/{url}/?unique_id={unique_id}"
    try:
        # websocket.enableTrace(True)
        ws = websocket.WebSocket()
        ws.connect(websocket_url)
        ws.send(json.dumps(data))
        ws.close()
        print("Data sent via WebSocket successfully.")
    except Exception as e:
        print("Error sending data via WebSocket:", str(e))
"""""
        
def send_data_via_websocket(url, data, unique_id,notification_data = None,fcm_token = None):
    websocket_url = f"wss://api.demo.xircls.in/{url}/?unique_id={unique_id}"
    print(notification_data)
    print("in websocket")
    try:
        # WebSocket communication
        ws = websocket.WebSocket()
        ws.connect(websocket_url)
        ws.send(json.dumps(data))
        print(json.dumps(data))
        ws.close()
        print("Data sent via WebSocket successfully.")
    except Exception as e:
        print("Error sending data via WebSocket:", str(e))

    message = json.dumps(data)
    # Firebase push notification
    if url == "ws/relation":
        if isinstance(fcm_token, list) and fcm_token:
            #fcm_token = BusinessDetails.objects.filter(outlet_id=outlet_id).values_list('fcm_token', flat=True).first()
        
            try:
                # message = messaging.Message(
                #     notification=messaging.Notification(
                #         title = notification_data['display_name'],
                #         body = notification_data['body'] , 
                #         image = notification_data['img'] if notification_data['img'] else None
                #     ),
                #     token=fcm_token
                # )
                # response = messaging.send(message)
                message = messaging.MulticastMessage(
                    notification = messaging.Notification(
                        title = notification_data['display_name'],
                        body  = notification_data['body'] ,
                        image = notification_data['img'] if notification_data['img'] else None
                    ),data  = { "title": notification_data['display_name'],
                    "body" : notification_data['body'],
                    },
                    tokens = fcm_token
                )
                response = messaging.send_multicast(message)
                print(f'Push notification sent successfully: {response}')
            except Exception as e:
                print(f'Error sending push notification: {str(e)}')
        else:
            print("fcm_token token not found")
    else:
        pass


def get_display_name(message_relation_instance):
    if message_relation_instance.receiver_info.first_name :
        if message_relation_instance.receiver_info.first_name and message_relation_instance.receiver_info.last_name :
            display_name = message_relation_instance.receiver_info.first_name + " " + message_relation_instance.receiver_info.last_name
        else :
            display_name = message_relation_instance.receiver_info.first_name
    else:
        if message_relation_instance.display_name :
            display_name = message_relation_instance.display_name
        else:
            display_name = message_relation_instance.receiver
    return display_name
# ##############################################################################################################################################
# Section: ADD CONTACT
# ##############################################################################################################################################     

#Add contact from csv file 
@csrf_exempt
@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def import_customer(request):
    try:
        csv_file = request.FILES.get('csvFile')
        outlet_api_key          = request.META.get('HTTP_API_KEY')
        project_api_key         = request.META.get('HTTP_WHATSAPP_PROJECT_KEY')
        if outlet_api_key is None :
            return JsonResponse({'error': 'outlet_api_key is missing'}, status=404)
        if project_api_key is None :
            return JsonResponse({'error': 'project_api_key is missing'}, status=404)
        if not csv_file:
            return JsonResponse({'error': 'No file provided', 'success': False}, status=404)
        outlet_obj      = outlet_details.objects.get(api_key= outlet_api_key)
        project_obj     = ProjectDetails.objects.get(api_key = project_api_key)
        decoded_file    = csv_file.read().decode('utf-8').splitlines()
        csv_reader      = csv.DictReader(decoded_file)
        contact_arr     = []
        existing_arr    = []
        for row in csv_reader:
            contact     = row.get('contact')
            first_name  = row.get('first_name')
            last_name   = row.get('last_name')
            phone_code  = row.get('code','91')
            if not re.match(r'^[a-zA-Z0-9 ]+$', contact):
                continue  
            if Contacts.objects.filter(contact=contact,outlet=outlet_obj,project=project_obj).exists():
                existing_contact_obj = Contacts.objects.filter(contact=contact,outlet=outlet_obj,project=project_obj).last()
                existing_contact_obj.first_name = first_name
                existing_contact_obj.last_name  = last_name
                existing_contact_obj.outlet     = outlet_obj
                existing_contact_obj.is_active  = True
                existing_contact_obj.save()
                existing_arr.append(existing_contact_obj)
                print('ssssssssssssssssssssssssss')
                continue
            print('hjjhjhjjj')
            contact_obj = Contacts(
                contact    = contact,
                phone_code = phone_code,
                first_name = first_name,
                last_name  = last_name,
                outlet     = outlet_obj,
                project    = project_obj,
                is_active  = True
            )
            contact_obj.save()
            contact_arr.append(contact_obj)
        print(contact_arr,existing_arr,"===========================================================>")
        # Contacts.objects.bulk_create(contact_arr)
        if request.POST.get('contact_group', None):
            try:
                group_list = [int(x) for x in request.POST.get('group_list').split(',')]
            except:
                group_list = [request.POST.get('group_list')]
            group_objects = ContactsGroup.objects.filter(id__in=group_list,project=project_obj)
            if request.POST.get('add'):
                all_contact_arr = contact_arr + existing_arr
                len_all_contact = len(all_contact_arr)
                for group_obj in group_objects:
                    group_obj.update(count=F('count')+len_all_contact)
                    group_obj.contact.add(*all_contact_arr)
        
        return JsonResponse({'message': 'File uploaded successfully', 'success': True},status=status.HTTP_200_OK)
    except (outlet_details.DoesNotExist,ProjectDetails.DoesNotExist) as e:
        if isinstance(e, outlet_details.DoesNotExist):
            return JsonResponse({'error': 'Invalid API Key outlet details not found'}, status=404)
        elif isinstance(e, ProjectDetails.DoesNotExist):
            return JsonResponse({'error': 'Project details not found'}, status=404)
    except Exception as e:
        print(str(e))
        return JsonResponse({"error": "Something went wrong!"}, status=500)
    
@csrf_exempt
@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def import_contacts_from_shopify(request):
    try:
        outlet_api_key  = request.META.get('HTTP_API_KEY')
        project_api_key = request.META.get('HTTP_WHATSAPP_PROJECT_KEY')
        if outlet_api_key is None :
            return JsonResponse({'error': 'outlet_api_key is missing'}, status=404)
        if project_api_key is None :
            return JsonResponse({'error': 'project_api_key is missing'}, status=404)
        outlet_obj      = outlet_details.objects.get(api_key= outlet_api_key)
        project_obj     = ProjectDetails.objects.get(api_key = project_api_key)
        shop=outlet_obj.web_url
        shopify_obj = ShopifyXirclsApp.objects.get(shop=shop,app="whatsapp")
        url=f"https://{shop}/admin/api/{SHOPIFY_API_YEAR}/customers.json"
        headers = {
                        'X-Shopify-Access-Token' : shopify_obj.access_token,
                        'Content-Type': 'application/json',
                        'accept': 'application/json'
                    }
        response=requests.get(url=url,headers=headers)
        response=json.loads(response.text)
        customer_list=response.get('customers')
        contact_arr=[]
        for cust_data in customer_list:
            first_name=cust_data.get('first_name')
            last_name=cust_data.get('last_name')
            phone=cust_data.get('phone')
            email=cust_data.get('email')
            phone_code='91'
            if phone is None:
                phone=cust_data.get('default_address').get('phone')

            if phone is not None:
                if phone[0]=='+':
                    phone=phone[-10:]
                if Contacts.objects.filter(contact=phone,outlet=outlet_obj,project=project_obj).exists():
                    continue
                contact_obj = Contacts(
                    contact    = phone,
                    phone_code = phone_code,
                    first_name = first_name,
                    last_name  = last_name,
                    email      = email,
                    outlet     = outlet_obj,
                    project    = project_obj,
                    is_active  = True
                )
                contact_arr.append(contact_obj)
        Contacts.objects.bulk_create(contact_arr)
        return JsonResponse({'message':'Contacts Added Successfully', 'success': True},status=status.HTTP_200_OK)
    except (outlet_details.DoesNotExist,ProjectDetails.DoesNotExist) as e:
        if isinstance(e, outlet_details.DoesNotExist):
            return JsonResponse({'error': 'Invalid API Key outlet details not found'}, status=404)
        elif isinstance(e, ProjectDetails.DoesNotExist):
            return JsonResponse({'error': 'Project details not found'}, status=404)
    except Exception as e:
        print(str(e))
        return JsonResponse({"error": "Something went wrong!"}, status=500)

@csrf_exempt
@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def add_whatsapp_contanct(request):
    try:
        outlet_api_key          = request.META.get('HTTP_API_KEY')
        project_api_key         = request.META.get('HTTP_WHATSAPP_PROJECT_KEY')
        if outlet_api_key is None :
            return JsonResponse({'error': 'outlet_api_key is missing'}, status=404)
        if project_api_key is None :
            return JsonResponse({'error': 'project_api_key is missing'}, status=404)
        outlet_obj   = outlet_details.objects.get(api_key = outlet_api_key)
        project_obj  = ProjectDetails.objects.get(api_key = project_api_key)
        contact_list_json = request.POST.get('contact_list')
        if contact_list_json:
            contact_list = json.loads(contact_list_json)
        else:
            return JsonResponse({'error': 'contact_list is empty'}, status=404)
        contact_arr = []
        for contact_obj in contact_list:
            contact_no   = contact_obj.get('contact',None)
            first_name   = contact_obj.get('first_name',None)
            last_name    = contact_obj.get('last_name',None)
            country_code = contact_obj.get('phone_code',None)
            if contact_no is not None:
                try:
                    Contacts.objects.get(phone_code=country_code,contact=contact_no,outlet=outlet_obj,project=project_obj)
                except Exception as e:
                    print(str(e))
                    contact_object = Contacts(
                        contact=contact_no,
                        phone_code=country_code,
                        first_name=first_name,
                        last_name=last_name,
                        outlet=outlet_obj,
                        project=project_obj,
                        is_active=True
                    )
                    contact_arr.append(contact_object)
        Contacts.objects.bulk_create(contact_arr)
        return JsonResponse({'message': 'contact list added successfully','success': True}, status=status.HTTP_200_OK)
    except (outlet_details.DoesNotExist,ProjectDetails.DoesNotExist) as e:
        if isinstance(e, outlet_details.DoesNotExist):
            return JsonResponse({'error': 'Invalid API Key outlet details not found'}, status=404)
        elif isinstance(e, ProjectDetails.DoesNotExist):
            return JsonResponse({'error': 'Project details not found'}, status=404)
    except Exception as e:
        print(str(e))
        return JsonResponse({"error": "Something went wrong!"}, status=500)

@csrf_exempt
@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def contact_delete(request):
    try:
        project_api_key         = request.META.get('HTTP_WHATSAPP_PROJECT_KEY')
        if project_api_key is None :
            return JsonResponse({'error': 'project_api_key is missing'}, status=404)
        project_obj = ProjectDetails.objects.get(api_key = project_api_key)
        try:
            contact_list = [int(x) for x in request.POST.get('contact_list').split(',')]
            print(" try Contact List  ================== ", contact_list) 
        except:   
            contact_list = [str(request.POST.get('contact_list'))] 
            print("Contact List  ================== ", contact_list) 
        contact_objects = Contacts.objects.filter(id__in=contact_list,project=project_obj)
        print(contact_objects,"===================================")
        contact_groups = ContactsGroup.objects.filter(contact__in=contact_objects,project=project_obj)
        for contact_group in contact_groups:
            for contact in contact_objects:
                contact_group.contact.remove(contact)
        contact_groups.update(count =F('count') - contact_objects.count())
        contact_objects.update(is_active = False)
        response = {
            'message': 'Deleted successfully',
            'success':True
        }
        return JsonResponse(response, status=status.HTTP_200_OK)
    except (ProjectDetails.DoesNotExist) as e:
        if isinstance(e, ProjectDetails.DoesNotExist):
            return JsonResponse({'error': 'Project details not found'}, status=404)
    except Exception as e:
        print(str(e))
        print("======================== ERROR ==============================")
        return JsonResponse({"error": "Something went Wrong!"}, status=500)
    
@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def get_group_contact(request):
    try:
        datatables = request.POST
        start = int(datatables.get('page'))
        length = int(datatables.get('size'))
        over_all_search = datatables.get('searchValue')
        field_mapping = {
            0: "first_name__icontains",
            1: "last_name__icontains",
            2: "phone_code__icontains",
            3: "contact__icontains",
        }
        advance_filter = Q()
        for col, field in field_mapping.items():
            value = datatables.get(f"columns[{col}][search][value]", None)
            if value:
                advance_filter &= Q(**{field: value})
        if over_all_search:
            overall_search_filter = Q()
            for field in field_mapping.values():
                overall_search_filter |= Q(**{field: over_all_search})
            advance_filter |= overall_search_filter
        group_list = [int(x) for x in request.POST.get('group_contact').split(',')]
        contact_group_ids = ContactsGroup.objects.filter(id__in=group_list).values_list('contact', flat=True)
        contact_obj = Contacts.objects.filter(id__in=contact_group_ids).filter(advance_filter).values(
            contact_details_id = F('id'),
            contact_first_name = F("first_name"),
            contact_last_name = F("last_name"),
            contact_details_phone_code =F("phone_code"),
            contact_details_contact =F("contact"),
        ).order_by('-id')
        contact_obj_count = contact_obj.count()
        paginator = Paginator(contact_obj, length)
        try:
            object_list = paginator.page(start).object_list
        except (PageNotAnInteger, EmptyPage):
            object_list = paginator.page(1).object_list
        message = {
            'contact_grp_count': contact_obj_count,
            "contact_grp": list(object_list)
        }
        return JsonResponse(message, safe = False, status=200)
    except Exception as e:
        print(str(e))
        print("======================== ERROR ==============================")
        return JsonResponse({"error": "Something went Wrong!"}, status=500)
# Get contact details for advance tables

@csrf_exempt
@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def contact_details(request):
    try:
        datatables = request.POST
        outlet_api_key          = request.META.get('HTTP_API_KEY')
        project_api_key         = request.META.get('HTTP_WHATSAPP_PROJECT_KEY')
        if outlet_api_key is None :
            return JsonResponse({'error': 'outlet_api_key is missing'}, status=404)
        if project_api_key is None :
            return JsonResponse({'error': 'project_api_key is missing'}, status=404)
        outlet_obj      = outlet_details.objects.get(api_key = outlet_api_key)
        project_obj     = ProjectDetails.objects.get(api_key = project_api_key)
        over_all_search = datatables.get('searchValue')
        field_mapping = {
            0: "cont.first_name",
            1: "cont.last_name",
            2: "cont.phone_code",
            3: "cont.contact",
            4: "cg.name",
        }
        sql_query = '''
            SELECT
                cont.id AS contact_details_id,
                cont.phone_code AS contact_details_phone_code,
                cont.contact AS contact_details_contact,
                cont.first_name AS contact_first_name,
                cont.last_name AS contact_last_name,
                JSON_ARRAYAGG(cg.name) AS contact_details_groups
            FROM
                xl2024_contacts AS cont
            LEFT JOIN
                xl2024_contacts_group_contact AS cont_grp ON cont.id = cont_grp.contacts_id
            LEFT JOIN
                xl2024_contacts_group AS cg ON cont_grp.contactsgroup_id = cg.id
            JOIN
                xl925_outlet_basic_details AS o ON cont.outlet_id = o.id
            JOIN
                xl2024_project_details AS proj ON cont.project_id = proj.id
            WHERE
                o.id = {0}
                AND cont.is_active = True 
                AND proj.id = {1}
        '''.format(outlet_obj.id,project_obj.id)

        if over_all_search:
            # Construct the search condition for all fields
            search_conditions = " OR ".join(field + " LIKE '%" + over_all_search + "%'" for field in field_mapping.values())
            # Append the search condition to the SQL query
            sql_query += " AND (" + search_conditions +") "
        sql_query += "GROUP BY cont.id ORDER BY cont.id DESC"
        print(sql_query)
        connection = mysql.connector.connect(
            database=API_DB_NAME,
            user=API_USER_NAME,
            password=API_DB_PASSWORD
        )
        cursor = connection.cursor()
        cursor.execute(sql_query)

        contact_obj = dictfetchall(cursor)
        print(contact_obj)
        cursor.close()
        connection.close()
        start = int(datatables.get('page'))
        length = int(datatables.get('size'))
        
        contact_obj_count = len(contact_obj)
        paginator = Paginator(contact_obj, length)
        try:
            object_list = paginator.page(start).object_list
        except (PageNotAnInteger, EmptyPage):
            object_list = paginator.page(1).object_list
        print(contact_obj_count)
        response = {
            'contact_count': contact_obj_count,
            "contact_details_obj": object_list
        }
        return JsonResponse(response, status=status.HTTP_200_OK)
    except (outlet_details.DoesNotExist,ProjectDetails.DoesNotExist) as e:
        if isinstance(e, outlet_details.DoesNotExist):
            return JsonResponse({'error': 'Invalid API Key outlet details not found'}, status=404)
        elif isinstance(e, ProjectDetails.DoesNotExist):
            return JsonResponse({'error': 'Project details not found'}, status=404)
    except Exception as e:
        print(str(e))
        print("======================== ERROR ==============================")
        return JsonResponse({"error": "Something went wrong!"}, status=500)
# ##############################################################################################################################################
# Section: GROUP CHAT
# ##############################################################################################################################################     

# Create group data
@csrf_exempt
@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def create_group(request):
    try:
        outlet_api_key          = request.META.get('HTTP_API_KEY')
        project_api_key         = request.META.get('HTTP_WHATSAPP_PROJECT_KEY')
        if outlet_api_key is None :
            return JsonResponse({'error': 'outlet_api_key is missing'}, status=404)
        if project_api_key is None :
            return JsonResponse({'error': 'project_api_key is missing'}, status=404)
        outlet_obj  = outlet_details.objects.get(api_key = outlet_api_key)
        project_obj = ProjectDetails.objects.get(api_key = project_api_key)
        group = ContactsGroup.objects.create(
            name = request.POST.get('group_name'),
            description = request.POST.get('group_description'),
            outlet = outlet_obj,
            project = project_obj,
            count  = 0
        )
        return JsonResponse({'msg': f'Group created successfully.', 'success': True}, status=200)
    except (outlet_details.DoesNotExist,ProjectDetails.DoesNotExist) as e:
        if isinstance(e, outlet_details.DoesNotExist):
            return JsonResponse({'error': 'Invalid API Key outlet details not found'}, status=404)
        elif isinstance(e, ProjectDetails.DoesNotExist):
            return JsonResponse({'error': 'Project details not found'}, status=404)
    except Exception as e:
        print(str(e))
        print("======================== ERROR ==============================")
        return JsonResponse({"error": "Something went wrong!"}, status=500)
# Get group data
@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def group_details(request):
    group_id                =  request.POST.get('group_id')
    outlet_api_key          = request.META.get('HTTP_API_KEY')
    project_api_key         = request.META.get('HTTP_WHATSAPP_PROJECT_KEY') 
    if outlet_api_key is None :
        return JsonResponse({'error': 'outlet_api_key is missing'}, status=404)
    elif project_api_key is None :
        return JsonResponse({'error': 'project_api_key is missing'}, status=404)
    elif group_id is None :
            return JsonResponse({'error': 'group_id is missing'}, status=404)
    else:
        pass
    project_obj = ProjectDetails.objects.get(api_key = project_api_key)
    group   = ContactsGroup.objects.get(id=group_id,project = project_obj)
    contact = group.contact.filter(is_active=True)
    try:
        datatables = request.POST
        start = int(datatables.get('page'))
        length = int(datatables.get('size'))
        over_all_search = datatables.get('searchValue')
        field_mapping = {
            0: "first_name__icontains",
            1: "last_name__icontains",
            2: "contact__icontains",
            
        }
        advance_filter = Q()
        for col, field in field_mapping.items():
            value = datatables.get(f"columns[{col}][search][value]", None)
            if value:
                advance_filter &= Q(**{field: value})
        if over_all_search:
            overall_search_filter = Q()
            for field in field_mapping.values():
                overall_search_filter |= Q(**{field: over_all_search})
            advance_filter |= overall_search_filter
        contact = contact.filter(advance_filter).values(
            contact_id = F('id'),
            contact_first_name = F("first_name"),
            contact_last_name = F("last_name"),
            contact_contact =F("contact"),
            contact_phone_code =F("phone_code"),
        )
        contact_count = contact.count()
        paginator = Paginator(contact, length)
        try:
            object_list = paginator.page(start).object_list
        except (PageNotAnInteger, EmptyPage):
            object_list = paginator.page(1).object_list
        response = {
            'group_count': contact_count,
            "group_details_obj": list(object_list)
        }
        return JsonResponse(response,status=status.HTTP_200_OK)
    except (ContactsGroup.DoesNotExist,ProjectDetails.DoesNotExist) as e:
        if isinstance(e, ContactsGroup.DoesNotExist):
            return JsonResponse({'error': f"Group with id {group_id} does not exist."}, status=404)
        elif isinstance(e, ProjectDetails.DoesNotExist):
            return JsonResponse({'error': 'Project details not found'}, status=404)
    except Exception as e:
        print(str(e))
        print("======================== ERROR ==============================")
        return JsonResponse({"error": "Something went wrong!"}, status=500)

@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def group_base_details(request):
    try:
        outlet_api_key          = request.META.get('HTTP_API_KEY')
        project_api_key         = request.META.get('HTTP_WHATSAPP_PROJECT_KEY')
        if outlet_api_key is None :
            return JsonResponse({'error': 'outlet_api_key is missing'}, status=404)
        if project_api_key is None :
            return JsonResponse({'error': 'project_api_key is missing'}, status=404)
        outlet_obj      = outlet_details.objects.get(api_key = outlet_api_key)
        project_obj     = ProjectDetails.objects.get(api_key = project_api_key)
        datatables      = request.POST
        start           = int(datatables.get('page'))
        length          = int(datatables.get('size'))
        over_all_search = datatables.get('searchValue')
        field_mapping = {
            0: "name__icontains",
            1: "description__icontains",
            2: "count__icontains",
        }
        advance_filter = Q()
        for col, field in field_mapping.items():
            value = datatables.get(f"columns[{col}][search][value]", None)
            if value:
                advance_filter &= Q(**{field: value})
        if over_all_search:
            overall_search_filter = Q()
            for field in field_mapping.values():
                overall_search_filter |= Q(**{field: over_all_search})
            advance_filter |= overall_search_filter
        groups = ContactsGroup.objects.filter(outlet=outlet_obj,project=project_obj).filter(advance_filter).values(
            group_id = F("id"),
            group_name = F("name"),
            group_description = F("description"),
            group_contact =Count("contact"),
            group_count =F("count"),
        )
        if groups is None:
            return JsonResponse({'error': 'groups not found'}, status=404)
        else:
            pass
        groups_count = groups.count()
        paginator = Paginator(groups, length)
        try:
            object_list = paginator.page(start).object_list
        except (PageNotAnInteger, EmptyPage):
            object_list = paginator.page(1).object_list
        response = {
            'total_group_count': groups_count,
            "group_details_obj": list(object_list)
        }
        return JsonResponse(response, status=status.HTTP_200_OK)
    except (outlet_details.DoesNotExist,ProjectDetails.DoesNotExist) as e:
        if isinstance(e, outlet_details.DoesNotExist):
            return JsonResponse({'error': 'Invalid API Key outlet details not found'}, status=404)
        elif isinstance(e, ProjectDetails.DoesNotExist):
            return JsonResponse({'error': 'Project details not found'}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@csrf_exempt
@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def group_contact(request):
    try:
        try:
            contact_list = [int(x) for x in request.POST.get('contact_list').split(',')]
        except:
            contact_list = [request.POST.get('contact_list')]
        try:
            group_list  = [int(x) for x in request.POST.get('group_list').split(',')]
        except:
            group_list  = [request.POST.get('group_list')]
        contact_objects = Contacts.objects.filter(id__in=contact_list)
        group_objects   = ContactsGroup.objects.filter(id__in=group_list)
        if request.POST.get('add'):
            for group_obj in group_objects:
                # for contact_obj in contact_objects:
                group_obj.contact.add(*contact_objects)
            message ='Added successfully'
        else:
            for group_obj in group_objects:
                group_obj.contact.remove(*contact_objects)  
            message ='Remove successfully'
        group_objects = ContactsGroup.objects.filter(id__in=group_list)
        for group in group_objects:
            group_objects_count= group.contact.count()
            group_objects.update(count=group_objects_count)
        response = {
            'message': message,
            'success':True
        }
        return JsonResponse(response, status=status.HTTP_200_OK)
    except (ContactsGroup.DoesNotExist,Contacts.DoesNotExist) as e:
        if isinstance(e, ContactsGroup.DoesNotExist):
            return JsonResponse({"error": "Group does not exist."}, status=404)
        elif isinstance(e, Contacts.DoesNotExist):
            return JsonResponse({"error": "Contacts does not exist."}, status=404)
    except Exception as e:
        print(str(e))
        print("======================== ERROR ==============================")
        return JsonResponse({"error": "Something went wrong!"}, status=500)

@csrf_exempt
@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def group_delete(request):
    try:
        contact_list = [int(x) for x in request.POST.get('group_list').split(',')]
        contact_objects = ContactsGroup.objects.filter(id__in=contact_list)
        for obj in contact_objects:
            obj.contact.clear()
        contact_objects.delete()
        response = {
            'message': 'Deleted successfully',
            'success':True
        }
        return JsonResponse(response, status=status.HTTP_200_OK)
    except (ContactsGroup.DoesNotExist) as e:
        if isinstance(e, ContactsGroup.DoesNotExist):
            return JsonResponse({"error": "Group does not exist."}, status=404)
    except Exception as e:
        print(str(e))
        print("======================== ERROR ==============================")
        return JsonResponse({"error": "Something went wrong!"}, status=500)


@csrf_exempt
@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def group_import_customer(request):
    try:
        outlet_api_key          = request.META.get('HTTP_API_KEY')
        project_api_key         = request.META.get('HTTP_WHATSAPP_PROJECT_KEY')
        csv_file = request.FILES.get('csvFile')
        if outlet_api_key is None :
            return JsonResponse({'error': 'outlet_api_key is missing'}, status=404)
        elif project_api_key is None :
            return JsonResponse({'error': 'project_api_key is missing'}, status=404)
        elif not csv_file:
            return JsonResponse({'message': 'No file provided', 'success': False}, status=404)
        else:
            pass
        outlet_obj  = outlet_details.objects.get(api_key = outlet_api_key)
        project_obj = ProjectDetails.objects.get(api_key = project_api_key)
        try:
            group_list = [int(x) for x in request.POST.get('group_list').split(',')]
        except:
            group_list = [request.POST.get('group_list')]
        decoded_file = csv_file.read().decode('utf-8').splitlines()
        csv_reader = csv.DictReader(decoded_file)
        contact_arr = []
        existing_contacts = []
        print("===========================okkkkk")
        for row in csv_reader:
            contact     = row.get('contact')
            first_name  = row.get('first_name')
            last_name   = row.get('last_name')
            phone_code  = row.get('code','91')
            print(contact,first_name,phone_code,"===========================okkkkk")
            if not re.match(r'^[a-zA-Z0-9 ]+$', contact):
                continue  
            if Contacts.objects.filter(contact=contact,outlet=outlet_obj,project=project_obj).exists():
                contact_obj = Contacts.objects.filter(contact=contact,outlet=outlet_obj,project=project_obj).last()
                contact_obj.is_active = True
                contact_obj.save()
            else:
                contact_obj = Contacts(
                    contact=contact,
                    phone_code=phone_code,
                    first_name=first_name,
                    last_name=last_name,
                    outlet=outlet_obj,
                    project = project_obj,
                    is_active=True
                )
                contact_obj.save()
                contact_arr.append(contact_obj)
            existing_contacts.append(contact_obj)
        # try:
        #     Contacts.objects.bulk_create(contact_arr)
        #     print('000000000000000000000')
        # except:
        #     print('apsssssssssssssssssssss')
        #     pass
        if len(existing_contacts) > 0:
            contactgrp = ContactsGroup.objects.get(id__in=group_list)
            contactgrp.count += len(existing_contacts)
            contactgrp.contact.add(*existing_contacts)
            contactgrp.save()
        else:
            print("No existing contacts found.")
        print(len(contact_arr))
        return JsonResponse({'message': 'File uploaded successfully', 'success': True}, status=200)
    except (outlet_details.DoesNotExist,ProjectDetails.DoesNotExist) as e:
        if isinstance(e, outlet_details.DoesNotExist):
            return JsonResponse({'error': 'Invalid API Key outlet details not found'}, status=404)
        elif isinstance(e, outlet_details.MultipleObjectsReturned):
                return JsonResponse({'error': 'Multiple outlets found with the same API Key'}, status=400)
        elif isinstance(e, ProjectDetails.DoesNotExist):
            return JsonResponse({'error': 'Project details not found'}, status=404)
        elif isinstance(e, ProjectDetails.MultipleObjectsReturned):
                return JsonResponse({'error': 'Multiple projects found with the same API Key'}, status=400)
    except Exception as e:
        print(str(e))
        print("======================== ERROR ==============================")
        return JsonResponse({"error": "Something went wrong!"}, status=500)

# ##############################################################################################################################################
# Section: SEND MESSAGES FUNCTION
# ##############################################################################################################################################     

from django.shortcuts import redirect

@authentication_classes([])
@permission_classes([AllowAny])
def redirect_to_url(request):
    url = request.GET.get('url')
    id=request.GET.get('id')
    print(id,"=======================================id")
    reciever=request.GET.get('reciever')
    templateId=request.GET.get('templateId')
    print(url,"======================================url")
    if url:
        try:
            message_instance = MessageLog.objects.get(id=int(id),reciever=reciever,templateId=templateId)
            message_instance.url_count +=1
            message_instance.save()
            link_track_instance = LinkTracking.objects.create(
                url = url,
                messagelog=message_instance,
                project=message_instance.project,
                campaign=message_instance.campaign,
                template=message_instance.template
            )
            
        except:
            pass
        return redirect(f"{url}")
    else:
        return redirect('/')
    
# ### Subsection:TEMPLATE SENDING FUNCTION ###
#LATEST MESSAGE SEND FUNCTION 
class MessageSender:

    def __init__(self, **kwargs):
        self.button_variables   = kwargs.get('button_variables', None)
        self.template_instance  = kwargs.get('template_instance')
        self.project_instance   = self.template_instance.project
        self.campaign_id        = kwargs.get('campaign_id',None)
        self.wallet_transaction = None
        self.per_message_cost   = None
        self.trigger            = kwargs.get('trigger',False)
        self.entry_point        = kwargs.get('entry_point',None)
        self.response           = kwargs.get('response', False)

    def send_messages(self, customer_list):
        self.url     = f'{direct_server}/messages'
        self.headers  = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.template_instance.project.token}' 
        }
        count = 0
        kwargs = {
            'project_id' :self.template_instance.project.id,
            'total_messages' : len(customer_list),
            'template_type' : self.template_instance.template_type
        }
        fun_response, message, total_cost, self.per_message_cost= check_wallet_balance(**kwargs)
        print(fun_response, message, total_cost,"============================")
        if fun_response:
            kwargs = {
                'total_cost'       : total_cost,
                'project_id'       : self.template_instance.project.id,
                'template_type'    : self.template_instance.template_type,
                'per_message_cost' : self.per_message_cost,
                'campaign_id'      : self.campaign_id
            }
            self.wallet_transaction = new_block_amount(**kwargs)
            kwargs = {
                'per_message_cost'  : self.per_message_cost,
                'project_id'        : self.template_instance.project.id,
                'wallet_transaction': self.wallet_transaction,
                'template_type'     : self.template_instance.template_type
            }
            scheduled_block_amount(**kwargs)
            print(self.wallet_transaction,"======================wallet_transaction")
        else:
            return (False, message, None)
        
        for cust_instance in customer_list:
            data_dict = self.create_data_dict(cust_instance)
            print(data_dict,"data_dict======================")
            message_log_instance = MessageLog.objects.create(project=self.template_instance.project)
            self.message_log_id = message_log_instance.id
            print(message_log_instance)
            print(self.message_log_id)
            print("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$  message_log_instance  $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")
            self.receiver_phone_number                          = data_dict['phone_code'] + data_dict['contact'] if data_dict.get('contact',None) is not None else data_dict['phone_number_with_code']
            body_variable_list, body_variable_example_list      = self.process_body_variables(data_dict)
            header_variable_list, header_variable_example_list  = self.process_header_variables(data_dict)
            button_variable_list                                = self.button_variables
            component_list, context_payload                     = self.construct_components(data_dict, button_variable_list, body_variable_list, header_variable_list, header_variable_example_list, body_variable_example_list)
            self.add_carousel_components(data_dict, component_list, context_payload)
            payload                                             = self.construct_payload(data_dict, component_list)
            self.send_payload(payload, context_payload, data_dict)
            count += 1
        #eta = datetime.now() + timedelta(days=3)
            
        print((True, self.send_response, context_payload) if self.send_response else (False,True,None),"resssppppppp")
        return (True, self.send_response, context_payload) if self.send_response else (False,True,None)

    def create_data_dict(self, cust_instance):
        try:
            print({
                'FirstName': cust_instance.first_name,
                'LastName': cust_instance.last_name,
                'contact': cust_instance.contact,
                'phone_code': cust_instance.phone_code,
                'phone_number_with_code' : None,
                'abandoned_image' : "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRH_CglF1nTmh55EVintfBCZJyaAw-eSMymig&s",
                'abandoned_link' : "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRH_CglF1nTmh55EVintfBCZJyaAw-eSMymig&s",
            })
            return {
                'FirstName': cust_instance.first_name,
                'LastName': cust_instance.last_name,
                'contact': cust_instance.contact,
                'phone_code': cust_instance.phone_code,
                'phone_number_with_code' : None,
                'abandoned_image' : "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRH_CglF1nTmh55EVintfBCZJyaAw-eSMymig&s"
            }
        
        except:
            data_dict = {}
            extra_key = ['first_name', 'last_name', 'customer_name']
            extra_fields = {'first_name': 'FirstName', 'last_name': 'LastName', 'customer_name': 'customerName'}
            
            for key, value in cust_instance.items():
                if key not in extra_key:
                    data_dict[key] = str(cust_instance.get(key, ''))
                elif key == 'phone_code':
                    data_dict[key] = str(cust_instance.get(key, '91'))
                else:
                    data_dict[extra_fields[key]] = str(cust_instance.get(key, ''))
            # data_dict['AbandonCart'] = 
            print(data_dict,"====================data_dict")
            return data_dict
        
    def process_body_variables(self, data_dict):
        try:
            body_variable_list = eval(self.template_instance.body_variable_list)
            body_variable_example_list = []
            print(data_dict,"=======================================")
            print(body_variable_list,"=======================================")
            for variable in body_variable_list:
                print(variable["text"],"==================variable")
                print(data_dict.get(variable["text"], "--"),"data_dict.get=======================================")
                content = data_dict.get(variable["text"], "--") if data_dict.get(variable["text"], "--") is not None else "--"
                # content = data_dict.get(variable["text"], "--") if len(data_dict.get(variable["text"], "--")) > 0 else "--"
                body_variable_example_list.append(content)
                variable["text"] = content
            return body_variable_list, [body_variable_example_list]
        except Exception as e:
            print(str(e), "==================error")
            return [], []

    def process_header_variables(self, data_dict):
        try:
            header_variable_list = eval(self.template_instance.header_variable_list)
            header_variable_example_list = []
            for variable in header_variable_list:
                content = data_dict.get(variable["text"], "--") if data_dict.get(variable["text"], "--") is not None else "--"
                # content = data_dict.get(variable["text"], "--") if len(data_dict.get(variable["text"], "--")) > 0 else "--"
                header_variable_example_list.append(content)
                variable["text"] = content
            return header_variable_list, [header_variable_example_list]
        except Exception as e:
            return [], []

    def process_button_variables(self,button_variable_list,data_dict):
        from collections import defaultdict
        try:
            # button_variable_list    = eval(self.template_instance.button_variable_list)
            new_button_variable_list = []
            button_order          = {ele["type"]: count for count, ele in enumerate(button_variable_list)}
            # url_button_order      = {ele: count if ele == "URL" else pass for count, ele in enumerate(url_button_order)}
            url_order = defaultdict(list)

            # Iterate through the list and append the index to the corresponding type list
            for count, ele in enumerate(button_variable_list):
                if ele["type"] == 'URL':
                    url_order[ele["type"]].append(count)

            # Convert defaultdict to a regular dictionary if needed
            url_order = dict(url_order)
            print(button_order,"==================================button_order")
            print(url_order,"==================================url_order")
            url_count = 1
            for variable in button_variable_list:
                if variable['type'] in ['COPY_CODE']:
                    new_variable = {
                        "type": "button",
                        "sub_type": "COPY_CODE",
                        "index": button_order['COPY_CODE'],
                        "parameters": [
                            {
                                "type": "coupon_code",
                                "coupon_code": variable['example']
                            }
                        ]
                    }
                    new_button_variable_list.append(new_variable)
                if variable['type'] in ['URL']:
                    try:
                        print(json.loads(self.template_instance.dynamic_link),"=================================")
                        dynamic_link = json.loads(self.template_instance.dynamic_link)
                        print(f'url_{url_count}',dynamic_link,"==============================")
                        dynamic_link = dynamic_link.get(f'url_{url_count}')
                        print(url_order.get('URL')[int(url_count)-1],"==============================dynamic_link")
                        # {'url_1':{'url':'https://asdasd.com','parameters':'product'}}
                        url_index = url_order.get('URL')[int(url_count)-1]
                        if dynamic_link.get('parameters') != 'STATIC':
                            text_to_replace = data_dict[dynamic_link.get('parameters')] if data_dict.get(dynamic_link.get('parameters',None)) else ""
                            print(dynamic_link.get('url'),"===========================user_url")
                            user_url = dynamic_link.get('url').replace('{{1}}',text_to_replace)
                            part_url = f"redirect_to_url/?url={user_url}&reciever={self.receiver_phone_number}&templateId={self.template_instance.templateId}&id={self.message_log_id}"
                            new_variable = {
                                "type": "button",
                                "sub_type": "URL",
                                "index": url_index,
                                "parameters": [
                                    {
                                        "type": "text",
                                        "text": part_url
                                    }
                                ]
                            }   
                            url_count += 1
                            new_button_variable_list.append(new_variable)
                        else:
                            # text_to_replace = data_dict[dynamic_link.get('parameters')] if data_dict[dynamic_link.get('parameters',None)] else ""
                        
                            user_url = dynamic_link.get(f'url')
                            part_url = f"redirect_to_url/?url={user_url}&reciever={self.receiver_phone_number}&templateId={self.template_instance.templateId}&id={self.message_log_id}"
                            new_variable = {
                                "type": "button",
                                "sub_type": "URL",
                                "index": url_index,
                                "parameters": [
                                    {
                                        "type": "text",
                                        "text": part_url
                                    }
                                ]
                            }   
                            url_count += 1
                            new_button_variable_list.append(new_variable)
                            #pass
                    except:
                        pass
                else:
                    pass
            return new_button_variable_list
        except Exception as e:
            print(str(e),"=========================================++++")
            return new_button_variable_list

    def construct_components(self, data_dict, button_variable_list, body_variable_list, header_variable_list, header_variable_example_list, body_variable_example_list):
        component_list = []
        context_payload = json.loads(self.template_instance.payload)
        payload_order_index = {ele["type"]: count for count, ele in enumerate(context_payload["components"])}
        # print(payload_order_index, "========================payload_order")
        # print(context_payload, '======context_payload')

        if self.template_instance.file_type != 'text':
            self.add_file_header_component(data_dict,component_list)

        elif header_variable_list:
            self.add_text_header_component(component_list, header_variable_list, header_variable_example_list, context_payload, payload_order_index)

        if body_variable_list:
            self.add_body_component(component_list, body_variable_list, body_variable_example_list, context_payload, payload_order_index)

        button_index            = payload_order_index.get('BUTTONS',None) 
        if button_index is not None:
            button_variable_list      = context_payload["components"][button_index]["buttons"]
            print(button_variable_list,"==================================button_variable_list")
            button_variable_list    = self.process_button_variables(button_variable_list,data_dict)
            print(button_variable_list,"==================================button_variable_list2")
            self.add_button_component(button_variable_list, component_list, context_payload, payload_order_index)

        return component_list, context_payload

    def add_file_header_component(self,data_dict,component_list):
        try:
            try:
                dynamic_media = eval(self.template_instance.dynamic_media)
            except:
                dynamic_media = self.template_instance.dynamic_media
            print(dynamic_media,"=======================================dynamic_media")
            
            link = dynamic_media[0].get('header_media',None)
            if link is not None or link != 'DEFAULT':
                print(link,'==================================link') 
                file_type = self.template_instance.file_type
                media_format = 'png' if self.template_instance.file_type == 'image' else 'mp4'
                print(dynamic_media[0].get(f'header_media',None) is not None,"=================================ddd")
                link = data_dict.get(dynamic_media[0].get('header_media')) if dynamic_media[0].get(f'header_media',None) is not None else f"{XIRCLS_DOMAIN}/static/template_document/DUMMY_{file_type.upper()}.{media_format}"
                print(link,data_dict.get(dynamic_media[0].get('header_media')),self.template_instance.file_data,"=========================")
                if link is None:
                    link = f"{XIRCLS_DOMAIN}/static/template_document/DUMMY_{file_type.upper()}.{media_format}" if link is None or link == ''or ' ' else link
            print(link,'=================================')
            # print(self.template_instance.file_data.url is not None or len(self.template_instance.file_data.url) > 0)
            # print(len(self.template_instance.file_data.url) > 0)
            try:
                print(self.template_instance.file_data.url is not None or len(self.template_instance.file_data.url) > 0)
                if self.template_instance.file_data.url is not None or len(self.template_instance.file_data.url) > 0:
                    print("=======================in")
                    link = f"{XIRCLS_DOMAIN}/static/{self.template_instance.file_data}"
            except:
                pass
            print(link,"=======================truelink")
            component_list.append({
                "type": "header",
                "parameters": [{
                    "type": self.template_instance.file_type,
                    self.template_instance.file_type: {
                        "link": link,
                    }
                }]
            })
            if self.template_instance.file_type == 'document':
                component_list[0]["parameters"][0]["document"]['filename'] = self.template_instance.filename
        except Exception as e:
            print(str(e), "error header")

    def add_text_header_component(self, component_list, header_variable_list, header_variable_example_list, context_payload, payload_order_index):
        try:
            header_index = payload_order_index['HEADER']
            context_payload["components"][header_index]['example']['header_text'] = header_variable_example_list
            component_list.append({
                "type": "header",
                "parameters": header_variable_list
            })
        except Exception as e:
            print(str(e), "error header")

    def add_body_component(self, component_list, body_variable_list, body_variable_example_list, context_payload, payload_order_index):
        try:
            body_index = payload_order_index['BODY']
            context_payload["components"][body_index]['example']['body_text'] = body_variable_example_list
            component_list.append({
                "type": "body",
                "parameters": body_variable_list
            })
        except Exception as e:
            print(str(e), "error body")

    def add_button_component(self, button_variable_list, component_list, context_payload, payload_order_index):
        try:
            for button in button_variable_list:
                component_list.append(button)
        except Exception as e:
            print(str(e), "error button")

    def add_carousel_components(self, data_dict, component_list, context_payload):
        try:
            if str(context_payload['components'][1]['type']) == 'CAROUSEL':
                carsouel_list = []
                carsouel_payload = {
                    "type": "CAROUSEL",
                    "cards": []
                }
                carousel_instance = CarouselCard.objects.filter(template_details=self.template_instance).order_by('id')
                index = 0
                for obj in carousel_instance:
                    card_list = self.process_carousel_card(data_dict, obj, index)
                    card_payload = {
                        "card_index": index,
                        "components": card_list
                    }
                    carsouel_list.append(card_payload)
                    index += 1
                carsouel_payload['cards'] = carsouel_list
                component_list.append(carsouel_payload)
        except Exception as e:
            print(str(e), "carousel error")

    def process_carousel_card(self, data_dict, obj, index):
        card_list = []
        link = f"{XIRCLS_DOMAIN}/static/{self.template_instance.file_data}"
        # try:
        #     dynamic_media = eval(self.template_instance.dynamic_media)
        # except:
        #     dynamic_media = self.template_instance.dynamic_media
        # link = dynamic_media[0].get(f"carousel_image_{index}",f"{XIRCLS_DOMAIN}/static/{self.template_instance.file_data}")
            
        # link = data_dict.get(dynamic_media[0].get('header_image').replace('{','').replace('}','')) if dynamic_media[0].get('header_image',None) is not None else f"{XIRCLS_DOMAIN}/static/{self.template_instance.file_data}"
            
        try:
            if obj.file_data:
                link = f"{XIRCLS_DOMAIN}/static/{obj.file_data.url}"
                card_list.append({
                    "type": "header",
                    "parameters": [{
                        "type": obj.file_type,
                        obj.file_type: {
                            "link": link,
                        }
                    }]
                })
                if obj.file_type == 'document':
                    card_list[0]["parameters"][0]["document"]['filename'] = obj.filename
        except Exception as e:
            print(str(e), "carousel header error")

        try:
            carousel_body_variable_list = eval(obj.body_variable_list)
            for variable in carousel_body_variable_list:
                content = data_dict.get(variable["text"], "--") if len(data_dict.get(variable["text"], "--")) > 0 else "--"
                variable["text"] = content
            if carousel_body_variable_list:
                card_list.append({
                    "type": "body",
                    "parameters": carousel_body_variable_list
                })
        except Exception as e:
            print(str(e), "carousel body error")

        try:
            carousel_button_variable_list = eval(obj.button_variable_list)
            if carousel_button_variable_list:
                card_list.append({
                    "type": "button",
                    "sub_type": "url",
                    "index": "0",
                    "parameters": carousel_button_variable_list
                })
        except Exception as e:
            print(str(e), "carousel button error")

        return card_list

    def construct_payload(self, data_dict, component_list):
        return {
            "to": self.receiver_phone_number,
            "type": "template",
            "template": {
                "language": {
                    "policy": "deterministic",
                    "code": "en"
                },
                "name": self.template_instance.templateName,
                "components": component_list
            }
        }

    def send_payload(self, payload, context_payload, data_dict):
        
        try:
            response = requests.post(self.url, headers=self.headers, data=json.dumps(payload, indent=4)).json()
            print(payload, "=================================payload")
            # print(response, "======================response")
            self.send_response = response
        
            if 'code' in response:
                data = {
                    'templateId' : self.template_instance.templateId,
                    'message_id' : str(response["code"]),
                    'reciever'   : self.receiver_phone_number,
                    'sender'     : self.project_instance.phone_code + self.project_instance.phone_no,
                    'remark'     : response['message'],
                    'campaign_id': self.campaign_id,
                    'wallet_transaction': self.wallet_transaction,
                    'message_log_id'            : self.message_log_id
                }
                sending_log(data)
                kwargs = {
                    'template_type'         : self.template_instance.template_type,
                    'project'               : self.project_instance,
                    'receiver_phone_number' : self.receiver_phone_number,
                    'per_message_cost'      : self.per_message_cost,
                    'remark'                : response['message'],
                    'message_log_id'        : self.message_log_id
                }
                unblock_failed_at_sending(**kwargs)
                
            else:
                # print("=======================okk")
                template_inst = json.loads(self.template_instance.payload)
                template_type = template_inst['category']
                data = {
                    'templateId'    : self.template_instance.templateId,
                    'message_id'    : str(response['messages'][0]["id"]),
                    'reciever'      : response['contacts'][0]["wa_id"],
                    'sender'        : self.project_instance.phone_code + self.project_instance.phone_no,
                    'context'       : context_payload,
                    'remark'        : None,
                    'template_type' : template_type,
                    'campaign_id'   : self.campaign_id,
                    'trigger'       : self.trigger,
                    'entry_point'   : self.entry_point,
                    'customer_data' : [data_dict],
                    'wallet_transaction': self.wallet_transaction,
                    'message_log_id'    : self.message_log_id
                }
                # print(data,"============================================okkkkkk")
                sending_log(data)
                
        except Exception as e:
            print(str(e), "==================erorr 1")
            try:
                # create ContactsGroup if sending fails
                with transaction.atomic():
                    name = payload.get('name',default ='Failed Message Group')
                    description = payload.get('description',default ='Group created due to a failed message sending attempt')
                    outlet = payload.get('outlet')
                    project = payload.get('project')
                    Contacts = payload.get('Contacts', [])
                    Count = len(Contacts)

                    # ContactsGroup isinstance
                    contacts_group = ContactsGroup.objects.create(
                        name = name,
                        description = description,
                        outlet = outlet,
                        project = project,
                        count = Count,
                        created_at = timezone.now()
                    )

                    if Contacts:
                        contacts_group.contact.set(Contacts)
                    contacts_group.save()

                    print(f"Payload sending failed, created ContactsGroup with id: {contacts_group.id}")
                # template_inst = json.loads(self.template_instance.payload)
                # template_type = template_inst['category']
                # data = {
                #     'templateId': self.template_instance.templateId,
                #     'message_id': 'error',
                #     'reciever': self.receiver_phone_number,
                #     'sender': self.project_instance.phone_code + self.project_instance.phone_no,
                #     'context': context_payload,
                #     'remark': response,
                #     'template_type': template_type,
                #     'campaign_id': self.campaign_id,
                #     'wallet_transaction': self.wallet_transaction,
                #     'message_id'        : self.message_id,
                #     'message_log_id'    : self.message_log_id
                # }
                # sending_log(data)
            # except Exception as e:
            #     print(str(e), "==================payload error 2")
            except Exception as create_group_exception:
                print(str(create_group_exception), "==================payload error 2")


# ### Subsection: SEND SERIVCE MESSAGE ###
def send_service_message(outlet_id,reciever, **kwargs):
    try:
        message_body        = kwargs.get('message_body',None)
        caption             = kwargs.get('caption',None)
        filename            = kwargs.get('filename',None)
        type                = kwargs.get('type',None)
        file                = kwargs.get('file',None)
        data_dict           = kwargs.get('data_dict',{})
        per_message_cost    = kwargs.get('per_message_cost',0)
        project_id          = kwargs.get('project_id',None)
        file_type           = type.lower() if type else None
    
        url = f"{direct_server}/messages"
        try:
            project_instance = ProjectDetails.objects.get(id=project_id)
        except:
            return (False,{'error_message':'Project not found'})
        kwargs = {
            'project_id'     :project_instance.id,
            'total_messages' : 1,
            'template_type'  : 'SERVICING'
        }
        fun_response, message, total_cost, per_message_cost= check_wallet_balance(**kwargs)
        if fun_response:
            kwargs = {
                'total_cost'       :total_cost,
                'project_id'       :project_instance.id,
                'template_type'    :'SERVICING',
                'per_message_cost' : per_message_cost
            }
            wallet_transaction = new_block_amount(**kwargs)
        else:
            return (False, message , None)
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {project_instance.token}'
        }
        payload = {
            "to": reciever,
            "type": file_type,
        }
        print(reciever,'=======================================payloadddddddddddd')
        try:
            if file:
                model = MessageContext.objects.create(file_data=file,reply_context=None)
                # Accessing the URL of the uploaded file after saving it
                link = f"{XIRCLS_DOMAIN}/static{model.file_data.url}"
            else:
                link = kwargs.get('media_link',None)
        except Exception as e:
            print(str(e))
            link = None
        if file_type == 'text':
            body_text   = message_body
            for key, value in data_dict.items():
                if value is not None:
                    placeholder = "{{" + key + "}}"
                    body_text = body_text.replace(placeholder, value)
            payload[file_type] = {
                "body": body_text
            }
        else:
            payload[file_type] = {}
            if caption:
                payload[file_type]["caption"] = caption
            payload[file_type]["link"] = link
            if filename:
                payload[file_type]["filename"] = filename
        print(json.dumps(payload))
        response   = requests.request("POST", url, headers=headers, data = json.dumps(payload)).json()
        print(response,'========================')
        message_id = response.get('messages', [{}])[0].get('id', None)
        # time_now = timezone.now()
        if message_id is None : 
            message_log_instance = MessageLog.objects.create(sender=project_instance.phone_code + project_instance.phone_no,outlet=project_instance.outlet,reciever=reciever, message_id=message_id,message_type='SERVICING',project = project_instance,business = project_instance.business,timestamp_failed = datetime.now())
        else:
            
            kwargs = {
                'per_message_cost'  : per_message_cost,
                'project_id'        : project_instance.id,
                'wallet_transaction': wallet_transaction,
                'template_type'     : 'SERVICING',
                'waba_id'           : message_id
            }
            scheduled_block_amount(**kwargs)
            message_log_instance = MessageLog.objects.create(sender=project_instance.phone_code + project_instance.phone_no,outlet=project_instance.outlet,reciever=reciever, message_id=message_id,message_type='SERVICING',project = project_instance,business = project_instance.business,wallet_trans = wallet_transaction)
        try:
            message_context_instance = MessageContext.objects.get(id=model.id,reply_context=None)
        except:
            message_context_instance = MessageContext.objects.create(reply_context=None)
        message_context_instance.message_log=message_log_instance
        message_context_instance.context_text = message_body if message_body else payload.get("image", {}).get("caption")
        message_context_instance.context=json.dumps(payload)
        message_context_instance.save()
        return (True, response , payload)
    except Exception as e:
        print(str(e),'error')
        print(e)
        return (True, str(e), None)

# ### Subsection:INTERACTIVE SENDING FUNCTION ###
class InteractiveMessage:
    
    def __init__(self, **kwargs):
        self.template_instance  = kwargs.get('template_instance',None)
        self.campaign_instance  = kwargs.get('campaign_instance',None)
        self.payload            = json.loads(self.template_instance.payload)
        self.flow_id            = kwargs.get('flow_id',None)
        
    def send_messages(self, customer_list):
        project_instance = self.template_instance.project
        self.url     = f'{direct_server}/messages'
        self.project_instance = project_instance
        self.headers  = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {project_instance.token}' 
        }
        count = 0
        kwargs = {
            'project_id' :self.project_instance.id,
            'total_messages' : len(customer_list),
            'template_type' : 'SERVICING'
        }
        fun_response, message, total_cost, self.per_message_cost= check_wallet_balance(**kwargs)
        print(fun_response, message, total_cost,"============================")
        if fun_response:
            kwargs = {
                'total_cost' :total_cost,
                'project_id' :self.project_instance.id,
                'template_type' :'SERVICING',
                'per_message_cost' : self.per_message_cost
            }
            self.wallet_transaction = new_block_amount(**kwargs)
            print(self.wallet_transaction,"======================wallet_transaction")
        else:
            return (False, message, None)
        for cust_instance in customer_list:
            print(cust_instance,'=======================================customer_lis0')
            # print(eval(cust_instance),'=======================================customer_list1')
            data_dict = self.create_data_dict(cust_instance)
            self.receiver_phone_number =  data_dict['phone_code'] + data_dict['contact'] if data_dict.get('contact',None) is not None else data_dict['phone_number_with_code']
            self.construct_body_text(data_dict)
            print(self.payload.get('interactive').get('type'),"============================self.payload.get('interactive').get('type')")
            if self.payload.get('interactive').get('type') == 'flow':
                self.flow_id = self.payload.get('interactive').get('action').get('parameters').get('flow_id')
                print(self.flow_id,"==============================self.flow_id")
            self.send_payload(self.payload , data_dict)
            count += 1
        return (self.response,self.payload)
            
    def construct_body_text(self,data_dict):
        new_payload = self.payload
        body_text   = new_payload.get('interactive').get('body').get('text')
        for key, value in data_dict.items():
            if value is not None:
                placeholder = "{{" + key + "}}"
                body_text = body_text.replace(placeholder, value)
        new_payload['interactive']['body']['text'] = body_text
        new_payload['to'] = self.receiver_phone_number
        self.payload = new_payload
        return True
    
    def construct_header_text(self,data_dict):
        new_payload = self.payload
        body_text   = new_payload.get('interactive').get('header').get('text')
        for key, value in data_dict.items():
            if value is not None:
                placeholder = "{{" + key + "}}"
                body_text = body_text.replace(placeholder, value)
        new_payload['interactive']['header']['text'] = body_text
        new_payload['to'] = self.receiver_phone_number
        self.payload = new_payload
        return True
 
    def create_data_dict(self, cust_instance):
        try:
            return {
                'FirstName': cust_instance.first_name,
                'LastName': cust_instance.last_name,
                'contact': cust_instance.contact,
                'phone_code': cust_instance.phone_code,
                'phone_number_with_code' : None,
            }
        except:
            data_dict = {}
            extra_key = ['first_name', 'last_name', 'customer_name']
            extra_fields = {'first_name': 'FirstName', 'last_name': 'LastName', 'customer_name': 'customerName'}
            print(cust_instance,"===========================================")
            for key, value in cust_instance.items():
                if key == "contact":
                    print(key,value,"================================>key,value")
                if key not in extra_key:
                    data_dict[key] = str(cust_instance.get(key, ''))
                elif key == 'phone_code':
                    data_dict[key] = str(cust_instance.get(key, '91'))
                else:
                    data_dict[extra_fields[key]] = str(cust_instance.get(key, ''))
                    
            return data_dict
            
    def send_payload(self, payload, data_dict):
        self.response = requests.post(self.url, headers=self.headers, data=json.dumps(payload, indent=4)).json()
        print(self.response,"------------------------------------------------response 123213")
        try:
            print(self.flow_id,"==================================self.flow_id")
            if self.flow_id is not None:
                form_instance = WhatsAppFlowForm.objects.get(flow_form_id=self.flow_id)
            else:
                form_instance = None
        except Exception as e:
            form_instance = None
        try:
            message_relation = MessageRelation.objects.get(sender=self.project_instance.phone_code + self.project_instance.phone_no,receiver=self.response['contacts'][0]["wa_id"])
        except Exception as e:
            print(str(e),"=================================================eruieurguergugueguefu")
            message_relation = MessageRelation.objects.create(sender=self.project_instance.phone_code + self.project_instance.phone_no,receiver=self.response['contacts'][0]["wa_id"])
        message_log_instance = MessageLog.objects.create(
            project=self.project_instance,
            outlet=self.project_instance.outlet,
            business=self.project_instance.business,
            message_type= 'SERVICING',
            sender = self.project_instance.phone_code + self.project_instance.phone_no,
            reciever=self.response['contacts'][0]["wa_id"],
            message_id=self.response['messages'][0]["id"],
            campaign=self.campaign_instance,
            form    =  form_instance
        )
        MessageContext.objects.create(message_log=message_log_instance,context=json.dumps(payload),reply_context=None,contact_relation=message_relation)
        kwargs = {
            'per_message_cost'  : self.per_message_cost,
            'project_id'        :self.project_instance.id,
            'wallet_transaction': self.wallet_transaction,
            'template_type'     :'SERVICING',
            'waba_id'           :self.response['messages'][0]["id"],
        }
        scheduled_block_amount(**kwargs)
        
# ### Subsection: SINGLE MESSAGE SENDING / TEST SENDING ###
@csrf_exempt
@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def sendMessage(request):  
    try:
        templateId          = request.POST.get("template_id")
        outlet_api_key      = request.META.get('HTTP_API_KEY')
        project_api_key     = request.META.get('HTTP_WHATSAPP_PROJECT_KEY')   
        if outlet_api_key is None :
                return JsonResponse({'error': 'outlet_api_key is missing'}, status=404)
        elif project_api_key is None :
            return JsonResponse({'error': 'project_api_key is missing'}, status=404)
        elif templateId is None :
            return JsonResponse({'error': 'template_id is missing'}, status=404)
        outlet_obj          = outlet_details.objects.get(api_key = outlet_api_key)
        business_instance   = BusinessDetails.objects.get(outlet = outlet_obj)
        template            = TemplateDetails.objects.get(templateId=templateId,business=business_instance)
        reciver_number      = request.POST.get("reciver_no",None)
        first_name          = request.POST.get("first_name","--")
        last_name           = request.POST.get("last_name","--")
        body_variables      = dict(json.loads(request.POST.get("body_variables",'{}')))
        header_variables    = dict(json.loads(request.POST.get("header_variables",'{}')))

        customer_list       = [{
            'contact'           : request.POST.get("phone"),
            'phone_code'        : request.POST.get("phone_code",'91'),
            'reciver_number'    : reciver_number,
            'last_name'         : last_name,
            'first_name'        : first_name
        }]

        data_add = {**body_variables, **header_variables}
        customer_list[0].update(data_add)
        # print(customer_list,"============================customer_list")

        msg_sender = MessageSender(
            template_instance = template,
            response = True
        )
        fun_repsone , response, context_payload = msg_sender.send_messages(customer_list,)
        print(fun_repsone, response,'===================response')
        if 'error_data' or 'error_message' in response:
            return JsonResponse(response, safe=False,status=400)
        response['success'] = True
        return JsonResponse(response, safe=False,status=200)
    except (outlet_details.DoesNotExist,ProjectDetails.DoesNotExist,ProjectDetails.MultipleObjectsReturned,outlet_details.MultipleObjectsReturned) as e:
        if isinstance(e, outlet_details.DoesNotExist):
            return JsonResponse({'error': 'Invalid API Key outlet details not found'}, status=404)
        elif isinstance(e, outlet_details.MultipleObjectsReturned):
                return JsonResponse({'error': 'Multiple outlets found with the same API Key'}, status=400)
        elif isinstance(e, ProjectDetails.DoesNotExist):
            return JsonResponse({'error': 'Project details not found'}, status=404)
        elif isinstance(e, ProjectDetails.MultipleObjectsReturned):
                return JsonResponse({'error': 'Multiple projects found with the same API Key'}, status=400)
    except Exception as e:
        print(str(e))
        print("======================== ERROR ==============================")
        return JsonResponse({"error": "Something went wrong!"}, status=500)
    

# ### Subsection: BULK MESSAGE SENDING ###
@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def bulk_message(request):
    try:
        template_id = request.POST.get('template_id', 609)
        # print(template_id,"=======================template_id")
        template_instance   = TemplateDetails.objects.get(id = template_id)
        coupon_variables    = request.POST.get("coupon_variables",None)
        contact_ids = request.POST.get('contact_ids', '')
        contact_ids = [int(x) for x in contact_ids.split(',')] if contact_ids else []
        try:
            contact_group_list = [int(x) for x in request.POST.get('contact_group_list').split(',')]
        except:
            contact_group_list = [request.POST.get('contact_group_list')]
        customer_groups = ContactsGroup.objects.filter(id__in =contact_group_list)
        print(customer_groups)
        unique_contacts = set()
        for group in customer_groups:
            unique_contacts.update(group.contact.filter(is_active=True, is_opt_out=False))
        customer_list = list(unique_contacts)
        # Fetch individual contacts
        individual_contacts = Contacts.objects.filter(id__in=contact_ids)
        unique_contacts.update(individual_contacts)


        kwargs = {
            'project_id' :template_instance.project.id,
            'total_messages' : len(customer_list),
            'template_type' : template_instance.template_type
        }
        fun_response, message, total_cost, per_message_cost= check_wallet_balance(**kwargs)
        print(fun_response, message, total_cost,"==========")
        if fun_response:
            pass
        else:
            return JsonResponse(message, safe = False, status=400)
        
        try:
            button_variables = request.POST.get('button_variables',None)
            msg_send = MessageSender(
                button_variables=button_variables,
                template_instance=template_instance,
                campaign_id=None,
                trigger=True
            )

            message_thread = threading.Thread(target=msg_send.send_messages, args=(customer_list,))
            message_thread.start()
            return JsonResponse({'message':'success'}, safe = True, status=200)
        except Exception as e :
            message ={
                "message": f"{str(e)}",
                "success": False
            }
        
        return JsonResponse(message, safe = False, status=400)
    except (TemplateDetails.DoesNotExist,TemplateDetails.MultipleObjectsReturned) as e:
        if isinstance(e, TemplateDetails.DoesNotExist):
            return JsonResponse({'error': 'Template not found'}, status=404)
        elif isinstance(e, TemplateDetails.MultipleObjectsReturned):
            return JsonResponse({'error': 'Multiple Template found with the given template_id'}, status=400)
    except Exception as e:
        print(str(e))
        print("======================== ERROR ==============================")
        return JsonResponse({"error": "Something went wrong!"}, status=500)

# ### Subsection: ADD CONTACT AND MESSAGE SENDING ###
@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def contact_to_send_template(request):
    try:
        outlet_api_key          = request.META.get('HTTP_API_KEY')
        project_api_key         = request.META.get('HTTP_WHATSAPP_PROJECT_KEY')
        template_id             = request.POST.get('template')
        if outlet_api_key is None :
            return JsonResponse({'error': 'outlet_api_key is missing'}, status=404)
        elif project_api_key is None :
            return JsonResponse({'error': 'project_api_key is missing'}, status=404)
        elif template_id is None :
            return JsonResponse({'error': 'template id is missing'}, status=404)
        outlet_obj              = outlet_details.objects.get(api_key = outlet_api_key)
        project_obj             = ProjectDetails.objects.get(api_key = project_api_key)
        template_instance       = TemplateDetails.objects.get(id = template_id)

        phone_code          = request.POST.get('phone_code')
        contact             = request.POST.get('contact')

        customer_list = [{
            'contact' : contact,
            'phone_code': phone_code,
        }]
        response = {
            'message':'success'
        }
        if request.method == 'POST':
            try:
                contact_instance = Contacts.objects.filter(outlet=outlet_obj,contact=contact,phone_code=phone_code).last()
                contact_instance.is_active = True
                contact_instance.save()
            except:
                contact_instance = Contacts.objects.create(outlet=outlet_obj,contact=contact,phone_code=phone_code,is_active=True)
            msg_send = MessageSender(
                template_instance = template_instance,
                response = True
            )
            try:
                fun_repsone , response, context_payload = msg_send.send_messages(customer_list,)
            except Exception as e:
                # print(msg_sender.send_messages(customer_list,),'==================================aaaaa')
                print(str(e),"====error")
            print('error_data' in response,'==============================+++++++++')
            if 'error_data' in response:
                return JsonResponse(response, safe=False,status=400)
            response['success'] = True
        return JsonResponse(response , status=status.HTTP_200_OK) 
        
    except (outlet_details.DoesNotExist,ProjectDetails.DoesNotExist,ProjectDetails.MultipleObjectsReturned,outlet_details.MultipleObjectsReturned,TemplateDetails.DoesNotExist,TemplateDetails.MultipleObjectsReturned) as e:
        if isinstance(e, outlet_details.DoesNotExist):
            return JsonResponse({"error": "Invalid API Key outlet details not found"}, status=404)
        elif isinstance(e, outlet_details.MultipleObjectsReturned):
                return JsonResponse({"error": "Multiple outlets found with the same API Key"}, status=400)
        elif isinstance(e, ProjectDetails.DoesNotExist):
            return JsonResponse({"error": "Project details not found"}, status=404)
        elif isinstance(e, ProjectDetails.MultipleObjectsReturned):
                return JsonResponse({"error": "Multiple projects found with the same API Key"}, status=400)
        elif isinstance(e, TemplateDetails.MultipleObjectsReturned):
                return JsonResponse({"error": "Template details not found"}, status=400)
        elif isinstance(e, TemplateDetails.MultipleObjectsReturned):
                return JsonResponse({"error": "Multiple Template found with the given id"}, status=400)
    except Exception as e:
        print(str(e))
        print("======================== ERROR ==============================")
        return JsonResponse({"error": "Something went wrong!"}, status=500)
 
# ### Subsection: OLD TEMPLATE MESSAGE SEND FUNCTION ###
#to be decrpyted
def send_messages(button_variables, customer_list, template_instance, url, headers,business_instance,per_message_cost=0,coupon_variables=None,campaign_id=None):
    count = 0
    print( customer_list, template_instance, url, headers,business_instance,"===============================customer_list")
    for cust_instance in customer_list:
        count += 1
        try:
            data_dict = {
                'FirstName'  : cust_instance.first_name,
                'LastName'   :cust_instance.last_name,
                # 'order_id': cust_instance.order_id,
                'contact'    :cust_instance.contact,
                'phone_code' :cust_instance.phone_code,
                'phone_number': cust_instance.get('phone_number', None),
            }
        except:
            data_dict = {
                'FirstName'   : cust_instance.get('first_name', ''),  # Provide default empty string if key doesn't exist
                'LastName'    : cust_instance.get('last_name', ''),    # Provide default empty string if key doesn't exist
                'customerName': cust_instance.get('customer_name', ''),   
                'contact'     : cust_instance.get('email'),
                'contact'     : cust_instance.get('contact'),
                'phone_code'  : cust_instance.get('phone_code','91'),
                'phone_number': cust_instance.get('phone_number', None),
                'OrderID'     : str(cust_instance.get('order_id','')),
            }
        print(data_dict['contact'],"==============contact_send")
        print(count,"==================================count")
        try:
            body_variable_list          = eval(template_instance.body_variable_list)
            body_variable_example_list  = []
            for variable in body_variable_list:
                content = data_dict.get(variable["text"], "--") if len(data_dict.get(variable["text"], "--")) > 0 else "--"
                body_variable_example_list.append(content)
                variable["text"] = content
            body_variable_example_list = [body_variable_example_list]
            print(body_variable_list,'body_variable_list')
            print(body_variable_example_list,'body_variable_example_list')
        except Exception as e:
            print(str(e),"errror body_variable_list")
        try:
            header_variable_list          = eval(template_instance.header_variable_list)
            header_variable_example_list  = []
            for variable in header_variable_list:
                content = data_dict.get(variable["text"], "--") if len(data_dict.get(variable["text"], "--")) > 0 else "--"
                header_variable_example_list.append(content)
                variable["text"] = content
            header_variable_example_list = [header_variable_example_list]
            print(header_variable_list,'header_variable_list')
            print(header_variable_example_list,'header_variable_example_list')
        except Exception as e:
            print(str(e),"errror header_variable_list")
            
        """""
        try:
            button_variable_list = eval(button_variables)
            # for variable in button_variable_list:variable["text"] = data_dict[variable["text"]] if data_dict[variable["text"]] != None and variable["text"] in data_dict else "--"
        except Exception as e:
            pass
        """""
        component_list = []
        payload = {
            "to": data_dict['phone_number'] if data_dict['phone_number'] else data_dict['phone_code']+data_dict['contact'],
            "type": "template",
            "template": {
                "language": {
                    "policy": "deterministic",
                    "code": "en"
                },
                "name":template_instance.templateName,
                "components": []
            }
        }
        context_payload = json.loads(template_instance.payload)
        payload_order_index   = {ele["type"]:count for count, ele in enumerate(context_payload["components"])}
        print(payload_order_index,"========================payload_order")
        print(context_payload,'======context_payload')
        try:
            if template_instance.file_data:
                link = f"{XIRCLS_DOMAIN}/static/{template_instance.file_data}"
                component_list.append({
                    "type": "header",
                    "parameters": [{
                        "type": template_instance.file_type,
                        template_instance.file_type: {
                            "link": link ,
                        }
                    }]
                })
                if template_instance.file_type == 'document':
                    component_list[0]["parameters"][0]["document"]['filename'] = template_instance.filename
            elif header_variable_list:
                header_index = payload_order_index['HEADER']
                context_payload["components"][header_index]['example']['header_text']= header_variable_example_list
                component_list.append({
                    "type": "header",
                    "parameters": header_variable_list
                })
        except Exception as e:
            print(str(e),"errror header")
        try:
            if body_variable_list is not None:
                body_index = payload_order_index['BODY']
                # print(body_variable_example_list, "===========body_variable_example_list===========")
                context_payload["components"][body_index]['example']['body_text'] = body_variable_example_list
                component_list.append({
                    "type": "body",
                    "parameters": body_variable_list
                })
        except Exception as e:
            print(str(e),"errror body")
        # print(component_list,"===============================component_list-0")
        try:
            if button_variables is not None:
                button_variable_list = eval(button_variables)
                if button_variable_list is not None:
                    component_list.append({
                        "type": "button",
                        "sub_type": "url",
                        "index": "0",
                        "parameters": button_variable_list
                    })
            """""
            if coupon_variables is not None:
                print(coupon_variables)
                print("<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<coupon variable>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
                coupon_variables = json.loads(coupon_variables)
                print(coupon_variables)
                print("<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
                component_list.append({
                    "type": "button",
                    "sub_type": "copy_code",
                    "index": "0", 
                    "parameters": [{
                    "type": "coupon_code",
                    "coupon_code": coupon_variables
                }]
                })
            """""
            coupen_code = template_instance.default_coupen_code
            print(coupen_code)
            if coupen_code is not None:
                if coupon_variables is not None:
                    coupon_variable = json.loads(coupon_variables)
                else:
                    coupon_variable =   [{
                        "type": "coupon_code",
                        "coupon_code": f"{coupen_code}"
                    }]
                component_list.append({
                    "type": "button",
                    "sub_type": "copy_code",
                    "index": "0",
                    "parameters": coupon_variable
                })
            else:
                pass
        except Exception as e:
            print(str(e),"errror body")
        try:
            # print(str(context_payload['components'][1]),"inside eeeeeeeeeeeeeeeeeeeeeeee")
            if str(context_payload['components'][1]['type']) == 'CAROUSEL':
                # print('yeeeeeeeeeeeeeeeeeeeee')
                carsouel_list = []
                carsouel_payload = {
                    "type": "CAROUSEL",
                    "cards": []
                }
                carousel_instance = CarouselCard.objects.filter(template_details=template_instance).order_by('id')
                # print(carousel_instance,"============================carsiay")
                # print(component_list,"===============================component_list0")
                index = 0
                for obj in carousel_instance:
                
                    # print(carsouel_payload,"===========================carsouel_payload")
                    # print(obj,"===========================carsouel_payload")
                    
                    card_list = []
                    card_payload = {
                        "card_index": index,
                        "components": []
                    }
                    try:
                        carousel_body_variable_list          = eval(obj.body_variable_list)
                        # body_variable_example_list  = []
                        for variable in carousel_body_variable_list:
                            content = data_dict.get(variable["text"], "--") if len(data_dict.get(variable["text"], "--")) > 0 else "--"
                            # body_variable_example_list.append(content)
                            variable["text"] = content
                        # body_variable_example_list = [body_variable_example_list]
                        # print(body_variable_list,'body_variable_list')
                        # print(body_variable_example_list,'body_variable_example_list')
                    except Exception as e:
                        print(str(e),"errror body_variable_list")
                    try:
                        carousel_button_variable_list          = eval(obj.button_variable_list)
                        # body_variable_example_list  = []
                        # for variable in carousel_body_variable_list:
                            # content = data_dict.get(variable["text"], "--") if len(data_dict.get(variable["text"], "--")) > 0 else "--"
                            # body_variable_example_list.append(content)
                            # variable["text"] = content
                        # body_variable_example_list = [body_variable_example_list]
                        # print(body_variable_list,'body_variable_list')
                        # print(body_variable_example_list,'body_variable_example_list')
                    except Exception as e:
                        print(str(e),"errror body_variable_list")
                    
                    try:
                        print(obj.file_type,"headerrrrrrrrrrrrrrrrrrrrrrrrrrrrrr")
                        if obj.file_data:
                            link = f"{XIRCLS_DOMAIN}/static/{obj.file_data}"
                            card_list.append({
                                "type": "header",
                                "parameters": [{
                                    "type": obj.file_type,
                                    obj.file_type: {
                                        "link": link ,
                                    }
                                }]
                            })
                            if obj.file_type == 'document':
                                card_list[0]["parameters"][0]["document"]['filename'] = obj.filename
                        print(card_list,"=====================card_list")
                    except Exception as e:
                        print(str(e),"errror header")
                    try:
                        if carousel_body_variable_list is not None:
                            # print(carousel_body_variable_example_list, "===========body_variable_example_list===========")
                            # context_payload["components"][1]['example']['body_text'] = body_variable_example_list
                            card_list.append({
                                "type": "body",
                                "parameters": carousel_body_variable_list
                            })
                    except Exception as e:
                        print(str(e),"errror body")
                    # try:
                    #     if carousel_button_variables is not None:
                    #         carousel_button_variable_list = eval(carousel_button_variables)
                    #         if carousel_button_variable_list is not None:
                    #             card_list.append({
                    #                 "type": "button",
                    #                 "sub_type": "url",
                    #                 "index": "0",
                    #                 "parameters": carousel_button_variable_list
                    #             })
                    #     else:
                    #         pass
                    # except Exception as e:
                    #     print(str(e),"errror body")
                    card_payload['components'] = card_list
                    
                    carsouel_list.append(card_payload)
                    index += 1
                    # print(card_payload,"===============================card_payload")
                    # print(carsouel_list,"===============================carsouel_list")
                carsouel_payload['cards']= carsouel_list
                component_list.append(carsouel_payload)
                # print(component_list,"===============================component_list")
        except Exception as e:
            # print(str(e),"=================carousel eroro")
            pass
        payload['template']['components'] = component_list
        # print(payload,"===========================payload_send_messages")
        response = requests.post(url, headers=headers, data=json.dumps(payload, indent=4)).json()
        print(response,"======================respos")
        
        try:
            if 'code' in response:
                data = {
                    'templateId': template_instance.templateId,
                    'message_id': response["code"],
                    'reciever': data_dict['phone_code']+data_dict['contact'],
                    'sender': business_instance.phone_code + business_instance.contact, 
                    'remark': response['message'],
                    'campaign_id': campaign_id
                }
            else:
                template_inst =  json.loads(template_instance.payload)
                template_type   = template_inst['category']
                data = {
                    'templateId': template_instance.templateId,
                    'message_id': str(response['messages'][0]["id"]),
                    'reciever': response['contacts'][0]["wa_id"], 
                    'sender': business_instance.phone_code + business_instance.contact, 
                    'context':context_payload,
                    'remark': None,
                    'template_type': template_type,
                    'campaign_id': campaign_id,
                    'per_message_cost': per_message_cost,
                    'outlet' : business_instance.outlet
                }
                #wallet_obj.balance -= per_message_cost
                #wallet_obj.is_block += per_message_cost
                #WhatsappWallet.objects.filter(outlet=business_instance.outlet).update(balance=F('balance') - per_message_cost, is_block=F('is_block') + per_message_cost)
                #wallet_obj.save()
            sending_log(data)
        except:
            pass
        print(count,"=======================count_send_message")

# ### Subsection: MESSAGE LOG CREATION ###
def sending_log(data):
    try:
        # print(data,"===================sending_log")
        template_id       = data.get('templateId')
        try:
            print(data.get('campaign_id',None),"===============================================campaign_id")
            campaign_obj = WhatsappCampaign.objects.get(id=data.get('campaign_id',None))
            print(data.get('trigger', False), campaign_obj.campaign_type, campaign_obj.campaign_type,"========================================4298")
            print((data.get('trigger', False) and campaign_obj.campaign_type in ['broadcast-flow']),'=====================')
            if (data.get('trigger', False) and campaign_obj.campaign_type in ['broadcast-flow']):
                
                flowcheck = Flowcheck(
                    outlet_instance = campaign_obj.outlet, 
                    phone         = data.get('reciever'),
                    customer_data = data.get('customer_data'),
                    brodcast_flow = True
                )
                campaign_obj_list = [campaign_obj]
                print(flowcheck,"========================================flowcheck")
                kwargs = {'create': True,'phone':data.get('reciever'),'campaign_instances':campaign_obj_list}
                try:
                    flowcheck.check_customer_flow_log(**kwargs)
                except Exception as e:
                    print(str(e),"=============================floqqqq1")
        except:
            campaign_obj = None
        #template_instance = TemplateDetails.objects.get(templateId=template_id)
        try:
            if not data.get('message_id').startswith("wamid."):
                TemplateDetails.objects.filter(templateId=template_id).update(template_failed = F('template_failed')+1)
                #template_instance.template_failed += 1
        except:
            pass
        TemplateDetails.objects.filter(templateId=template_id).update(template_total_sent = F('template_total_sent')+1)
        #template_instance.template_total_sent += 1
        #template_instance.save()
        template_instance = TemplateDetails.objects.get(templateId=template_id)
        print(data.get('template_type',None),"====================template_type")
        try:
            try:
                message_log_instance = MessageLog.objects.get(id=data.get('message_log_id'),project=template_instance.project)
                message_log_instance.outlet=template_instance.outlet
                message_log_instance.business=template_instance.business
                message_log_instance.message_type=data.get('template_type',None)
                message_log_instance.template=template_instance
                message_log_instance.templateId=template_id
                message_log_instance.sender=data.get('sender')
                message_log_instance.reciever=data.get('reciever')
                message_log_instance.message_id=data.get('message_id')
                message_log_instance.campaign=campaign_obj
                message_log_instance.wallet_trans = data.get('wallet_transaction')
                message_log_instance.save()
            except:
                message_log_instance = MessageLog.objects.create(project=template_instance.project,outlet=template_instance.outlet,business=template_instance.business,message_type=data.get('template_type',None),template=template_instance, templateId=template_id, sender=data.get('sender'),reciever=data.get('reciever'), message_id=data.get('message_id'), campaign=campaign_obj,wallet_trans = data.get('wallet_transaction'))
            
            if not data.get('message_id').startswith("wamid."):
                message_log_instance.timestamp_failed = timezone.now()
                message_log_instance.save()
            context = data.get('context',None)
            if context:
                context = json.dumps(data.get('context'))
            project_instance = ProjectDetails.objects.annotate(
                phone_number=Concat(F('phone_code'), F('phone_no'))
            ).get(
                Q(phone_number=data.get('sender'))
            )
            # business_details = BusinessDetails.objects.get(contact=data.get('sender'))
            outlet_details   = project_instance.outlet
            contact_info = Contacts.objects.annotate(
                phone_number=Concat(F('phone_code'), F('contact'))
            ).filter(phone_number=data.get('reciever'), outlet=outlet_details, is_active=True).last()
            # print(contact_info,"==================================contact_info")
            if contact_info is None:
                print("whyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyy")
                country_code , contact_no = get_phone_code(data.get('reciever'))
                contact_info = Contacts.objects.create(
                    first_name = data.get('customer_data')[0].get('first_name',None),
                    last_name = data.get('customer_data')[0].get('last_name',None),
                    phone_code=country_code,
                    contact=contact_no,
                    outlet=outlet_details,
                    is_active=True
                )
            if data.get('entry_point', None) is not None and 'abandoned':
                try:
                    tags_instance = Tags.objects.get(id=10)
                    # print(tags_instance,"========================================tags_instance")
                    try:
                        customer_tags = CustomerTagsNotes.objects.get(contact=contact_info)
                    except:
                        customer_tags = CustomerTagsNotes.objects.create(contact=contact_info)
                    customer_tags.tags.add(tags_instance)
                    customer_tags.save()
                except:
                    pass
            try:
                message_relation = MessageRelation.objects.get(sender=data.get('sender'),receiver=data.get('reciever'))
                message_relation.receiver_info = contact_info
                message_relation.save()
            except:
                message_relation = MessageRelation.objects.create(sender=data.get('sender'),receiver=data.get('reciever'),receiver_info=contact_info)
            # message_relation.last_message_type = data.get('template_type','SERVICING')
            message_relation.save()
            # print(message_relation,"=======================messsage_relation")
            # if isinstance(context,str) and context!="":
            #     dumped_context=json.loads(context)
            #     components=dumped_context.get('components')
            #     body_text=components[0]['text'] if components[0]['type']=="BODY" else components[1]['text']
            #     print("BODYTEXT=============",body_text)
            #     MessageContext.objects.create(message_log=message_log_instance,context=context,context_text = body_text,reply_context=None,contact_relation=message_relation)
            # else:
            MessageContext.objects.create(message_log=message_log_instance,context=context,reply_context=None,contact_relation=message_relation)
        except Exception as e:
            print(str(e),"===========================")
        print(message_log_instance.id)
        return True
    except Exception as e:
        print(str(e),"===========================error")
        return True
   
# ##############################################################################################################################################
# Section: LIVE CHAT
# ##############################################################################################################################################     

# ### Subsection: SEND LIVE MESSAGES/ SERVICE MESSAGE API/ LIVE CHAT SENDING MESSAGE ###
@csrf_exempt
@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def send_live_message(request):
    try:
        outlet_api_key          = request.META.get('HTTP_API_KEY')
        project_api_key         = request.META.get('HTTP_WHATSAPP_PROJECT_KEY')
        if outlet_api_key is None :
            return JsonResponse({'error': 'outlet_api_key is missing'}, status=404)
        if project_api_key is None :
            return JsonResponse({'error': 'project_api_key is missing'}, status=404)
        
        outlet_obj       = outlet_details.objects.get(api_key = outlet_api_key)
        project_obj      = ProjectDetails.objects.get(api_key = project_api_key)
        wallet_obj       = WhatsappWallet.objects.get(outlet = outlet_obj,project = project_obj)
        if wallet_obj.subscription is None:
            return JsonResponse({"message": "Purchase Subscription","success":False}, status=status.HTTP_200_OK)
        if wallet_obj.subscription.end_date < timezone.now():
            return JsonResponse({"message": "Subscription is Expired","success":False}, status=status.HTTP_200_OK)
        else:
            pass
        if Decimal(wallet_obj.deduction_plan.get("SERVICING")) > Decimal(wallet_obj.balance):
            return JsonResponse({'message':'insufficent fund in wallet','sucess':False}, status=200)
        else:
            pass
        kwargs = {
            'message_body': request.POST.get('message_body'),
            'caption': request.POST.get('caption'),
            'filename': request.POST.get('filename'),
            'type': request.POST.get('type'),
            'file': request.FILES.get('file'),
            'per_message_cost': wallet_obj.deduction_plan.get("SERVICING"),
            'project_id' : project_obj.id
        }
    
        outlet_id = outlet_obj.id
        print(request.POST.get('receiver'),"===================re")
        result, response , message_id = send_service_message(outlet_id=outlet_id,reciever=request.POST.get('receiver'), **kwargs)
        print(result, response ,"===================response")
        message = {
            "message": response if 'message' not in response else "Something went wrong!",
            "success": 'message' not in response
        }
        return JsonResponse(message, status=200, safe=False)
    except (outlet_details.DoesNotExist,ProjectDetails.DoesNotExist,ProjectDetails.MultipleObjectsReturned,outlet_details.MultipleObjectsReturned) as e:
        if isinstance(e, outlet_details.DoesNotExist):
            return JsonResponse({"error": "Invalid API Key outlet details not found"}, status=404)
        elif isinstance(e, outlet_details.MultipleObjectsReturned):
                return JsonResponse({"error": "Multiple outlets found with the same API Key"}, status=400)
        elif isinstance(e, ProjectDetails.DoesNotExist):
            return JsonResponse({"error": "Project details not found"}, status=404)
        elif isinstance(e, ProjectDetails.MultipleObjectsReturned):
                return JsonResponse({"error": "Multiple projects found with the same API Key"}, status=400)
    except Exception as e:
        print(str(e))
        print("======================== ERROR ==============================")
        return JsonResponse({"error": "Something went wrong!"}, status=500)

# @csrf_exempt
# @api_view(['POST'])
# @authentication_classes([JWTAuthentication])
# @permission_classes([IsAuthenticated])
# def react_to_message(request):
#     try:
#         outlet_api_key          = request.META.get('HTTP_API_KEY')
#         project_api_key         = request.META.get('HTTP_WHATSAPP_PROJECT_KEY')
#         message_id              = request.POST.get('message_id')
#         emoji                   = request.POST.get('emoji')
#         if outlet_api_key is None :
#             return JsonResponse({'error': 'outlet_api_key is missing'}, status=404)
#         if project_api_key is None :
#             return JsonResponse({'error': 'project_api_key is missing'}, status=404)
        
#         outlet_obj       = outlet_details.objects.get(api_key = outlet_api_key)
#         project_obj      = ProjectDetails.objects.get(api_key = project_api_key)
#         wallet_obj       = WhatsappWallet.objects.get(outlet = outlet_obj,project = project_obj)
#         if wallet_obj.subscription is None:
#             return JsonResponse({"message": "Purchase Subscription","success":False}, status=status.HTTP_200_OK)
#         if wallet_obj.subscription.end_date < timezone.now():
#             return JsonResponse({"message": "Subscription is Expired","success":False}, status=status.HTTP_200_OK)
#         else:
#             pass
#         if Decimal(wallet_obj.deduction_plan.get("SERVICING")) > Decimal(wallet_obj.balance):
#             return JsonResponse({'message':'insufficent fund in wallet','sucess':False}, status=200)
        
#         headers = {
#             'Accept': 'application/json',
#             'Content-Type': 'application/json',
#             'Authorization': f'Bearer {project_obj.token}' 
#         }
#         url = "https://backend.aisensy.com/direct-apis/t1/messages"
#         payload = {
#             "messaging_product": "whatsapp",
#             "recipient_type": "individual",
#             "to": "+918928684454",
#             "type": "reaction",
#             "reaction": {
#                 "message_id": message_id,
#                 "emoji": emoji
#             }
#         }
#         print(emoji)
#         print(headers)
#         print(payload)
#         json_payload = json.dumps(payload, ensure_ascii=False)
#         print("JSON Payload:", json_payload)
#         response = requests.post(url, json = json_payload, headers = headers)
#         response = requests.post(url, json=payload, headers=headers)
#         print(response.json() ,"===================response")
#         if 'message' not in response:
#             MessageContext.objects.filter(message_log__project = project_obj,message_log__outlet = outlet_obj,message_log__message_id = message_id).update(reaction_merchant = emoji)
#             message = {
#                 "message": response if 'message' not in response else "Something went wrong!",
#                 "success": 'message' not in response
#             }
#             return JsonResponse(message, status=200, safe=False)
#         else:
#             message = {
#                 "message": response if 'message' not in response else "Something went wrong!",
#                 "success": 'message' not in response
#             }
#             return JsonResponse(message, status=404, safe=False)
#     except (outlet_details.DoesNotExist,ProjectDetails.DoesNotExist,ProjectDetails.MultipleObjectsReturned,outlet_details.MultipleObjectsReturned) as e:
#         if isinstance(e, outlet_details.DoesNotExist):
#             return JsonResponse({"error": "Invalid API Key outlet details not found"}, status=404)
#         elif isinstance(e, outlet_details.MultipleObjectsReturned):
#                 return JsonResponse({"error": "Multiple outlets found with the same API Key"}, status=400)
#         elif isinstance(e, ProjectDetails.DoesNotExist):
#             return JsonResponse({"error": "Project details not found"}, status=404)
#         elif isinstance(e, ProjectDetails.MultipleObjectsReturned):
#                 return JsonResponse({"error": "Multiple projects found with the same API Key"}, status=400)
#     except Exception as e:
#         print(str(e))
#         print("======================== ERROR ==============================")
#         return JsonResponse({"error": "Something went wrong!"}, status=500)

# @csrf_exempt
# @api_view(['POST'])
# @authentication_classes([JWTAuthentication])
# @permission_classes([IsAuthenticated])
# def react_to_message(request):
#     try:
#         outlet_api_key = request.META.get('HTTP_API_KEY')
#         project_api_key = request.META.get('HTTP_WHATSAPP_PROJECT_KEY')
#         message_id = request.POST.get('message_id')
#         emoji = request.POST.get('emoji')
#         print(emoji)
#         print(json.dumps(emoji))
#         print(emoji.encode('utf-8'))

#         if not outlet_api_key:
#             return JsonResponse({'error': 'outlet_api_key is missing'}, status=404)
#         if not project_api_key:
#             return JsonResponse({'error': 'project_api_key is missing'}, status=404)
        
#         outlet_obj = outlet_details.objects.get(api_key=outlet_api_key)
#         project_obj = ProjectDetails.objects.get(api_key=project_api_key)
#         wallet_obj = WhatsappWallet.objects.get(outlet=outlet_obj, project=project_obj)

#         if wallet_obj.subscription is None:
#             return JsonResponse({"message": "Purchase Subscription", "success": False}, status=status.HTTP_200_OK)
#         if wallet_obj.subscription.end_date < timezone.now():
#             return JsonResponse({"message": "Subscription is Expired", "success": False}, status=status.HTTP_200_OK)
#         if Decimal(wallet_obj.deduction_plan.get("SERVICING")) > Decimal(wallet_obj.balance):
#             return JsonResponse({'message': 'insufficient fund in wallet', 'success': False}, status=200)
        
#         headers = {
#             'Accept': 'application/json',
#             'Content-Type': 'application/json',
#             'Authorization': f'Bearer {project_obj.token}'
#         }
#         url = "https://backend.aisensy.com/direct-apis/t1/messages"
        
#         # Decode the emoji if it's double-escaped
#         if emoji.startswith('\\u'):
#             #emoji = emoji.encode('utf-8').decode('unicode_escape')
#             try:
#                 emoji_encoded = emoji.encode('utf-8').decode('unicode_escape')
#             except UnicodeDecodeError:
#                 return JsonResponse({'error': 'Invalid emoji encoding'}, status=400)
        
#         payload = {
#             "messaging_product": "whatsapp",
#             "recipient_type": "individual",
#             "to": "+918928684454",
#             "type": "reaction",
#             "reaction": {
#                 "message_id": message_id,
#                 "emoji": emoji_encoded
#             }
#         }

#         # Make the POST request with the payload directly
#         print(payload)
#         response = requests.post(url, json=payload, headers=headers)
        
#         # Handle the response
#         response_data = response.json()
#         print("Response Data:", response_data)
#         utfemoji = emoji.encode('utf-8')

#         if 'messages' in response_data:
#             MessageContext.objects.filter(
#                 message_log__project=project_obj,
#                 message_log__outlet=outlet_obj,
#                 message_log__message_id=message_id
#             ).update(reaction_merchant = emoji)
#             message = {
#                 "message": response_data.get('messages', "Something went wrong!"),
#                 "success": True
#             }
#             return JsonResponse(message, status=200, safe=False)
#         else:
#             message = {
#                 "message": "Something went wrong!",
#                 "success": False
#             }
#             return JsonResponse(message, status=404, safe=False)

#     except (outlet_details.DoesNotExist, ProjectDetails.DoesNotExist, ProjectDetails.MultipleObjectsReturned, outlet_details.MultipleObjectsReturned) as e:
#         if isinstance(e, outlet_details.DoesNotExist):
#             return JsonResponse({"error": "Invalid API Key outlet details not found"}, status=404)
#         elif isinstance(e, outlet_details.MultipleObjectsReturned):
#             return JsonResponse({"error": "Multiple outlets found with the same API Key"}, status=400)
#         elif isinstance(e, ProjectDetails.DoesNotExist):
#             return JsonResponse({"error": "Project details not found"}, status=404)
#         elif isinstance(e, ProjectDetails.MultipleObjectsReturned):
#             return JsonResponse({"error": "Multiple projects found with the same API Key"}, status=400)
#     except Exception as e:
#         print(str(e))
#         print("======================== ERROR ==============================")
#         return JsonResponse({"error": "Something went wrong!"}, status=500)


# @csrf_exempt
# @api_view(['POST'])
# @authentication_classes([JWTAuthentication])
# @permission_classes([IsAuthenticated])
# def react_to_message(request):
#     try:
#         outlet_api_key  = request.META.get('HTTP_API_KEY')
#         project_api_key = request.META.get('HTTP_WHATSAPP_PROJECT_KEY')
#         message_id      = request.POST.get('message_id')
#         emoji           = request.POST.get('emoji')
#         phone_no        = request.POST.get('phone_no')
#         emoji           = emoji.encode().decode('unicode_escape').encode("latin1").decode("utf-8")
#         if not outlet_api_key:
#             return JsonResponse({'error': 'outlet_api_key is missing'}, status=404)
#         if not project_api_key:
#             return JsonResponse({'error': 'project_api_key is missing'}, status=404)
#         outlet_obj  = outlet_details.objects.get(api_key=outlet_api_key)
#         project_obj = ProjectDetails.objects.get(api_key=project_api_key)
#         wallet_obj  = WhatsappWallet.objects.get(outlet=outlet_obj, project=project_obj)
#         if wallet_obj.subscription is None:
#             return JsonResponse({"message": "Purchase Subscription", "success": False}, status=status.HTTP_200_OK)
#         if wallet_obj.subscription.end_date < timezone.now():
#             return JsonResponse({"message": "Subscription is Expired", "success": False}, status=status.HTTP_200_OK)
#         if Decimal(wallet_obj.deduction_plan.get("SERVICING")) > Decimal(wallet_obj.balance):
#             return JsonResponse({'message': 'insufficient fund in wallet', 'success': False}, status=200)
#         headers = {
#             'Accept': 'application/json',
#             'Content-Type': 'application/json',
#             'Authorization': f'Bearer {project_obj.token}'
#         }
#         url = "https://backend.aisensy.com/direct-apis/t1/messages"
#         payload = {
#             "messaging_product": "whatsapp",
#             "recipient_type": "individual",
#             "to": phone_no,
#             "type": "reaction",
#             "reaction": {
#                 "message_id": message_id,
#                 "emoji": emoji
#             }
#         }
#         response = requests.post(url, json=payload, headers=headers)
#         response_data = response.json()
#         print("Response Data:", response_data)
#         if 'messages' in response_data:
#             MessageContext.objects.filter(message_log__project = project_obj,message_log__outlet = outlet_obj,message_log__message_id = message_id).update(reaction_merchant = emoji)
#             message = {
#                 "message": response_data.get('messages', "Something went wrong!"),
#                 "success": True
#             }
#             return JsonResponse(message, status=200, safe=False)
#         else:
#             message = {
#                 "message": "Something went wrong!"
#             }
#             return JsonResponse(message, status=404, safe=False)

#     except (outlet_details.DoesNotExist, ProjectDetails.DoesNotExist, ProjectDetails.MultipleObjectsReturned, outlet_details.MultipleObjectsReturned) as e:
#         if isinstance(e, outlet_details.DoesNotExist):
#             return JsonResponse({"error": "Invalid API Key outlet details not found"}, status=404)
#         elif isinstance(e, outlet_details.MultipleObjectsReturned):
#             return JsonResponse({"error": "Multiple outlets found with the same API Key"}, status=400)
#         elif isinstance(e, ProjectDetails.DoesNotExist):
#             return JsonResponse({"error": "Project details not found"}, status=404)
#         elif isinstance(e, ProjectDetails.MultipleObjectsReturned):
#             return JsonResponse({"error": "Multiple projects found with the same API Key"}, status=400)
#     except Exception as e:
#         print(str(e))
#         print("======================== ERROR ==============================")
#         return JsonResponse({"error": "Something went wrong!"}, status=500)


@csrf_exempt
@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def react_to_message(request):
    try:
        outlet_api_key  = request.META.get('HTTP_API_KEY')
        project_api_key = request.META.get('HTTP_WHATSAPP_PROJECT_KEY')
        message_id      = request.POST.get('message_id')
        emoji           = request.POST.get('emoji')
        phone_no        = request.POST.get('phone_no')
        code_point      = int(emoji, 16)
        character       = chr(code_point)
        utf16_bytes     = character.encode('utf-16be')
        #utf16_surrogate_pairs = ''.join(f'\\u{utf16_bytes[i]:02X}{utf16_bytes[i + 1]:02X}' for i in range(0, len(utf16_bytes), 2))
        utf8_bytes      = character.encode('utf-8')
        utf8_hex        = ''.join(f'\\x{b:02X}' for b in utf8_bytes)
        if not outlet_api_key:
            return JsonResponse({'error': 'outlet_api_key is missing'}, status=404)
        if not project_api_key:
            return JsonResponse({'error': 'project_api_key is missing'}, status=404)
        outlet_obj  = outlet_details.objects.get(api_key=outlet_api_key)
        project_obj = ProjectDetails.objects.get(api_key=project_api_key)
        wallet_obj  = WhatsappWallet.objects.get(outlet=outlet_obj, project=project_obj)
        if wallet_obj.subscription is None:
            return JsonResponse({"message": "Purchase Subscription", "success": False}, status=status.HTTP_200_OK)
        if wallet_obj.subscription.end_date < timezone.now():
            return JsonResponse({"message": "Subscription is Expired", "success": False}, status=status.HTTP_200_OK)
        if Decimal(wallet_obj.deduction_plan.get("SERVICING")) > Decimal(wallet_obj.balance):
            return JsonResponse({'message': 'insufficient fund in wallet', 'success': False}, status=200)
        headers = {
            'Accept'       : 'application/json',
            'Content-Type' : 'application/json',
            'Authorization': f'Bearer {project_obj.token}'
        }
        url = "https://backend.aisensy.com/direct-apis/t1/messages"
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type"   : "individual",
            "to"               : phone_no,
            "type"             : "reaction",
            "reaction"         : {
                "message_id": message_id,
                "emoji"     : utf8_bytes
            }
        }
        response      = requests.post(url, json=payload, headers=headers)
        response_data = response.json()
        print("Response Data:", response_data)
        if 'messages' in response_data:
            MessageContext.objects.filter(message_log__project = project_obj,message_log__outlet = outlet_obj,message_log__message_id = message_id).update(reaction_merchant = utf8_hex.encode().decode('unicode_escape').encode("latin1").decode("utf-8"))
            message = {
                "message": response_data.get('messages', "Something went wrong!"),
                "success": True
            }
            return JsonResponse(message, status=200, safe=False)
        else:
            message = {
                "message": "Something went wrong!"
            }
            return JsonResponse(message, status=404, safe=False)

    except (outlet_details.DoesNotExist, ProjectDetails.DoesNotExist, ProjectDetails.MultipleObjectsReturned, outlet_details.MultipleObjectsReturned) as e:
        if isinstance(e, outlet_details.DoesNotExist):
            return JsonResponse({"error": "Invalid API Key outlet details not found"}, status=404)
        elif isinstance(e, outlet_details.MultipleObjectsReturned):
            return JsonResponse({"error": "Multiple outlets found with the same API Key"}, status=400)
        elif isinstance(e, ProjectDetails.DoesNotExist):
            return JsonResponse({"error": "Project details not found"}, status=404)
        elif isinstance(e, ProjectDetails.MultipleObjectsReturned):
            return JsonResponse({"error": "Multiple projects found with the same API Key"}, status=400)
    except Exception as e:
        print(str(e))
        print("======================== ERROR ==============================")
        return JsonResponse({"error": "Something went wrong!"}, status=500)
# ### Subsection: GET PREVIOUS CHAT ###
# @api_view(['POST'])
# @authentication_classes([])
# @permission_classes([AllowAny])
# @csrf_exempt
# def get_all_message(request):
#     try: 
#         outlet_obj = outlet_details.objects.get(api_key=request.META.get('HTTP_API_KEY'))
#         # business_details = BusinessDetails.objects.get(outlet=outlet_obj)
#         project_instance = ProjectDetails.objects.get(api_key=request.META.get('HTTP_WHATSAPP_PROJECT_KEY'))
        
#         datatables = request.POST
#         print(datatables)
#         start = int(datatables.get('page'))
#         length = int(datatables.get('size'))
#         over_all_search = datatables.get('searchValue')
#         field_mapping = {
#             0: "created_at__icontains",
#         }
       
#         advance_filter = Q()
#         if over_all_search:
#             overall_search_filter = Q()
#             for field in field_mapping.values():
#                 overall_search_filter |= Q(**{field: over_all_search})
#             advance_filter |= overall_search_filter
#         project_no  = project_instance.phone_code + project_instance.phone_no
#         # print(project_no)
#         selected_no = request.POST.get('selected_no')#919511671955
#         # print(selected_no,'=====================')
#         print(Q(message_log__sender=project_no) & Q(message_log__reciever=selected_no)) 
#         messages_instance       = MessageContext.objects.filter((Q(message_log__sender__icontains=project_no) & Q(message_log__reciever__icontains=selected_no)) | (Q(message_log__sender__icontains=selected_no) & Q(message_log__reciever__icontains=project_no)))
        
#         messages = messages_instance.filter(advance_filter).order_by('-message_log__created_at').values(
#             messages_sender                 = F('message_log__sender'),
#             messages_reciever               = F('message_log__reciever'),
#             messages_context                = F('context'),
#             messages_reply_context          = F('reply_context__context'),
#             messages_message_id             = F('message_log__message_id'),
#             messages_timestamp_sent         = F('message_log__timestamp_sent'),
#             messages_timestamp_delivered    = F('message_log__timestamp_delivered'),
#             messages_timestamp_read         = F('message_log__timestamp_read'),
#             messages_timestamp_failed       = F('message_log__timestamp_failed'),
#             messages_failed_remark          = F('message_log__remark'),
#         ).order_by('-message_log__created_at')
#         message_thread = threading.Thread(target=mark_message_read_fun, args=(selected_no,project_no))
#         message_thread.start()
#         contact_obj_count = messages.count()
#         paginator = Paginator(messages, length)
#         try:
#             object_list = paginator.page(start).object_list
#         except (PageNotAnInteger, EmptyPage):
#             object_list = paginator.page(1).object_list
#         # serialized_messages = json.loads(serialize('json', object_list))
#         response = {
#             'messages_count': contact_obj_count,
#             "messages": list(object_list)
#         }
#         return JsonResponse(response,status=status.HTTP_200_OK)
#     except Exception as e:
#         return JsonResponse({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
@api_view(['POST'])
@authentication_classes([])
@permission_classes([AllowAny])
@csrf_exempt
def get_all_message(request):
    try: 
        outlet_api_key          = request.META.get('HTTP_API_KEY')
        project_api_key         = request.META.get('HTTP_WHATSAPP_PROJECT_KEY')
        if outlet_api_key is None :
            return JsonResponse({'error': 'outlet_api_key is missing'}, status=404)
        if project_api_key is None :
            return JsonResponse({'error': 'project_api_key is missing'}, status=404)
        outlet_obj       = outlet_details.objects.get(api_key = outlet_api_key)
        project_instance = ProjectDetails.objects.get(api_key = project_api_key)
        
        datatables      = request.POST
        print(datatables)
        start           = int(datatables.get('page'))
        length          = int(datatables.get('size'))
        over_all_search = datatables.get('searchValue')
        field_mapping   = {
            0: "created_at__icontains",
        }
       
        advance_filter = Q()
        if over_all_search:
            overall_search_filter = Q()
            for field in field_mapping.values():
                overall_search_filter |= Q(**{field: over_all_search})
            advance_filter |= overall_search_filter
        project_no  = project_instance.phone_code + project_instance.phone_no
        print(project_no)
        selected_no = request.POST.get('selected_no')#919511671955
        print(selected_no,'=====================')

        # message_filter = (
        #     (Q(message_log__sender__icontains=project_no) & Q(message_log__reciever__icontains=selected_no)) |
        #     (Q(message_log__sender__icontains=selected_no) & Q(message_log__reciever__icontains=project_no))
        # )
        
        
        # Fetch and filter messages
        # messages_instance = MessageContext.objects.select_related('message_log').filter(message_filter).order_by('-message_log__created_at')
        
        # Select specific fields from the filtered messages
        # messages = messages_instance.values(
        #     messages_sender=F('message_log__sender'),
        #     messages_reciever=F('message_log__reciever'),
        #     messages_context=F('context'),
        #     messages_reply_context=F('reply_context__context'),
        #     messages_message_id=F('message_log__message_id'),
        #     messages_timestamp_sent=F('message_log__timestamp_sent'),
        #     messages_timestamp_delivered=F('message_log__timestamp_delivered'),
        #     messages_timestamp_read=F('message_log__timestamp_read'),
        #     messages_timestamp_failed=F('message_log__timestamp_failed'),
        #     messages_failed_remark=F('message_log__remark')
        # )
        message_filter = (
            (Q(sender__icontains=project_no) & Q(reciever__icontains=selected_no)) |
            (Q(sender__icontains=selected_no) & Q(reciever__icontains=project_no))
        )
        start_index = 0 if start == 1 else (start - 1) * length
        end_index = start_index + length
        messages_log_instance = MessageLog.objects.filter(message_filter).order_by('-id').values_list('id', flat=True)
        print(messages_log_instance,"==================================message_lg")
        message_log_ids = list(messages_log_instance[start_index:end_index])
        print(message_log_ids,"==================================message_lg")
        print(message_log_ids,"==================================message_lg")

        # Use the filtered IDs to query the MessageContext and join with MessageLog
        messages_instance = MessageContext.objects.select_related('message_log').filter(message_log__id__in=message_log_ids).order_by('-message_log__created_at')

        # Select specific fields from the filtered messages
        messages = messages_instance.values(
            messages_sender              = F('message_log__sender'),
            messages_reciever            = F('message_log__reciever'),
            messages_context             = F('context'),
            messages_reply_context       = F('reply_context__context'),
            messages_message_id          = F('message_log__message_id'),
            messages_timestamp_sent      = F('message_log__timestamp_sent'),
            messages_timestamp_delivered = F('message_log__timestamp_delivered'),
            messages_timestamp_read      = F('message_log__timestamp_read'),
            messages_timestamp_failed    = F('message_log__timestamp_failed'),
            messages_failed_remark       = F('message_log__remark'),
            messages_reaction_reciver    = F('reaction_reciver'),
            messages_reaction_merchant   = F('reaction_merchant')
        )
        message_thread = threading.Thread(target=mark_message_read_fun, args=(selected_no,project_no))
        message_thread.start()
        contact_obj_count = messages_log_instance.count()
        paginator         = Paginator(messages, length)
        try:
            object_list = paginator.page(start).object_list
        except (PageNotAnInteger, EmptyPage):
            object_list = paginator.page(1).object_list
        # serialized_messages = json.loads(serialize('json', object_list))
        response = {
            'messages_count': contact_obj_count,
            "messages": list(object_list)
        }
        return JsonResponse(response,status=status.HTTP_200_OK)
    except (outlet_details.DoesNotExist,ProjectDetails.DoesNotExist,ProjectDetails.MultipleObjectsReturned,outlet_details.MultipleObjectsReturned) as e:
        if isinstance(e, outlet_details.DoesNotExist):
            return JsonResponse({"error": "Invalid API Key outlet details not found"}, status=404)
        elif isinstance(e, outlet_details.MultipleObjectsReturned):
            return JsonResponse({"error": "Multiple outlets found with the same API Key"}, status=400)
        elif isinstance(e, ProjectDetails.DoesNotExist):
            return JsonResponse({"error": "Project details not found"}, status=404)
        elif isinstance(e, ProjectDetails.MultipleObjectsReturned):
            return JsonResponse({"error": "Multiple projects found with the same API Key"}, status=400)
    except Exception as e:
        print(str(e))
        print("======================== ERROR ==============================")
        return JsonResponse({"error": "Something went wrong!"}, status=500)

# ### Subsection: GET CONTACT ###
@api_view(['POST'])
@authentication_classes([])
@permission_classes([AllowAny])
@csrf_exempt
def contact_relation(request):
    try: 
        outlet_api_key          = request.META.get('HTTP_API_KEY')
        project_api_key         = request.META.get('HTTP_WHATSAPP_PROJECT_KEY')
        if outlet_api_key is None :
            return JsonResponse({'error': 'outlet_api_key is missing'}, status=404)
        if project_api_key is None :
            return JsonResponse({'error': 'project_api_key is missing'}, status=404)   
        outlet_obj = outlet_details.objects.get(api_key = outlet_api_key)
        project    = ProjectDetails.objects.get(api_key = project_api_key)
        datatables = request.POST
        start      = int(datatables.get('page'))
        length     = int(datatables.get('size'))
        over_all_search = datatables.get('searchValue')
        print(outlet_obj, "==================")
        print(start, "start =====================")
        print(length, "length ===================")
        field_mapping = {
            0: "created_at__icontains",
            1: "receiver__icontains",
            2: "display_name__icontains",
            3: "receiver_info__first_name__icontains",
            4: "receiver_info__last_name__icontains"
        }
        advance_filter = Q()
        if over_all_search:
            overall_search_filter = Q()
            for field in field_mapping.values():
                overall_search_filter |= Q(**{field: over_all_search})
            advance_filter |= overall_search_filter
        # if request.POST.get('asc') == True or 'true':
        #     order = 'updated_at'
        # else:
        #     print('-')
        #     order = '-updated_at'
        print(project,"===============prject")
        print(project.phone_no,"=====================================phone_no")
        print(project.phone_code,"===============================phone_no")
        project_no     = project.phone_code + project.phone_no #919820016363
        threshold_time = timezone.now() - timedelta(hours=24)
        time_filter    = Q()
        if request.POST.get('section').lower() == 'broadcast':
            time_filter |= Q(last_message_type = 'MARKETING')
            time_filter |= Q(bot__isnull=True)
            if request.POST.get('type') == 'unread':
                time_filter |= Q(chat_status = 'pending')
                time_filter &= Q(count__gt=0)
            if request.POST.get('type') == 'lapsed':
                time_filter |= Q(chat_status = 'pending')
                time_filter &= Q(servicing_window__lte=threshold_time)
            if request.POST.get('type') == 'live':
                time_filter |= Q(marketing_window__gte=threshold_time)
                time_filter |= Q(utility_window__gte=threshold_time)
                time_filter |= Q(servicing_window__gte=threshold_time)
            if request.POST.get('type') == 'closed':
                time_filter |= Q(chat_status = 'closed')
            messages_relation = MessageRelation.objects.filter(sender=project_no).filter(time_filter).filter(advance_filter).distinct()
            if request.POST.get('type') == 'history':
                time_filter |= Q(marketing_window__gte=threshold_time)
                time_filter |= Q(utility_window__gte=threshold_time)
                time_filter |= Q(servicing_window__gte=threshold_time)
                messages_relation = messages_relation.exclude(time_filter)
        if request.POST.get('section').lower() == 'support':
            time_filter |= Q(last_message_type = 'SERVICING')
            time_filter |= Q(bot__isnull=True)
            if request.POST.get('type') == 'unread':
                time_filter |= Q(chat_status = 'pending')
                time_filter &= Q(count__gt=0)
            if request.POST.get('type') == 'lapsed':
                time_filter |= Q(chat_status = 'pending')
                time_filter &= Q(servicing_window__lte=threshold_time)
            if request.POST.get('type') == 'live':
                time_filter |= Q(marketing_window__gte=threshold_time)
                time_filter |= Q(utility_window__gte=threshold_time)
                time_filter |= Q(servicing_window__gte=threshold_time)
            if request.POST.get('type') == 'closed':
                time_filter |= Q(chat_status = 'closed')
            messages_relation = MessageRelation.objects.filter(sender=project_no).filter(time_filter).filter(advance_filter).distinct()
            if request.POST.get('type') == 'history':
                time_filter |= Q(marketing_window__gte=threshold_time)
                time_filter |= Q(utility_window__gte=threshold_time)
                time_filter |= Q(servicing_window__gte=threshold_time)
                messages_relation = messages_relation.exclude(time_filter)
        if request.POST.get('section').lower() == 'bot':
            time_filter |= Q(bot = 'bot')
            if request.POST.get('type') == 'unread':
                time_filter |= Q(chat_status = 'pending')
                time_filter &= Q(count__gt=0)
            if request.POST.get('type') == 'lapsed':
                time_filter |= Q(chat_status = 'pending')
                time_filter &= Q(servicing_window__lte=threshold_time)
            if request.POST.get('type') == 'live':
                time_filter |= Q(marketing_window__gte=threshold_time)
                time_filter |= Q(utility_window__gte=threshold_time)
                time_filter |= Q(servicing_window__gte=threshold_time)
            if request.POST.get('type') == 'closed':
                time_filter |= Q(chat_status = 'closed')
            messages_relation = MessageRelation.objects.filter(sender=project_no).filter(time_filter).filter(advance_filter).distinct()
            if request.POST.get('type') == 'history':
                time_filter |= Q(marketing_window__gte=threshold_time)
                time_filter |= Q(utility_window__gte=threshold_time)
                time_filter |= Q(servicing_window__gte=threshold_time)
                messages_relation = messages_relation.exclude(time_filter)
        print(project_no,'===========================')
        message_context = []
        if over_all_search:
            print(over_all_search)
            print(project_no)
            message_context = MessageContext.objects.filter(message_log__project=project,context_text__icontains=over_all_search).values(
                messages_unique_id                          = F('contact_relation__unique_id'),
                messages_sender                             = F('contact_relation__sender'),
                messages_receiver                           = F('contact_relation__receiver'),
                messages_text                               = F('context_text'),
                messages_display_name                       = F('contact_relation__display_name'),
                messages_marketing_window                   = F('contact_relation__marketing_window'),
                messages_servicing_window                   = F('contact_relation__servicing_window'),
                messages_message                            = F('context'),
                messages_receiver_firstname                 = F('contact_relation__receiver_info__first_name'),
                messages_reciever_lastname                  = F('contact_relation__receiver_info__last_name'),
            ).order_by('-message_log__created_at')
            print(message_context)
        messages          = messages_relation.values(
            contacts_id                                 = F("id"),
            messages_unique_id                          = F('unique_id'),
            messages_sender                             = F('sender'),
            messages_receiver                           = F('receiver'),
            messages_display_name                       = F('display_name'),
            messages_chat_status                        = F('chat_status'),
            messages_marketing_window                   = F('marketing_window'),
            messages_servicing_window                   = F('servicing_window'),
            messages_last_message                       = F('last_message__context'),
            messages_receiver_firstname                 = F('receiver_info__first_name'),
            messages_reciever_lastname                  = F('receiver_info__last_name'),
            messages_last_message_timestamp_sent        = F('last_message__message_log__timestamp_sent'),
            messages_last_message_timestamp_delivered   = F('last_message__message_log__timestamp_delivered'),
            messages_last_message_timestamp_read        = F('last_message__message_log__timestamp_read'),
            messages_count                              = F('count'),
            messages_updated_at                         = F('updated_at'),
        ).order_by('-last_message__message_log__timestamp_sent')
        contact_obj_count = messages.count()
        if contact_obj_count == 0:
            # if length < contact_obj_count :
            #     paginator         = Paginator(messages, length)
            # else:
            #     paginator         = Paginator(messages, contact_obj_count)
            # try:
            #     object_list = paginator.page(start).object_list
            # except (PageNotAnInteger, EmptyPage):
            object_list = []
        else:
            length = min(length, contact_obj_count)
            paginator = Paginator(messages, length)
            try:
                object_list = paginator.page(start).object_list
            except (PageNotAnInteger, EmptyPage):
                object_list = []
        response = {
            "messages_count": contact_obj_count,
            "messages"      : list(object_list),
            "matching_messages"      : list(message_context),
            "project_no"    : project_no
        }
        return JsonResponse(response,status=status.HTTP_200_OK)
    except (outlet_details.DoesNotExist,ProjectDetails.DoesNotExist,ProjectDetails.MultipleObjectsReturned,outlet_details.MultipleObjectsReturned) as e:
        if isinstance(e, outlet_details.DoesNotExist):
            return JsonResponse({"error": "Invalid API Key outlet details not found"}, status=404)
        elif isinstance(e, outlet_details.MultipleObjectsReturned):
            return JsonResponse({"error": "Multiple outlets found with the same API Key"}, status=400)
        elif isinstance(e, ProjectDetails.DoesNotExist):
            return JsonResponse({"error": "Project details not found"}, status=404)
        elif isinstance(e, ProjectDetails.MultipleObjectsReturned):
            return JsonResponse({"error": "Multiple projects found with the same API Key"}, status=400)
    except Exception as e:
        print(str(e))
        print("======================== ERROR ==============================")
        return JsonResponse({"error": "Something went wrong!"}, status=500)

@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def mark_message_read(request):
    try:
        # outlet_obj          = outlet_details.objects.get(api_key = request.META.get('HTTP_API_KEY'))
        project_api_key    = request.META.get('HTTP_WHATSAPP_PROJECT_KEY')
        unique_id          = request.POST.get('unique_id')
        if project_api_key is None :
            return JsonResponse({'error': 'project_api_key is missing'}, status=404)  
        elif unique_id is None :
            return JsonResponse({'error': 'unique_id is missing'}, status=404)   
        else:
            pass       
        project             = ProjectDetails.objects.get(api_key = project_api_key)
        unique_id           = unique_id.replace("-","") 
        token               = project.token
        url = f"{direct_server}/mark-read"
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {token}' 
        }
        MessageRelation.objects.filter(unique_id=unique_id).update(count=0)
        payload = { "messageId": request.POST.get('messageId') }
        response = requests.post(url, json=payload, headers=headers)
        return JsonResponse(response.json(), status=status.HTTP_200_OK)
    except (ProjectDetails.DoesNotExist,ProjectDetails.MultipleObjectsReturned) as e:
        if isinstance(e, ProjectDetails.DoesNotExist):
            return JsonResponse({"error": "Project details not found"}, status=404)
        elif isinstance(e, ProjectDetails.MultipleObjectsReturned):
            return JsonResponse({"error": "Multiple projects found with the same API Key"}, status=400)
    except Exception as e:
        print(str(e))
        print("======================== ERROR ==============================")
        return JsonResponse({"error": "Something went wrong!"}, status=500)

def mark_message_read_fun(selected_no,project_no):
    print('asdsadsad')
    try:
        project_instance = ProjectDetails.objects.annotate(phone_number = Concat(F('phone_code'),F('phone_no'))).get(phone_number=project_no)
        token = project_instance.token
        message_context_unread = MessageContext.objects.filter(
            Q(message_log__sender=selected_no) &
            Q(message_log__reciever=project_no) &
            Q(message_log__timestamp_failed=None)&
            Q(message_log__timestamp_read=None)
        )
        print(message_context_unread,"====================")
        messages_message_unread = message_context_unread.values(
            message_id=F('message_log__message_id')
        )
        print(message_context_unread,"====================")
        url = f'{direct_server}/mark-read'
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {token}' 
        }
        print(url,headers,"=====================headers")
        for i in messages_message_unread:
            print(i['message_id'])
            try:
                payload = {
                    "messageId": i['message_id']
                }
                print(payload,"======================")
                response = requests.post(url, headers=headers, data=json.dumps(payload, indent=4)).json()
                print(response,'===================')
                MessageLog.objects.filter(message_id=i['message_id']).update(timestamp_read=timezone.now())
            except Exception as e:
                print(str(e),'====================errror')
                pass
        try:
            MessageRelation.objects.filter(
                Q(sender=project_no) &
                Q(receiver=selected_no)
            ).update(count=0)    
        except Exception as e:
            print(str(e),'====================errror')
            pass
    except Exception as e:
        print(str(e),'====================errror')
        pass
    return True

# ### Subsection: QUICK REPLAY ###
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])  
class quick_replay(APIView):
    def get(self, request):
        try:
            outlet_api_key          = request.META.get('HTTP_API_KEY')
            project_api_key         = request.META.get('HTTP_WHATSAPP_PROJECT_KEY')
            if outlet_api_key is None :
                return JsonResponse({'error': 'outlet_api_key is missing'}, status=404)
            if project_api_key is None :
                return JsonResponse({'error': 'project_api_key is missing'}, status=404)
            outlet_obj           = outlet_details.objects.get(api_key = outlet_api_key)
            project              = ProjectDetails.objects.get(api_key = project_api_key)           
            print(project)
            quick_reply_obj      = quickreply.objects.filter(project_id = project)
            print(quick_reply_obj)
            if quick_reply_obj.exists():
                serialized_data      = QuickReplySerializer(quick_reply_obj, many=True).data
                print(serialized_data)
                print(type(serialized_data))

                return JsonResponse(serialized_data,safe=False, status=status.HTTP_200_OK)
            else:
               return JsonResponse({"message": "not found reply"}, status=status.HTTP_200_OK) 
        except (ProjectDetails.DoesNotExist,ProjectDetails.MultipleObjectsReturned) as e:
            if isinstance(e, ProjectDetails.DoesNotExist):
                return JsonResponse({"error": "Project details not found"}, status=404)
            elif isinstance(e, ProjectDetails.MultipleObjectsReturned):
                return JsonResponse({"error": "Multiple projects found with the same API Key"}, status=400)
        except Exception as e:
            print(str(e))
            print("======================== ERROR ==============================")
            return JsonResponse({"error": "Something went wrong!"}, status=500)
        
    
    def post(self, request):
        try:
            outlet_api_key          = request.META.get('HTTP_API_KEY')
            project_api_key         = request.META.get('HTTP_WHATSAPP_PROJECT_KEY')
            if outlet_api_key is None :
                return JsonResponse({"error": "outlet_api_key is missing"}, status=404)
            elif project_api_key is None :
                return JsonResponse({"error": "project_api_key is missing"}, status=404)
            else:
                pass
            outlet_obj           = outlet_details.objects.get(api_key = outlet_api_key)          
            project              = ProjectDetails.objects.get(api_key = project_api_key)
            action               = request.data.get('action')
            if action == 'create':
                quick_reply          = quickreply.objects.create(project_id=project.id,title=request.data.get("title",None) ,message=request.data.get("message",None),created_at=datetime.now())
                return JsonResponse({"message": "quick reply saved successfully"}, status=status.HTTP_200_OK)
            elif action == 'get':
                datatables         = request.POST
                start              = int(datatables.get('page'))
                length             = int(datatables.get('size'))
                over_all_search    = datatables.get('searchValue')
                field_mapping = {
                        0: "title__icontains",
                        1: "message__icontains",
                    }
                advance_filter = Q()
                for col, field in field_mapping.items():
                    value = datatables.get(f"columns[{col}][search][value]", None)
                    if value:
                        advance_filter &= Q(**{field: value})
                if over_all_search:
                    overall_search_filter = Q()
                    for field in field_mapping.values():
                        overall_search_filter |= Q(**{field: over_all_search})
                    advance_filter |= overall_search_filter
                quick_reply_obj      = quickreply.objects.filter(project_id=project).filter(advance_filter).values(
                                            quick_reply_id         = F("id"),
                                            quick_reply_title      = F("title"),
                                            quick_reply_message    = F("message"),
                                            quick_reply_created_at = F("created_at"),
                                        ).order_by('-created_at')
                quick_reply_obj_count = quick_reply_obj.count()
                paginator = Paginator(quick_reply_obj, length)
                try:
                    object_list = paginator.page(start).object_list
                except (PageNotAnInteger, EmptyPage):
                    object_list = paginator.page(1).object_list
                response = {
                    'quick_reply_count': quick_reply_obj_count,
                    "quick_reply": list(object_list)
                }
                return JsonResponse(response, status=200)

        except (ProjectDetails.DoesNotExist,ProjectDetails.MultipleObjectsReturned) as e:
            if isinstance(e, ProjectDetails.DoesNotExist):
                return JsonResponse({"error": "Project details not found"}, status= 404)
            elif isinstance(e, ProjectDetails.MultipleObjectsReturned):
                return JsonResponse({"error": "Multiple projects found with the same API Key"}, status= 400)
        except Exception as e:
            print(str(e))
            print("======================== ERROR ==============================")
            return JsonResponse({"error": "Something went wrong!"}, status= 500)
            
            
    def delete(self,request):
        try:
            quick_reply_obj  = quickreply.objects.filter(id=request.GET.get('id'))
            print()
            for i in quick_reply_obj:
                i.delete()
            return JsonResponse({"message": "quick_reply_deleted successfully"}, status=status.HTTP_200_OK)
          
        except Exception as e:
            print(str(e))
            print("======================== ERROR ==============================")
            return JsonResponse({"error": "Something went wrong!"}, status= 500)
            
        
    def put(self, request):
        try:
            quick_reply_id       = request.data.get("id")
            if quick_reply_id is None :
                return JsonResponse({'error': 'quick_reply_id is missing'}, status=404)
            else:
                pass
            quick_reply_obj      = quickreply.objects.get(id = quick_reply_id)
            serialized_data      = QuickReplySerializer(quick_reply_obj, data=request.data)
            if serialized_data.is_valid():
                serialized_data .save()
                return JsonResponse(serialized_data .data)
            return JsonResponse(serialized_data .errors, status=status.HTTP_400_BAD_REQUEST)
        except (quickreply.DoesNotExist,quickreply.MultipleObjectsReturned) as e:
            if isinstance(e, quickreply.DoesNotExist):
                return JsonResponse({"error": "quickreply details not found"}, status= 404)
            elif isinstance(e, quickreply.MultipleObjectsReturned):
                return JsonResponse({"error": "Multiple quickreply found with the same id"}, status= 400)
        except Exception as e:
            print(str(e))
            print("======================== ERROR ==============================")
            return JsonResponse({"error": "Something went wrong!"}, status= 500)

# ### Subsection: CHAT STATUS ###
@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def chat_status(request):
    try:
        outlet_api_key          = request.META.get('HTTP_API_KEY')
        project_api_key         = request.META.get('HTTP_WHATSAPP_PROJECT_KEY')
        if outlet_api_key is None :
                return JsonResponse({"error": "outlet_api_key is missing"}, status=404)
        elif project_api_key is None :
            return JsonResponse({"error": "project_api_key is missing"}, status=404)
        else:
            pass
        outlet_obj           = outlet_details.objects.get(api_key = outlet_api_key)          
        project              = ProjectDetails.objects.get(api_key = project_api_key)          
        #sender      =   request.POST.get("sender")
        unique_id   =   request.POST.get("messages_unique_id",None).replace('-', '')
        print(unique_id)
        print("<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
        #reciver     =   request.POST.get("reciver")
        chat_status      =   request.POST.get("chat_status")
        MessageRelation.objects.filter(unique_id = unique_id).update(chat_status = chat_status)
        return JsonResponse({"message": "Status saved successfully"}, status=status.HTTP_200_OK)
    except (outlet_details.DoesNotExist,outlet_details.MultipleObjectsReturned,ProjectDetails.DoesNotExist) as e:
            if isinstance(e, outlet_details.DoesNotExist):
                return JsonResponse({"error": "outlet_details details not found"}, status= 404)
            elif isinstance(e, outlet_details.MultipleObjectsReturned):
                return JsonResponse({"error": "Multiple outlet_details found with the same api key"}, status= 400)
            elif isinstance(e, ProjectDetails.MultipleObjectsReturned):
                return JsonResponse({"error": "Project details not found"}, status= 400)
    except Exception as e:
        print(str(e))
        print("======================== ERROR ==============================")
        return JsonResponse({"error": "Something went wrong!"}, status= 500)
# ##############################################################################################################################################
# Section: CATALOG
# ##############################################################################################################################################     

# ### Subsection: SEND CATALOG ###
@csrf_exempt
@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def send_catalog(request):
    outlet_api_key          = request.META.get('HTTP_API_KEY')
    project_api_key         = request.META.get('HTTP_WHATSAPP_PROJECT_KEY')
    if outlet_api_key is None :
        return JsonResponse({"error": "outlet_api_key is missing"}, status=404)
    elif project_api_key is None :
        return JsonResponse({"error": "project_api_key is missing"}, status=404)
    else:
        pass
    outlet_obj  = outlet_details.objects.get(api_key = outlet_api_key)
    project     = ProjectDetails.objects.get(api_key = project_api_key)
    token       = project.token
    url = f"{direct_server}/messages"
    customer_list = Contacts.objects.filter(id__in =eval(request.POST.get('contact_group_list')))
    try:
        for cust_instance in customer_list:
            data_dict = {
                'FirstName': cust_instance.first_name,
                'LastName':cust_instance.last_name,
                'contact' :cust_instance.contact,
            }
            payload = {
                "recipient_type": "individual",
                "messaging_product": "whatsapp",
                "to": data_dict['contact'],
                "type": "interactive",
                "interactive": {
                    "type": "product_list",
                    "header": {
                        "type": "text",
                        "text": "Interactive Msg Header"
                    },
                    "body": { "text": "Body text of interactive msg here" },
                    "footer": { "text": "Interactive Msg Footer" },
                    "action": {
                        "catalog_id": "",
                        "sections": [
                            {
                                "title": "Product",
                                "product_items": []
                            },
                        ]
                    }
                }
            }

            catalog_id_from_request = request.POST.get('catalog_id')
            product_items_from_request = request.POST.get('product_items')
            payload['interactive']['action']['catalog_id'] = catalog_id_from_request
            payload['interactive']['action']['sections'][0]['product_items'] = product_items_from_request

            json_payload = json.dumps(payload)
            headers = {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {token}'
            }
            response = requests.request("POST", url, headers=headers, data=json_payload)
            response = json.loads(response.text)
        return JsonResponse(response,status=200)
    except (outlet_details.DoesNotExist,ProjectDetails.DoesNotExist,ProjectDetails.MultipleObjectsReturned,outlet_details.MultipleObjectsReturned) as e:
        if isinstance(e, outlet_details.DoesNotExist):
            return JsonResponse({"error": "Invalid API Key outlet details not found"}, status=404)
        elif isinstance(e, outlet_details.MultipleObjectsReturned):
            return JsonResponse({"error": "Multiple outlets found with the same API Key"}, status=400)
        elif isinstance(e, ProjectDetails.DoesNotExist):
            return JsonResponse({"error": "Project details not found"}, status=404)
        elif isinstance(e, ProjectDetails.MultipleObjectsReturned):
            return JsonResponse({"error": "Multiple projects found with the same API Key"}, status=400)
    except Exception as e:
        print(str(e))
        print("======================== ERROR ==============================")
        return JsonResponse({"error": "Something went wrong!"}, status=500)

# ### Subsection: GET CATALOG FROM AISENSY ###
@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def get_catalog(request):
    try:
        outlet_api_key          = request.META.get('HTTP_API_KEY')
        project_api_key         = request.META.get('HTTP_WHATSAPP_PROJECT_KEY')
        if outlet_api_key is None :
            return JsonResponse({"error": "outlet_api_key is missing"}, status=404)
        elif project_api_key is None :
            return JsonResponse({"error": "project_api_key is missing"}, status=404)
        else:
            pass
        outlet_obj  = outlet_details.objects.get(api_key = outlet_api_key)
        project     = ProjectDetails.objects.get(api_key = project_api_key)    
        token       = project.token
        url = f"{direct_server}/catalog"
        payload={}
        headers = {
            'Authorization': f'Bearer {token}'
        }

        response = requests.request("GET", url, headers=headers, data=payload)
        response = json.loads(response.text)

        return JsonResponse(response, status=200,safe=False)
    except (outlet_details.DoesNotExist,ProjectDetails.DoesNotExist,ProjectDetails.MultipleObjectsReturned,outlet_details.MultipleObjectsReturned) as e:
        if isinstance(e, outlet_details.DoesNotExist):
            return JsonResponse({"error": "Invalid API Key outlet details not found"}, status=404)
        elif isinstance(e, outlet_details.MultipleObjectsReturned):
            return JsonResponse({"error": "Multiple outlets found with the same API Key"}, status=400)
        elif isinstance(e, ProjectDetails.DoesNotExist):
            return JsonResponse({"error": "Project details not found"}, status=404)
        elif isinstance(e, ProjectDetails.MultipleObjectsReturned):
            return JsonResponse({"error": "Multiple projects found with the same API Key"}, status=400)
    except Exception as e:
        print(str(e))
        print("======================== ERROR ==============================")
        return JsonResponse({"error": "Something went wrong!"}, status=500)

# ### Subsection: GET SPECIFIC CATALOG ###
@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def catalog_details(request):
    try:
        outlet_api_key          = request.META.get('HTTP_API_KEY')
        project_api_key         = request.META.get('HTTP_WHATSAPP_PROJECT_KEY')
        if outlet_api_key is None :
            return JsonResponse({"error": "outlet_api_key is missing"}, status=404)
        elif project_api_key is None :
            return JsonResponse({"error": "project_api_key is missing"}, status=404)
        else:
            pass   
        outlet_obj  = outlet_details.objects.get(api_key = outlet_api_key)
        project     = ProjectDetails.objects.get(api_key = project_api_key)
        token       = project.token
        url = f"{direct_server}/product?catalogId={request.GET.get('catalog_id')}"
        payload={}
        headers = {
            'Authorization': f'Bearer {token}'
        }
        response = requests.request("GET", url, headers=headers, data=payload)
        response = json.loads(response.text)

        return JsonResponse(response, status=200,safe=False)
    except (outlet_details.DoesNotExist,ProjectDetails.DoesNotExist,ProjectDetails.MultipleObjectsReturned,outlet_details.MultipleObjectsReturned) as e:
        if isinstance(e, outlet_details.DoesNotExist):
            return JsonResponse({"error": "Invalid API Key outlet details not found"}, status=404)
        elif isinstance(e, outlet_details.MultipleObjectsReturned):
            return JsonResponse({"error": "Multiple outlets found with the same API Key"}, status=400)
        elif isinstance(e, ProjectDetails.DoesNotExist):
            return JsonResponse({"error": "Project details not found"}, status=404)
        elif isinstance(e, ProjectDetails.MultipleObjectsReturned):
            return JsonResponse({"error": "Multiple projects found with the same API Key"}, status=400)
    except Exception as e:
        print(str(e))
        print("======================== ERROR ==============================")
        return JsonResponse({"error": "Something went wrong!"}, status=500)

# ##############################################################################################################################################
# Section: DASHBOARD
# ##############################################################################################################################################     
# ### Subsection: DASHBOARD INFO ###
@csrf_exempt
@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def dashboard_view(request):
    try:
        print(request.META,"=====================================")
        outlet_api_key          = request.META.get('HTTP_API_KEY')
        print(outlet_api_key,"=====================================")
        project_api_key         = request.META.get('HTTP_WHATSAPP_PROJECT_KEY')
        if outlet_api_key is None :
            return JsonResponse({"error": "outlet_api_key is missing"}, status=404)
        elif project_api_key is None :
            return JsonResponse({"error": "project_api_key is missing"}, status=404)
        else:
            pass
        outlet_obj            = outlet_details.objects.get(api_key = outlet_api_key)
        project_instance      = ProjectDetails.objects.get(api_key = project_api_key)
        #time filters
        now = timezone.now()
        month_start = now.replace(day=1)
        week_start = now - timedelta(days=now.weekday())
        template_instance     = TemplateDetails.objects.filter(project=project_instance)
        #Lifetime data
        total_template        = template_instance.aggregate(total_count=Sum('template_total_sent'))
        total_template_count  = total_template['total_count'] if total_template['total_count'] else 0
        approved_template     = template_instance.filter(status=True).count()
        active_template       = template_instance.filter(is_active=True).count()
        total_group           = ContactsGroup.objects.filter(outlet=outlet_obj).count()
        total_contact         = Contacts.objects.filter(outlet=outlet_obj, is_active=True).count()
        #month-wise data
        monthly_templates = template_instance.filter(created_at__gte = month_start)
        total_monthly_templates = monthly_templates.aggregate(total_count = Sum('template_total_sent'))
        total_monthly_templates_count = total_monthly_templates['total_count'] if total_monthly_templates['total_count'] else 0
        approved_monthly_templates = monthly_templates.filter(status = True).count()
        active_monthly_templates = monthly_templates.filter(is_active = True).count()
        #monthly group and contact data
        monthly_group = ContactsGroup.objects.filter(outlet=outlet_obj, created_at__gte = month_start).count()
        monthly_contact = Contacts.objects.filter(outlet=outlet_obj, is_active=True, created_at_gte = month_start).count()

        #week wise data
        weekly_templates = template_instance.filter(created_at__gte = week_start)
        total_weekly_templates = weekly_templates.aggregate(total_count = Sum('template_total_sent'))
        total_weekly_templates_count = total_weekly_templates['total_count'] if total_weekly_templates['total_count'] else 0
        approved_weekly_templates = weekly_templates.filter(status = True).count()
        active_weekly_templates = weekly_templates.filter(is_active = True).count()
        #weekly group and contact data
        weekly_group = ContactsGroup.objects.filter(outlet=outlet_obj, created_at__gte = week_start).count()
        weekly_contact = Contacts.objects.filter(outlet=outlet_obj, is_active=True, created_at__gte = week_start).count()

        plan_subscription_obj = PlanSubscription.objects.filter(project = project_instance).first()
        plan_duration = plan_subscription_obj.membership_plan.plan_duration if plan_subscription_obj and plan_subscription_obj.membership_plan else None
        period = request.POST.get('period', 'all').lower()
        
        if period == 'lifetime':
            response = {
                'active_plan'      : plan_duration,

                'lifetime' : {
                'total_sent'       : total_template_count,
                'total_template'   : template_instance.count(),
                'active_campaign'  : active_template,
                'approved_template': approved_template,
                'total_group'      : total_group,
                'total_contact'    : total_contact,
                }
            }
        elif period == 'monthly':
            response = {
                'active_plan'      : plan_duration,
                'monthly'  :{
                'total_sent'       : total_monthly_templates_count,
                'total_template'   : monthly_templates.count(),
                'active_campaign'  : active_monthly_templates,
                'approved_template': approved_monthly_templates,
                'total_group'      : monthly_group,
                'total_contact'    : monthly_contact,
                }
            }

        elif period == 'weekly' : 
            response = {
                'active_plan'      : plan_duration,
                'weekly'  :{
                'total_sent'       : total_weekly_templates_count,
                'total_template'   : weekly_templates.count(),
                'active_campaign'  : active_weekly_templates,
                'approved_template': approved_weekly_templates,
                'total_group'      : weekly_group,
                'total_contact'    : weekly_contact,
                }
            }
        else:
            response = {
                'active_plan'      : plan_duration,
                'lifetime'  :{
                    'total_sent'       : total_template_count,
                    'total_template'   : template_instance.count(),
                    'active_campaign'  : active_template,
                    'approved_template': approved_template,
                    'total_group'      : total_group,
                    'total_contact'    : total_contact,
                    },
                'monthly'  : {
                    'total_sent'       : total_monthly_templates_count,
                    'total_template'   : monthly_templates.count(),
                    'active_campaign'  : active_monthly_templates,
                    'approved_template': approved_monthly_templates,
                    'total_group'      : monthly_group,
                    'total_contact'    : monthly_contact,
                    },
                'weekly'  : {
                    'total_sent'       : total_weekly_templates_count,
                    'total_template'   : weekly_templates.count(),
                    'active_campaign'  : active_weekly_templates,
                    'approved_template': approved_weekly_templates,
                    'total_group'      : weekly_group,
                    'total_contact'    : weekly_contact,
                    }
                }

            
        return JsonResponse(response, status=200)
    except (outlet_details.DoesNotExist,ProjectDetails.DoesNotExist,ProjectDetails.MultipleObjectsReturned,outlet_details.MultipleObjectsReturned) as e:
        if isinstance(e, outlet_details.DoesNotExist):
            return JsonResponse({"error": "Invalid API Key outlet details not found"}, status=404)
        elif isinstance(e, outlet_details.MultipleObjectsReturned):
            return JsonResponse({"error": "Multiple outlets found with the same API Key"}, status=400)
        elif isinstance(e, ProjectDetails.DoesNotExist):
            return JsonResponse({"error": "Project details not found"}, status=404)
        elif isinstance(e, ProjectDetails.MultipleObjectsReturned):
            return JsonResponse({"error": "Multiple projects found with the same API Key"}, status=400)
    except Exception as e:
        print(str(e))
        print("======================== ERROR ==============================")
        return JsonResponse({"error": "Something went wrong!"}, status=500)
# ### Subsection: GET TEMPLATE REPORT ###
@csrf_exempt
@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def template_view(request):
    try:
        outlet_api_key          = request.META.get('HTTP_API_KEY')
        project_api_key         = request.META.get('HTTP_WHATSAPP_PROJECT_KEY')
        if outlet_api_key is None :
                return JsonResponse({"error": "outlet_api_key is missing"}, status=404)
        elif project_api_key is None :
            return JsonResponse({"error": "project_api_key is missing"}, status=404)
        else:
            pass
        outlet_obj        = outlet_details.objects.get(api_key = outlet_api_key)
        project_instance  = ProjectDetails.objects.get(api_key = project_api_key)
        datatables      = request.POST
        start           = int(datatables.get('page'))
        length          = int(datatables.get('size'))
        over_all_search = datatables.get('searchValue')
        field_mapping = {
            0: "t.templateId",
            1: "t.templateName",
            2: "t.created_at",
        }
        outlet_obj        = outlet_details.objects.get(api_key=request.META.get('HTTP_API_KEY'))
        sql_query = '''
            SELECT d.template_id, 
                COUNT(*) AS template_template_total_sent,
                COUNT(CASE WHEN d.timestamp_sent IS NOT NULL THEN 1 END) AS template_template_sent,
                COUNT(CASE WHEN d.timestamp_delivered IS NOT NULL THEN 1 END) AS template_template_delivered,
                COUNT(CASE WHEN d.timestamp_failed IS NOT NULL THEN 1 END) AS template_template_failed,
                COUNT(CASE WHEN d.timestamp_read IS NOT NULL THEN 1 END) AS template_template_read,
                t.templateName AS template_templateName,
                t.templateId AS template_templateId,
                t.created_at AS template_created_at
                
            FROM `xl2024_Messagelog_details` d
            LEFT JOIN `xl2024_template_details` t ON d.template_id = t.id
            WHERE d.templateId IS NOT NULL AND d.outlet_id = {0} AND t.project_id = {1}
            
        '''.format(outlet_obj.id,project_instance.id)

        if over_all_search:
            # Construct the search condition for all fields
            search_conditions = " OR ".join(field + " LIKE '%" + over_all_search + "%'" for field in field_mapping.values())
            # Append the search condition to the SQL query
            sql_query += " AND (" + search_conditions +") "
        sql_query += "GROUP BY d.templateId, t.templateName ORDER BY t.created_at DESC;"
        print(sql_query)
        connection = mysql.connector.connect(
            database=API_DB_NAME,
            user=API_USER_NAME,
            password=API_DB_PASSWORD
        )
        cursor = connection.cursor()
        cursor.execute(sql_query)

        contact_obj = dictfetchall(cursor)
        # print(contact_obj)
        cursor.close()
        connection.close()
        start = int(datatables.get('page'))
        length = int(datatables.get('size'))
        
        contact_obj_count = len(contact_obj)
        paginator = Paginator(contact_obj, length)
        try:
            object_list = paginator.page(start).object_list
        except (PageNotAnInteger, EmptyPage):
            object_list = paginator.page(1).object_list
        print(contact_obj_count)
        response = {
            'template_count': contact_obj_count,
            "template": object_list
        }
        return JsonResponse(response, status=200)
    except (outlet_details.DoesNotExist,ProjectDetails.DoesNotExist,ProjectDetails.MultipleObjectsReturned,outlet_details.MultipleObjectsReturned) as e:
        if isinstance(e, outlet_details.DoesNotExist):
            return JsonResponse({"error": "Invalid API Key outlet details not found"}, status=404)
        elif isinstance(e, outlet_details.MultipleObjectsReturned):
            return JsonResponse({"error": "Multiple outlets found with the same API Key"}, status=400)
        elif isinstance(e, ProjectDetails.DoesNotExist):
            return JsonResponse({"error": "Project details not found"}, status=404)
        elif isinstance(e, ProjectDetails.MultipleObjectsReturned):
            return JsonResponse({"error": "Multiple projects found with the same API Key"}, status=400)
    except Exception as e:
        print(str(e))
        print("======================== ERROR ==============================")
        return JsonResponse({"error": "Something went wrong!"}, status=500)
# ### Subsection: GET MESSAGE LOG REPORT ###
@csrf_exempt
@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def messagelog_view(request):
    try:
        if request.POST.get('export') == '1' or request.POST.get('export') == 1:
            try:
                advance_filter = Q()
                print("======inexport====")

                if request.POST.get('start_date') and request.POST.get('end_date'):
                    start_date = datetime.strptime(request.POST.get('start_date'), "%Y-%m-%d")
                    end_date = datetime.strptime(request.POST.get('end_date'), "%Y-%m-%d")
                    end_date = end_date + timedelta(hours=23, minutes=59, seconds=59)
                    advance_filter &= Q(created_at__range=[start_date, end_date])
                    
                if request.POST.get('campaign_id'):
                    advance_filter &= Q(campaign_id=request.POST.get('campaign_id'))

                MessageLog_obj = MessageLog.objects.filter(templateId=request.POST.get('templateId')).filter(advance_filter).order_by('-created_at')[0 if request.POST.get('page_size') == "ALL" else int(request.POST.get('batch')) * int(request.POST.get('page_size')):int(request.POST.get('count')) if request.POST.get('page_size') == "ALL" else int(request.POST.get('batch')) * int(request.POST.get('page_size')) + int(request.POST.get('page_size'))]

                messagelog_instance_list = []
                for i in MessageLog_obj:
                    try:
                        number = i.reciever[2:]
                        # print(number)
                        contact_obj = Contacts.objects.get(contact=number)
                    except Exception as e:
                        # print(e, "=============1743")
                        contact_obj = None
                        pass
                    temp = {}
                    temp['created_at'] = i.created_at
                    temp['first_name'] = contact_obj.first_name if contact_obj else ''
                    temp['last_name'] = contact_obj.last_name if contact_obj else ''
                    temp['contact'] = i.reciever
                    temp['timestamp_sent'] = i.timestamp_sent
                    temp['timestamp_delivered'] = i.timestamp_delivered
                    temp['timestamp_read'] = i.timestamp_read
                    temp['timestamp_failed'] = i.timestamp_failed
                    temp['remark'] = i.remark
                    messagelog_instance_list.append(temp)   

                fields = ["Created On", "First Name", "Last Name", "Contact", "Sent", "Delivered", "Read", "Failed" "Remark"]
                response = export_csv(fields, messagelog_instance_list, "values")
                print(response, "responseresponseresponse")
                return response
            except Exception as e:
                return JsonResponse(str(e), safe=False)

        datatables = request.POST
        print(datatables)
        print(request.POST)
        start = int(datatables.get('page'))
        length = int(datatables.get('size'))
        over_all_search = datatables.get('searchValue')
        time_range = datatables.get('time_range')
        field_mapping = {
            0: "created_at__range",
            1: "reciever__icontains",
            2: "timestamp_sent__range",
            3: "timestamp_delivered__range",
            4: "timestamp_read__range",
            5: "timestamp_failed__range",
            6: "remark__icontains",
        }
        exclude_from_overall_search = ["created_at__range","timestamp_sent__range","timestamp_delivered__range","timestamp_read__range","timestamp_failed__range"]
        advance_filter = Q()
        if request.POST.get('campaign_id'):
            advance_filter &= Q(campaign_id=request.POST.get('campaign_id'))
        for col, field in field_mapping.items():
            value = datatables.get(f"columns[{col}][search][value]", None)
            if value:
                if field.endswith("__range"):  # Handle range queries
                    start_date, end_date = value.split(",")  # Split the range value
                    start_date      = datetime.strptime(start_date, "%Y-%m-%d")
                    end_date        = datetime.strptime(end_date, "%Y-%m-%d")
                    end_date        = end_date + timedelta(hours=23, minutes=59, seconds=59)
                    advance_filter &= Q(**{field: (start_date, end_date)})
                else:
                    advance_filter &= Q(**{field: value})
        if over_all_search:
            overall_search_filter = Q()
            for field in field_mapping.values():
                if field not in exclude_from_overall_search:
                    overall_search_filter |= Q(**{field: over_all_search})
            advance_filter |= overall_search_filter
        print(advance_filter,"================advance_filter")
        messagelog_instance = MessageLog.objects.filter(templateId=request.POST.get('templateId')).filter(advance_filter).values(
            messagelog_message_id           = F("message_id"),
            messagelog_created_at           = F("created_at"),
            messagelog_contact              = F("reciever"),
            messagelog_content              = F("content"),
            messagelog_timestamp_sent       = F("timestamp_sent"),
            messagelog_timestamp_delivered  = F("timestamp_delivered"),
            messagelog_timestamp_read       = F("timestamp_read"),
            messagelog_timestamp_failed     = F("timestamp_failed"),
            messagelog_remark               = F("remark"),
        ).order_by('-created_at')
        contact_obj_count = messagelog_instance.count()
        batch = start - 1
        messagelog_instance_list = []
        for i in messagelog_instance[batch * length: batch * length + length]:
            try:
                number = i.get('messagelog_contact')[2:]
                # print(number)
                contact_obj = Contacts.objects.get(contact=number)
            except Exception as e:
                print(e, "=============1743")
                contact_obj = None
                pass
            temp = {}
            temp['first_name'] = contact_obj.first_name if contact_obj else ''
            temp['last_name'] = contact_obj.last_name if contact_obj else ''
            temp['data'] = i
            messagelog_instance_list.append(temp)
            

        # contact_obj_count = message_log_count_adv if message_log_count_adv else message_log_count
        paginator = Paginator(messagelog_instance_list, length)
        try:
            object_list = paginator.page(start).object_list
        except (PageNotAnInteger, EmptyPage):
            object_list = paginator.page(1).object_list
        response = {
            'messagelog_count': contact_obj_count,
            "messagelog": list(object_list)
        }
        return JsonResponse(response, status=200)
    except Exception as e:
        return JsonResponse({"message":f"{str(e)}"},status= 500)
    
    
# ### Subsection: CAMPAIGN REPORT ### 
@csrf_exempt
@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def campaign_report(request):
    if request.method == "GET":
        sql_query = '''
            SELECT  
                COUNT(*) AS campaign_total_sent,
                COUNT(CASE WHEN msg_log.timestamp_sent IS NOT NULL THEN 1 END) AS campaign_sent,
                COUNT(CASE WHEN msg_log.timestamp_delivered IS NOT NULL THEN 1 END) AS campaign_delivered,
                COUNT(CASE WHEN msg_log.timestamp_failed IS NOT NULL THEN 1 END) AS campaign_failed,
                COUNT(CASE WHEN msg_log.timestamp_read IS NOT NULL THEN 1 END) AS campaign_read
            FROM `xl2024_messagelog_details` AS msg_log  WHERE msg_log.campaign_id  = {0};
        '''.format(request.GET.get('campaign_id'))
        connection = mysql.connector.connect(
            database=API_DB_NAME,
            user=API_USER_NAME,
            password=API_DB_PASSWORD
        )
        cursor = connection.cursor()
        cursor.execute(sql_query)

        campaign_report = dictfetchall(cursor)
        # print(campaign_report)
        cursor.close()
        connection.close()
    return JsonResponse({"data":campaign_report })

# ##############################################################################################################################################
# Section: OPT IN OR OUT
# ##############################################################################################################################################     

# ### Subsection: OPT MESSAGE SENDING ###
class OptSend:
    def __init__(self, sender, phone_no, messages):
        self.sender = sender
        self.phone_no = phone_no
        self.messages = messages

    def get_project_opt_details(self):
        print(self.sender,self.phone_no,self.messages)
        project_instance = ProjectDetails.objects.annotate(phone_number=Concat(F('phone_code'), F('phone_no'))).get(phone_number=self.phone_no)
        outlet_instance = project_instance.business.outlet
        self.project_id = project_instance.id
        opt_settings_instance = OptSettings.objects.filter(project=project_instance, outlet=outlet_instance)
        print(opt_settings_instance,outlet_instance,"====================================1111111")
        return self.decide_opt_in_or_out(opt_settings_instance, outlet_instance)

    def decide_opt_in_or_out(self, opt_settings_instance, outlet_instance):
        for obj in opt_settings_instance:
            if self.messages in eval(obj.opt_keyword):
                return obj, outlet_instance
        return None, outlet_instance

    def send_message_opt(self):
        try:
            opt_instance, outlet_instance = self.get_project_opt_details()
        except Exception as e:
            print(str(e),"=======================recivemessagein")
        print(opt_instance, outlet_instance,"==============================222")
        if opt_instance is not None:
            try:
                country_code , contact_no = get_phone_code(self.sender)
                contact_instance = Contacts.objects.filter(phone_code=country_code,contact=contact_no, outlet=outlet_instance).last()
                if opt_instance.is_active:
                    if opt_instance.template:
                        button_variables = None
                        customer_list = [{'Firstname': contact_instance.first_name, 'Lastname': contact_instance.last_name, 'phone_number': self.sender}]
                        template_instance = opt_instance.template
                        msg_send = MessageSender(
                            button_variables=button_variables,
                            template_instance=template_instance,
                            campaign_id=None
                        )
                        message_thread = threading.Thread(target=msg_send.send_messages, args=(customer_list,))
                        message_thread.start()
                    else:
                        kwargs = eval(opt_instance.message_data)
                        kwargs['project_id'] = self.project_id
                        send_service_message(outlet_instance.id, self.sender, **kwargs)
                contact_instance.is_active = True
                contact_instance.is_opt_out = opt_instance.opt_out
                contact_instance.save()
                return True
            except Exception as e:
                print(str(e),"=======================recivemessagein")
        return True

# ### Subsection: OPT SETTINGS SAVE / GET / UPDATE ###
@api_view(['POST','GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def opt_settings(request):
    try:
        outlet_api_key          = request.META.get('HTTP_API_KEY')
        project_api_key         = request.META.get('HTTP_WHATSAPP_PROJECT_KEY')
        if outlet_api_key is None :
                return JsonResponse({"error": "outlet_api_key is missing"}, status=404)
        elif project_api_key is None :
            return JsonResponse({"error": "project_api_key is missing"}, status=404)
        else:
            pass
        outlet_obj              = outlet_details.objects.get(api_key = outlet_api_key)           
        project_instance        = ProjectDetails.objects.get(api_key = project_api_key)
        opt_settings_instance   = OptSettings.objects.filter(project=project_instance,outlet=outlet_obj)
        response = {
            'message':'success'
        }
        if request.method == 'POST':
            opt = True if request.POST.get('opt') == 'true' or request.POST.get('opt') == 'True' else False
            print(opt,"========================================")
            print(request.POST.get('opt',False),"========================================")
            print(opt_settings_instance,"===============================")
            try:
                opt_settings_instance   = opt_settings_instance.get(opt_in=True) if opt else opt_settings_instance.get(opt_out=True)
            except:
                opt_settings_instance = None
            if opt_settings_instance is None:
                opt_settings_instance   = OptSettings.objects.create(project=project_instance,outlet=outlet_obj)
                if opt:
                    opt_settings_instance.opt_in  = True
                    opt_settings_instance.opt_out = False
                else:
                    opt_settings_instance.opt_in  = False
                    opt_settings_instance.opt_out = True
            
                
            print(opt_settings_instance,"===============================")
            if request.POST.get('keyword_list',None):
                keyword_list            = [str(x) for x in request.POST.get('keyword_list').split(',')]
                opt_settings_instance.opt_keyword = keyword_list
            elif request.POST.get('templateId',None):
                template_instance =  TemplateDetails.objects.get(templateId=request.POST.get('templateId'))
                opt_settings_instance.template     = template_instance
                opt_settings_instance.message_data = None
            elif request.POST.get('message_body', None) or request.POST.get('caption',None) or request.POST.get('filename',None) or request.POST.get('type',None):

                data = {
                    'message_body': request.POST.get('message_body'),
                    'caption': request.POST.get('caption'),
                    'filename': request.POST.get('filename'),
                    'type': request.POST.get('type'),
                }
                if request.FILES.get('file', None) is not None:
                    print(opt_settings_instance,"===============================")
                    print(request.FILES.get('file', None),"===================request.FILES.get('file', None)")
                    opt_settings_instance.document = request.FILES.get('file')
                    opt_settings_instance.save()
                    link = f"{XIRCLS_DOMAIN}/static{opt_settings_instance.document.url}"
                else:
                    link = None
                data['media_link'] = link
                opt_settings_instance.message_data = data
                opt_settings_instance.template     = None
            else:
                is_active = True if request.POST.get('is_active') == 'true' or request.POST.get('is_active') == 'True' else False
                opt_settings_instance.is_active = is_active
            opt_settings_instance.save()
            
        if request.method == 'GET':
            response['opt_settings_instance'] = OptSettingsSerializer(opt_settings_instance, many=True).data
            try:
                response['opt_settings_instance'][0]['opt_keyword'] = eval(response['opt_settings_instance'][0]['opt_keyword'])
                response['opt_settings_instance'][1]['opt_keyword'] = eval(response['opt_settings_instance'][1]['opt_keyword'])
            except:
                pass
        return JsonResponse(response , status=status.HTTP_200_OK) 
    except (outlet_details.DoesNotExist,ProjectDetails.DoesNotExist,ProjectDetails.MultipleObjectsReturned,outlet_details.MultipleObjectsReturned) as e:
        if isinstance(e, outlet_details.DoesNotExist):
            return JsonResponse({"error": "Invalid API Key outlet details not found"}, status=404)
        elif isinstance(e, outlet_details.MultipleObjectsReturned):
            return JsonResponse({"error": "Multiple outlets found with the same API Key"}, status=400)
        elif isinstance(e, ProjectDetails.DoesNotExist):
            return JsonResponse({"error": "Project details not found"}, status=404)
        elif isinstance(e, ProjectDetails.MultipleObjectsReturned):
            return JsonResponse({"error": "Multiple projects found with the same API Key"}, status=400)
    except Exception as e:
        print(str(e))
        print("======================== ERROR ==============================")
        return JsonResponse({"error": "Something went wrong!"}, status=500)

# ##############################################################################################################################################
# Section: WABA PROFILE 
# ##############################################################################################################################################     
# ### Subsection: UPDATE PROFILE ###
@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def update_profile(request):
    try:
        outlet_api_key      = request.META.get('HTTP_API_KEY')
        project_api_key     = request.META.get('HTTP_WHATSAPP_PROJECT_KEY')
        if outlet_api_key is None :
                return JsonResponse({"error": "outlet_api_key is missing"}, status=404)
        elif project_api_key is None :
            return JsonResponse({"error": "project_api_key is missing"}, status=404)
        else:
            pass
        outlet_obj          = outlet_details.objects.get(api_key = outlet_api_key)           
        project             = ProjectDetails.objects.get(api_key = project_api_key)
        token               = project.token
        print(token)
        url = f"{direct_server}/update-profile-picture"
        headers = {
            'Accept'        : 'application/json',
            'Content-Type'  : 'application/json',
            'Authorization' : f'Bearer {token}' 
        }
        mediafiles            = request.FILES.get('profile',None)
        whatsAppAbout         = request.POST.get("about",None) 
        address               = request.POST.get("address",None) 
        description           = request.POST.get("description",None) 
        vertical              = request.POST.get("vertical",None) 
        email                 = request.POST.get("email",None) 
        websites              = request.POST.getlist('websites',None) 
        profileonly           = request.POST.get('profileonly') 
        print(profileonly)
        if profileonly == "1":
            # print("<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<in profileonly>>>>>>>>>>>>>>>>>>>>>>>>> ")
            url = f"{direct_server}/update-profile-picture"
            carouselcard = CarouselCard.objects.create(file_data=mediafiles,file_type='img')
            link = f"{XIRCLS_DOMAIN}/static{carouselcard.file_data.url}"
            payload = { "whatsAppDisplayImage": link }
            print(payload)
            response = requests.patch(url, json=payload, headers=headers)
            carouselcard.delete()
            
        else:
            # print("<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<in else>>>>>>>>>>>>>>>>>>>>>>>>> ")
            url = f"{direct_server}/update-profile"
            if mediafiles:
               carouselcard = CarouselCard.objects.create(file_data=mediafiles,file_type='img')
               link = f"{XIRCLS_DOMAIN}/static{carouselcard.file_data.url}"
            else:
                link = None
            payload = {
                "whatsAppAbout"         : whatsAppAbout ,
                "address"               : address,
                "description"           : description,
                "vertical"              : vertical,
                "email"                 : email,
                "websites"              : websites,
                "whatsAppDisplayImage"  : link
            }
            print(payload)
            response = requests.patch(url, json=payload, headers=headers)
            if mediafiles:
                carouselcard.delete()
            else:
                pass
        return JsonResponse(response.json(), status=status.HTTP_200_OK)
    except (outlet_details.DoesNotExist,ProjectDetails.DoesNotExist,ProjectDetails.MultipleObjectsReturned,outlet_details.MultipleObjectsReturned) as e:
        if isinstance(e, outlet_details.DoesNotExist):
            return JsonResponse({"error": "Invalid API Key outlet details not found"}, status=404)
        elif isinstance(e, outlet_details.MultipleObjectsReturned):
            return JsonResponse({"error": "Multiple outlets found with the same API Key"}, status=400)
        elif isinstance(e, ProjectDetails.DoesNotExist):
            return JsonResponse({"error": "Project details not found"}, status=404)
        elif isinstance(e, ProjectDetails.MultipleObjectsReturned):
            return JsonResponse({"error": "Multiple projects found with the same API Key"}, status=400)
    except Exception as e:
        print(str(e))
        print("======================== ERROR ==============================")
        return JsonResponse({"error": "Something went wrong!"}, status=500)
# ### Subsection: GET PROJECT PROFILE ###
@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def get_project_profile(request):
    try:
        outlet_api_key      = request.META.get('HTTP_API_KEY')
        project_api_key     = request.META.get('HTTP_WHATSAPP_PROJECT_KEY')
        if outlet_api_key is None :
                return JsonResponse({"error": "outlet_api_key is missing"}, status=404)
        elif project_api_key is None :
            return JsonResponse({"error": "project_api_key is missing"}, status=404)
        else:
            pass
        outlet_obj          = outlet_details.objects.get(api_key = outlet_api_key)           
        project             = ProjectDetails.objects.get(api_key = project_api_key)
        token               = project.token
        url1 = f"{direct_server}/get-profile"
        url2 = f"https://apis.aisensy.com/partner-apis/v1/partner/{partner_id}/project/{project.project_id}"
        headers1 = {
            'Accept': 'application/json',
            'Authorization': f'Bearer {token}' 
        }
        headers2 = {
                "Accept": "application/json",
                'X-AiSensy-Partner-API-Key': apikey
            }
        profile_data        =   requests.get(url1, headers=headers1)
        project_data        =   requests.get(url2, headers=headers2)
        profile_data_parsed =   profile_data.json()
        project_data_parsed =   project_data.json()
        profile_data        =   profile_data_parsed.get("profileData", [{}])[0] 
        profile_data["wa_display_name"]     = project_data_parsed.get("wa_display_name", None)
        profile_data["wa_number"]           = project_data_parsed.get("wa_number", None)
        profile_data["wa_quality_rating"]   = project_data_parsed.get("wa_quality_rating", None)
        profile_data["wa_display_name_status"]   = project_data_parsed.get("wa_display_name_status", None)

        return JsonResponse(profile_data, status=status.HTTP_200_OK)
    except (outlet_details.DoesNotExist,ProjectDetails.DoesNotExist,ProjectDetails.MultipleObjectsReturned,outlet_details.MultipleObjectsReturned) as e:
        if isinstance(e, outlet_details.DoesNotExist):
            return JsonResponse({"error": "Invalid API Key outlet details not found"}, status=404)
        elif isinstance(e, outlet_details.MultipleObjectsReturned):
            return JsonResponse({"error": "Multiple outlets found with the same API Key"}, status=400)
        elif isinstance(e, ProjectDetails.DoesNotExist):
            return JsonResponse({"error": "Project details not found"}, status=404)
        elif isinstance(e, ProjectDetails.MultipleObjectsReturned):
            return JsonResponse({"error": "Multiple projects found with the same API Key"}, status=400)
    except Exception as e:
        print(str(e))
        print("======================== ERROR ==============================")
        return JsonResponse({"error": "Something went wrong!"}, status=500)
# ##############################################################################################################################################
# Section: PROFILE TAGS
# ##############################################################################################################################################     

# ### Subsection: CRUD ASSIGN TAGS ###   
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])  
class customer_tags_notes(APIView):
    def get(self, request):
        try:
            outlet_api_key         = request.META.get('HTTP_API_KEY')
            project_api_key        = request.META.get('HTTP_WHATSAPP_PROJECT_KEY')
            if outlet_api_key is None :
                return JsonResponse({"error": "outlet_api_key is missing"}, status=404)
            elif project_api_key is None :
                return JsonResponse({"error": "project_api_key is missing"}, status=404)
            else:
                pass
            outlet_obj             = outlet_details.objects.get(api_key = outlet_api_key)
            project                = ProjectDetails.objects.get(api_key = project_api_key)
            contact_number         = request.GET.get("contact",None) 
            phone_code             = request.GET.get("phone_code",None) 
            customer_tag_notes_obj = CustomerTagsNotes.objects.filter(contact__contact = contact_number,contact__phone_code = phone_code,contact__outlet = outlet_obj,contact__project = project).first()
            if customer_tag_notes_obj:
                tags = list(customer_tag_notes_obj.tags.values('id', 'tag'))
                data = {
                    "id": customer_tag_notes_obj.id,
                    "contact": customer_tag_notes_obj.contact.contact,
                    "phone_code": customer_tag_notes_obj.contact.phone_code,
                    "tags": tags,
                    "notes": customer_tag_notes_obj.notes,
                    "created_at": customer_tag_notes_obj.created_at.strftime("%Y-%m-%d %H:%M:%S")
                }
            else:
                data = {
                    
                }
            return JsonResponse(data, status=status.HTTP_200_OK)
        except (outlet_details.DoesNotExist,ProjectDetails.DoesNotExist,ProjectDetails.MultipleObjectsReturned,outlet_details.MultipleObjectsReturned) as e:
            if isinstance(e, outlet_details.DoesNotExist):
                return JsonResponse({"error": "Invalid API Key outlet details not found"}, status=404)
            elif isinstance(e, outlet_details.MultipleObjectsReturned):
                return JsonResponse({"error": "Multiple outlets found with the same API Key"}, status=400)
            elif isinstance(e, ProjectDetails.DoesNotExist):
                return JsonResponse({"error": "Project details not found"}, status=404)
            elif isinstance(e, ProjectDetails.MultipleObjectsReturned):
                return JsonResponse({"error": "Multiple projects found with the same API Key"}, status=400)
        except Exception as e:
            print(str(e))
            print("======================== ERROR ==============================")
            return JsonResponse({"error": "Something went wrong!"}, status=500)
                
    def post(self,request):
        try:
            outlet_api_key         = request.META.get('HTTP_API_KEY')
            project_api_key        = request.META.get('HTTP_WHATSAPP_PROJECT_KEY')
            if outlet_api_key is None :
                return JsonResponse({"error": "outlet_api_key is missing"}, status=404)
            elif project_api_key is None :
                return JsonResponse({"error": "project_api_key is missing"}, status=404)
            else:
                pass
            outlet_obj    = outlet_details.objects.get(api_key = outlet_api_key)
            project       = ProjectDetails.objects.get(api_key = project_api_key)
            contact       = request.POST.get("contact",None)
            phone_code    = request.POST.get("phone_code",None) 
            #tag        = request.POST.get("tag_ids",None)
            tag_ids       = request.POST.getlist("tag_ids", None)
            tag           = request.POST.get("tag", None)
            notes         = request.POST.get("notes",None)
            # print(tag)
            # print(tag_ids)
            # print("<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<tagssss>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
            if notes is None :
                if tag and not tag_ids :
                    custom_tag = Tags.objects.create(project = project, tag = tag ,created_at = datetime.now())
                    tag_ids = [custom_tag.id]
                    # print(tag_ids)
                    # print("<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<list>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
                else:
                    pass
                customer_tag = CustomerTagsNotes.objects.filter(contact__contact=contact,contact__phone_code = phone_code,contact__outlet = outlet_obj,contact__project = project).first()
                if customer_tag is None:
                    contact_instance = Contacts.objects.get(contact=contact, phone_code=phone_code,outlet = outlet_obj)
                    customer_tag     = CustomerTagsNotes.objects.create(contact=contact_instance,created_at = datetime.now())
                else:
                    pass
                customer_tag.tags.add(*tag_ids)
                
            elif notes and not tag_ids:
                custom_tag = CustomerTagsNotes.objects.filter(contact__contact=contact,contact__phone_code = phone_code,contact__outlet = outlet_obj,contact__project = project).first()
                if custom_tag is None:
                    contact_instance = Contacts.objects.get(contact=contact, phone_code=phone_code , outlet = outlet_obj, project = project)
                    custom_tag       = CustomerTagsNotes.objects.create(contact=contact_instance,created_at = datetime.now(),notes = notes)
                else:
                    CustomerTagsNotes.objects.filter(contact__contact=contact,contact__phone_code = phone_code).update(notes = notes)
            else:
                contact_instance = Contacts.objects.get(contact=contact, phone_code=phone_code,outlet = outlet_obj, project = project)
                custom_tag       = CustomerTagsNotes.objects.create(contact = contact_instance, notes = notes, created_at = datetime.now())
                #custom_tag = CustomerTagsNotes.objects.create(contact__contact=contact,contact__phone_code = phone_code,contact__outlet = outlet_obj, notes = notes,created_at = datetime.now())
                if tag_ids:
                    custom_tag.tags.add(*tag_ids) 
            return JsonResponse({"message": "saved successfully"}, status=status.HTTP_200_OK)
        except (outlet_details.DoesNotExist,ProjectDetails.DoesNotExist,ProjectDetails.MultipleObjectsReturned,outlet_details.MultipleObjectsReturned) as e:
            if isinstance(e, outlet_details.DoesNotExist):
                return JsonResponse({"error": "Invalid API Key outlet details not found"}, status=404)
            elif isinstance(e, outlet_details.MultipleObjectsReturned):
                return JsonResponse({"error": "Multiple outlets found with the same API Key"}, status=400)
            elif isinstance(e, ProjectDetails.DoesNotExist):
                return JsonResponse({"error": "Project details not found"}, status=404)
            elif isinstance(e, ProjectDetails.MultipleObjectsReturned):
                return JsonResponse({"error": "Multiple projects found with the same API Key"}, status=400)
        except Exception as e:
            print(str(e))
            print("======================== ERROR ==============================")
            return JsonResponse({"error": "Something went wrong!"}, status=500)
                
    def delete(self, request):
        try:
            outlet_api_key  = request.META.get('HTTP_API_KEY')
            project_api_key = request.META.get('HTTP_WHATSAPP_PROJECT_KEY')
            if outlet_api_key is None :
                return JsonResponse({"error": "outlet_api_key is missing"}, status=404)
            elif project_api_key is None :
                return JsonResponse({"error": "project_api_key is missing"}, status=404)
            else:
                pass
            outlet_obj     = outlet_details.objects.get(api_key = outlet_api_key)
            project        = ProjectDetails.objects.get(api_key = project_api_key)
            contact        = request.GET.get("contact",None)
            tag            = request.GET.get("tag_id",None)
            phone_code     = request.GET.get("phone_code",None) 
            if tag is None:
                CustomerTagsNotes.objects.filter(contact__contact=contact,contact__phone_code = phone_code,contact__outlet = outlet_obj).update(notes='')
            else:
                custom_tag     = CustomerTagsNotes.objects.filter(contact__contact=contact,contact__phone_code = phone_code,contact__outlet = outlet_obj).first()
                custom_tag.tags.remove(tag)
            return JsonResponse({"message": "removed successfully"}, status=status.HTTP_200_OK)
        except (outlet_details.DoesNotExist,ProjectDetails.DoesNotExist,ProjectDetails.MultipleObjectsReturned,outlet_details.MultipleObjectsReturned) as e:
            if isinstance(e, outlet_details.DoesNotExist):
                return JsonResponse({"error": "Invalid API Key outlet details not found"}, status=404)
            elif isinstance(e, outlet_details.MultipleObjectsReturned):
                return JsonResponse({"error": "Multiple outlets found with the same API Key"}, status=400)
            elif isinstance(e, ProjectDetails.DoesNotExist):
                return JsonResponse({"error": "Project details not found"}, status=404)
            elif isinstance(e, ProjectDetails.MultipleObjectsReturned):
                return JsonResponse({"error": "Multiple projects found with the same API Key"}, status=400)
        except Exception as e:
            print(str(e))
            print("======================== ERROR ==============================")
            return JsonResponse({"error": "Something went wrong!"}, status=500)

# ### Subsection: CRUD TAGS ###          
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])  
class tags(APIView):
    def post(self,request):
        try:
            project_api_key = request.META.get('HTTP_WHATSAPP_PROJECT_KEY')
            if project_api_key is None :
                return JsonResponse({"error": "project_api_key is missing"}, status=404)
            else:
                pass
            project    = ProjectDetails.objects.get(api_key = project_api_key)
            #project_id = request.POST.get("id",None) 
            Tags.objects.create(project = project, tag = request.POST.get("tags",None) ,created_at = datetime.now())
            return JsonResponse({"message": "tag saved successfully"}, status=status.HTTP_200_OK)
        except (ProjectDetails.DoesNotExist,ProjectDetails.MultipleObjectsReturned) as e:
            if isinstance(e, ProjectDetails.DoesNotExist):
                return JsonResponse({"error": "Project details not found"}, status=404)
            elif isinstance(e, ProjectDetails.MultipleObjectsReturned):
                return JsonResponse({"error": "Multiple projects found with the same API Key"}, status=400)
        except Exception as e:
            print(str(e))
            print("======================== ERROR ==============================")
            return JsonResponse({"error": "Something went wrong!"}, status=500)
     
    def get(self,request):
        try:
            project_api_key         = request.META.get('HTTP_WHATSAPP_PROJECT_KEY')
            if project_api_key is None :
                return JsonResponse({"error": "project_api_key is missing"}, status=404)
            else:
                pass
            project       = ProjectDetails.objects.get(api_key = project_api_key)
            tags_obj      = Tags.objects.filter(Q(project = project) | Q(project = None))
            if tags_obj.exists():
                    serialized_data      = TagsSerializer(tags_obj, many=True).data
                    return JsonResponse(serialized_data,safe=False, status=status.HTTP_200_OK)
            else:
                pass
        except (ProjectDetails.DoesNotExist,ProjectDetails.MultipleObjectsReturned) as e:
            if isinstance(e, ProjectDetails.DoesNotExist):
                return JsonResponse({"error": "Project details not found"}, status=404)
            elif isinstance(e, ProjectDetails.MultipleObjectsReturned):
                return JsonResponse({"error": "Multiple projects found with the same API Key"}, status=400)
        except Exception as e:
            print(str(e))
            print("======================== ERROR ==============================")
            return JsonResponse({"error": "Something went wrong!"}, status=500)
    
    def delete(self, request):
        try:
            project_api_key         = request.META.get('HTTP_WHATSAPP_PROJECT_KEY')
            if project_api_key is None :
                return JsonResponse({"error": "project_api_key is missing"}, status=404)
            else:
                pass
            project       = ProjectDetails.objects.get(api_key = project_api_key)
            #project_id    = request.GET.get("project_id",None)
            obj           = Tags.objects.get(id=request.GET.get('id'),project = project)
            obj.delete()
            return JsonResponse({"message": "Tag deleted successfully"}, status=status.HTTP_200_OK)
        except (ProjectDetails.DoesNotExist,ProjectDetails.MultipleObjectsReturned,Tags.DoesNotExist,Tags.MultipleObjectsReturned) as e:
            if isinstance(e, ProjectDetails.DoesNotExist):
                return JsonResponse({"error": "Project details not found"}, status=404)
            elif isinstance(e, ProjectDetails.MultipleObjectsReturned):
                return JsonResponse({"error": "Multiple projects found with the same API Key"}, status=400)
            elif isinstance(e, Tags.DoesNotExist):
                return JsonResponse({"error": "Tag details not found"}, status=400)
            elif isinstance(e, Tags.MultipleObjectsReturned):
                return JsonResponse({"error": "Multiple Tags found with the same id"}, status=400)
        except Exception as e:
            print(str(e))
            print("======================== ERROR ==============================")
            return JsonResponse({"error": "Something went wrong!"}, status=500)
# ##############################################################################################################################################
# Section: CAMPAIGN 
# ##############################################################################################################################################     
# ### Subsection: CREATE CAMPAIGN ###   
@csrf_exempt
@api_view(['POST', 'GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def create_campaign(request):
    try:
        project       = ProjectDetails.objects.get(api_key = request.META.get('HTTP_WHATSAPP_PROJECT_KEY'))
        outlet_obj = outlet_details.objects.get(api_key = request.META.get('HTTP_API_KEY'))
        campaign_id = ""
        if request.method == 'POST':
            print(request.POST)
            try:
                # campaign_object = WhatsappCampaign.objects.get(id=request.POST.get("id"))
                try:
                    template_obj = TemplateDetails.objects.get(id=request.POST.get("template_id"))
                    template_id = template_obj.id
                except Exception as e:
                    print("==========>>>>1799", str(e))
                    template_obj = None
                    template_id = None
                    
                if request.POST.get("id"):
                    connection = mysql.connector.connect(
                        database=API_DB_NAME,
                        user=API_USER_NAME,
                        password=API_DB_PASSWORD
                    )
                    cursor = connection.cursor()
                    cursor.execute('''SELECT * FROM `xl2024_whatsapp_campaign_details` WHERE `id` = {0};'''.format(request.POST.get("id")))

                    campaign_data = dictfetchall(cursor)
                    print(campaign_data, "<<<<<<<<<<<<<<<<data")
                    cursor.close()
                    connection.close()
                
                    if len(campaign_data) > 0:
                        print("===============innnnnnn")

                        connection = mysql.connector.connect(
                            database=API_DB_NAME,
                            user=API_USER_NAME,
                            password=API_DB_PASSWORD
                        )
                        cursor = connection.cursor()
                        end_date_val = request.POST.get("end_date", "")
                        start_date_val = request.POST.get("start_date", "")
                        end_data_str = f"'{end_date_val}.000000'" if end_date_val else 'NULL'
                        start_data_str = f"'{start_date_val}.000000'" if start_date_val else 'NULL'
                        template_id_str = f"'{template_id}'" if template_id else 'NULL'
                        trigger =f"'{request.POST.get('trigger')}'" if request.POST.get('trigger') else 'NULL'
                        cursor.execute(
                            '''UPDATE `xl2024_whatsapp_campaign_details` SET `campaign_name` = '{1}', `campaign_type` = '{2}', `custom_json` = '{3}', `template_id` = {4}, `start_date` = {5}, `end_date` = {6}, `shop` = '{8}', `outlet_id` = '{9}', `trigger_details_id` = {10}  WHERE `xl2024_whatsapp_campaign_details`.`id` = {0};'''
                        .format(request.POST.get("id"), request.POST.get("campaign_name",""), request.POST.get("campaign_type",""), request.POST.get("custom_json",""), template_id_str, start_data_str, end_data_str, 0, request.POST.get("shop",""), outlet_obj.id, trigger))
                        connection.commit()
                        connection.close()

                else:
                    print("===============newwwwww")
                    campaign_object = WhatsappCampaign()
                    campaign_object.campaign_name = request.POST.get("campaign_name","")
                    campaign_object.campaign_type = request.POST.get("campaign_type","")
                    campaign_object.custom_json = request.POST.get("custom_json","")
                    campaign_object.trigger_details_id = request.POST.get("trigger","")
                    campaign_object.template = template_obj
                    if request.POST.get("start_date"):
                        campaign_object.start_date = request.POST.get("start_date", None)
                    if request.POST.get("end_date"):
                        campaign_object.end_date = request.POST.get("end_date", "")
                    campaign_object.is_draft = 0
                    campaign_object.shop = request.POST.get("shop","")
                    campaign_object.outlet = outlet_obj
                    campaign_object.project = project
                    campaign_object.save()
                    campaign_id = campaign_object.id
                    
            except Exception as e:
                print(str(e), "<<<<<<<<<<<<<<<<<<<<<<<<<<<<<1832")

            return JsonResponse({'message': 'saved successfully', 'data': {'id': campaign_id}}, status=200)
        if request.method == 'GET':
            try:
                campaign_object = WhatsappCampaign.objects.get(id=request.GET.get("campaign_id")) 
            except:
                campaign_object = []
                serialized_obj = []
            else:
                serialized_obj = WhatsappCampaginSerializer(campaign_object).data
            
            return JsonResponse({'data': serialized_obj}, status=200)
    except (ProjectDetails.DoesNotExist,ProjectDetails.MultipleObjectsReturned,WhatsappCampaign.DoesNotExist,WhatsappCampaign.MultipleObjectsReturned) as e:
        if isinstance(e, ProjectDetails.DoesNotExist):
            return JsonResponse({"error": "Project details not found"}, status=404)
        elif isinstance(e, ProjectDetails.MultipleObjectsReturned):
            return JsonResponse({"error": "Multiple projects found with the same API Key"}, status=400)
        elif isinstance(e, WhatsappCampaign.DoesNotExist):
            return JsonResponse({"error": "WhatsappCampaign details not found"}, status=400)
        elif isinstance(e, WhatsappCampaign.MultipleObjectsReturned):
            return JsonResponse({"error": "Multiple WhatsappCampaign found with the same id"}, status=400)
    # except Exception as e:
    #     print(str(e))
    #     print("======================== ERROR ==============================")
    #     return JsonResponse({"error": "Something went wrong!"}, status=500)


# ### Subsection: GET CAMPAIGN ###  
@csrf_exempt
@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def view_campaign(request):
    try:
        if request.method == "POST":
            outlet_api_key          = request.META.get('HTTP_API_KEY')
            project_api_key         = request.META.get('HTTP_WHATSAPP_PROJECT_KEY')
            if outlet_api_key is None :
                return JsonResponse({"error": "outlet_api_key is missing"}, status=404)
            elif project_api_key is None :
                return JsonResponse({"error": "project_api_key is missing"}, status=404)
            else:
                pass
            outlet_obj      = outlet_details.objects.get(api_key = outlet_api_key)
            project_obj     = ProjectDetails.objects.get(api_key = project_api_key)
            datatables      = request.POST
            start           = int(datatables.get('page'))
            length          = int(datatables.get('size'))
            over_all_search = datatables.get('searchValue')
            advance_filter  = Q()
            whatsapp_campaign_instance = WhatsappCampaign.objects.filter(outlet=outlet_obj,project = project_obj,is_trash=False).filter(advance_filter).values(
                whatsapp_id                 = F("id"),
                whatsapp_campaign_name      = F("campaign_name"),
                whatsapp_trigger            = F("trigger_details__topic"),
                whatsapp_trigger_id         = F("trigger_details__id"),
                whatsapp_campaign_type      = F("campaign_type"),
                whatsapp_custom_json        = F("custom_json"),
                whatsapp_template           = F("template__templateName"),
                whatsapp_template_id        = F("template__templateId"),
                whatsapp_created_at         = F("created_at"),
                whatsapp_campaign_clicks    = F("campaign_clicks"),
                whatsapp_campaign_sent      = F("campaign_sent"),
                whatsapp_campaign_delivered = F("campaign_delivered"),
                whatsapp_campaign_failed    = F("campaign_failed"),
                whatsapp_campaign_read      = F("campaign_read"),
                whatsapp_start_date         = F("start_date"),
                whatsapp_end_date           = F("end_date"),
                whatsapp_is_draft           = F("is_draft"),
                whatsapp_is_active          = F("is_active"),
                whatsapp_is_trash           = F("is_trash"),
                whatsapp_shop               = F("shop"),
                whatsapp_outlet             = F("outlet")
            ).order_by('-created_at')
            campaign_obj_count = whatsapp_campaign_instance.count()
            paginator          = Paginator(whatsapp_campaign_instance, length)

            try:
                object_list = paginator.page(start).object_list
            except (PageNotAnInteger, EmptyPage):
                object_list = paginator.page(1).object_list
            response = {
                'whatsapp_count': campaign_obj_count,
                "whatsapp"      : list(object_list)
            }
            return JsonResponse(response, status=200)
    except (outlet_details.DoesNotExist,ProjectDetails.DoesNotExist,ProjectDetails.MultipleObjectsReturned,outlet_details.MultipleObjectsReturned) as e:
        if isinstance(e, outlet_details.DoesNotExist):
            return JsonResponse({"error": "Invalid API Key outlet details not found"}, status=404)
        elif isinstance(e, outlet_details.MultipleObjectsReturned):
                return JsonResponse({"error": "Multiple outlets found with the same API Key"}, status=400)
        elif isinstance(e, ProjectDetails.DoesNotExist):
            return JsonResponse({"error": "Project details not found"}, status=404)
        elif isinstance(e, ProjectDetails.MultipleObjectsReturned):
                return JsonResponse({"error": "Multiple projects found with the same API Key"}, status=400)
    except Exception as e:
        print(str(e))
        print("======================== ERROR ==============================")
        return JsonResponse({"error": "Something went wrong!"}, status=500)

# ### Subsection: CHANGE STATUS CAMPAIGN ###  
@csrf_exempt
@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def change_campaign_status(request):

    if request.method == "POST":
        outlet_obj = outlet_details.objects.get(api_key = request.META.get('HTTP_API_KEY'))
        project       = ProjectDetails.objects.get(api_key = request.META.get('HTTP_WHATSAPP_PROJECT_KEY'))
        trigger = request.POST.get('trigger')
        try:
            campaign_object = WhatsappCampaign.objects.get(id=request.POST.get("id"))
        except Exception as e:
            return JsonResponse({'message': 'Campaign Not Found'}, status=404)
        else:
            status = 1 if request.POST.get('status') == 'true' else 0
            
            if status:
                connection = mysql.connector.connect(
                    database=API_DB_NAME,
                    user=API_USER_NAME,
                    password=API_DB_PASSWORD
                )
                cursor = connection.cursor()
                if request.POST.get('check_status') == "1" or request.POST.get('check_status') == 1:
                    sql=f"SELECT * from `xl2024_whatsapp_campaign_details` WHERE `trigger_details_id`='{campaign_object.trigger_details.id}' and `outlet_id`='{outlet_obj.id}' and `project_id` = {project.id} and not `id`='{campaign_object.id}'and `is_active`=1;"
                    print(sql)
                    cursor.execute(sql)
                    data=dictfetchall(cursor)
                    # cursor.execute(sql)
                    
                    if data:
                        cursor.close()
                        connection.close()
                        return JsonResponse({'message':'Conflicting Campaign Exists','data':data},status=200)
                    
                
                sql=f"UPDATE `xl2024_whatsapp_campaign_details` SET `is_active` = 0 where `trigger_details_id`='{campaign_object.trigger_details.id}' and `project_id` = {project.id} and `outlet_id`='{outlet_obj.id}';"
                print(sql)
                cursor.execute(sql)
                connection.commit()
                cursor.close()
                connection.close()

            print(campaign_object.campaign_type, "campaign_objectcampaign_objectcampaign_objectcampaign_object")
            
            campaign_object.is_active = status
            campaign_object.save()
            # json_data = json.loads(campaign_object.custom_json).get('converted_flow_data')
            # print(json_data, "====================SelectedTrigger")
            shop = request.POST.get('shop')
            webhook_response = ""
            try:
                shopify_obj = ShopifyXirclsApp.objects.get(shop=shop,app="whatsapp")
            except Exception as e:
                print(str(e), "==============1947")
                return JsonResponse({'message': 'Shopify Details not Found'}, status=500)
            else:
                if campaign_object.campaign_type == "automated-message" and campaign_object.trigger_details.platform == "Shopify":
                    if status:
                        remove_webhook(campaign_object.trigger_details.topic,shopify_obj)
                        webhook_response=add_webhook(campaign_object.trigger_details.topic,shopify_obj)
                    else:
                        webhook_response=remove_webhook(campaign_object.trigger_details.topic,shopify_obj)
                    

                return JsonResponse({'message': 'Status changed successfully', 'response': str(webhook_response)}, status=200)


@csrf_exempt
@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def campaign_view_data(request):
    try:

        connection = mysql.connector.connect(
            database=API_DB_NAME,
            user=API_USER_NAME,
            password=API_DB_PASSWORD
        )
        cursor = connection.cursor()
        cursor.execute('''
            SELECT
                t.templateId,
                t.id,
                t.templateName,
                t.template_total_sent,
                t.template_delivered,
                t.template_failed,
                t.template_read,
                t.template_sent,
                t.template_delivered,
                m.message_id,
                m.created_at,
                m.reciever,
                COUNT(m.timestamp_sent) AS sent_count,
                COUNT(m.timestamp_delivered) AS delivered_count,
                COUNT(m.timestamp_read) AS read_count,
                COUNT(m.timestamp_failed) AS failed_count,
                m.remark
            FROM
                `xl2024_Messagelog_details` m
            JOIN `xl2024_template_details` t ON
                m.template_id = t.id
            WHERE
                m.campaign_id = {0}
            GROUP BY
                m.template_id
            ORDER BY
                m.id
            DESC;
        '''.format(request.POST.get('campaign_id')))

        campaign_data = dictfetchall(cursor)
        print(campaign_data, "<<<<<<<<<<<<<<<<data")
        cursor.close()
        connection.close()

        return JsonResponse({"data": campaign_data}, status=200)
    except Exception as e:
        print(str(e))
        print("======================== ERROR ==============================")
        return JsonResponse({"error": "Something went wrong!"}, status=500)
   

@csrf_exempt
@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def delete_campaigns(request):
    if request.method == "POST":
        id_list=request.POST.getlist('id')
        try: 
            shop=request.POST.get('shop')
            shopify_obj = ShopifyXirclsApp.objects.get(shop=shop,app="whatsapp")
        except:
            return JsonResponse({'message':'Shop Not Found'},status=500)
        campaign_objects=WhatsappCampaign.objects.filter(id__in=id_list)
        active_campaigns=campaign_objects.filter(is_active=1)
        for triggers in active_campaigns.values('trigger'):
            trigger=triggers.get('trigger')
            remove_webhook(trigger,shopify_obj)
        campaign_objects.update(is_trash=True, is_active=False)
        return JsonResponse({'message':'Campaigns Deleted Successfully'},status=200)

@csrf_exempt
def campaign_details_list(request):
    if request.method == "GET":
        campagin_obj = ""
        try:
            outlet_api_key          = request.META.get('HTTP_API_KEY')
            project_api_key         = request.META.get('HTTP_WHATSAPP_PROJECT_KEY')
            if outlet_api_key is None :
                return JsonResponse({"error": "outlet_api_key is missing"}, status=404)
            elif project_api_key is None :
                return JsonResponse({"error": "project_api_key is missing"}, status=404)
            else:
                pass
            outlet_obj    = outlet_details.objects.get(api_key = outlet_api_key)
            project_obj   = ProjectDetails.objects.get(api_key = project_api_key)
        except:
            outlet_obj = None
        finally:
            campagin_obj      = WhatsappCampaign.objects.filter(outlet_id=outlet_obj.id, project_id = project_obj.id)
            serializered_data = WhatsappCampaginSerializer(campagin_obj, many=True)
    return JsonResponse({"data": serializered_data.data})

# ##############################################################################################################################################
# Section: WIDGET 
# ##############################################################################################################################################     
# ### Subsection: WIDGET CRUD ###   
@csrf_exempt
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def widgets_view(request):
    try:
        outlet_instance = None
        outlet_api_key   = request.META.get('HTTP_API_KEY')
        if outlet_api_key is None :
                return JsonResponse({"error": "outlet_api_key is missing"}, status=404)
        outlet_instance = outlet_details.objects.get(api_key = outlet_api_key)
        if request.method == 'POST':

            data = request.POST
            custom_json = data.get('custom_json')
            is_active = data.get('is_active', False)
            is_draft = data.get('is_draft', False)
            platform = data.get('platform')
            shop = data.get('shop')

            widget, created = widgets_data.objects.get_or_create(
                outlet=outlet_instance, 
                shop=shop
            )

            if not created:
                # Update existing widget
                widget.custom_json = custom_json
                widget.is_active = is_active
                widget.is_draft = is_draft
                widget.platform = platform or widget.platform
                widget.save()
                message = 'Widget Found, Hence Modified - Success'
            else:
                message = 'Created New Widget - Success'


            return JsonResponse({
                'message': message,
                'data': {
                    'custom_json': widget.custom_json,
                    'outlet': widget.outlet.id if widget.outlet else None,
                    'shop': widget.shop,
                    'is_active': widget.is_active,
                    'is_draft': widget.is_draft,
                    'platform': widget.platform
                }
            })


        elif request.method == 'DELETE':


            data = request.POST
            shop = data.get('shop')
            widget = widgets_data.objects.get(outlet=outlet_instance, shop=shop)
            widget.delete()
            return JsonResponse({'message': 'Widget deleted successfully'})

        elif request.method == 'GET':
            shop = request.GET.get('shop') 
            if not shop:
                return JsonResponse({'message': 'Shop is required'}, status=400)


            widgets = widgets_data.objects.filter(shop=shop, outlet=outlet_instance)
            # Serialize widgets data
            widgets_list = []
            for widget in widgets:
                widgets_list.append({
                    'custom_json': widget.custom_json,
                    'outlet': widget.outlet.id if widget.outlet else None,
                    'shop': widget.shop,
                    'is_active': widget.is_active,
                    'is_draft': widget.is_draft,
                    'platform': widget.platform
                })

            return JsonResponse({'widgets': widgets_list})
    except (outlet_details.DoesNotExist,outlet_details.MultipleObjectsReturned,widgets_data.DoesNotExist,widgets_data.MultipleObjectsReturned) as e:
        if isinstance(e, outlet_details.DoesNotExist):
            return JsonResponse({"error": "Invalid API Key outlet details not found"}, status=404)
        elif isinstance(e, outlet_details.MultipleObjectsReturned):
                return JsonResponse({"error": "Multiple outlets found with the same API Key"}, status=400)
        if isinstance(e, widgets_data.DoesNotExist):
            return JsonResponse({"error": "widgets data not found"}, status=404)
        elif isinstance(e, widgets_data.MultipleObjectsReturned):
                return JsonResponse({"error": "Multiple widgets found with the same oulet"}, status=400)
    except Exception as e:
        print(str(e))
        print("======================== ERROR ==============================")
        return JsonResponse({"error": "Something went wrong!"}, status=500)

# ##############################################################################################################################################
# Section: FLOW BUILDER 
# ##############################################################################################################################################     
 
# ### Subsection: CHECK CUSTOMER ACTIVE FLOW AND CONTINUE ###       
class ContinueFlow:
    def __init__(self, **kwargs):
        self.entry              = kwargs.get('entry', {})
        changes                 = self.entry.get('changes', [{}])[0]
        value                   = changes.get('value', {})
        messages                = value.get('messages', [{}])[0]
        contacts                = value.get('contacts', [{}])[0]
        self.reply_json_data    = messages.get('interactive',{}).get('nfm_reply',{}).get('response_json',None)
        self.messages_from      = messages.get("from", "")
        self.customer_message   = messages
        self.customer_number    = contacts.get('wa_id', '')
        self.message_id         = messages.get('context', {}).get('id', None)
        self.reply_btn_text     = messages.get('button', {}).get('text', None) if messages.get('button', {}).get('text', None) is not None else messages.get('interactive',{}).get('button_reply', {}).get('id', None) if messages.get('interactive',{}).get('button_reply', {}).get('id', None) else messages.get('interactive',{}).get('list_reply', {}).get('id', None)
        self.outlet_instance    = kwargs.get('outlet_instance')
        
    def trigger_flow(self):
        kwargs = {'create': False}
        if self.reply_json_data is not None:
            self.reply_btn_text = self.message_id
            self.json_data = json.loads(self.reply_json_data)
        else:
            self.json_data = None
        flow_check = Flowcheck(
            phone=self.messages_from,
            reply_btn_text=self.reply_btn_text,
            outlet_instance  = self.outlet_instance,
            form_data = self.json_data
        )
        customer_flow_instance = flow_check.check_customer_flow_log(**kwargs)
        if customer_flow_instance is not None:
            
            print(customer_flow_instance,"========================================step2")
            customer_flow_instance = flow_check.check_flow_log(customer_flow_instance,self.json_data)
            if self.message_id is not None and self.json_data is not None:
                messagelog_instance = MessageLog.objects.get(message_id=self.message_id)
                try:
                    formdata = eval(customer_flow_instance.form_data)
                except:
                    formdata = customer_flow_instance.form_data
                if formdata is None:
                    formdata = []
                print(formdata,"============================formdatabefore")
                formdata = formdata if len(formdata) > 0 else []
                print(formdata,"============================formdataafter")
                form_data_append = dict(self.json_data)
                form_data_append['form_id'] = messagelog_instance.form.id
                formdata.append(form_data_append)
                customer_flow_instance.form_data = formdata
                customer_flow_instance.save()
                customer_flow_instance = CustomerFlowLog.objects.get(id = customer_flow_instance.id)
            print(customer_flow_instance,"========================================step3")
        if customer_flow_instance is not None:
            print(customer_flow_instance,"========================================step4")
            flow_check.trigger_action(customer_flow_instance,self.json_data)
        return True           

# ### Subsection: FLOW SENDING  ###       
class Flowcheck:
    def __init__(self, **kwargs):
        self.trigger         = kwargs.get('trigger', None)
        self.outlet_instance = kwargs.get('outlet_instance')
        self.email           = kwargs.get('email', None)
        self.phone           = kwargs.get('phone', None)
        self.reply_btn_text  = kwargs.get('reply_btn_text', None)
        self.customer_data   = kwargs.get('customer_data', None)
        self.next_node       = kwargs.get('next_node', None)
        self.form_data       = kwargs.get('form_data',None)
        self.brodcast_flow   = kwargs.get('brodcast_flow',False)

    def check_active_campaign(self):
        campaign_instance = WhatsappCampaign.objects.filter(is_active=True, outlet=self.outlet_instance, trigger=self.trigger)
        if campaign_instance:
            return campaign_instance
        return None

    def update_value(self, customer_data,phone_no):
        self.customer_data = customer_data
        self.phone         = phone_no
        return True

    def check_customer_flow_log(self, **kwargs):
        
        if kwargs.get('create', False):
            self.continue_flow = True
            print(kwargs,"----------------------------")
            # Assuming you want to create multiple instances if not found
            customer_flow_instance = []
            for campaign_instance in kwargs.get('campaign_instances', []):
                print(campaign_instance,"====================")
                try:
                    node_payload = eval(json.loads(campaign_instance.custom_json).get('converted_flow_data'))
                except:
                    node_payload = json.loads(campaign_instance.custom_json).get('converted_flow_data')
                next_node_payload = node_payload[0]
                if self.brodcast_flow:
                    pass
                else:
                    try:
                        if next_node_payload.get('webhook_condition',None) is not None:
                            print(next_node_payload.get('webhook_condition'),"======================next_node_payload.get('webhook_condition')")
                            print(self.customer_data,"======================next_node_payload.get('webhook_condition')")
                            for key, value in next_node_payload.get('webhook_condition').items():
                                try:
                                    print(self.customer_data[0][key],"===================================customer_data[0][key]")
                                    print(value,"===================================customer_data[0][key]")
                                    print(any(item in value for item in self.customer_data[0][key]),"===================================self.customer_data[0][key][0] in value")
                                    if any(item in value for item in self.customer_data[0][key]):
                                        print("ooooooooooooooooooooooooooooooye")
                                        self.continue_flow = True
                                        pass
                                    else:
                                        print("returned None because there is no cod")
                                        return None
                                except Exception as e:
                                    print(str(e),"=========================error")
                                    print("returned None because there is no None2")
                                    return None
                        if next_node_payload.get('trigger_condition',None) is not None:
                        
                            print(next_node_payload.get('trigger_condition'),"======================next_node_payload.get('webhook_condition')")
                            for key, value in next_node_payload.get('trigger_condition').items():
                                message_body = kwargs.get('message_body')
                                if key == 'equal':
                                    if message_body in value:
                                        self.continue_flow = True
                                        break
                                    
                                    else:
                                        pass
                                elif key == 'starts_with':
                                    if any(message_body.startswith(start) for start in value):
                                        self.continue_flow = True
                                        break
                                    else:
                                        pass
                                elif key == 'include':
                                    if any(keyword in message_body for keyword in value):
                                        self.continue_flow = True
                                        break
                                    else:
                                        self.continue_flow = False
                    except:
                        pass
                if self.continue_flow:
                    first_instance = CustomerFlowLog.objects.create(
                        phone_no=self.phone,
                        campaign=campaign_instance,
                        is_active=True,
                        customer_data=self.customer_data,
                        current_node = 0,
                        current_node_json= json.dumps(next_node_payload),
                        outlet = self.outlet_instance
                    )
                    next_instance_node = next_node_payload.get('conditional_node').get('next_node')
                    instance = CustomerFlowLog.objects.create(
                        phone_no=self.phone,
                        campaign=campaign_instance,
                        is_active=True,
                        customer_data=self.customer_data,
                        current_node = next_instance_node,
                        current_node_json= json.dumps(node_payload[next_instance_node]),
                        outlet = self.outlet_instance
                    )
                    customer_flow_instance.append(instance)
                    self.next_node = next_instance_node
                    break
        else:
            customer_flow_instance = CustomerFlowLog.objects.filter(outlet = self.outlet_instance,phone_no=self.phone, is_active=True)
        
        print(customer_flow_instance,"========================================customer_flow_instance1")
        return customer_flow_instance

    def check_flow_log(self, customer_flow_instances,form_data):
        if not customer_flow_instances:
            return None
        for customer_flow_instance in customer_flow_instances.order_by("-id"):
            try:
                payload_edit = json.loads(customer_flow_instance.current_node_json)
                json_data = payload_edit.get('conditional_node',{})
                if json_data.get(self.reply_btn_text):
                    self.next_node = json_data.get(self.reply_btn_text)
                    if payload_edit.get('sub_condition',None) is not None:
                        print('trueeeeeeeeeeeeeeeeeeeeeeeesub_contion')
                        form_data = dict(form_data)
                        sub_condition   = payload_edit.get('sub_condition')
                        print(sub_condition,'trueeeeeeeeeeeeeeeeeeeeeeeesub_contion')
                        selected_option = form_data.get(sub_condition['select_option'])
                        print(selected_option,'trueeeeeeeeeeeeeeeeeeeeeeeesub_contion')
                        sub_condition = sub_condition.get('next_node')
                        print(sub_condition,"==================================sub_condition")
                        print(sub_condition.get(selected_option, None),"==================================sub_condition")
                        self.next_node  = sub_condition.get(selected_option) if sub_condition.get(selected_option, None) is not None else sub_condition.get('notmatch')
                        print(self.next_node,"==================================next_mode")
                    
                    self.selected_option = [{}]
                    for key, value in json_data.items():
                        self.selected_option[0].update({key:True}) if key == self.reply_btn_text else self.selected_option[0].update({key:False})
                    customer_log = CustomerFlowReport.objects.filter(customer_log=customer_flow_instance.id).last()
                    customer_log.selected_option = self.selected_option
                    customer_log.save()
                    flow_report, created  = CampaignFlowReport.objects.get_or_create(
                        node=payload_edit.get('current_node'),
                        campaign=customer_log.campaign,
                        outlet=customer_log.campaign.outlet,
                        defaults={'node_json':json.dumps(payload_edit),'trigger_on_report' : None}
                    )
                    try:
                        selected_condition_report = json.loads(flow_report.selected_option_report)
                    except:
                        selected_condition_report = flow_report.selected_option_report
                    print(selected_condition_report,json_data,'iiiiiiii')
                    if selected_condition_report is None:
                        selected_condition_report = { v: 0  for k, v in enumerate(json_data)}
                       
                    print(selected_condition_report,"============================+++++")
                    if self.reply_btn_text.startswith("wamid."):
                        count = selected_condition_report['next_node'] + 1
                        selected_condition_report['next_node'] = count 
                    else:
                        count = selected_condition_report[self.reply_btn_text] + 1
                        selected_condition_report[self.reply_btn_text] = count 
                    flow_report.selected_option_report = json.dumps(selected_condition_report)
                    flow_report.save()
                    return customer_flow_instance
            except Exception as e:
                print(str(e),"=====================================except")
                pass
        
        return None
    
    def sub_action(self, **kwargs):
        try:
            shop            = kwargs.get('shop',None)
            url             = kwargs.get('url')
            customer_data   = kwargs.get('customer_data')
            method          = kwargs.get('method')
            payload         = kwargs.get('payload',None)
            apps_url = f'{APP_DOMAIN}/api/v1/add/shop_details/?shop={shop}&app=whatsapp'
            apps_payload = {
                'app' :'whatsapp',
                'shop': shop
            }
            apps_headers = {
                
            }
            apps_response = requests.request("GET", apps_url, headers=apps_headers, data=apps_payload).json()
            
            if not apps_response:
                return False
            
            access_token = apps_response['response'][0]['access_token']
            url = url.format(id=customer_data.get('id'))
            url = f"https://{shop}/admin/api/{SHOPIFY_API_YEAR}/{url}"
            if method == "DELETE":
                headers = {
                    "X-Shopify-Access-Token": access_token
                }
            else:
                headers = {
                    "X-Shopify-Access-Token": access_token,
                    "Content-Type": "application/json"
                }
            def update_json(json_obj, update_dict):
                if isinstance(json_obj, dict):
                    for key, value in json_obj.items():
                        if isinstance(value, dict):
                            update_json(value, update_dict)
                        elif isinstance(value, list):
                            for item in value:
                                update_json(item, update_dict)
                        else:
                            if key == 'tags':
                                json_obj[key] =  update_dict.get(key, value) + json_obj['tags'] if len(str(update_dict.get(key, value))) > 0 else value
                            else:
                                json_obj[key] =  update_dict.get(key, value) if len(str(update_dict.get(key, value))) > 0 else value
                return json_obj

            if payload is not None:
                try:
                    json_data = json.loads(payload)
                    json_data = update_json(json_data, customer_data)
                    response = requests.request(method, url, headers=headers, data=json.dumps(json_data))
                except:
                    response = requests.request(method, url, headers=headers)
            else:
                response = requests.request(method, url, headers=headers)
            
            return True
        except Exception as e:
            return False
                          
    def trigger_action(self, customer_flow_instance, json_data = None):
        try:
            customer_list = eval(customer_flow_instance.customer_data)
        except:
            customer_list = customer_flow_instance.customer_data
        node_payload              = json.loads(customer_flow_instance.campaign.custom_json).get('converted_flow_data')
        self.node_index           = {node['current_node']:index for index, node in enumerate(node_payload)}
        print(self.node_index,"=================================node_index")
        next_node_payload         = node_payload[self.node_index[self.next_node]]
        action                    = next_node_payload.get('action')
        self.campaign_instance    = customer_flow_instance.campaign
        customer_flow_instance_id = customer_flow_instance.id
        self.customerflow_report  = CustomerFlowReport.objects.create(
            customer_log  = customer_flow_instance,
            phone_no=self.phone,
            campaign=self.campaign_instance,
            travelled_node = self.next_node,
            travelled_node_json = json.dumps(next_node_payload),
            selected_option = next_node_payload.get('conditional_node'),
            trigger_on = self.trigger_option if self.next_node == 0 else None,
            outlet = self.campaign_instance.outlet,
            form_data = json.dumps(self.form_data) if self.form_data is not None else None
        )
        print(next_node_payload.get('delay_condition',{}).get('delay_type',None))
        if next_node_payload.get('delay_condition',{}).get('delay_type',None) is not None:
            print(next_node_payload.get('delay_condition',{}).get('delay_type',None),"===================in")
            delay_condition = next_node_payload.get('delay_condition')
            delay = int(delay_condition.get('delay', 0))
            delay_type = delay_condition.get('delay_type', None)
            if delay_type == 'minutes':
                eta = timezone.now() + timedelta(minutes=delay)
            elif delay_type == 'seconds':
                eta = timezone.now() + timedelta(seconds=delay)
            elif delay_type == 'hours':
                eta = timezone.now() + timedelta(hours=delay)
            elif delay_type == 'days':
                eta = timezone.now() + timedelta(days=delay)
            else:
                eta = None

            schedule_kwargs = {
                'customer_flow_log_id': customer_flow_instance.id,
            }
            if eta is not None:
                eta = eta.astimezone(timezone.utc).replace(tzinfo=None)
                eta = timezone.make_aware(eta)
            print(eta,'===========================================')
            scheduled_flow.apply_async(
                kwargs=schedule_kwargs,
                eta=eta
            )
        if next_node_payload.get('sub_action',None) is not None:
            for sub_action_data in next_node_payload.get('sub_action'):
                customer_dict = CustomerDict()
                data_dict     = customer_dict.create_data_dict(customer_list[0])
                if json_data is not None:
                    data_dict                          = customer_dict.update_customer(data_dict,json_data)
                    append_data_customer_report        = self.customerflow_report.form_data.append(json_data) if self.customerflow_report.form_data is not None else [json_data]
                    self.customerflow_report.form_data = append_data_customer_report
                    self.customerflow_report.save()
                kwargs = {
                    'customer_data' : data_dict,
                    'url' : sub_action_data.get('url'),
                    'method' :sub_action_data.get('method'),
                    'payload' :sub_action_data.get('payload',None),
                    'shop' : customer_flow_instance.outlet.web_url
                }
                resp = self.sub_action(**kwargs) 
                customer_list = [data_dict]
                customer_flow_instance = CustomerFlowLog.objects.get(id=customer_flow_instance_id)
                customer_flow_instance.customer_data = customer_list
                customer_flow_instance.save()
                try:
                    customer_list = eval(customer_flow_instance.customer_data)
                except:
                    customer_list = customer_flow_instance.customer_data
        if action.get('app') == 'whatsapp': 
            message_type = action.get('type','')
            if message_type == 'service_message':
                kwargs   = json.loads(action.get('payload'))
                kwargs   = dict(kwargs)
                customer_dict = CustomerDict()
                data_dict = customer_dict.create_data_dict(customer_list[0])
                reciever = customer_flow_instance.phone_no
                kwargs['data_dict'] = data_dict
                kwargs['campaign_instance'] = self.campaign_instance
                kwargs['project_id'] = self.campaign_instance.project.id
                fun_reps , response, self.context_payload = send_service_message(self.campaign_instance.outlet.id,reciever, **kwargs)
                self.waba_id = response.get('messages', [{}])[0].get('id')
            if message_type == 'template_message':
                template_instance = TemplateDetails.objects.get(id=action.get('template_id'))
                trigger_condition = False

                msg_send = MessageSender(
                    button_variables = None,
                    template_instance=template_instance,
                    campaign_id=self.campaign_instance.id,
                    trigger = trigger_condition
                )
                # print(msg_send.send_messages(customer_list,),'+===============')
                fun_repsonse, response, self.context_payload = msg_send.send_messages(customer_list,)
                # print(message_id,"==========================message_id")
                self.waba_id = response.get('messages', [{}])[0].get('id')
            if message_type == "interactive_message":
                print(self.node_index[self.next_node],"===========================")
                print(next_node_payload,'=============================')
                print(action,"======================================")
                print(action.get('payload'),"===================")
                template_instance = TemplateDetails.objects.get(id=action.get('payload').get('id'))
                msg_send = InteractiveMessage(
                    template_instance = template_instance,
                    trigger = False,
                    campaign_instance=self.campaign_instance
                )
                interactive_response, self.context_payload = msg_send.send_messages(customer_list,)
                print(interactive_response,"===============================asdasd")
                self.waba_id = interactive_response.get('messages', [{}])[0].get('id')
                # print(waba_id,"==================================")
                
                if next_node_payload.get('change_conditional_node', None) is not None:
                    conditional_node = next_node_payload['conditional_node']
                    # Collect items to change
                    items_to_change = {}
                    for items, value in conditional_node.items():
                        if items == "next_node":
                            items_to_change[self.waba_id] = value

                    # Apply changes outside the loop
                    conditional_node.update(items_to_change)
                    next_node_payload['conditional_node'] = conditional_node

                    print(next_node_payload,"======================a")

        self.update_customer_flow_log(customer_flow_instance, next_node_payload)
        return True

    def update_customer_flow_log(self, customer_flow_instance, next_node_payload):
        customer_flow_instance.current_node_json = json.dumps(next_node_payload)
        customer_flow_instance.current_node      = self.next_node
        customer_flow_instance.is_active         = False if 'status' in next_node_payload else True
        customer_flow_instance.save()
        messagelog_instance                     = MessageLog.objects.get(message_id=self.waba_id)
        customerflow_report                     = CustomerFlowReport.objects.get(id = self.customerflow_report.id)
        payload_edit                            = json.loads(customerflow_report.travelled_node_json)
        payload_edit['action']['payload']       = json.dumps(self.context_payload)
        customerflow_report.message_log         = messagelog_instance
        customerflow_report.travelled_node_json = json.dumps(payload_edit)
        customerflow_report.save()
        flow_report, created  = CampaignFlowReport.objects.get_or_create(
            node=self.node_index[self.next_node],
            campaign=self.campaign_instance,
            outlet=self.campaign_instance.outlet,
            defaults={'node_json':json.dumps(payload_edit),'trigger_on_report' : None}
        )
        self.trigger_condition_payload = json.loads(customerflow_report.travelled_node_json).get('trigger_condition',None)
        if self.trigger_condition_payload is not None and self.next_node == 0:
            print('iiiiiiii')
            try:
                trigger_condition_report = json.loads(flow_report.trigger_on_report)
            except:
                trigger_condition_report = flow_report.trigger_on_report
            print(trigger_condition_report,'iiiiiiii')
            if trigger_condition_report is None:
                trigger_condition_report = {
                    k: { vl: 0 for it, vl in enumerate(v)} for k, v in self.trigger_condition_payload.items()
                }
            item_trigger_selected, value_trigger_selected = next(iter(self.trigger_option[0].items()))
            count = trigger_condition_report[item_trigger_selected][value_trigger_selected] + 1
            print(count,"============================count")
            trigger_condition_report[item_trigger_selected][value_trigger_selected] = count 
            flow_report.trigger_on_report = json.dumps(trigger_condition_report)
        print(False if 'status' in next_node_payload else True,"======================================status")
        if (True if 'status' in next_node_payload else False):
            print('iiiiiiii')
            try:
                status_conditon_report = json.loads(flow_report.selected_option_report)
            except:
                status_conditon_report = flow_report.selected_option_report
            print(status_conditon_report,'iiiiiiii')
            if status_conditon_report is None:
                status_conditon_report = {
                    'status' : 0
                }
            stat_count = status_conditon_report['status'] + 1
            status_conditon_report['status'] = stat_count 
            flow_report.selected_option_report = json.dumps(status_conditon_report)
        flow_report.save()
        return True

# ###FLOW REPORTS GET SINGLE CUSTOMER###
class FlowReport(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            outlet_obj = outlet_details.objects.get(api_key=request.META.get('HTTP_API_KEY'))
            project_obj = ProjectDetails.objects.get(api_key=request.META.get('HTTP_WHATSAPP_PROJECT_KEY'))
            
            customer_report_log_instance = CustomerFlowReport.objects.filter(
                customer_log__id=request.GET.get('customer_flow_id'),
                campaign__project=project_obj,
                outlet=outlet_obj
            )
            print(request.GET.get('customer_flow_id'),customer_report_log_instance,"===========================customer_report")
            
            customer_report_serializers = CustomerReportSerializers(customer_report_log_instance, many=True)
            return JsonResponse({'data': customer_report_serializers.data, 'success': True}, status=200)
        except Exception as e:
            return JsonResponse({'message': str(e), 'success': False}, status=500)
        
    def post(self, request):
        try:
            outlet_obj = outlet_details.objects.get(api_key=request.META.get('HTTP_API_KEY'))
            project_obj = ProjectDetails.objects.get(api_key=request.META.get('HTTP_WHATSAPP_PROJECT_KEY'))
            
            customer_report_log_instance = CampaignFlowReport.objects.filter(
                campaign__id=request.POST.get('campaign_id'),
                outlet=outlet_obj
            )
            
            
            customer_report_serializers = CampaignFlowReportSerializers(customer_report_log_instance, many=True)
            return JsonResponse({'data': customer_report_serializers.data, 'success': True}, status=200)
        except Exception as e:
            return JsonResponse({'message': str(e), 'success': False}, status=500)
            
# ##############################################################################################################################################
# Section: FLOW BUILDER 
# ##############################################################################################################################################     
 
# ### Subsection: CHECK CUSTOMER ACTIVE FLOW AND CONTINUE ###       
class ContinueFlow:
    def __init__(self, **kwargs):
        self.entry              = kwargs.get('entry', {})
        changes                 = self.entry.get('changes', [{}])[0]
        value                   = changes.get('value', {})
        messages                = value.get('messages', [{}])[0]
        contacts                = value.get('contacts', [{}])[0]
        self.reply_json_data    = messages.get('interactive',{}).get('nfm_reply',{}).get('response_json',None)
        self.messages_from      = messages.get("from", "")
        self.customer_message   = messages
        self.customer_number    = contacts.get('wa_id', '')
        self.message_id         = messages.get('context', {}).get('id', None)
        self.reply_btn_text     = messages.get('button', {}).get('text', None) if messages.get('button', {}).get('text', None) is not None else messages.get('interactive',{}).get('button_reply', {}).get('id', None) if messages.get('interactive',{}).get('button_reply', {}).get('id', None) else messages.get('interactive',{}).get('list_reply', {}).get('id', None)
        self.outlet_instance    = kwargs.get('outlet_instance')
        
    def trigger_flow(self):
        kwargs = {'create': False}
        if self.reply_json_data is not None:
            self.reply_btn_text = self.message_id
            self.json_data = json.loads(self.reply_json_data)
        else:
            self.json_data = None
        flow_check = Flowcheck(
            phone=self.messages_from,
            reply_btn_text=self.reply_btn_text,
            outlet_instance  = self.outlet_instance
        )
        customer_flow_instance = flow_check.check_customer_flow_log(**kwargs)
        if customer_flow_instance is not None:
            
            print(customer_flow_instance,"========================================step2")
            customer_flow_instance = flow_check.check_flow_log(customer_flow_instance,self.json_data)
            if self.message_id is not None and self.json_data is not None:
                messagelog_instance = MessageLog.objects.get(message_id=self.message_id)
                try:
                    formdata = eval(customer_flow_instance.form_data)
                except:
                    formdata = customer_flow_instance.form_data
                if formdata is None:
                    formdata = []
                print(formdata,"============================formdatabefore")
                formdata = formdata if len(formdata) > 0 else []
                print(formdata,"============================formdataafter")
                form_data_append = dict(self.json_data)
                form_data_append['form_id'] = messagelog_instance.form.id
                formdata.append(form_data_append)
                customer_flow_instance.form_data = formdata
                customer_flow_instance.save()
                customer_flow_instance = CustomerFlowLog.objects.get(id = customer_flow_instance.id)
            print(customer_flow_instance,"========================================step3")
        if customer_flow_instance is not None:
            print(customer_flow_instance,"========================================step4")
            flow_check.trigger_action(customer_flow_instance,self.json_data)
        return True           

# ### Subsection: FLOW SENDING  ###       
class Flowcheck:
    def __init__(self, **kwargs):
        self.trigger         = kwargs.get('trigger', None)
        self.outlet_instance = kwargs.get('outlet_instance')
        self.email           = kwargs.get('email', None)
        self.phone           = kwargs.get('phone', None)
        self.reply_btn_text  = kwargs.get('reply_btn_text', None)
        self.customer_data   = kwargs.get('customer_data', None)
        self.next_node       = kwargs.get('next_node', None)
        self.form_data       = kwargs.get('form_data',None)
        self.brodcast_flow   = kwargs.get('brodcast_flow',False)
        self.waba_id         = None
        

    def check_active_campaign(self):
        campaign_instance = WhatsappCampaign.objects.filter(is_active=True, outlet=self.outlet_instance, trigger=self.trigger)
        if campaign_instance:
            return campaign_instance
        return None

    def update_value(self, customer_data,phone_no):
        self.customer_data = customer_data
        self.phone         = phone_no
        return True

    def check_customer_flow_log(self, **kwargs):
        
        if kwargs.get('create', False):
            self.continue_flow = True
            self.trigger_option = self.trigger
            print(kwargs,"----------------------------")
            # Assuming you want to create multiple instances if not found
            customer_flow_instance = []
            for campaign_instance in kwargs.get('campaign_instances', []):
                print(campaign_instance,"====================")
                try:
                    node_payload = eval(json.loads(campaign_instance.custom_json).get('converted_flow_data'))
                except:
                    node_payload = json.loads(campaign_instance.custom_json).get('converted_flow_data')
                next_node_payload = node_payload[0]
                if self.brodcast_flow:
                    pass
                else:
                    try:
                        if next_node_payload.get('webhook_condition',None) is not None:
                            print(next_node_payload.get('webhook_condition'),"======================next_node_payload.get('webhook_condition')")
                            print(self.customer_data,"======================next_node_payload.get('webhook_condition')")
                            for key, value in next_node_payload.get('webhook_condition').items():
                                try:
                                    print(self.customer_data[0][key],"===================================customer_data[0][key]")
                                    print(value,"===================================customer_data[0][key]")
                                    print(any(item in value for item in self.customer_data[0][key]),"===================================self.customer_data[0][key][0] in value")
                                    if any(item in value for item in self.customer_data[0][key]):
                                        print("ooooooooooooooooooooooooooooooye")
                                        self.continue_flow = True
                                        pass
                                    else:
                                        print("returned None because there is no cod")
                                        return None
                                except Exception as e:
                                    print(str(e),"=========================error")
                                    print("returned None because there is no None2")
                                    return None
                        if next_node_payload.get('trigger_condition',None) is not None:
                        
                            print(next_node_payload.get('trigger_condition'),"======================next_node_payload.get('webhook_condition')")
                            for key, value in next_node_payload.get('trigger_condition').items():
                                message_body = kwargs.get('message_body')
                                if key == 'equal':
                                    if message_body in value:
                                        self.continue_flow = True
                                        self.trigger_option = [{'equal':message_body}]
                                        break
                                    
                                    else:
                                        pass
                                elif key == 'starts_with':
                                    if any(message_body.startswith(start) for start in value):
                                        self.continue_flow = True
                                        self.trigger_option = [{'starts_with':message_body}]
                                        break
                                    else:
                                        pass
                                elif key == 'include':
                                    if any(keyword in message_body for keyword in value):
                                        self.continue_flow = True
                                        self.trigger_option = [{'include':message_body}]
                                        break
                                    else:
                                        self.continue_flow = False
                    except:
                        pass
                if self.continue_flow:
                    CustomerFlowLog.objects.create(
                        phone_no=self.phone,
                        campaign=campaign_instance,
                        is_active=True,
                        customer_data=self.customer_data,
                        current_node = 0,
                        current_node_json= json.dumps(next_node_payload),
                        outlet = self.outlet_instance
                    )
                    # customer_flow_instance.append(instance)
                    # self.next_node = 0
                    # break
                    next_instance_node = next_node_payload.get('conditional_node').get('next_node')
                    instance = CustomerFlowLog.objects.create(
                        phone_no=self.phone,
                        campaign=campaign_instance,
                        is_active=True,
                        customer_data=self.customer_data,
                        current_node = next_instance_node,
                        current_node_json= json.dumps(node_payload[next_instance_node]),
                        outlet = self.outlet_instance
                    )
                    customer_flow_instance.append(instance)
                    self.next_node = next_instance_node
                    break
        else:
            customer_flow_instance = CustomerFlowLog.objects.filter(outlet = self.outlet_instance,phone_no=self.phone, is_active=True)
        
        print(customer_flow_instance,"========================================customer_flow_instance1")
        return customer_flow_instance

    def check_flow_log(self, customer_flow_instances,form_data):
        if not customer_flow_instances:
            return None
        for customer_flow_instance in customer_flow_instances.order_by("-id"):
            try:
                payload_edit = json.loads(customer_flow_instance.current_node_json)
                json_data = payload_edit.get('conditional_node',{})
                if json_data.get(self.reply_btn_text):
                    self.next_node = json_data.get(self.reply_btn_text)
                    print(self.next_node,"================================heck_next-node")
                    if payload_edit.get('sub_condition',None) is not None:
                        print('trueeeeeeeeeeeeeeeeeeeeeeeesub_contion')
                        form_data = dict(form_data)
                        sub_condition   = payload_edit.get('sub_condition')
                        print(sub_condition,'trueeeeeeeeeeeeeeeeeeeeeeeesub_contion')
                        selected_option = form_data.get(sub_condition['select_option'])
                        print(selected_option,'trueeeeeeeeeeeeeeeeeeeeeeeesub_contion')
                        sub_condition = sub_condition.get('next_node')
                        print(sub_condition,"==================================sub_condition")
                        print(sub_condition.get(selected_option, None),"==================================sub_condition")
                        self.next_node  = sub_condition.get(selected_option) if sub_condition.get(selected_option, None) is not None else sub_condition.get('notmatch')
                        print(self.next_node,"==================================next_mode")
                    
                    print('ooooooooooooooooooooooooooookkkk')
                    self.selected_option = [{}]
                    for key, value in json_data.items():
                        self.selected_option[0].update({key:True}) if key == self.reply_btn_text else self.selected_option[0].update({key:False})
                    print(customer_flow_instance,"=====================================")
                    
                    try:
                        customer_log = CustomerFlowReport.objects.filter(customer_log__id=customer_flow_instance.id).last()
                    except CustomerFlowReport.DoesNotExist:
                        print('----------------------------------')
                        customer_log = CustomerFlowReport.objects.create(customer_log=customer_flow_instance,campaign=customer_flow_instance.campaign,outlet=customer_flow_instance.outlet)
                    if customer_log is None:
                        customer_log = CustomerFlowReport.objects.create(customer_log=customer_flow_instance,campaign=customer_flow_instance.campaign,outlet=customer_flow_instance.outlet)
                    customer_log.selected_option = self.selected_option
                    customer_log.save()
                    flow_report, created  = CampaignFlowReport.objects.get_or_create(
                        node=payload_edit.get('current_node'),
                        campaign=customer_log.campaign,
                        outlet=customer_log.outlet,
                        defaults={'node_json':json.dumps(payload_edit),'trigger_on_report' : None}
                    )
                    try:
                        selected_condition_report = json.loads(flow_report.selected_option_report)
                    except:
                        selected_condition_report = flow_report.selected_option_report
                    print(selected_condition_report,json_data,'iiiiiiii')
                    if selected_condition_report is None:
                        selected_condition_report = { v: 0  for k, v in enumerate(json_data)}
                       
                    print(selected_condition_report,"============================+++++")
                    count = selected_condition_report[self.reply_btn_text] + 1
                    selected_condition_report[self.reply_btn_text] = count 
                    flow_report.selected_option_report = json.dumps(selected_condition_report)
                    flow_report.save()
                    
                    return customer_flow_instance
            except Exception as e:
                print(str(e),"=====================================except")
                pass
        
        return None
    
    def sub_action(self, **kwargs):
        try:
            shop            = kwargs.get('shop',None)
            url             = kwargs.get('url')
            customer_data   = kwargs.get('customer_data')
            method          = kwargs.get('method')
            payload         = kwargs.get('payload',None)
            apps_url = f'{APP_DOMAIN}/api/v1/add/shop_details/?shop={shop}&app=whatsapp'
            apps_payload = {
                'app' :'whatsapp',
                'shop': shop
            }
            apps_headers = {
                
            }
            apps_response = requests.request("GET", apps_url, headers=apps_headers, data=apps_payload).json()
            
            if not apps_response:
                return False
            
            access_token = apps_response['response'][0]['access_token']
            url = url.format(id=customer_data.get('id'))
            url = f"https://{shop}/admin/api/{SHOPIFY_API_YEAR}/{url}"
            if method == "DELETE":
                headers = {
                    "X-Shopify-Access-Token": access_token
                }
            else:
                headers = {
                    "X-Shopify-Access-Token": access_token,
                    "Content-Type": "application/json"
                }
            def update_json(json_obj, update_dict):
                if isinstance(json_obj, dict):
                    for key, value in json_obj.items():
                        if isinstance(value, dict):
                            update_json(value, update_dict)
                        elif isinstance(value, list):
                            for item in value:
                                update_json(item, update_dict)
                        else:
                            if key == 'tags':
                                json_obj[key] =  update_dict.get(key, value) + json_obj['tags'] if len(str(update_dict.get(key, value))) > 0 else value
                            else:
                                json_obj[key] =  update_dict.get(key, value) if len(str(update_dict.get(key, value))) > 0 else value
                return json_obj

            if payload is not None:
                try:
                    json_data = json.loads(payload)
                    json_data = update_json(json_data, customer_data)
                    response = requests.request(method, url, headers=headers, data=json.dumps(json_data))
                except:
                    response = requests.request(method, url, headers=headers)
            else:
                response = requests.request(method, url, headers=headers)
            
            return True
        except Exception as e:
            return False
                          
    def trigger_action(self, customer_flow_instance, json_data = None):
        try:
            customer_list = eval(customer_flow_instance.customer_data)
        except:
            customer_list = customer_flow_instance.customer_data
        node_payload              = json.loads(customer_flow_instance.campaign.custom_json).get('converted_flow_data')
        self.node_index           = {node['current_node']:index for index, node in enumerate(node_payload)}
        print(self.node_index,"=================================node_index")
        next_node_payload         = node_payload[self.node_index[self.next_node]]
        action                    = next_node_payload.get('action')
        self.campaign_instance    = customer_flow_instance.campaign
        customer_flow_instance_id = customer_flow_instance.id
        self.customerflow_report  = CustomerFlowReport.objects.create(
            customer_log  = customer_flow_instance,
            phone_no=self.phone,
            campaign=self.campaign_instance,
            travelled_node = self.next_node,
            travelled_node_json = json.dumps(next_node_payload),
            selected_option = next_node_payload.get('conditional_node'),
            trigger_on = self.trigger_option if self.next_node == 0 else None,
            outlet = self.campaign_instance.outlet,
            form_data = json.dumps(self.form_data) if self.form_data is not None else None
        )
        print(next_node_payload.get('delay_condition',{}).get('delay_type',None))
        if next_node_payload.get('delay_condition',{}).get('delay_type',None) is not None:
            print(next_node_payload.get('delay_condition',{}).get('delay_type',None),"===================in")
            delay_condition = next_node_payload.get('delay_condition')
            delay = int(delay_condition.get('delay', 0))
            delay_type = delay_condition.get('delay_type', None)

            if delay_type == 'minutes':
                eta                = make_aware(datetime.now() + timedelta(minutes=delay))
                # eta = time_now + timedelta(minutes=delay)
            elif delay_type == 'seconds':
                eta                = make_aware(datetime.now() + timedelta(seconds=delay))
                # eta = time_now + timedelta(seconds=delay)
            elif delay_type == 'hours':
               eta                = make_aware(datetime.now() + timedelta(seconds=delay))
            elif delay_type == 'days':
               eta                = make_aware(datetime.now() + timedelta(seconds=delay))
            else:
                eta = None

            schedule_kwargs = {
                'customer_flow_log_id': customer_flow_instance.id,
            }

            print(eta,'===========================================')
            scheduled_flow.apply_async(
                kwargs=schedule_kwargs,
                eta=eta
            )
        if next_node_payload.get('sub_action',None) is not None:
            for sub_action_data in next_node_payload.get('sub_action'):
                customer_dict = CustomerDict()
                data_dict     = customer_dict.create_data_dict(customer_list[0])
                if json_data is not None:
                    data_dict                          = customer_dict.update_customer(data_dict,json_data)
                    append_data_customer_report        = self.customerflow_report.form_data.append(json_data) if self.customerflow_report.form_data is not None else [json_data]
                    self.customerflow_report.form_data = append_data_customer_report
                    self.customerflow_report.save()
                kwargs = {
                    'customer_data' : data_dict,
                    'url' : sub_action_data.get('url'),
                    'method' :sub_action_data.get('method'),
                    'payload' :sub_action_data.get('payload',None),
                    'shop' : customer_flow_instance.outlet.web_url
                }
                resp = self.sub_action(**kwargs) 
                customer_list = [data_dict]
                customer_flow_instance = CustomerFlowLog.objects.get(id=customer_flow_instance_id)
                customer_flow_instance.customer_data = customer_list
                customer_flow_instance.save()
                try:
                    customer_list = eval(customer_flow_instance.customer_data)
                except:
                    customer_list = customer_flow_instance.customer_data
        if action is not None:
            print("===================================startedwhat")
            if action.get('app') == 'whatsapp': 
                message_type = action.get('type','')
                if message_type == 'service_message':
                    kwargs   = json.loads(action.get('payload'))
                    kwargs   = dict(kwargs)
                    customer_dict = CustomerDict()
                    data_dict = customer_dict.create_data_dict(customer_list[0])
                    reciever = customer_flow_instance.phone_no
                    kwargs['data_dict'] = data_dict
                    kwargs['campaign_instance'] = self.campaign_instance
                    kwargs['project_id'] = self.campaign_instance.project.id
                    fun_reps , response, self.context_payload = send_service_message(self.campaign_instance.outlet.id,reciever, **kwargs)
                    self.waba_id = response.get('messages', [{}])[0].get('id')
                if message_type == 'template_message':
                    template_instance = TemplateDetails.objects.get(templateId=action.get('template_id'))
                    trigger_condition = False

                    msg_send = MessageSender(
                        button_variables = None,
                        template_instance=template_instance,
                        campaign_id=self.campaign_instance.id,
                        trigger = trigger_condition
                    )
                    # print(msg_send.send_messages(customer_list,),'+===============')
                    fun_repsonse, response, self.context_payload = msg_send.send_messages(customer_list,)
                    print(response.get('messages', [{}])[0].get('id'),"==========================message_id")
                    self.waba_id = response.get('messages', [{}])[0].get('id')
                    if self.waba_id is None:
                        return True
                if message_type == "interactive_message":
                    print(self.node_index[self.next_node],"===========================")
                    print(next_node_payload,'=============================')
                    print(action,"======================================")
                    print(action.get('payload'),"===================")
                    # business_instance = BusinessDetails.objects.get(outlet=self.campaign_instance.outlet)
                    # payload = action.get('payload')
                    # msg_send = InteractiveMessage(
                    #     payload = payload,
                    #     business_instance=business_instance,
                    #     trigger = True if self.trigger is not None else False,
                    #     campaign_instance=self.campaign_instance
                    # )
                    template_instance = TemplateDetails.objects.get(id=action.get('payload').get('id'))
                    msg_send = InteractiveMessage(
                        payload = action.get('payload'),
                        trigger = False,
                        campaign_instance=self.campaign_instance
                    )
                    interactive_response, self.context_payload = msg_send.send_messages(customer_list,)
                    print(interactive_response,"===============================asdasd")
                    self.waba_id = interactive_response.get('messages', [{}])[0].get('id')
                    if self.waba_id is None:
                        return True
                    print(interactive_response.get('messages', [{}])[0].get('id'),"==================================")
                    
                    if next_node_payload.get('change_conditional_node', None) is not None:
                        conditional_node = next_node_payload['conditional_node']
                        # Collect items to change
                        items_to_change = {}
                        for items, value in conditional_node.items():
                            if items == "next_node":
                                items_to_change[self.waba_id] = value

                        # Apply changes outside the loop
                        conditional_node.update(items_to_change)
                        next_node_payload['conditional_node'] = conditional_node

                        print(next_node_payload,"======================a")
        print("========================out")
        self.update_customer_flow_log(customer_flow_instance, next_node_payload)
        print("========================out")
        return True

    def update_customer_flow_log(self, customer_flow_instance, next_node_payload):
        customerflow_report                     = CustomerFlowReport.objects.get(id = self.customerflow_report.id)
        print(self.waba_id,"===============================================self.waba_id")
        if self.waba_id is not None:
            
            messagelog_instance                     = MessageLog.objects.get(message_id=self.waba_id)
            payload_edit                            = json.loads(customerflow_report.travelled_node_json)
            payload_edit['action']['payload']       = json.dumps(self.context_payload)
        else:
            messagelog_instance = None
            payload_edit = {}
        customer_flow_instance.current_node_json = json.dumps(next_node_payload)
        customer_flow_instance.current_node      = self.next_node
        customer_flow_instance.is_active         = False if 'status' in next_node_payload else True
        customer_flow_instance.last_message      = messagelog_instance
        customer_flow_instance.save()
        
        customerflow_report.message_log         = messagelog_instance
        customerflow_report.travelled_node_json = json.dumps(payload_edit)
        customerflow_report.save()
        flow_report, created  = CampaignFlowReport.objects.get_or_create(
            node=self.node_index[self.next_node],
            campaign=self.campaign_instance,
            outlet=self.campaign_instance.outlet,
            defaults={'node_json':json.dumps(payload_edit),'trigger_on_report' : None}
        )
        self.trigger_condition_payload = json.loads(customerflow_report.travelled_node_json).get('trigger_condition',None)
        if self.trigger_condition_payload is not None and self.next_node == 0:
            print('iiiiiiii')
            try:
                trigger_condition_report = json.loads(flow_report.trigger_on_report)
            except:
                trigger_condition_report = flow_report.trigger_on_report
            print(trigger_condition_report,'iiiiiiii')
            if trigger_condition_report is None:
                trigger_condition_report = {
                    k: { vl: 0 for it, vl in enumerate(v)} for k, v in self.trigger_condition_payload.items()
                }
            item_trigger_selected, value_trigger_selected = next(iter(self.trigger_option[0].items()))
            count = trigger_condition_report[item_trigger_selected][value_trigger_selected] + 1
            print(count,"============================count")
            trigger_condition_report[item_trigger_selected][value_trigger_selected] = count 
            flow_report.trigger_on_report = json.dumps(trigger_condition_report)
        print(False if 'status' in next_node_payload else True,"======================================status")
        if (True if 'status' in next_node_payload else False):
            print('iiiiiiii')
            try:
                status_conditon_report = json.loads(flow_report.selected_option_report)
            except:
                status_conditon_report = flow_report.selected_option_report
            print(status_conditon_report,'iiiiiiii')
            if status_conditon_report is None:
                status_conditon_report = {
                    'status' : 0
                }
            stat_count = status_conditon_report['status'] + 1
            status_conditon_report['status'] = stat_count 
            flow_report.selected_option_report = json.dumps(status_conditon_report)
        flow_report.save()
        if next_node_payload.get('conditional_node',{}).get('next_node',None) is not None:
            delay_condition = payload_edit.get('next_node_delay_condition',None)
            if delay_condition is not None:
                delay = int(delay_condition.get('delay', 0))
                delay_type = delay_condition.get('delay_type', None)

                if delay_type == 'minutes':
                    eta                = make_aware(datetime.now() + timedelta(minutes=delay))
                    # eta = time_now + timedelta(minutes=delay)
                elif delay_type == 'seconds':
                    eta                = make_aware(datetime.now() + timedelta(seconds=delay))
                    # eta = time_now + timedelta(seconds=delay)
                elif delay_type == 'hours':
                    eta                = make_aware(datetime.now() + timedelta(seconds=delay))
                elif delay_type == 'days':
                    eta                = make_aware(datetime.now() + timedelta(seconds=delay))
                else:
                    eta = None
                print(self.next_node,"==========================next_node_schedule")
                schedule_kwargs = {
                    'customer_flow_log_id': customer_flow_instance.id,
                    'current_node': self.next_node
                }

                print(eta,'===========================================')
                scheduled_conditional_flow.apply_async(
                    kwargs=schedule_kwargs,
                    eta=eta
                )
        return True

# ###FLOW REPORTS GET SINGLE CUSTOMER###
class FlowReport(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            outlet_obj = outlet_details.objects.get(api_key=request.META.get('HTTP_API_KEY'))
            project_obj = ProjectDetails.objects.get(api_key=request.META.get('HTTP_WHATSAPP_PROJECT_KEY'))
            
            customer_report_log_instance = CustomerFlowReport.objects.filter(
                customer_log__id=request.GET.get('customer_flow_id'),
                campaign__project=project_obj,
                outlet=outlet_obj
            )
            print(request.GET.get('customer_flow_id'),customer_report_log_instance,"===========================customer_report")
            
            customer_report_serializers = CustomerReportSerializers(customer_report_log_instance, many=True)
            return JsonResponse({'data': customer_report_serializers.data, 'success': True}, status=200)
        except Exception as e:
            return JsonResponse({'message': str(e), 'success': False}, status=500)
        
    def post(self, request):
        try:
            outlet_obj = outlet_details.objects.get(api_key=request.META.get('HTTP_API_KEY'))
            project_obj = ProjectDetails.objects.get(api_key=request.META.get('HTTP_WHATSAPP_PROJECT_KEY'))
            
            customer_report_log_instance = CampaignFlowReport.objects.filter(
                campaign__id=request.POST.get('campaign_id'),
                outlet=outlet_obj
            )
            
            
            customer_report_serializers = CampaignFlowReportSerializers(customer_report_log_instance, many=True)
            return JsonResponse({'data': customer_report_serializers.data, 'success': True}, status=200)
        except Exception as e:
            return JsonResponse({'message': str(e), 'success': False}, status=500)
            
           
# ##############################################################################################################################################
# Section: TRIGGER
# ##############################################################################################################################################     
# ### Subsection: ADD / UPDATE/ GET TRIGGER ###
@csrf_exempt
@api_view(['GET', 'POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def get_trigger_events(request):
    try:
        outlet_api_key          = request.META.get('HTTP_API_KEY')
        if outlet_api_key is None :
                return JsonResponse({"error": "outlet_api_key is missing"}, status=404)
        outlet_obj     = outlet_details.objects.get(api_key = outlet_api_key)
        if request.method == "GET":
            app                = request.GET.get('app')
            platform           = request.GET.get('platform', 'shopify')
            all_obj            = TriggerEvent.objects.all().order_by('-id')
            app_wise           = all_obj.filter(app__contains = app, platform = platform)
            current_outlet_obj = all_obj.filter(outlet = outlet_obj.id)

            app_wise_serialized_obj = TriggerEventsSerializer(app_wise, many=True).data
            current_outlet_serialized_obj = TriggerEventsSerializer(current_outlet_obj, many=True).data

            concatatedObj = current_outlet_serialized_obj + app_wise_serialized_obj

            return JsonResponse({'data': concatatedObj}, status=200)

        elif request.method == "POST":
            trigger_event_obj          = TriggerEvent()
            trigger_event_obj.name     = request.POST.get('new_trigger')
            trigger_event_obj.topic    = request.POST.get('new_trigger')
            trigger_event_obj.app      = "all"
            trigger_event_obj.platform = "Custom"
            trigger_event_obj.slug     = str(request.POST.get('new_trigger')).replace(" ", "_")
            trigger_event_obj.description = request.POST.get('description')
            trigger_event_obj.outlet   = outlet_obj
            trigger_event_obj.shop     = request.POST.get('shop')
            trigger_event_obj.placeholders = request.POST.get('parameters')
            trigger_event_obj.save()

            return JsonResponse({"Message": "Trigger Added SuccessFully!"}, status=200)
    except (outlet_details.DoesNotExist,ProjectDetails.DoesNotExist,ProjectDetails.MultipleObjectsReturned,outlet_details.MultipleObjectsReturned,TemplateDetails.DoesNotExist,TemplateDetails.MultipleObjectsReturned) as e:
        if isinstance(e, outlet_details.DoesNotExist):
            return JsonResponse({"error": "Invalid API Key outlet details not found"}, status=404)
        elif isinstance(e, outlet_details.MultipleObjectsReturned):
                return JsonResponse({"error": "Multiple outlets found with the same API Key"}, status=400)
        elif isinstance(e, ProjectDetails.DoesNotExist):
            return JsonResponse({"error": "Project details not found"}, status=404)
        elif isinstance(e, ProjectDetails.MultipleObjectsReturned):
                return JsonResponse({"error": "Multiple projects found with the same API Key"}, status=400)
    except Exception as e:
        print(str(e))
        print("======================== ERROR ==============================")
        return JsonResponse({"error": "Something went wrong!"}, status=500)
# ### Subsection: SEND TRIGGER MESSAGAE###
@csrf_exempt
def send_trigger_message(request):
    if request.method != "POST":
        return JsonResponse({'response': 'Invalid request method.'}, status=405)
    
    required_params = ['trigger', 'contact']
    missing_params = [param for param in required_params if not request.POST.get(param)]
    
    if missing_params:
        return JsonResponse({'response': f'{", ".join(missing_params)} parameter(s) not found!'}, status=400)
    if not request.META.get('HTTP_API_KEY'):
        return JsonResponse({'response': f'Missing header Api-Key'}, status=400)

    try:
        outlet_obj = outlet_details.objects.get(api_key = request.META.get('HTTP_API_KEY'))
    except:
        return JsonResponse({'response': f'Outlet Details not found!'}, status=400)

    try:
        campaign_object = WhatsappCampaign.objects.get(is_active=1, outlet_id=outlet_obj.id, trigger=request.POST.get('trigger'))
    except Exception as e:
        return JsonResponse({'response': f'Active Campaign not found!'}, status=400)

    try:
        business_instance   = BusinessDetails.objects.get(outlet=outlet_obj)
    except:
        return JsonResponse({'response': f'Business Details not found!'}, status=400)

    customer_list = [{
        'first_name': '',
        'last_name': '',
        'contact' : request.POST.get('contact')
    }]
    button_variables = []

    msg_send = MessageSender(
        button_variables=button_variables,
        template_instance=campaign_object.template,
        business_instance=business_instance,
        campaign_id=campaign_object.id if campaign_object else None,
        trigger = False
    )
    message_thread = threading.Thread(target=msg_send.send_messages, args=(customer_list,))
    message_thread.start()

    
        
    return JsonResponse({'response': 'Message sent successfully'}, status=200)
# ##############################################################################################################################################
# Section: BILLING 
# ##############################################################################################################################################     
# ### Subsection: BILLING AMOUNT ###
def block_amount(total_cost,wallet_obj):
    wallet_obj = WhatsappWallet.objects.get(id = wallet_obj.id)
    with connection.cursor() as cursor:
        cursor.execute("""
            UPDATE xl2024_wallet_whatsapp
            SET balance = ROUND(balance - %s, 5),
                is_block = ROUND(is_block + %s, 5)
            WHERE id = %s
        """, [Decimal(total_cost), Decimal(total_cost), wallet_obj.id])
    wallet_obj_new = WhatsappWallet.objects.get(id = wallet_obj.id)
    wallet_transaction_obj = WhatsappWalletTransaction.objects.create(
        transaction_no          = str(uuid.uuid4()).replace('-', ''),
        payment_status          = 'Blocked',
        payment_date            = datetime.now(),       
        outlet                  = wallet_obj.outlet,
        shop                    = wallet_obj.outlet.web_url,
        amount                  = total_cost,
        block_amount            = wallet_obj_new.is_block,
        original_balance_amount = wallet_obj.balance,
        balance_amount          = wallet_obj_new.balance,
        wallet                  = wallet_obj,
        project                 = wallet_obj.project,
        business                = wallet_obj.business,
    )
    return wallet_transaction_obj
# ### Subsection:   NEW BILLING AMOUNT ###
def new_block_amount(**kwargs):
    total_cost    = kwargs.get('total_cost')
    template_type = kwargs.get('template_type')
    campaign_id   = kwargs.get('campaign_id')
    wallet_obj    = WhatsappWallet.objects.get(project__id = kwargs.get('project_id'))
    print('new_bloc_amount')
    with connection.cursor() as cursor:
        block_columns = {
            "MARKETING" : "marketing_balance_block",
            "SERVICING"  : "servicing_balance_block",
            "UTILITY"   : "utility_balance_block",
        }
        balance_columns = {
            "MARKETING": "marketing_balance",
            "SERVICING" : "servicing_balance",
            "UTILITY"  : "utility_balance",
        }
        print(template_type,template_type in balance_columns,"===============")
        if template_type in balance_columns:
            print('new_bloc_amount --------in condition')
            block_column_name = block_columns[template_type]
            balance_column_name = balance_columns[template_type]
            cursor.execute(f"""
                UPDATE xl2024_wallet_whatsapp
                SET balance = ROUND(balance - %s, 5),
                    {balance_column_name} = ROUND({balance_column_name} - %s, 5),
                    is_block = ROUND(is_block + %s, 5),
                    {block_column_name} = ROUND({block_column_name} + %s, 5)
                WHERE id = %s
            """, [Decimal(total_cost), Decimal(total_cost), Decimal(total_cost), Decimal(total_cost), wallet_obj.id])

    wallet_obj_new = WhatsappWallet.objects.get(id = wallet_obj.id)
    wallet_transaction_obj = WhatsappWalletTransaction.objects.create(
        transaction_no          = str(uuid.uuid4()).replace('-', ''),
        payment_status          = 'Blocked',
        payment_date            = datetime.now(),       
        outlet                  = wallet_obj.outlet,
        shop                    = wallet_obj.outlet.web_url,
        amount                  = total_cost,
        block_amount            = wallet_obj_new.is_block,
        original_balance_amount = wallet_obj.balance,
        balance_amount          = wallet_obj_new.balance,
        wallet                  = wallet_obj,
        project                 = wallet_obj.project,
        business                = wallet_obj.business,
        message_type            = template_type,
        campaign_id             = campaign_id
    )
    return wallet_transaction_obj
# ### Subsection: SCHEDULED BLOCK AMOUNT ###
def scheduled_block_amount(**kwargs):
    eta                = make_aware(datetime.now() + timedelta(hours=1))
    wallet_obj         = WhatsappWallet.objects.get(project__id=kwargs.get('project_id'))
    wallet_transaction = model_to_dict(kwargs.get('wallet_transaction'))
    wallet_obj_dict    = model_to_dict(wallet_obj)
    template_type      = kwargs.get('template_type')
    # print(wallet_obj_dict,"================================")
    unblock_found_scheduled.apply_async(
        args=[wallet_obj_dict,wallet_transaction['id'],kwargs.get('per_message_cost'),template_type,kwargs.get('waba_id')],
        eta=eta
    )
    return True

def unblock_failed_at_sending(**kwargs):
    project_instance = kwargs.get("project")
    wallet_obj = WhatsappWallet.objects.get(project = project_instance.id)
    block_columns = {
                    "MARKETING" : "marketing_balance_block",
                    "SERVICNG"  : "servicing_balance_block",
                    "UTILITY"   : "utility_balance_block",
                }
    balance_columns = {
        "MARKETING": "marketing_balance",
        "SERVICNG" : "servicing_balance",
        "UTILITY"  : "utility_balance",
    }

    template_type       = kwargs.get('template_type')
    block_column_name   = block_columns[template_type]
    balance_column_name = balance_columns[template_type]

    query = f"""
            UPDATE xl2024_wallet_whatsapp
            SET balance = ROUND(balance + %s, 5),
                {balance_column_name} = ROUND({balance_column_name} + %s, 5),
                is_block = ROUND(is_block - %s, 5),
                {block_column_name} =  ROUND({block_column_name} - %s, 5)
            WHERE project_id = %s
        """
    
    params = [
        Decimal(kwargs.get("per_message_cost")), 
        Decimal(kwargs.get("per_message_cost")), 
        Decimal(kwargs.get("per_message_cost")), 
        Decimal(kwargs.get("per_message_cost")), 
        project_instance.id
    ]
    with connection.cursor() as cursor:
        cursor.execute(query, params)
    message_instance = MessageLog.objects.get(id=kwargs.get('message_log_id'))
    wallet_obj_new = WhatsappWallet.objects.get(project = project_instance.id)
    WhatsappWalletTransaction.objects.create(
        transaction_no  = str(uuid.uuid4()).replace('-', ''),
        wallet          = wallet_obj,
        payment_status  = 'Unblocked',
        reciever        = kwargs.get("receiver_phone_number"),
        sender          = project_instance.phone_code + project_instance.phone_no,
        payment_date    = datetime.now(),
        original_balance_amount = wallet_obj.balance,
        balance_amount  = wallet_obj_new.balance,
        debit_amount    = 0,
        block_amount    = wallet_obj_new.is_block,
        amount          = kwargs.get("per_message_cost"),
        outlet          = project_instance.outlet,
        project         = project_instance,
        business        = project_instance.business,
        remarks         = 'Message sending Failed at sending amount it added back in balance',
        message_log     = message_instance,
        message_type    =  template_type,
    )
    return True

# ### Subsection: CHECK MESSAGE BALANCE ###
def check_wallet_balance(**kwargs):
    wallet_obj          = WhatsappWallet.objects.get(project__id=kwargs.get('project_id'))
    print(wallet_obj,"-===========winnnn1")
    if wallet_obj.subscription is None:
        print(wallet_obj,"-===========winnnn6")
        return (False,{"message": "Purchase Subscription"},None,0)
    if wallet_obj.subscription.end_date < timezone.now():
        print(wallet_obj,"-===========winnnn5")
        return (False,{"message": "Subscription is Expired"},None,0)
    else:
        pass
    template_type = kwargs.get('template_type')
    print(wallet_obj,"-===========winnnn4")
    total_messages        = kwargs.get('total_messages')
    template_type         = template_type
    per_message_cost      = wallet_obj.deduction_plan.get(template_type)
    total_cost            = total_messages * per_message_cost
    fieldname             = f"{template_type.lower()}_balance"
    template_type_balance  = getattr(wallet_obj,fieldname)
    print(total_cost,fieldname,template_type_balance)
    if Decimal(total_cost) > Decimal(template_type_balance):
        number_of_messages_possible = int(template_type_balance / per_message_cost)
        return (False,{'message':f'insufficent fund can only send {number_of_messages_possible} messages with present fund'},0, per_message_cost)
    else:
        return (True,None,total_cost,per_message_cost)

# ##############################################################################################################################################
# Section: PAYMENT GATEWAY
# ##############################################################################################################################################     

# RAZORPAY_KEY_ID = 'rzp_test_qHo9NbmS7irLV4'
# RAZORPAY_KEY_SECRET = 'yXn8isx70zfRMVeatgpAHfXB'
# ### Subsection: RAZORPAY LINK CREATION ###
@csrf_exempt
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def create_order(request):
    if request.method == "POST":
        amount    = request.POST.get('amount')
        client    = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))
        unique_id = str(uuid.uuid4())
        customer_name   = 'soham'
        customer_number = '919511671955'
        payment         = client.order.create({'amount': int(amount) * 100, 'currency': 'INR', 'payment_capture': '1'})
        # client = razorpay.Client(auth=(RAZORPAY_API_KEY, RAZORPAY_SECRET_KEY))
        expiry_time_minutes = 30
        response = client.payment_link.create({
            "amount": int(amount) * 100,
            "currency": 'INR',
            "accept_partial": 'false',
            "expire_by": int(time.time() + (expiry_time_minutes * 60)),
            "description": "For XYZ purpose",
            "customer": {
                "name": customer_name,
                "contact": customer_number
            },
            "notify": {
                "sms": 'false',
                "email": 'false'
            },
            "reminder_enable": 'false',
            "notes": {
                "unique_id": unique_id,
                "name": customer_name,
                "contact": customer_number
            },
            "callback_url": "",
            "callback_method": "get"
        })

        url = response['short_url']
        return JsonResponse({
            'payment' : payment,
            'order_id': payment['id'],
            'amount': amount,
            'currency': 'INR',
            'razorpay_key_id': RAZORPAY_KEY_ID,
            'url':url,
            "unique_id": unique_id,
        })
               
# ### Subsection: RAZORPAY WEBHOOK ###

# @csrf_exempt
# def razorpay_webhook(request):
#     print(request.body,'================razorpay_webook')
#     data = request.body
#     json_data = json.loads(data.decode('UTF-8'))
#     event          = json_data.get('event')
#     payload        = json_data.get('payload', {})
#     payment        = payload.get('payment', {})
#     payment_entity  = payment.get('entity', {})
#     acquirer_data   = payment_entity.get('acquirer_data', {})
#     transaction_id = acquirer_data.get('transaction_id')
#     order          = payload.get('order', {})
#     order_entity   = order.get('entity', {})
#     order_id       = payment_entity.get('order_id')
#     amount_paid    = order_entity.get('amount_paid')
#     currency    = order_entity.get('currency')
#     amount         = payment_entity.get('amount')
#     notes          = payment_entity.get('notes', {})
#     unique_id      = notes.get('unique_id')
#     status         = payment_entity.get('status')
#     payment_id     = payment_entity.get('id')
#     payment_method = payment_entity.get('method')
#     wallet         = payment_entity.get('wallet')
#     bank           = payment_entity.get('bank')
#     card_id        = payment_entity.get('card_id')
#     tax            = payment_entity.get('tax')
#     fee            = payment_entity.get('fee')
#     print(f"Event: {event}")
#     print(f"Transaction ID: {transaction_id}")
#     print(f"Amount Paid: {amount_paid}")
#     print(f"Amount: {amount}")
#     print(f"Unique ID: {unique_id}")
#     print(f"Status: {status}")
#     print(f"Payment ID: {payment_id}")
#     print(f"Payment Method: {payment_method}")
#     print(f"Wallet: {wallet}")
#     print(f"Bank: {bank}")
#     print(f"Card ID: {card_id}")
#     print(f"Tax: {tax}")
#     print(f"Fee: {fee}")
#     print(f"Order ID: {order_id}")
#     if event  == "order.paid":
#         amount_paid    = order_entity.get('amount_paid')
#         childtransaction_obj = ChildTransactions.objects.filter(unique_id = unique_id).first()
#         if childtransaction_obj :
#             childtransaction_obj.payment_stage = "Completed"
#             childtransaction_obj.payment_method = payment_method
#             childtransaction_obj.payment_wallet = wallet
#             childtransaction_obj.bank = bank
#             childtransaction_obj.card_id = card_id
#             childtransaction_obj.currency = currency
#             childtransaction_obj.transaction_no = transaction_id
#             childtransaction_obj.amount_with_gst = amount_paid/100
#             childtransaction_obj.payment_id = payment_id
#             childtransaction_obj.order_id = order_id
#             childtransaction_obj.tax = tax/100
#             childtransaction_obj.fees = fee/100
#             childtransaction_obj.error_code = None
#             childtransaction_obj.error_description = None
#             childtransaction_obj.error_source = None
#             childtransaction_obj.error_step = None
#             childtransaction_obj.error_reason = None
#             childtransaction_obj.save()
#             PlanSubscription.objects.filter(project = childtransaction_obj.project).update(status = 'Active',is_active = True)
#             timeline_update(childtransaction_obj.outlet, childtransaction_obj.outlet.web_url, 'is_plan_purchased', True, childtransaction_obj.project.api_key)
#         else:
#             wallet_transactions_obj = WhatsappWalletTransaction.objects.filter(unique_id = unique_id).first()
#             print("<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<,in_wallet_trans>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
#             print(wallet_transactions_obj)
#             if wallet_transactions_obj:
#                 amount = amount/100
#                 wallet_transactions_obj.credit_amount = amount_paid/100
#                 wallet_transactions_obj.payment_stage = "Completed"
#                 wallet_transactions_obj.payment_method = payment_method
#                 wallet_transactions_obj.payment_wallet = wallet
#                 wallet_transactions_obj.bank = bank
#                 wallet_transactions_obj.card_id = card_id
#                 wallet_transactions_obj.currency = currency
#                 wallet_transactions_obj.transaction_no = transaction_id
#                 wallet_transactions_obj.amount = amount_paid/100
#                 wallet_transactions_obj.payment_id = payment_id
#                 wallet_transactions_obj.order_id = order_id
#                 wallet_transactions_obj.tax = tax/100
#                 wallet_transactions_obj.fees = fee/100
#                 wallet_transactions_obj.save()
#                 with connection.cursor() as cursor:
#                     cursor.execute("""
#                                 UPDATE xl2024_wallet_whatsapp
#                                 SET balance = ROUND(balance + %s, 5),
#                                 total_balance = ROUND(total_balance + %s, 5)
#                                 WHERE project_id = %s
#                             """, [amount,amount, wallet_transactions_obj.project.id])
#             else:
#                 pass
#     elif event == "payment.failed":
#         error_code        = payment_entity.get('error_code')
#         error_description = payment_entity.get('error_description')
#         error_source      = payment_entity.get('error_source')
#         error_step        = payment_entity.get('error_step')
#         error_reason      = payment_entity.get('error_reason')
#         print(f"Error Code: {error_code}")
#         print(f"Error Description: {error_description}")
#         print(f"Error Source: {error_source}")
#         print(f"Error Step: {error_step}")
#         print(f"Error Reason: {error_reason}")
#         childtransaction_obj = ChildTransactions.objects.filter(unique_id = unique_id).first()
#         if childtransaction_obj :
#             #PlanSubscriptionsLog_obj= PlanSubscriptionsLog.objects.filter(project = childtransaction_obj.project,,status = 'Expired').last()
#             #PlanSubscription.objects.filter(project = childtransaction_obj.project).update(membership_plan = PlanSubscriptionsLog_obj.membership_plan,deduction_plan = PlanSubscriptionsLog_obj.deduction_plan,is_active = False,status = 'Expired',start_date = PlanSubscriptionsLog_obj.start_date,end_date = PlanSubscriptionsLog_obj.end_date)
#             #PlanSubscriptionsLog_obj.delete()
#             childtransaction_obj.payment_stage = "failed"
#             childtransaction_obj.payment_method = payment_method
#             childtransaction_obj.payment_wallet = wallet
#             childtransaction_obj.bank = bank
#             childtransaction_obj.card_id = card_id
#             childtransaction_obj.currency = currency
#             childtransaction_obj.transaction_no = transaction_id
#             childtransaction_obj.amount_with_gst = amount/100
#             childtransaction_obj.payment_id = payment_id
#             childtransaction_obj.order_id = order_id
#             childtransaction_obj.error_code = error_code
#             childtransaction_obj.error_description = error_description
#             childtransaction_obj.error_source = error_source
#             childtransaction_obj.error_step = error_step
#             childtransaction_obj.error_reason = error_reason
#             childtransaction_obj.save()
#         else:
#             wallet_transactions_obj = WhatsappWalletTransaction.objects.filter(unique_id = unique_id).first()
#             if wallet_transactions_obj:
#                 wallet_transactions_obj.credit_amount = 0.0
#                 wallet_transactions_obj.payment_stage = "Faild"
#                 wallet_transactions_obj.payment_method = payment_method
#                 wallet_transactions_obj.payment_wallet = wallet
#                 wallet_transactions_obj.bank = bank
#                 wallet_transactions_obj.card_id = card_id
#                 wallet_transactions_obj.currency = currency
#                 wallet_transactions_obj.transaction_no = transaction_id
#                 wallet_transactions_obj.amount = amount/100
#                 wallet_transactions_obj.payment_id = payment_id
#                 wallet_transactions_obj.order_id = order_id
#                 wallet_transactions_obj.error_code = error_code
#                 wallet_transactions_obj.error_description = error_description
#                 wallet_transactions_obj.error_source = error_source
#                 wallet_transactions_obj.error_step = error_step
#                 wallet_transactions_obj.error_reason = error_reason
#                 wallet_transactions_obj.save()
#             else:
#                 pass
#     elif event == "payment_link.expired":
#         payment_link        = payload.get('payment_link', {})
#         payment_link_entity = payment_link.get('entity', {})
#         notes               = payment_link_entity.get('notes', {})
#         unique_id           = notes.get('unique_id')
#         currency            = payment_link_entity.get('currency')

#         childtransaction_obj = ChildTransactions.objects.filter(unique_id = unique_id).first()
#         if childtransaction_obj :
#             PlanSubscriptionsLog_obj= PlanSubscriptionsLog.objects.filter(project = childtransaction_obj.project)
#             PlanSubscription.objects.filter(project = childtransaction_obj.project).update(membership_plan = PlanSubscriptionsLog_obj.membership_plan,deduction_plan = PlanSubscriptionsLog_obj.deduction_plan,is_active = False,status = 'Expired',start_date = PlanSubscriptionsLog_obj.start_date,end_date = PlanSubscriptionsLog_obj.end_date)
#             PlanSubscriptionsLog_obj.delete()
#             childtransaction_obj.payment_stage = "Link Expired"
#             childtransaction_obj.currency = currency
#             childtransaction_obj.save()
#         else:
#             wallet_transactions_obj = WhatsappWalletTransaction.objects.filter(unique_id = unique_id).first()
#             if wallet_transactions_obj:
#                 wallet_transactions_obj.payment_stage = "Link Expired"
#                 wallet_transactions_obj.currency = currency
#                 wallet_transactions_obj.save()
#             else:
#                 pass
#     else:
#         pass     
        
#     return HttpResponse(status=200)







@csrf_exempt
def razorpay_webhook(request):
    print(request.body,'================razorpay_webook')
    data = request.body
    json_data = json.loads(data.decode('UTF-8'))
    event          = json_data.get('event')
    payload        = json_data.get('payload', {})
    payment        = payload.get('payment', {})
    payment_entity = payment.get('entity', {})
    acquirer_data  = payment_entity.get('acquirer_data', {})
    transaction_id = acquirer_data.get('transaction_id')
    order          = payload.get('order', {})
    order_entity   = order.get('entity', {})
    order_id       = payment_entity.get('order_id')
    amount_paid    = order_entity.get('amount_paid')
    currency       = order_entity.get('currency')
    amount         = payment_entity.get('amount')
    notes          = payment_entity.get('notes', {})
    marketing_amount = notes.get('marketing_amount')
    servicing_amount = notes.get('servicing_amount')
    utility_amount = notes.get('utility_amount')
    authentication_balance = notes.get('authentication_balance')
    unique_id      = notes.get('unique_id')
    status         = payment_entity.get('status')
    payment_id     = payment_entity.get('id')
    payment_method = payment_entity.get('method')
    wallet         = payment_entity.get('wallet')
    bank           = payment_entity.get('bank')
    card_id        = payment_entity.get('card_id')
    tax            = payment_entity.get('tax')
    fee            = payment_entity.get('fee')
    print(f"Event: {event}")
    print(f"Transaction ID: {transaction_id}")
    print(f"Amount Paid: {amount_paid}")
    print(f"Amount: {amount}")
    print(f"Unique ID: {unique_id}")
    print(f"Status: {status}")
    print(f"Payment ID: {payment_id}")
    print(f"Payment Method: {payment_method}")
    print(f"Wallet: {wallet}")
    print(f"Bank: {bank}")
    print(f"Card ID: {card_id}")
    print(f"Tax: {tax}")
    print(f"Fee: {fee}")
    print(f"Order ID: {order_id}")
    if event  == "order.paid":
        amount_paid    = order_entity.get('amount_paid')
        childtransaction_obj = ChildTransactions.objects.filter(unique_id = unique_id).first()
        if childtransaction_obj :
            childtransaction_obj.payment_stage = "Completed"
            childtransaction_obj.payment_method = payment_method
            childtransaction_obj.payment_wallet = wallet
            childtransaction_obj.bank = bank
            childtransaction_obj.card_id = card_id
            childtransaction_obj.currency = currency
            childtransaction_obj.transaction_no = transaction_id
            childtransaction_obj.amount_with_gst = amount_paid/100
            childtransaction_obj.payment_id = payment_id
            childtransaction_obj.order_id = order_id
            childtransaction_obj.tax = tax/100
            childtransaction_obj.fees = fee/100
            childtransaction_obj.error_code = None
            childtransaction_obj.error_description = None
            childtransaction_obj.error_source = None
            childtransaction_obj.error_step = None
            childtransaction_obj.error_reason = None
            childtransaction_obj.save()
            membership_plan_obj = MembershipPlan.objects.get(id = notes.get('membership_plan_id'))
            membership_unit         = membership_plan_obj.plan_period_unit
            membership_duration     = membership_plan_obj.plan_period_length
            if membership_duration is None and membership_unit == 'FE' :
                end_date  = None
            else:
                if membership_unit   == 'MT':
                    membership_length_days = membership_duration * 30
                elif membership_unit == 'YR':
                    membership_length_days = membership_duration * 365
                elif membership_unit == 'DY':
                    membership_length_days = membership_duration
                else:
                    pass
                end_date = datetime.now()+timedelta(days=membership_length_days)
            plan_subscription_obj = PlanSubscription.objects.filter(project=childtransaction_obj.project).first()
            if plan_subscription_obj:
                # plan_log  = PlanSubscriptionsLog.objects.filter(
                #     outlet          =  childtransaction_obj.outlet,
                #     business        =  childtransaction_obj.business,
                #     project         =  childtransaction_obj.project
                # ).last()
                PlanSubscriptionsLog.objects.create(
                    membership_plan =  plan_subscription_obj.membership_plan,
                    outlet          =  childtransaction_obj.outlet,
                    business        =  childtransaction_obj.business,
                    project         =  childtransaction_obj.project,
                    status          =  'Expired',
                    deduction_plan  =  plan_subscription_obj.deduction_plan,
                    start_date      =  plan_subscription_obj.start_date ,
                    end_date        =  plan_subscription_obj.end_date,
                    # childtransaction = plan_log.childtransaction
                )
                PlanSubscriptionsLog.objects.create(
                    membership_plan =  membership_plan_obj,
                    outlet          =  childtransaction_obj.outlet,
                    business        =  childtransaction_obj.business,
                    project         =  childtransaction_obj.project,
                    status          =  'Active' if timezone.now() > plan_subscription_obj.end_date else 'Upgraded',
                    deduction_plan  =  membership_plan_obj.deduction_plan,
                    start_date      =  datetime.now() ,
                    end_date        =  end_date,
                    childtransaction = childtransaction_obj
                )
                plan_subscription_obj.membership_plan  = membership_plan_obj
                plan_subscription_obj.status           = 'Active'
                plan_subscription_obj.start_date       = datetime.now()
                plan_subscription_obj.end_date         = end_date
                plan_subscription_obj.is_active        = True
                plan_subscription_obj.deduction_plan   = membership_plan_obj.deduction_plan
                plan_subscription_obj.save()
            else:
                plan_subscription_obj  =  PlanSubscription.objects.create(
                    membership_plan =   membership_plan_obj,
                    outlet          =   childtransaction_obj.outlet,
                    business        =   childtransaction_obj.business,
                    project         =   childtransaction_obj.project,
                    status          =   'Active',
                    is_active       =   True,
                    start_date      =   datetime.now(),
                    deduction_plan  =   membership_plan_obj.deduction_plan,
                    end_date        =   end_date,
                )
                PlanSubscriptionsLog.objects.create(
                    membership_plan =  membership_plan_obj,
                    outlet          =  childtransaction_obj.outlet,
                    business        =  childtransaction_obj.business,
                    project         =  childtransaction_obj.project,
                    status          =  'Active' ,
                    deduction_plan  =  membership_plan_obj.deduction_plan,
                    start_date      =  datetime.now() ,
                    end_date        =  end_date,
                    childtransaction = childtransaction_obj
                )
            childtransaction_obj.subscription = plan_subscription_obj
            childtransaction_obj.save()
            updated =  WhatsappWallet.objects.filter(project = childtransaction_obj.project).update(deduction_plan =  membership_plan_obj.deduction_plan,subscription = plan_subscription_obj)  
            if updated == 0 :
                WhatsappWallet.objects.create(business = childtransaction_obj.business,project = childtransaction_obj.project,outlet = childtransaction_obj.outlet,deduction_plan =  membership_plan_obj.deduction_plan,subscription = plan_subscription_obj)
            else:
                pass
            timeline_update(childtransaction_obj.outlet, childtransaction_obj.outlet.web_url, 'is_plan_purchased', True, childtransaction_obj.project.api_key)
        else:
            wallet_transactions_obj = WhatsappWalletTransaction.objects.filter(unique_id = unique_id).first()
            print("<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<,in_wallet_trans>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
            print(wallet_transactions_obj)
            if wallet_transactions_obj:
                amount = amount/100
                wallet_transactions_obj.payment_stage = "Completed"
                wallet_transactions_obj.payment_method = payment_method
                wallet_transactions_obj.payment_wallet = wallet
                wallet_transactions_obj.bank = bank
                wallet_transactions_obj.card_id = card_id
                wallet_transactions_obj.currency = currency
                wallet_transactions_obj.transaction_no = transaction_id
                wallet_transactions_obj.payment_id = payment_id
                wallet_transactions_obj.order_id = order_id
                wallet_transactions_obj.tax = tax/100
                wallet_transactions_obj.fees = fee/100
                wallet_transactions_obj.amount_with_gst = amount_paid/100
                wallet_transactions_obj.save()
                print(amount,"=====================amount")
                with connection.cursor() as cursor:
                    cursor.execute("""
                        UPDATE xl2024_wallet_whatsapp
                        SET balance                  = ROUND(balance + %s, 5),
                        total_balance                = ROUND(total_balance + %s, 5),
                        marketing_balance            = ROUND(marketing_balance + %s, 5),
                        total_marketing_balance      = ROUND(total_marketing_balance + %s, 5),
                        servicing_balance            = ROUND(servicing_balance + %s, 5),
                        total_servicing_balance      = ROUND(total_servicing_balance + %s, 5),
                        utility_balance              = ROUND(utility_balance + %s, 5),
                        total_utility_balance        = ROUND(total_utility_balance + %s, 5),
                        authentication_balance       = ROUND(authentication_balance + %s, 5),
                        total_authentication_balance = ROUND(total_authentication_balance + %s, 5)
                        WHERE project_id = %s
                    """, [wallet_transactions_obj.amount,wallet_transactions_obj.amount,marketing_amount,marketing_amount,servicing_amount,servicing_amount,utility_amount,utility_amount,authentication_balance,authentication_balance, wallet_transactions_obj.project.id])
            else:
                pass
    elif event == "payment.failed":
        error_code        = payment_entity.get('error_code')
        error_description = payment_entity.get('error_description')
        error_source      = payment_entity.get('error_source')
        error_step        = payment_entity.get('error_step')
        error_reason      = payment_entity.get('error_reason')
        print(f"Error Code: {error_code}")
        print(f"Error Description: {error_description}")
        print(f"Error Source: {error_source}")
        print(f"Error Step: {error_step}")
        print(f"Error Reason: {error_reason}")
        childtransaction_obj = ChildTransactions.objects.filter(unique_id = unique_id).first()
        if childtransaction_obj :
            #PlanSubscriptionsLog_obj= PlanSubscriptionsLog.objects.filter(project = childtransaction_obj.project,,status = 'Expired').last()
            #PlanSubscription.objects.filter(project = childtransaction_obj.project).update(membership_plan = PlanSubscriptionsLog_obj.membership_plan,deduction_plan = PlanSubscriptionsLog_obj.deduction_plan,is_active = False,status = 'Expired',start_date = PlanSubscriptionsLog_obj.start_date,end_date = PlanSubscriptionsLog_obj.end_date)
            #PlanSubscriptionsLog_obj.delete()
            childtransaction_obj.payment_stage = "failed"
            childtransaction_obj.payment_method = payment_method
            childtransaction_obj.payment_wallet = wallet
            childtransaction_obj.bank = bank
            childtransaction_obj.card_id = card_id
            childtransaction_obj.currency = currency
            childtransaction_obj.transaction_no = transaction_id
            childtransaction_obj.amount_with_gst = amount/100
            childtransaction_obj.payment_id = payment_id
            childtransaction_obj.order_id = order_id
            childtransaction_obj.error_code = error_code
            childtransaction_obj.error_description = error_description
            childtransaction_obj.error_source = error_source
            childtransaction_obj.error_step = error_step
            childtransaction_obj.error_reason = error_reason
            childtransaction_obj.save()
        else:
            wallet_transactions_obj = WhatsappWalletTransaction.objects.filter(unique_id = unique_id).first()
            if wallet_transactions_obj:
                wallet_transactions_obj.credit_amount = 0.0
                wallet_transactions_obj.payment_stage = "Faild"
                wallet_transactions_obj.payment_method = payment_method
                wallet_transactions_obj.payment_wallet = wallet
                wallet_transactions_obj.bank = bank
                wallet_transactions_obj.card_id = card_id
                wallet_transactions_obj.currency = currency
                wallet_transactions_obj.transaction_no = transaction_id
                wallet_transactions_obj.amount_with_gst = amount/100
                wallet_transactions_obj.payment_id = payment_id
                wallet_transactions_obj.order_id = order_id
                wallet_transactions_obj.error_code = error_code
                wallet_transactions_obj.error_description = error_description
                wallet_transactions_obj.error_source = error_source
                wallet_transactions_obj.error_step = error_step
                wallet_transactions_obj.error_reason = error_reason
                wallet_transactions_obj.save()
            else:
                pass
    elif event == "payment_link.expired":
        payment_link        = payload.get('payment_link', {})
        payment_link_entity = payment_link.get('entity', {})
        notes               = payment_link_entity.get('notes', {})
        unique_id           = notes.get('unique_id')
        currency            = payment_link_entity.get('currency')

        childtransaction_obj = ChildTransactions.objects.filter(unique_id = unique_id).first()
        if childtransaction_obj :
            childtransaction_obj.payment_stage = "Link Expired"
            childtransaction_obj.currency = currency
            childtransaction_obj.save()
        else:
            wallet_transactions_obj = WhatsappWalletTransaction.objects.filter(unique_id = unique_id).first()
            if wallet_transactions_obj:
                wallet_transactions_obj.payment_stage = "Link Expired"
                wallet_transactions_obj.currency = currency
                wallet_transactions_obj.save()
            else:
                pass
    else:
        pass     
        
    return HttpResponse(status=200)





RAZORPAY_KEY_ID     = 'rzp_test_qHo9NbmS7irLV4'
RAZORPAY_KEY_SECRET = 'yXn8isx70zfRMVeatgpAHfXB'
def payment_create_order(amount,customer_name,customer_number,redirect_url,membership_plan_id = None,**kwargs):
    amount                = Decimal(amount)
    print(kwargs,"====================================kwargs")
    marketing_amount      = Decimal(kwargs.get('marketing_amount')) if kwargs.get('marketing_amount',None) is not None else None
    servicing_amount      = Decimal(kwargs.get('servicing_amount')) if kwargs.get('servicing_amount',None) is not None else None
    utility_amount        = Decimal(kwargs.get('utility_amount')) if kwargs.get('utility_amount',None) is not None  else None
    authentication_balance = Decimal(kwargs.get('authentication_balance')) if kwargs.get('authentication_balance',None) is not None else None
    client                = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))
    unique_id             = str(uuid.uuid4())

    payment         = client.order.create({'amount': int(amount) * 100, 'currency': 'INR', 'payment_capture': '1'})
    # client = razorpay.Client(auth=(RAZORPAY_API_KEY, RAZORPAY_SECRET_KEY))
    expiry_time_minutes = 16
    response = client.payment_link.create({
        "amount": round(amount * 100),
        "currency": 'INR',
        "accept_partial": 'false',
        "expire_by": int(time.time() + (expiry_time_minutes * 60)),
        "description": "For XYZ purpose",
        "customer": {
            "name": customer_name,
            "contact": customer_number
        },
        "notify": {
            "sms": 'false',
            "email": 'false'
        },
        "reminder_enable": 'false',
        "notes": {
            "unique_id"             : unique_id,
            "name"                  : customer_name,
            "contact"               : customer_number,
            "membership_plan_id"    : membership_plan_id,
            'marketing_amount': float(marketing_amount) if marketing_amount is not None else None,
            'servicing_amount': float(servicing_amount) if servicing_amount is not None else None,
            'utility_amount': float(utility_amount) if utility_amount is not None else None,
            'authentication_balance': float(authentication_balance) if authentication_balance is not None else None,
        },
        "callback_url": redirect_url,
        "callback_method": "get"
    })

    url = response['short_url']
    return url,unique_id
    
# ### Subsection: PAYPAL CREATION ###

import paypalrestsdk
from django.conf import settings
from django.shortcuts import render, redirect
from django.http import JsonResponse

# Configure PayPal SDK
paypalrestsdk.configure({
    "mode": 'sandbox',  # sandbox or live
    "client_id": 'AQPX9NbHxlfmnYAdjxBpwH8sxzEwY5KzY4AOYvhh4QzuMgLxBEImFYhF_-43u9B9vAmRQQJvaJCL6BMB',
    "client_secret": 'ELpWCP5klJi62Es5MAs9n3venQNEsKdwapNRhon9sun45HNz0QfzY_F71ICvxmdF5yB4keHaurcQlk93',
})
@csrf_exempt
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def create_paypal_payment(request):
    if request.method == 'POST':
        unique_id = str(uuid.uuid4())
        amount = request.POST.get('amount')
        payment = paypalrestsdk.Payment({
            "intent": "sale",
            "payer": {
                "payment_method": "paypal"
            },
            "redirect_urls": {
                "return_url": "https://api.demo.xircls.in/talk/paypal_execute",
                "cancel_url": "http://localhost:8000/payment/cancel"
            },
            "transactions": [{
                "item_list": {
                    "items": [{
                        "name": "Item Name",
                        "sku": "item",
                        "price": amount,
                        "currency": "USD",
                        "quantity": 1
                    }]
                },
                "amount": {
                    "total": amount,
                    "currency": "USD"
                },
                #"description": "This is the payment transaction description.",
                "description": unique_id
            }]
        })

        if payment.create():
            for link in payment.links:
                if link.rel == "approval_url":
                    approval_url = str(link.href)
                    return JsonResponse({'approval_url': approval_url})
        else:
            return JsonResponse({'error': payment.error})


@csrf_exempt
def execute_paypal_payment(request):
    payment_id = request.GET.get('paymentId')
    payer_id = request.GET.get('PayerID')

    payment = paypalrestsdk.Payment.find(payment_id)
    print(payment)
    print("******************************************************************paypal*******************************************************************")

    if payment.execute({"payer_id": payer_id}):
        return JsonResponse({'status': 'Payment executed successfully'})
    else:
        return JsonResponse({'error': payment.error})

# ### Subsection: PAYPAL WEBHOOK ###
@csrf_exempt
def paypal_webhook(request):
    print(request.body,'================paypal_webhook')
    data = request.body
    json_data = json.loads(data.decode('UTF-8'))
    event = json_data.get("event_type")
    print(event)
    print("******************************************************************paypal*******************************************************************")
    if event == "PAYMENTS.PAYMENT.CREATED":
        status         = json_data.get("resource", {}).get("state")
        id             = json_data.get("id"),
        summary        = json_data.get("summary")
        transaction_id = json_data.get("resource", {}).get("id")
        currency       = json_data.get("resource", {}).get("transactions", [{}])[0].get("amount", {}).get("currency")
        merchant_id    = json_data.get("resource", {}).get("transactions", [{}])[0].get("payee", {}).get("merchant_id")
        email          = json_data.get("resource", {}).get("transactions", [{}])[0].get("payee", {}).get("email")
        description    = json_data.get("resource", {}).get("transactions", [{}])[0].get("description")
        tax            = json_data.get("resource", {}).get("transactions", [{}])[0].get("item_list", {}).get("items", [{}])[0].get("tax")
        shipping_address = json_data.get("resource", {}).get("transactions", [{}])[0].get("item_list", {}).get("shipping_address")
        payer_id       = json_data.get("resource", {}).get("payer", {}).get("payer_info", {}).get("payer_id")
        parent_payment = json_data.get("resource", {}).get("transactions", [{}])[0].get("related_resources", [{}])[0].get("sale", {}).get("parent_payment")
        transaction_fee_value = json_data.get("resource", {}).get("transactions", [{}])[0].get("related_resources", [{}])[0].get("sale", {}).get("transaction_fee", {}).get("value")
        transaction_fee_currency = json_data.get("resource", {}).get("transactions", [{}])[0].get("related_resources", [{}])[0].get("sale", {}).get("transaction_fee", {}).get("currency")
        payment_mode   = json_data.get("resource", {}).get("transactions", [{}])[0].get("related_resources", [{}])[0].get("sale", {}).get("payment_mode")
        print(f"status: {status}")
        print(f"id: {id}")
        print(f"summary: {summary}")
        print(f"transaction_id: {transaction_id}")
        print(f"currency: {currency}")
        print(f"merchant_id: {merchant_id}")
        print(f"email: {email}")
        print(f"description: {description}")
        print(f"tax: {tax}")
        print(f"shipping_address: {shipping_address}")
        print(f"payer_id: {payer_id}")
        print(f"parent_payment: {parent_payment}")
        print(f"transaction_fee_value: {transaction_fee_value}")
        print(f"transaction_fee_currency: {transaction_fee_currency}")
        print(f"payment_mode: {payment_mode}")

    if event == "PAYMENT.SALE.COMPLETED":
        id           = json_data.get("id")
        summary      = json_data.get("summary")
        total        = json_data.get("resource", {}).get("amount", {}).get("total")
        currency     = json_data.get("resource", {}).get("amount", {}).get("currency")
        payment_mode = json_data.get("resource", {}).get("payment_mode")
        transaction_fee_currency = json_data.get("resource", {}).get("transaction_fee", {}).get("currency")
        transaction_fee_value    = json_data.get("resource", {}).get("transaction_fee", {}).get("value")
        parent_payment           = json_data.get("resource", {}).get("parent_payment")
        state                    = json_data.get("resource", {}).get("state")
        transaction_id           = json_data.get("resource", {}).get("id")


        print(f"id: {id}")
        print(f"summary: {summary}")
        print(f"total: {total}")
        print(f"currency: {currency}")
        print(f"payment_mode: {payment_mode}")
        print(f"transaction_fee_currency: {transaction_fee_currency}")
        print(f"transaction_fee_value: {transaction_fee_value}")
        print(f"parent_payment: {parent_payment}")
        print(f"state: {state}")
        print(f"transaction_id: {transaction_id}")
    print(json_data)
    
    return HttpResponse(status=200)

# ##############################################################################################################################################
# Section: ADMIN 
# ##############################################################################################################################################     
# ### Subsection: ADMIN WEBHOOK ###

"""""
WEBHOOK_SHARED_SECRET = "a132cf9446963a99d25bc"

def create_hash(text, secret):
    return hmac.new(secret.encode(), text.encode(), hashlib.sha256).hexdigest()

@csrf_exempt
def admin_webhook(request):
    try:
        notification = json.loads(request.body.decode('UTF-8'))
        print(notification)
        received_signature = request.headers.get("x-aisensy-signature")
        #print(received_signature)
        #notification_str = json.dumps(notification, separators=(',', ':'))
        generated_signature = create_hash(json.dumps(notification), WEBHOOK_SHARED_SECRET)
        #print(generated_signature)
        
        if received_signature == generated_signature:
            print(notification)
            print("<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<  notification>>>>>>>>>>>>>>>>>")
            return JsonResponse({"message": "Signature Matched"}, status=200)
        else:
            print("didnt match")
            print("<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<  notification>>>>>>>>>>>>>>>>>")
            return HttpResponse(status=200)
    except Exception as err:
        print(err)
        return HttpResponse(status=200)  
    
    
""""" 
    

@csrf_exempt
def admin_webhook(request):
    try:
       notification = json.loads(request.body.decode('UTF-8')) 
       #print("Raw Body:", notification)
       return HttpResponse(status=200) 
    except Exception as err:
        print(err)
        return HttpResponse(status=200) 
"""""
def admin_webhook_proccess(notification):
    try:
        topic = notification.get('topic', None)
        if topic ==  'project-wc-created':
            business_id = notification.get('business_id')
            project_id = notification.get('project_id')
            created_at = notification.get('created_at')
            billing = notification.get('billing', {})
            central_balance = billing.get('centralBalance', {})
            template_credit = billing.get('templateCredit', {})
            central_amount_deducted = central_balance.get('amountDeducted')
            central_offset = central_balance.get('offset')
            template_amount_deducted = template_credit.get('amountDeducted')
            template_offset = template_credit.get('offset')
            message_data = notification.get('data', {}).get('message', {})
            whatsapp_conversation_details = message_data.get('whatsapp_conversation_details', {})
            message_type = whatsapp_conversation_details.get('type')
            message_id = whatsapp_conversation_details.get('id')
            project_instance = ProjectDetails.object.get(project_id = project_id)
            business_instance = BusinessDetails.object.get(business_id = business_id)
            message_log_instance = MessageLog.object.get(message_id=message_id)
            amount = central_amount_deducted / central_offset
            created_at = 
            AdminSideBiling.object.create(Project=project_instance.id,business=business_instance.id,message_log=message_log_instance.id,message_type=message_type,transaction_type = 'Debited',amount = amount)
  
"""""

# ##############################################################################################################################################
# Section: ORDER WEBHOOK 
# ##############################################################################################################################################     
# ### Subsection: ORDER WEBHOOK ###
@csrf_exempt
def order_webhook(request):
    try:

        shopify_app = request.META.get('HTTP_X_SHOPIFY_SHOP_DOMAIN')
        trigger = request.META.get('HTTP_X_SHOPIFY_TOPIC')
        test                   = request.body
        data                   = json.loads(test.decode('UTF-8'))
        print("data>>>>>>>>>>>>1928", data)
        print("data>>>>>>>>>>>>1929", test)
        print("shopify_app", shopify_app)
        referee_email           = data.get('email')
        headers = request.META
        for key, value in headers.items():
            print(f"{key}: {value}")
        try:
            outlet_obj = outlet_details.objects.get(web_url = shopify_app)
        except:
            outlet_obj = None
        else:
            try:
                flow_check = Flowcheck(outlet_instance=outlet_obj ,trigger=trigger)
                active_campaign = flow_check.check_active_campaign()
                print(active_campaign,"=========================================1310active")
                if active_campaign is not None:
                    customer_list = get_customer_list_trigger(shopify_app,trigger,data)
                    print(customer_list[0].get('id'),"====================================================customer_list1")
                    phone_no = customer_list[0].get('phone_code') + customer_list[0].get('contact')
                    flow_check.update_value(customer_list,phone_no)
                    print(customer_list,"====================================>customer_list")
                    kwargs = {
                        'create' : True,
                        'customer_data' : customer_list,
                        'campaign_instances' : active_campaign
                    }
                    print(kwargs,"====================================kwargs")
                    customer_flow_instance = flow_check.check_customer_flow_log(**kwargs)
                    if customer_flow_instance is not None:
                        print(customer_flow_instance,"========================================step3")
                        print(customer_flow_instance[0],"========================================step3")
                        customer_flow_instance = customer_flow_instance[0]
                        print(customer_flow_instance,"========================================step4")
                        flow_check.trigger_action(customer_flow_instance,None)
            except Exception as e:
                print(str(e),"========================================flow_error")
                pass
            try:
                campaign_object = WhatsappCampaign.objects.get(is_active=1, shop=shopify_app, outlet_id=outlet_obj.id, trigger=trigger)
                json_data = json.loads(campaign_object.custom_json).get('converted_flow_data')
            except Exception as e:
                print(str(e), "<<<<<<<<<<<<<<<<<==1988")
                return JsonResponse({'message': 'true'}, status=200)
            else:

                try:
                    template_instance = TemplateDetails.objects.get(templateId = json_data.get('template'))
                except:
                    template_instance = None
                    return JsonResponse({'message': 'true'}, status=200)
                
                business_instance   = BusinessDetails.objects.get(outlet=outlet_obj)

                customer_list = get_customer_list_trigger(shopify_app,trigger,data)

                print(customer_list,"===========================customer_list2")
                button_variables = []

                msg_send = MessageSender(
                    button_variables=button_variables,
                    template_instance=template_instance,
                    campaign_id=campaign_object.id
                )

                message_thread = threading.Thread(target=msg_send.send_messages, args=(customer_list,))
                message_thread.start()

            return JsonResponse({'message': 'true'}, status=200)
        return JsonResponse({'message': 'true'}, status=200)
    except Exception as e:
        print(str(e),"============================erore123")
        return JsonResponse({'message': 'true'}, status=200)
     
# def fetch_customer_data_from_cart(cart_token, shopify_obj):

#     url = f"https://{shopify_obj.shop}/admin/api/{SHOPIFY_API_YEAR}/graphql.json"
    
#     headers = {
#         "X-Shopify-Access-Token": shopify_obj.access_token,
#         "Content-Type": "application/json"
#     }
    
#     query = """
#     {
#       cart(cartId: "%s") {
#         customer {
#           id
#           email
#           firstName
#           lastName
#         }
#       }
#     }
#     """ % cart_token

#     response = requests.post(url, json={'query': query}, headers=headers)
    
#     if response.status_code == 200:
#         print(response.json(), '===================4206')
#         cart_data = response.json().get('data', {}).get('cart', {})
#         customer_data = cart_data.get('customer')
#         if customer_data:
#             return customer_data
#         else:
#             print("Customer data not found in cart.")
#             return {}
#     else:
#         print(f"Failed to fetch cart data: {response.json()}")
#         return {}

def get_customer_list_trigger(shopify_app,trigger,data):
    try:
        shopify_obj = ShopifyXirclsApp.objects.get(shop=shopify_app,app="whatsapp")
    except Exception as e:
        print("eeeeeeeee", str(e))
    first_name = ""
    last_name = ""
    customer_name = ""
    contact_number = ""
    order_details = ""
    billing_address = ""
    customer_list = transform_data(data)

    if trigger == 'orders/create':
        contact_number = data['billing_address']['phone'] if data['billing_address']['phone'] else data['customer']['phone']
        first_name = data['billing_address']['first_name'] if data['billing_address']['first_name'] else data['customer']['first_name']
        last_name = data['billing_address']['last_name'] if data['billing_address']['last_name'] else data['customer']['last_name']

        product_details = [f"{i['name']}-{i['price']}" for i in data["line_items"]]
        order_details = ' & '.join(product_details)

        print(order_details)

    elif trigger == 'carts/create':
        # customer_data = fetch_customer_data_from_cart(customer_list[0].get('token'), shopify_obj)
        # print(customer_data, "customer_data========")
        pass

    elif trigger == 'checkouts/delete':
        pass

    elif trigger == 'checkouts/create':

        contact_number = data['billing_address']['phone'] if data['billing_address']['phone'] else data['customer']['phone']
        first_name = data['billing_address']['first_name'] if data['billing_address']['first_name'] else data['customer']['first_name']
        last_name = data['billing_address']['last_name'] if data['billing_address']['last_name'] else data['customer']['last_name']

    elif trigger == 'carts/create':
        pass

    elif trigger == 'collection_listings/add':
        pass

    elif trigger == 'collections/create':
        pass

    elif trigger == 'draft_orders/create':
        
        contact_number = data['billing_address']['phone'] if data['billing_address']['phone'] else data['customer']['phone']
        first_name = data['billing_address']['first_name'] if data['billing_address']['first_name'] else data['customer']['first_name']
        last_name = data['billing_address']['last_name'] if data['billing_address']['last_name'] else data['customer']['last_name']

    elif trigger == 'draft_orders/delete':
        pass

    elif trigger == 'customers_email_marketing_consent/update':
        url = f"https://{shopify_app}/admin/api/{SHOPIFY_API_YEAR}/customers/{data['customer_id']}.json"
        headers = {
            'X-Shopify-Access-Token' : shopify_obj.access_token,
            'Content-Type': 'application/json',
            'accept': 'application/json'
        }
        customer_reponse = json.loads(requests.get(url, headers=headers).text)
        print(customer_reponse, "========4560")
        print(customer_reponse.get('customer').get('phone'), "========4560")

        contact_number = customer_reponse.get('customer').get('phone') if customer_reponse.get('customer').get('phone') else ''
        first_name = customer_reponse.get('customer').get('first_name') if customer_reponse.get('customer').get('first_name') else ''
        last_name = customer_reponse.get('customer').get('last_name') if customer_reponse.get('customer').get('last_name') else ''



    elif trigger == 'customers_marketing_consent/update':
        contact_number = data['phone'] if data['phone'] else ""


    elif trigger == 'fulfillments/update':
        contact_number = data['destination']['phone'] if data['destination']['phone'] else ''
        first_name = data['destination']['first_name'] if data['destination']['first_name'] else ''
        last_name = data['destination']['last_name'] if data['destination']['last_name'] else ''

        
    elif trigger == 'fulfillments/create':
        print(data['destination'], "======")
        contact_number = data['destination']['phone'] if data['destination']['phone'] else ''
        first_name = data['destination']['first_name'] if data['destination']['first_name'] else ''
        last_name = data['destination']['last_name'] if data['destination']['last_name'] else ''


    customer_name = str(first_name) + str(last_name) if first_name and last_name else ""
    phone_number = re.compile(r'^\+?91')
    phone_number = phone_number.sub('',contact_number)

    for customer in customer_list:
        customer['first_name'] = first_name
        customer['last_name'] = last_name
        customer['customer_name'] = customer_name
        customer['contact'] = phone_number
        customer['phone_code'] = "91"
        customer['order_details'] = order_details
    return customer_list

# ##############################################################################################################################################
# Section: TEST WEBHOOK 
# ##############################################################################################################################################     
@csrf_exempt
def webhook_test(request):
    print(request.body,'================razorpay_webook')
    data = request.body
    requested_instance = json.loads(data.decode('UTF-8'))
    return HttpResponse(status=200)

@csrf_exempt
def wb_webhook(request):
    print(request.body,'================wb_webhook')
    data = request.body
    requested_instance = json.loads(data.decode('UTF-8'))
    return HttpResponse(status=200)
# ##############################################################################################################################################
# Section: FUNCTIONS 
# ##############################################################################################################################################     
class CustomerDict:
    
    def __init__(self, **kwargs):
        self.cust_instance      = kwargs.get('cust_instance',{})
    
    def update_customer(self,cust_dict,json_data):
        print(cust_dict,json_data,"==================================================>>cust_dict,json_data")
        json_data = dict(json_data)
        for key, value in json_data.items():
            if cust_dict.get('key') is not None:
                cust_dict[key] = value
            else:
                cust_dict[key] = value
        return cust_dict
    
    def create_data_dict(self, cust_instance):
        try:
            return {
                'FirstName'              : cust_instance.first_name,
                'LastName'               : cust_instance.last_name,
                'contact'                : cust_instance.contact,
                'phone_code'             : cust_instance.phone_code,
                'phone_number_with_code' : None,
            }
        except:
            data_dict = {}
            extra_key = ['first_name', 'last_name', 'customer_name']
            extra_fields = {'first_name': 'FirstName', 'last_name': 'LastName', 'customer_name': 'customerName'}
            print(cust_instance,"===========================================")
            for key, value in cust_instance.items():
                if key == "contact":
                    print(key,value,"================================>key,value")
                if key not in extra_key:
                    data_dict[key] = str(cust_instance.get(key, ''))
                elif key == 'phone_code':
                    data_dict[key] = str(cust_instance.get(key, '91'))
                else:
                    data_dict[extra_fields[key]] = str(cust_instance.get(key, ''))
                    
            return data_dict
        

# ### Subsection: GET FILE FROM AISENSY ###
class FileHandler:
    
    def __init__(self, phone_no, direct_server):
        self.phone_no = phone_no
        self.direct_server = direct_server

    def get_file(self, messages):
        try:
            type_id = None
            if 'image' in messages:
                type_id = messages['image']['id']
            elif 'video' in messages:
                type_id = messages['video']['id']
            elif 'document' in messages:
                type_id = messages['document']['id']
            elif 'audio' in messages:
                type_id = messages['audio']['id']
            if type_id is None:
                return None

            print(type_id, "==========type_id")

            project = ProjectDetails.objects.annotate(
                phone_number=Concat(F('phone_code'), F('phone_no'))
            ).get(phone_number=self.phone_no)
            token = project.token
            url = f'{self.direct_server}/get-media/'
            payload = {'id': type_id}
            headers = {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {token}'
            }
            response = requests.post(url, headers=headers, json=payload)
            response_data = response.json()
            binary_data = bytes(response_data['data'])
            return ContentFile(binary_data)

        except Exception as e:
            print(str(e), '===================')
            return None

    def get_document_type(self, content_file):
        mime_type = magic.from_buffer(content_file.read(1024), mime=True)
        mime_to_extension = {
            'application/pdf': 'pdf',
            'application/msword': 'doc',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'docx',
        }
        return mime_to_extension.get(mime_type, 'bin')

    def save_file_and_get_link(self, file_data, file_type, content_file):
        file_name = f'file.{file_type}'
        file_data.save(file_name, content_file)
        return f'{XIRCLS_DOMAIN}/static{file_data.url}'

# ### Subsection: GET CONTACT PHONE CODE AND PHONE NUMBER SEPARATED ###
def get_phone_code(phone_number):
    if not phone_number.startswith('+'):
        phone_number = '+' + phone_number
    parsed_number = phonenumbers.parse(phone_number)
    country_code  = parsed_number.country_code
    contact_no    = parsed_number.national_number
    print(country_code,contact_no)
    return country_code , contact_no

# ### Subsection: TIMELINE UPDATE ###
def timeline_update(outlet_obj, web_url, field_name, value, project_api_key=None):
    try:
        print(outlet_obj, web_url, field_name, value, project_api_key,"========================================")
        outlettimeline_obj = OutletTimeline.objects.filter(outlet=outlet_obj, shop=web_url, app='whatsapp')
        if project_api_key is not None:
            outlettimeline_obj = outlettimeline_obj.filter(whatsapp_project__api_key=project_api_key)
            if outlettimeline_obj.last() is None:
                project_instance   = ProjectDetails.objects.get(api_key=project_api_key)
                outlettimeline_obj = OutletTimeline.objects.filter(outlet=outlet_obj, shop=web_url, app='whatsapp',whatsapp_project__isnull=True)
                if outlettimeline_obj.last() is not None:
                    outlettimeline_obj.update(whatsapp_project = project_instance)
                    outlettimeline_obj.last()
                else:
                    outlettimeline_obj = OutletTimeline.objects.create(outlet=outlet_obj,is_business=True,is_plugin_installed = True,shop=web_url, app='whatsapp',whatsapp_project=project_instance)
            else:
                outlettimeline_obj = outlettimeline_obj.last()  
        else:
            outlettimeline_obj = outlettimeline_obj.last()       
    except OutletTimeline.DoesNotExist:
        outlettimeline_obj = OutletTimeline(outlet=outlet_obj, shop=web_url, app='whatsapp')
    print(outlettimeline_obj, field_name, value,"==============================")
    try:
        setattr(outlettimeline_obj, field_name, value)
    except Exception as e:
        print(str(e),"=======================error")
    outlettimeline_obj.save()
    return outlettimeline_obj

def send_message(data):
    data = data
    token = data['token']
    url = f'{direct_server}/messages'

    headers     = {
        'Accept'        : 'application/json',
        'Content-Type'  : 'application/json',
        'Authorization' : f'Bearer {token}'
    }    
    
    
    template_name       = data['template_name']
    template            = TemplateDetails.objects.get(templateName=template_name)
    phone               = data.get('contact')
    type                = data['type']
    language            = 'en'
    header_variables    = data.get('header_variables',None)
    body_variables      = data.get('body_variables',None)
    button_variables    = data.get('button_variables', None)

    file_type           = type.lower()
    
    payload = {
        "to"    :phone,
        "type"  : "template",
        "template":{
            "language"  : {
                "policy"    : "deterministic",
                "code"      : language
            },
            "name"      : template_name,
            "components": []
        }
    }
        
    components = []
    try:
        file = data.get('file')
        template.file_data  = file
        template.file_type  = file_type
        template.save()
        
        path = template.files.url
        link = f'{XIRCLS_DOMAIN}' + path
    except:
        link = None
    if type == "TEXT":
        
        if header_variables is not None:
            # header_variables = json.loads(header_variables)
            components.append({
                "type"          : "header",
                "parameters"    : header_variables
            })
        if body_variables is not None:   
            # body_variables = json.loads(body_variables)
            components.append({
                "type"          : "body",
                "parameters"    : body_variables
            })
        if button_variables is not None:
            # button_variables = json.loads(button_variables)
            components.append({
                "type": "button",
                "sub_type": "url",
                "index": "0",
                "parameters": button_variables
            })
            
        payload['template']['components'] = components    
    
    elif type == 'IMAGE' or type == 'VIDEO' or type == 'DOCUMENT':
        # payload     = json.loads(template.payload)
        # link = payload['components'][0]['example']['header_handle'][0]
        components.append(
            {
                "type": "header",
                "parameters": [
                {
                    "type": file_type,
                    file_type: {
                        "link": link
                    }
                }
                ]
        })
            
        if body_variables is not None:
            body_variables = json.loads(body_variables)
            components.append({
                "type": "body",
                "parameters": body_variables
            })
        if button_variables is not None:
            button_variables = json.loads(button_variables)
            components.append({
                "type": "button",
                "sub_type": "url",
                "index": "0",
                "parameters": button_variables
            })
        payload['template']['components'] = components     
    payload = json.dumps(payload, indent =4)

    response = requests.request("POST", url, headers=headers, data=payload).json()
    return True

def fbStatuschecktimeline(api_key,project_api_key):
    '''
    takes outlet id and based on outlet id  gives the 
    business detail object from which we get the required fields
    '''
    outlet_obj = outlet_details.objects.get(api_key = api_key)
    business = BusinessDetails.objects.get(outlet=outlet_obj)
    print(api_key,project_api_key,"=========================================api_key,project_api_key")
    try:
        project_list = ProjectDetails.objects.filter(api_key=project_api_key)
    except Exception as e:
        print(str(e),"=============================erro")
        return False
    else:
        if project_list.filter(is_fb_verified =True):
            return True
    username = business.email
    password = business.password
    fb_status_code =[]
    print(project_list,"======================project_list")
    def process_theme(project):
        return checkprojectstatus(project,username,password)
    with concurrent.futures.ThreadPoolExecutor() as executor:
        fb_status_code = list(executor.map(process_theme, project_list))
    if any(fb_status_code):   
        timeline_update(outlet_obj,outlet_obj.web_url,'is_fb_verified',True,project_api_key)
        return True
    else:
        return False

def checkprojectstatus(project,username,password):
    project_id      = project.project_id
    token_string    = f"{username}:{password}:{project_id}"
    encoded_bytes   = base64.b64encode(token_string.encode('utf-8'))
    token           = encoded_bytes.decode('utf-8')
    url             = f'{direct_server}/users/regenrate-token'
    headers         = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    response        = requests.post(url, headers=headers)
    token           = response.json()['users'][0]['token']
    # token           = project_instance.token 
    url=f'{direct_server}/fb-verification-status'
    
    headers={
        'Authorization':f'Bearer {token}'
    }
    status = requests.get(url,headers=headers).json()
    print(status,"==============================fbstatus")
    verificationStatus          = status.get('verificationStatus',None)
    if verificationStatus == 'verified':
        message='Your WhatsApp buisness account is verified....'
        fb_status_code = True
    else:
        fb_status_code = False
        message = 'Your WhatsApp buisness account is not verified....'
    project.token = token
    project.is_fb_verified = fb_status_code
    project.save()
    url             = f'{direct_server}/settings/update-webhook'
    headers         = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    payload = {
        'webhook' : {
            'url' : f'{XIRCLS_DOMAIN}/talk/waba/webhook_handler/'
        }
    }
    response = requests.patch(url, headers=headers, json=payload)
    return fb_status_code

def delete_webhook(shop, access_token, webhook_id):
    webhook_url = f"https://{shop}/admin/api/{SHOPIFY_API_YEAR}/webhooks/{webhook_id}.json"

    headers = {
        'X-Shopify-Access-Token' : access_token,
        'Content-Type': 'application/json',
        'accept': 'application/json'
    }

    webhook_response = json.loads(requests.delete(webhook_url, headers = headers).text)

    return webhook_response

def transform_data(input_data):
    # input_data = json.loads(input_Data)
    def flatten_json(y, preserve_keys):
        out = {}

        def flatten(x, name=''):
            if isinstance(x, dict):
                for a in x:
                    flatten(x[a], name + a + '_')
            elif isinstance(x, list) and name[:-1] not in preserve_keys:
                for i, a in enumerate(x):
                    flatten(a, name + str(i) + '_')
            else:
                out[name[:-1]] = x

        flatten(y)
        return out

    # Determine which keys to preserve based on input_data
    preserve_keys = [key for key, value in input_data.items() if isinstance(value, list) and all(not isinstance(i, dict) for i in value)]

    flattened_data = flatten_json(input_data, preserve_keys)
    return [flattened_data]
    
######################### BILLING #########################

@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def wallet_credit(request):
    try:
        outlet_api_key          = request.META.get('HTTP_API_KEY')
        project_api_key         = request.META.get('HTTP_WHATSAPP_PROJECT_KEY')
        if outlet_api_key is None :
                return JsonResponse({"error": "outlet_api_key is missing"}, status=404)
        elif project_api_key is None :
            return JsonResponse({"error": "project_api_key is missing"}, status=404)
        else:
            pass
        outlet_obj       = outlet_details.objects.get(api_key = outlet_api_key)
        project          = ProjectDetails.objects.get(api_key = project_api_key)
        subscription_obj = PlanSubscription.objects.get(project = project , outlet = outlet_obj)
        amount           = round(Decimal(request.POST.get('amount'))* Decimal('1.18'),3)
        remark           = request.POST.get('remark',None)
        print(amount,project,outlet_obj,"===========================================")
        if subscription_obj.end_date < timezone.now():
            return JsonResponse({"error": "Subscription is Expired purches Subscription first then add found in wallet"}, status=status.HTTP_403_FORBIDDEN)
        else:
            pass
        business_obj    = project.business
        customer_name   = business_obj.company
        customer_number = business_obj.phone_code + business_obj.contact
        redirect_url    = "https://xircls.in/merchant/whatsapp/Billing/"
        # from decimal import Decimal, InvalidOperation

        def get_decimal_value(value):
            try:
                return round(Decimal(value), 3)
            except:
                return Decimal('0.000')  # or any other default value you prefer
        marketing_amount = get_decimal_value(request.POST.get('marketing_amount'))
        servicing_amount = get_decimal_value(request.POST.get('servicing_amount'))
        utility_amount = get_decimal_value(request.POST.get('utility_amount'))
        authentication_balance = get_decimal_value(request.POST.get('authentication_balance'))
        kwargs = {
            'marketing_amount': marketing_amount,
            'servicing_amount': servicing_amount,
            'utility_amount': utility_amount,
            'authentication_balance': authentication_balance,
        }

        url,unique_id   = payment_create_order(amount,customer_name,customer_number,redirect_url,**kwargs)
        try:
           oulateWalletDetails_obj = WhatsappWallet.objects.get(outlet=outlet_obj, project = project)
        except WhatsappWallet.DoesNotExist:
            oulateWalletDetails_obj = WhatsappWallet.objects.create(
                outlet   =   outlet_obj,
                business = business_obj,
                project  = project,
                total_balance = 0,
                balance  = 0
                # last_topup = datetime.now()
            )
        """""

        try:
            oulateWalletDetails_obj = WhatsappWallet.objects.get(outlet=outlet_obj)
            oulateWalletDetails_obj.total_balance += float(amount)
            oulateWalletDetails_obj.balance += float(amount)
            oulateWalletDetails_obj.last_topup = datetime.now()
            oulateWalletDetails_obj.save()
        except WhatsappWallet.DoesNotExist:
            oulateWalletDetails_obj = WhatsappWallet.objects.create(
                outlet   =   outlet_obj,
                business = business_obj,
                project  = project,
                total_balance = amount,
                balance  = amount,
                last_topup = datetime.now()
                )
        """""
        wallet_transaction = WhatsappWalletTransaction.objects.create(
            unique_id                = unique_id,
            shop                     = outlet_obj.web_url,
            outlet                   = outlet_obj,
            project                  = project,
            business                 = business_obj,
            wallet                   = oulateWalletDetails_obj,
            payment_status           = 'Credit',
            payment_date             = datetime.now(),
            original_balance_amount  = oulateWalletDetails_obj.total_balance,
            balance_amount           = round(Decimal(oulateWalletDetails_obj.total_balance) + Decimal(request.POST.get('amount')),3),
            credit_amount            = Decimal(request.POST.get('amount')),
            remarks                  = remark,
            payment_stage            = 'Initiated',
            gst_perc                 = 18.00,
            gst_amount               = round(Decimal(request.POST.get('amount')) * Decimal('0.18'),3),
            amount                   = Decimal(request.POST.get('amount')),
            amount_with_gst          = round(Decimal(request.POST.get('amount'))* Decimal('1.18'),3)
        )
        print(wallet_transaction.transaction_no,"======================transaction_no")
        return JsonResponse({"Payment_Link": url}, status=status.HTTP_200_OK)  
    except (outlet_details.DoesNotExist,ProjectDetails.DoesNotExist,ProjectDetails.MultipleObjectsReturned,outlet_details.MultipleObjectsReturned,PlanSubscription.DoesNotExist,PlanSubscription.MultipleObjectsReturned) as e:
        if isinstance(e, outlet_details.DoesNotExist):
            return JsonResponse({"error": "Invalid API Key outlet details not found"}, status=404)
        elif isinstance(e, outlet_details.MultipleObjectsReturned):
                return JsonResponse({"error": "Multiple outlets found with the same API Key"}, status=400)
        elif isinstance(e, ProjectDetails.DoesNotExist):
            return JsonResponse({"error": "Project details not found"}, status=404)
        elif isinstance(e, ProjectDetails.MultipleObjectsReturned):
                return JsonResponse({"error": "Multiple projects found with the same API Key"}, status=400)
        elif isinstance(e, PlanSubscription.MultipleObjectsReturned):
                return JsonResponse({"error": "Subsciption details not found!"}, status=400)
        elif isinstance(e, PlanSubscription.MultipleObjectsReturned):
                return JsonResponse({"error": "Multiple Subsciption details found with the given id"}, status=400)
    except Exception as e:
        print(str(e))
        print("======================== ERROR ==============================")
        return JsonResponse({"error": "Something went wrong!"}, status=500)
        
     
@api_view(['POST'])
@authentication_classes([])
@permission_classes([AllowAny])
def get_membership_plans(request):
    try:
        try:
            outlet_api_key          = request.META.get('HTTP_API_KEY')
            project_api_key         = request.META.get('HTTP_WHATSAPP_PROJECT_KEY')
            if outlet_api_key is None :
                return JsonResponse({"error": "outlet_api_key is missing"}, status=404)
            elif project_api_key is None :
                return JsonResponse({"error": "project_api_key is missing"}, status=404)
            else:
                pass
            outlet_obj            = outlet_details.objects.get(api_key = outlet_api_key)
            membership_plan_obj   = MembershipPlan.objects.filter(status = True,outlet=outlet_obj)
            if request.META.get('HTTP_WHATSAPP_PROJECT_KEY') is not None:
                project_obj = ProjectDetails.objects.get(api_key = project_api_key)
                membership_plan_obj   = membership_plan_obj.filter(outlet=outlet_obj)
            if membership_plan_obj.last() is None:
                membership_plan_obj = MembershipPlan.objects.filter(status=True, outlet=outlet_obj, project__isnull=True)
            if membership_plan_obj.last() is None:
                membership_plan_obj   = MembershipPlan.objects.filter(status = True, outlet__isnull=True, project__isnull=True)
            if membership_plan_obj:
                serialized_data   = MembershipPlanSerializer(membership_plan_obj, many=True).data
                return JsonResponse(serialized_data,safe=False, status=status.HTTP_200_OK)
            else:
                return JsonResponse({"message": "No plan found"}, status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            datatables = request.POST
            print(datatables)
            start = int(datatables.get('page'))
            length = int(datatables.get('size'))
            over_all_search = datatables.get('searchValue')
            field_mapping = {
                0:  "membership_plan_name__icontains",
                1:  "plan_price__icontains",
                2:  "discount__icontains",
                3:  "price_after_discount__icontains",
                4:  "outlet__outlet_name__icontains",
                5:  "project__project_name__icontains",
                6:  "plan_period_unit__icontains",
                7:  "plan_duration__icontains",
            }
        
            advance_filter = Q()
            for col, field in field_mapping.items():
                value = datatables.get(f"columns[{col}][search][value]", None)
                if value:
                    advance_filter &= Q(**{field: value})
            if over_all_search:
                overall_search_filter = Q()
                for field in field_mapping.values():
                    overall_search_filter |= Q(**{field: over_all_search})
                advance_filter |= overall_search_filter
            membership_plan_obj   = MembershipPlan.objects.filter(status = True).values(
                member_membership_plan_name = F('membership_plan_name'),
                member_membership_plan_id = F('id'),
                member_plan_price = F('plan_price'),
                member_discount = F('discount'),
                member_price_after_discount = F('price_after_discount'),
                member_deduction_plan = F('deduction_plan'),
                member_plan_duration = F('plan_duration'),
                member_plan_period_unit = F('plan_period_unit'),
                member_project_name = F('project__project_name'),
                member_outlet = F('outlet__outlet_name'),
            )
            member_obj_count = membership_plan_obj.count()
            paginator = Paginator(membership_plan_obj, length)
            try:
                object_list = paginator.page(start).object_list
            except (PageNotAnInteger, EmptyPage):
                object_list = paginator.page(1).object_list
            
            response = {
                'membership_plan_obj_count': member_obj_count,
                "membership_plan_obj": list(object_list)
            }
            return JsonResponse(response, status=status.HTTP_200_OK)
    except (outlet_details.DoesNotExist,ProjectDetails.DoesNotExist,ProjectDetails.MultipleObjectsReturned,outlet_details.MultipleObjectsReturned) as e:
        if isinstance(e, outlet_details.DoesNotExist):
            return JsonResponse({"error": "Invalid API Key outlet details not found"}, status=404)
        elif isinstance(e, outlet_details.MultipleObjectsReturned):
                return JsonResponse({"error": "Multiple outlets found with the same API Key"}, status=400)
        elif isinstance(e, ProjectDetails.DoesNotExist):
            return JsonResponse({"error": "Project details not found"}, status=404)
        elif isinstance(e, ProjectDetails.MultipleObjectsReturned):
                return JsonResponse({"error": "Multiple projects found with the same API Key"}, status=400)
    except Exception as e:
        print(str(e))
        print("======================== ERROR ==============================")
        return JsonResponse({"error": "Something went wrong!"}, status=500)

@api_view(['POST','PUT','GET'])
@authentication_classes([])
@permission_classes([AllowAny])
def membership_plans_crud(request):
    try:
        if request.method == 'GET':
            try:
                membership_plan_obj = MembershipPlan.objects.get(id = request.GET.get('membership_plan_id'))
                serialized_data     = MembershipPlanDepthSerializer(membership_plan_obj)
                return JsonResponse({"message":serialized_data.data},safe=False, status=status.HTTP_200_OK)
            except (MembershipPlan.DoesNotExist,MembershipPlan.MultipleObjectsReturned) as e:
                if isinstance(e, MembershipPlan.DoesNotExist):
                    return JsonResponse({"error": "Membership Plan details not found"}, status=404)
                elif isinstance(e, MembershipPlan.MultipleObjectsReturned):
                        return JsonResponse({"error": "Multiple Membership Plans found with the same id"}, status=400)
            except Exception as e:
                print(str(e))
                print("======================== ERROR ==============================")
                return JsonResponse({"error": "Something went wrong!"}, status=500)
        if request.method == 'POST':
            try:
                request_data = request.POST.copy()
                
                serialized_data   = MembershipPlanSerializer(data=request_data)
                if serialized_data.is_valid():
                    serialized_data.save()
                    return JsonResponse({"message": "saved successfully"}, safe=False, status=status.HTTP_200_OK)
                else:
                    return JsonResponse(serialized_data.errors, safe=False, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                return JsonResponse({'message': str(e)}, status=status.HTTP_200_OK)
        if request.method == 'PUT':
            try:
                request_data = request.POST.copy()
                print(request_data,request.POST.copy(),"==================================request_data")
                membership_plan_obj = MembershipPlan.objects.get(id = request.POST.get('membership_plan_id'))
                print(membership_plan_obj,'============membership_plan_obj')
                del request_data['membership_plan_id']
                serialized_data = MembershipPlanSerializer(data=request_data, instance=membership_plan_obj)
                if serialized_data.is_valid():
                    serialized_data.save()
                    return JsonResponse({"message": "saved successfully"}, safe=False, status=status.HTTP_200_OK)
                else:
                    return JsonResponse(serialized_data.errors, safe=False, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                return JsonResponse({'message': str(e)}, status=status.HTTP_200_OK)
    except Exception as e:
        return JsonResponse({"message": f"Error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)   
@api_view(['GET'])
@authentication_classes([])
@permission_classes([AllowAny])
def dropdown_outlet(request):
    if request.method == 'GET':
        try:
            outlet_obj        = outlet_details.objects.all()
            serialized_data   = OutletSerializer(outlet_obj,many=True)
            return JsonResponse({"message":serialized_data.data},safe=False, status=status.HTTP_200_OK)
        except Exception as e:
            return JsonResponse({'message': str(e)}, status=status.HTTP_200_OK)
    
    
@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def get_wallet_data(request):
    try:
        outlet_api_key          = request.META.get('HTTP_API_KEY')
        project_api_key         = request.META.get('HTTP_WHATSAPP_PROJECT_KEY')
        if outlet_api_key is None :
                return JsonResponse({"error": "outlet_api_key is missing"}, status=404)
        elif project_api_key is None :
            return JsonResponse({"error": "project_api_key is missing"}, status=404)
        else:
            pass
        outlet_obj  = outlet_details.objects.get(api_key = outlet_api_key)
        project_obj = ProjectDetails.objects.get(api_key = project_api_key)
        wallet_obj  = WhatsappWallet.objects.get(outlet = outlet_obj, project = project_obj)
        if wallet_obj:
            serialized_data   = WhatsappWalletSerializer(wallet_obj).data
            return JsonResponse(serialized_data,safe=False, status=status.HTTP_200_OK)
        else:
            return JsonResponse({"message": "No wallet found"}, status=status.HTTP_204_NO_CONTENT)
    except (outlet_details.DoesNotExist,ProjectDetails.DoesNotExist,ProjectDetails.MultipleObjectsReturned,outlet_details.MultipleObjectsReturned,WhatsappWallet.DoesNotExist,WhatsappWallet.MultipleObjectsReturned) as e:
        if isinstance(e, outlet_details.DoesNotExist):
            return JsonResponse({"error": "Invalid API Key outlet details not found"}, status=404)
        elif isinstance(e, outlet_details.MultipleObjectsReturned):
                return JsonResponse({"error": "Multiple outlets found with the same API Key"}, status=400)
        elif isinstance(e, ProjectDetails.DoesNotExist):
            return JsonResponse({"error": "Project details not found"}, status=404)
        elif isinstance(e, ProjectDetails.MultipleObjectsReturned):
                return JsonResponse({"error": "Multiple projects found with the same API Key"}, status=400)
        elif isinstance(e, WhatsappWallet.MultipleObjectsReturned):
                return JsonResponse({"error": "Wallet details not found"}, status=400)
        elif isinstance(e, WhatsappWallet.MultipleObjectsReturned):
                return JsonResponse({"error": "Multiple wallet found with the given project"}, status=400)
    except Exception as e:
        print(str(e))
        print("======================== ERROR ==============================")
        return JsonResponse({"error": "Something went wrong!"}, status=500)         
        
@api_view(['POST'])
@authentication_classes([])
@permission_classes([AllowAny])
@csrf_exempt
def get_wallet_transactions(request):
    try:
        outlet_api_key          = request.META.get('HTTP_API_KEY')
        project_api_key         = request.META.get('HTTP_WHATSAPP_PROJECT_KEY')
        if outlet_api_key is None :
                return JsonResponse({"error": "outlet_api_key is missing"}, status=404)
        elif project_api_key is None :
            return JsonResponse({"error": "project_api_key is missing"}, status=404)
        else:
            pass
        outlet_obj  = outlet_details.objects.get(api_key = outlet_api_key)
        project_obj = ProjectDetails.objects.get(api_key = project_api_key)
        # business_details = BusinessDetails.objects.get(outlet=outlet_obj)
        
        datatables = request.POST
        print(datatables)
        start = int(datatables.get('page'))
        length = int(datatables.get('size'))
        over_all_search = datatables.get('searchValue')
        field_mapping = {
            0:  "transaction_no__icontains",
            1:  "debit_amount__icontains",
            2:  "credit_amount__icontains",
            3:  "payment_date__icontains",
            4:  "payment_status__icontains",
            5:  "message_type__icontains",
            6:  "remarks__icontains",
            7:  "sender__icontains",
            8:  "reciever__icontains"
        }
       
        #advance_filter = Q()
        advance_filter = ~Q(payment_stage='initiated')
        for col, field in field_mapping.items():
            value = datatables.get(f"columns[{col}][search][value]", None)
            if value:
                advance_filter &= Q(**{field: value})
        if over_all_search:
            overall_search_filter = Q()
            for field in field_mapping.values():
                overall_search_filter |= Q(**{field: over_all_search})
            advance_filter &= overall_search_filter
        transactions = WhatsappWalletTransaction.objects.filter(outlet = outlet_obj,project = project_obj).filter(advance_filter).order_by('-created_at').values(
            #Outlet                     = F('outlet__name'),
            Shop                       = F('shop'),
            Transaction_no             = F('transaction_no'),
            Plan_subcription           = F('plan_subscription'),
            Plan_deduction_type        = F('plan_deduction_type'),
            Payment_status             = F('payment_status'),
            Payment_date               = F('payment_date'),
            Original_balance_amount    = F('original_balance_amount'),
            Balance_amount             = F('balance_amount'),
            Debit_amount               = F('debit_amount'),
            Credit_amount              = F('credit_amount'),
            Remarks                    = F('remarks'),
            Message_type               = F('message_type'),
            Reciever                   = F('reciever'),
            Sender                     = F('sender'),
            Block_amount               = F('block_amount'),
            Payment_stage              = F('payment_stage'),
            Payment_id                 = F('payment_id'),
            Payment_method             = F('payment_method'),
            Payment_wallet             = F('payment_wallet'),
            Error_reason               = F('error_reason')
        )
        
        contact_obj_count = transactions.count()
        paginator = Paginator(transactions, length)
        try:
            object_list = paginator.page(start).object_list
        except (PageNotAnInteger, EmptyPage):
            object_list = paginator.page(1).object_list
        
        response = {
            'transactions_count': contact_obj_count,
            "transactions": list(object_list)
        }
        return JsonResponse(response, status=status.HTTP_200_OK)
    except (outlet_details.DoesNotExist,ProjectDetails.DoesNotExist,ProjectDetails.MultipleObjectsReturned,outlet_details.MultipleObjectsReturned) as e:
        if isinstance(e, outlet_details.DoesNotExist):
            return JsonResponse({"error": "Invalid API Key outlet details not found"}, status=404)
        elif isinstance(e, outlet_details.MultipleObjectsReturned):
                return JsonResponse({"error": "Multiple outlets found with the same API Key"}, status=400)
        elif isinstance(e, ProjectDetails.DoesNotExist):
            return JsonResponse({"error": "Project details not found"}, status=404)
        elif isinstance(e, ProjectDetails.MultipleObjectsReturned):
                return JsonResponse({"error": "Multiple projects found with the same API Key"}, status=400)
    except Exception as e:
        print(str(e))
        print("======================== ERROR ==============================")
        return JsonResponse({"error": "Something went wrong!"}, status=500)



@api_view(['POST'])
@authentication_classes([])
@permission_classes([AllowAny])
@csrf_exempt
def get_child_transactions(request):
    try:

        outlet_api_key          = request.META.get('HTTP_API_KEY')
        project_api_key         = request.META.get('HTTP_WHATSAPP_PROJECT_KEY')
        if outlet_api_key is None :
                return JsonResponse({"error": "outlet_api_key is missing"}, status=404)
        elif project_api_key is None :
            return JsonResponse({"error": "project_api_key is missing"}, status=404)
        else:
            pass
        outlet_obj  = outlet_details.objects.get(api_key = outlet_api_key)
        project_obj = ProjectDetails.objects.get(api_key = project_api_key)
        # business_details = BusinessDetails.objects.get(outlet=outlet_obj)
        
        datatables = request.POST
        print(datatables)
        start = int(datatables.get('page'))
        length = int(datatables.get('size'))
        over_all_search = datatables.get('searchValue')
        field_mapping = {
            0:  "payment_date__range",
            1:  "transaction_no__icontains",
            2:  "payment_status__icontains",
            3:  "message_type__icontains",
            4:  "remarks__icontains",
            5:  "sender__icontains",
            6:  "reciever__icontains"
        }
       
        advance_filter = Q()
        for col, field in field_mapping.items():
            value = datatables.get(f"columns[{col}][search][value]", None)
            if value:
                advance_filter &= Q(**{field: value})
        if over_all_search:
            overall_search_filter = Q()
            for field in field_mapping.values():
                overall_search_filter |= Q(**{field: over_all_search})
            advance_filter |= overall_search_filter
        transactions = ChildTransactions.objects.filter(outlet = outlet_obj,project = project_obj).filter(advance_filter).order_by('-payment_date').values(
            #Outlet                     = F('outlet__name'),
                Shop              = F('shop'),
                Transaction_no    = F('transaction_no'),
                Plan_subscription = F('subscription'),
                Plan_deduction_type = F('plan_deduction_type'),
                Payment_status      = F('payment_status'),
                Payment_stage       = F('payment_stage'),
                Payment_date        = F('payment_date'),
                Original_balance_amount = F('original_balance_amount'),
                Balance_amount          = F('balance_amount'),
                Amount                  = F('amount'),
                Remarks                 = F('remarks'),
                Block_amount            = F('block_amount'),
                Payment_id              = F('payment_id'),
                Order_id                = F('order_id'),
                Unique_id               = F('unique_id'),
                Payment_method          = F('payment_method'),
                Payment_wallet          = F('payment_wallet'),
                Bank                    = F('bank'),
                Card_id                 = F('card_id'),
                Currency                = F('currency'),
                Tax                     = F('tax'),
                Fees                    = F('fees'),
                Error_code              = F('error_code'),
                Error_step              = F('error_step'),
                Error_reason            = F('error_reason'),
                Error_description       = F('error_description'),
                Created_at              = F('created_at'),
                Commission_percentage   = F('commission_percentage'),
                Gst_perc                = F('gst_perc'),
                Amount_with_gst         = F('amount_with_gst'),
                Gst_amount              = F('gst_amount'))
        contact_obj_count = transactions.count()
        paginator = Paginator(transactions, length)
        try:
            object_list = paginator.page(start).object_list
        except (PageNotAnInteger, EmptyPage):
            object_list = paginator.page(1).object_list
        
        response = {
            'transactions_count': contact_obj_count,
            "transactions": list(object_list)
        }
        return JsonResponse(response, status=status.HTTP_200_OK)
    except (outlet_details.DoesNotExist,ProjectDetails.DoesNotExist,ProjectDetails.MultipleObjectsReturned,outlet_details.MultipleObjectsReturned) as e:
        if isinstance(e, outlet_details.DoesNotExist):
            return JsonResponse({"error": "Invalid API Key outlet details not found"}, status=404)
        elif isinstance(e, outlet_details.MultipleObjectsReturned):
                return JsonResponse({"error": "Multiple outlets found with the same API Key"}, status=400)
        elif isinstance(e, ProjectDetails.DoesNotExist):
            return JsonResponse({"error": "Project details not found"}, status=404)
        elif isinstance(e, ProjectDetails.MultipleObjectsReturned):
                return JsonResponse({"error": "Multiple projects found with the same API Key"}, status=400)
    except Exception as e:
        print(str(e))
        print("======================== ERROR ==============================")
        return JsonResponse({"error": "Something went wrong!"}, status=500)


@api_view(['POST'])
@authentication_classes([])
@permission_classes([AllowAny])
@csrf_exempt
def get_plan_subscriptions_log(request):
    try:
        outlet_api_key          = request.META.get('HTTP_API_KEY')
        project_api_key         = request.META.get('HTTP_WHATSAPP_PROJECT_KEY')
        if outlet_api_key is None :
                return JsonResponse({"error": "outlet_api_key is missing"}, status=404)
        elif project_api_key is None :
            return JsonResponse({"error": "project_api_key is missing"}, status=404)
        else:
            pass
        outlet_obj  = outlet_details.objects.get(api_key = outlet_api_key)
        project_obj = ProjectDetails.objects.get(api_key = project_api_key)
        # business_details = BusinessDetails.objects.get(outlet=outlet_obj)
        
        datatables = request.POST
        print(datatables)
        start = int(datatables.get('page'))
        length = int(datatables.get('size'))
        over_all_search = datatables.get('searchValue')
        field_mapping = {
            0: "membership_plan__membership_plan_name__icontains",
            1: "start_date__icontains",
            2: "end_date__icontains",
        }
       
        advance_filter = Q()
        for col, field in field_mapping.items():
            value = datatables.get(f"columns[{col}][search][value]", None)
            if value:
                advance_filter &= Q(**{field: value})
        if over_all_search:
            overall_search_filter = Q()
            for field in field_mapping.values():
                overall_search_filter |= Q(**{field: over_all_search})
            advance_filter &= overall_search_filter
        plan_subscriptions_log_obj = PlanSubscriptionsLog.objects.filter(outlet = outlet_obj,project = project_obj).filter(advance_filter).order_by('-created_at').values(
            # Transaction_no             = F('transaction_no'),
            Shop                       = F('outlet__outlet_name'),
            Status                     = F('status'),
            Start_date                 = F('start_date'),
            End_date                   = F('end_date'),
            Created_at                 = F('created_at'),
            Deduction_plan             = F('deduction_plan'),
            Membership_plan_name       = F('membership_plan__membership_plan_name'),
            Membership_plan_price      = F('membership_plan__plan_price'),
            Transaction_no             = F('childtransaction__transaction_no')
        )
        
        contact_obj_count = plan_subscriptions_log_obj.count()
        paginator = Paginator(plan_subscriptions_log_obj, length)
        try:
            object_list = paginator.page(start).object_list
        except (PageNotAnInteger, EmptyPage):
            object_list = paginator.page(1).object_list
        
        response = {
            'plan_subscriptions_log_count': contact_obj_count,
            "plan_subscriptions_log": list(object_list)
        }
        return JsonResponse(response, status=status.HTTP_200_OK)
    except (outlet_details.DoesNotExist,ProjectDetails.DoesNotExist,ProjectDetails.MultipleObjectsReturned,outlet_details.MultipleObjectsReturned) as e:
        if isinstance(e, outlet_details.DoesNotExist):
            return JsonResponse({"error": "Invalid API Key outlet details not found"}, status=404)
        elif isinstance(e, outlet_details.MultipleObjectsReturned):
                return JsonResponse({"error": "Multiple outlets found with the same API Key"}, status=400)
        elif isinstance(e, ProjectDetails.DoesNotExist):
            return JsonResponse({"error": "Project details not found"}, status=404)
        elif isinstance(e, ProjectDetails.MultipleObjectsReturned):
                return JsonResponse({"error": "Multiple projects found with the same API Key"}, status=400)
    except Exception as e:
        print(str(e))
        print("======================== ERROR ==============================")
        return JsonResponse({"error": "Something went wrong!"}, status=500)
    
@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def check_subscription_status(request):
    try:
        outlet_api_key          = request.META.get('HTTP_API_KEY')
        project_api_key         = request.META.get('HTTP_WHATSAPP_PROJECT_KEY')
        if outlet_api_key is None :
            return JsonResponse({"error": "outlet_api_key is missing"}, status=404)
        elif project_api_key is None :
            return JsonResponse({"error": "project_api_key is missing"}, status=404)
        else:
            pass
        outlet_obj            = outlet_details.objects.get(api_key = outlet_api_key)
        plan_subscription_obj = PlanSubscription.objects.get(project__api_key = project_api_key,outlet = outlet_obj)
        current_time = timezone.now().astimezone(plan_subscription_obj.end_date.tzinfo)
        print(timezone.now())
        print(plan_subscription_obj.end_date)
        plan_subscription_serializer = PlanSubcriptionSerializer(plan_subscription_obj).data
        if plan_subscription_obj.end_date > timezone.now() and plan_subscription_obj.status == 'Active':
            time_to_expire =  plan_subscription_obj.end_date - timezone.now()
            days = time_to_expire.days
            hours, remainder = divmod(time_to_expire.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            time_to_expire_str = f"{days:02}:{hours:02}:{minutes:02}:{seconds:02}"
            plan_subscription_serializer['time_to_expire'] = time_to_expire_str
            timeline_update(outlet_obj, outlet_obj.web_url, 'is_plan_purchased', True,request.META.get('HTTP_WHATSAPP_PROJECT_KEY'))
            return JsonResponse({"subscription": True,'subscription_data':plan_subscription_serializer }, status=status.HTTP_200_OK)
        if plan_subscription_obj.end_date < timezone.now():
            plan_subscription_serializer['time_to_expire'] = 0
            plan_subscription_obj.status     = 'Expired'
            plan_subscription_obj.is_active  = False
            plan_subscription_obj.save()
            timeline_update(outlet_obj, outlet_obj.web_url, 'is_plan_purchased', False,request.META.get('HTTP_WHATSAPP_PROJECT_KEY'))
            return JsonResponse({"subscription": False,'subscription_data':plan_subscription_serializer }, status=status.HTTP_200_OK)
        else:
            return JsonResponse({"subscription": False,'subscription_data':plan_subscription_serializer }, status=status.HTTP_200_OK)
    except (outlet_details.DoesNotExist,ProjectDetails.DoesNotExist,ProjectDetails.MultipleObjectsReturned,outlet_details.MultipleObjectsReturned,PlanSubscription.DoesNotExist,PlanSubscription.MultipleObjectsReturned) as e:
        if isinstance(e, outlet_details.DoesNotExist):
            return JsonResponse({"error": "Invalid API Key outlet details not found"}, status=404)
        elif isinstance(e, outlet_details.MultipleObjectsReturned):
                return JsonResponse({"error": "Multiple outlets found with the same API Key"}, status=400)
        elif isinstance(e, ProjectDetails.DoesNotExist):
            return JsonResponse({"error": "Project details not found"}, status=404)
        elif isinstance(e, ProjectDetails.MultipleObjectsReturned):
                return JsonResponse({"error": "Multiple projects found with the same API Key"}, status=400)
        elif isinstance(e, PlanSubscription.DoesNotExist):
            timeline_update(outlet_obj, outlet_obj.web_url, 'is_plan_purchased', False,request.META.get('HTTP_WHATSAPP_PROJECT_KEY'))
            return JsonResponse({"error": "subscription plan dose not exist"}, status=404)
        elif isinstance(e, PlanSubscription.MultipleObjectsReturned):
                return JsonResponse({"error": "Multiple Template found with the given id"}, status=400)
    except Exception as e:
        print(str(e))
        print("======================== ERROR ==============================")
        return JsonResponse({"error": "Something went wrong!"}, status=500)


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def subscription_purchase(request):
    try:
        outlet_api_key          = request.META.get('HTTP_API_KEY')
        project_api_key         = request.META.get('HTTP_WHATSAPP_PROJECT_KEY')
        membership_plan_id      = request.POST.get('membership_plan_id')
        if outlet_api_key is None :
            return JsonResponse({"error": "outlet_api_key is missing"}, status=404)
        elif project_api_key is None :
            return JsonResponse({"error": "project_api_key is missing"}, status=404)
        elif membership_plan_id is None :
            return JsonResponse({"error": "membership_plan_id is missing"}, status=404)
        else:
            pass
        outlet_obj              = outlet_details.objects.get(api_key = outlet_api_key)
        project_obj             = ProjectDetails.objects.get(api_key = project_api_key)
        business_obj            = project_obj.business
        membership_plan_obj     = MembershipPlan.objects.get(id = membership_plan_id)
        plan_subscriptions_obj  = PlanSubscription.objects.filter(outlet=outlet_obj,project = project_obj).first()
        amount                  = round(membership_plan_obj.price_after_discount * Decimal('1.18'),3)
        customer_name           = business_obj.company
        customer_number         = business_obj.phone_code + business_obj.contact
        redirect_url            = "https://xircls.in/merchant/whatsapp/Billing/"
        url,unique_id           = payment_create_order(amount,customer_name,customer_number,redirect_url ,request.POST.get('membership_plan_id'))
        ChildTransactions.objects.create(
        subscription   = plan_subscriptions_obj if plan_subscriptions_obj else None,
        shop           = outlet_obj.web_url,
        outlet         = outlet_obj,
        business       = business_obj,
        project        = project_obj,
        unique_id      = unique_id,
        payment_status = 'Credit',
        payment_stage  = 'Initiated',
        gst_perc       = 18.00,
        app_name       = 'Whatsapp',
        gst_amount     = membership_plan_obj.price_after_discount * Decimal('0.18'),
        amount         = membership_plan_obj.price_after_discount,
        amount_with_gst= membership_plan_obj.price_after_discount * Decimal('1.18')
        )
        return JsonResponse({"Payment_Link": url}, status=status.HTTP_200_OK)
    except (outlet_details.DoesNotExist,ProjectDetails.DoesNotExist,ProjectDetails.MultipleObjectsReturned,outlet_details.MultipleObjectsReturned,MembershipPlan.DoesNotExist,MembershipPlan.MultipleObjectsReturned) as e:
        if isinstance(e, outlet_details.DoesNotExist):
            return JsonResponse({"error": "Invalid API Key outlet details not found"}, status=404)
        elif isinstance(e, outlet_details.MultipleObjectsReturned):
                return JsonResponse({"error": "Multiple outlets found with the same API Key"}, status=400)
        elif isinstance(e, ProjectDetails.DoesNotExist):
            return JsonResponse({"error": "Project details not found"}, status=404)
        elif isinstance(e, ProjectDetails.MultipleObjectsReturned):
                return JsonResponse({"error": "Multiple projects found with the same API Key"}, status=400)
        elif isinstance(e, MembershipPlan.MultipleObjectsReturned):
                return JsonResponse({"error": "Membership Plan details not found"}, status=400)
        elif isinstance(e, MembershipPlan.DoesNotExist):
                return JsonResponse({"error": "Multiple Membership Plan found with the given id"}, status=400)
    except Exception as e:
        print(str(e))
        print("======================== ERROR ==============================")
        return JsonResponse({"error": "Something went wrong!"}, status=500)



# ##############################################################################################################################################
# Section: WHATS APP FLOW FORM
# ##############################################################################################################################################

@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def create_whatsapp_flow_form(request):
    try:
        outlet_api_key          = request.META.get('HTTP_API_KEY')
        project_api_key         = request.META.get('HTTP_WHATSAPP_PROJECT_KEY')
        name                    = request.POST.get('name')
        category                = request.POST.get('category')
        if outlet_api_key is None :
            return JsonResponse({"error": "outlet_api_key is missing"}, status=404)
        elif project_api_key is None :
            return JsonResponse({"error": "project_api_key is missing"}, status=404)
        elif name is None :
            return JsonResponse({"error": "name is missing"}, status=404)
        elif category is None :
            return JsonResponse({"error": "category is missing"}, status=404)
        else:
            pass
        outlet_obj     = outlet_details.objects.get(api_key = outlet_api_key)
        project_obj    = ProjectDetails.objects.get(api_key = project_api_key)
        headers = {
            'Accept'       : 'application/json',
            'Content-Type' : 'application/json',
            'Authorization': f'Bearer {project_obj.token}' 
        }
        url     = "https://backend.aisensy.com/direct-apis/t1/flows"
        payload = {
                "name"      : name,
                "categories": [category]
            }
        response = requests.post(url, json=payload, headers=headers).json()
        if 'id' in response :
            obj = WhatsAppFlowForm.objects.create(flow_form_Id = response.get("id"),
                form_Name   = name ,
                outlet      = outlet_obj,
                business    = project_obj.business,
                project     = project_obj,
                is_draft    = 1,
                form_status = 'Draft')
            return JsonResponse({"message": "whatsapp flow form created successfully","id":obj.id}, status=status.HTTP_200_OK)
        else:
            return JsonResponse(response, status=status.HTTP_200_OK)
    except (outlet_details.DoesNotExist,ProjectDetails.DoesNotExist,ProjectDetails.MultipleObjectsReturned,outlet_details.MultipleObjectsReturned) as e:
        if isinstance(e, outlet_details.DoesNotExist):
            return JsonResponse({"error": "Invalid API Key outlet details not found"}, status=404)
        elif isinstance(e, outlet_details.MultipleObjectsReturned):
                return JsonResponse({"error": "Multiple outlets found with the same API Key"}, status=400)
        elif isinstance(e, ProjectDetails.DoesNotExist):
            return JsonResponse({"error": "Project details not found"}, status=404)
        elif isinstance(e, ProjectDetails.MultipleObjectsReturned):
                return JsonResponse({"error": "Multiple projects found with the same API Key"}, status=400)
    except Exception as e:
        print(str(e))
        print("======================== ERROR ==============================")
        return JsonResponse({"error": "Something went wrong!"}, status=500)   




@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def get_whatsapp_flow_form(request):
    try:
        outlet_api_key          = request.META.get('HTTP_API_KEY')
        project_api_key         = request.META.get('HTTP_WHATSAPP_PROJECT_KEY')
        form_id                 = request.POST.get('form_id')
        if outlet_api_key is None :
            return JsonResponse({"error": "outlet_api_key is missing"}, status=404)
        elif project_api_key is None :
            return JsonResponse({"error": "project_api_key is missing"}, status=404)
        else:
            pass
        outlet_obj            = outlet_details.objects.get(api_key = outlet_api_key)
        project_obj           = ProjectDetails.objects.get(api_key = project_api_key)
        if form_id:
            flow_forms            = WhatsAppFlowForm.objects.filter(id = form_id,project = project_obj, outlet = outlet_obj)
            flow_forms_serialized = WhatsAppFlowFormSerializer(flow_forms,many=True).data
            return JsonResponse({"form_data": flow_forms_serialized}, status=status.HTTP_200_OK)
        else:
            datatables      = request.POST
            print(datatables)
            start           = int(datatables.get('page'))
            length          = int(datatables.get('size'))
            over_all_search = datatables.get('searchValue')
            field_mapping = {
                0: "form_Name__icontains",
                1: "form_catagory__icontains",
                2: "form_status__icontains",
                3: "created_at__icontains",
                4: "is_published__icontains",
                5: "is_draft__icontains",
                6: "updated_at__icontains",
            }
            advance_filter = Q()
            for col, field in field_mapping.items():
                value = datatables.get(f"columns[{col}][search][value]", None)
                if value:
                    advance_filter &= Q(**{field: value})
            if over_all_search:
                overall_search_filter = Q()
                for field in field_mapping.values():
                    overall_search_filter |= Q(**{field: over_all_search})
                advance_filter &= overall_search_filter
            flow_forms_obj = WhatsAppFlowForm.objects.filter(outlet = outlet_obj,project = project_obj).filter(advance_filter).order_by('-created_at').values(
            Id                         = F('id'),
            Flow_form_Id               = F('flow_form_Id'),
            Form_Name                  = F('form_Name'),
            Form_catagory              = F('form_catagory'),
            Form_status                = F('form_status'),
            Is_draft                   = F('is_draft'),
            Is_published               = F('is_published'),
            Json_data                  = F('json_data'),
            ) 
            flow_forms_obj_count = flow_forms_obj.count()
            paginator = Paginator(flow_forms_obj, length)
            try:
                object_list = paginator.page(start).object_list
            except (PageNotAnInteger, EmptyPage):
                object_list = paginator.page(1).object_list
            
            response = {
                'flow_forms_obj_count': flow_forms_obj_count,
                "form_data": list(object_list)
            }
            return JsonResponse(response, status=status.HTTP_200_OK)
    except (outlet_details.DoesNotExist,ProjectDetails.DoesNotExist,ProjectDetails.MultipleObjectsReturned,outlet_details.MultipleObjectsReturned) as e:
        if isinstance(e, outlet_details.DoesNotExist):
            return JsonResponse({"error": "Invalid API Key outlet details not found"}, status=404)
        elif isinstance(e, outlet_details.MultipleObjectsReturned):
                return JsonResponse({"error": "Multiple outlets found with the same API Key"}, status=400)
        elif isinstance(e, ProjectDetails.DoesNotExist):
            return JsonResponse({"error": "Project details not found"}, status=404)
        elif isinstance(e, ProjectDetails.MultipleObjectsReturned):
                return JsonResponse({"error": "Multiple projects found with the same API Key"}, status=400)
    except Exception as e:
        print(str(e))
        print("======================== ERROR ==============================")
        return JsonResponse({"error": "Something went wrong!"}, status=500)  
       
@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def update_json_whatsapp_flow_form(request):
    try:
        outlet_api_key          = request.META.get('HTTP_API_KEY')
        project_api_key         = request.META.get('HTTP_WHATSAPP_PROJECT_KEY')
        whatsapp_form_id        = request.POST.get("form_id")
        json_data               = json.loads(request.POST.get("json"))
        if outlet_api_key is None :
            return JsonResponse({"error": "outlet_api_key is missing"}, status=404)
        elif project_api_key is None :
            return JsonResponse({"error": "project_api_key is missing"}, status=404)
        elif whatsapp_form_id is None :
            return JsonResponse({"error": "whatsapp_form_id is missing"}, status=404)
        elif json_data is None :
            return JsonResponse({"error": "json is missing"}, status=404)
        else:
            pass
        outlet_obj        = outlet_details.objects.get(api_key = outlet_api_key)
        project_obj       = ProjectDetails.objects.get(api_key = project_api_key)
        whatsapp_form_obj = WhatsAppFlowForm.objects.get(id  = whatsapp_form_id)
        
        file_name = str(uuid.uuid4()) + '.json'
        file_path = os.path.join(settings.MEDIA_ROOT, file_name)
        with open(file_path, 'w') as json_file:
            json.dump(json_data, json_file, indent = 4)
        json_bytes = json.dumps(json_data, indent = 4).encode('utf-8')
        json_file  = InMemoryUploadedFile(
            file         = BytesIO(json_bytes),
            field_name   = 'file',
            name         = file_name,
            content_type = 'application/json',
            size         = len(json_bytes),
            charset      = 'utf-8'
        )
        files = {
            'file': (json_file.name, json_file.read(), json_file.content_type),
        }
        headers = {
            'Authorization': f'Bearer {project_obj.token}'
        }
        url      = f"https://backend.aisensy.com/direct-apis/t1/flows/{whatsapp_form_obj.flow_form_Id}/assets"
        response = requests.post(url, files=files, headers=headers).json()
        os.remove(file_path)
        print(response)
        if response.get('success', False):
            validation_errors = response.get('validation_errors')
            if isinstance(validation_errors, list) and len(validation_errors) == 0:
                whatsapp_form_obj.json_data = json_data
                whatsapp_form_obj.save()
                return JsonResponse({"message": "whatsapp flow form created successfully"}, status=status.HTTP_200_OK)
            else:
                return JsonResponse(response, status = status.HTTP_200_OK)
        else:
            return JsonResponse(response, status = status.HTTP_200_OK)
    except (outlet_details.DoesNotExist,ProjectDetails.DoesNotExist,ProjectDetails.MultipleObjectsReturned,outlet_details.MultipleObjectsReturned,WhatsAppFlowForm.DoesNotExist,WhatsAppFlowForm.MultipleObjectsReturned) as e:
        if isinstance(e, outlet_details.DoesNotExist):
            return JsonResponse({"error": "Invalid API Key outlet details not found"}, status=404)
        elif isinstance(e, outlet_details.MultipleObjectsReturned):
                return JsonResponse({"error": "Multiple outlets found with the same API Key"}, status=400)
        elif isinstance(e, ProjectDetails.DoesNotExist):
            return JsonResponse({"error": "Project details not found"}, status=404)
        elif isinstance(e, ProjectDetails.MultipleObjectsReturned):
                return JsonResponse({"error": "Multiple projects found with the same API Key"}, status=400)
        elif isinstance(e, WhatsAppFlowForm.DoesNotExist):
                return JsonResponse({"error": "WhatsApp Flow Form details not found with given id"}, status=400)
        elif isinstance(e, WhatsAppFlowForm.MultipleObjectsReturned):
                return JsonResponse({"error": "Multiple WhatsApp Flow Form found with the given id"}, status=400)
    except Exception as e:
        print(str(e))
        print("======================== ERROR ==============================")
        return JsonResponse({"error": "Something went wrong!"}, status=500)
            
            
@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def send_draft_whatsapp_flow_form(request):
    try:
        outlet_api_key          = request.META.get('HTTP_API_KEY')
        project_api_key         = request.META.get('HTTP_WHATSAPP_PROJECT_KEY')
        whatsapp_form_id        = request.POST.get("form_id")
        reciver_no              = request.POST.get("reciver")
        if outlet_api_key is None :
            return JsonResponse({"error": "outlet_api_key is missing"}, status=404)
        elif project_api_key is None :
            return JsonResponse({"error": "project_api_key is missing"}, status=404)
        elif whatsapp_form_id is None :
            return JsonResponse({"error": "whatsapp_form_id is missing"}, status=404)
        elif reciver_no is None :
            return JsonResponse({"error": "reciver is missing"}, status=404)
        else:
            pass
        outlet_obj        = outlet_details.objects.get(api_key = outlet_api_key)
        project_obj       = ProjectDetails.objects.get(api_key = project_api_key)
        whatsapp_form_obj = WhatsAppFlowForm.objects.get(id  = whatsapp_form_id)
        json_data         = whatsapp_form_obj.json_data
        url               = "https://backend.aisensy.com/direct-apis/t1/messages"
        headers = {
                    "Content-Type": "application/json",
                    "Accept": "application/json, application/xml",
                    'Authorization': f'Bearer {project_obj.token}'
                }
        payload = {
                    "messaging_product": "whatsapp",
                    "to": reciver_no,
                    "recipient_type": "individual",
                    "type": "interactive",
                    "interactive": {
                        "type": "flow",
                        "header": {
                            "type": "text",
                            "text": "Not shown in draft mode"
                        },
                        "body"  : { "text": "Not shown in draft mode" },
                        "footer": { "text": "Not shown in draft mode" },
                        "action": {
                            "name": "flow",
                            "parameters": {
                                "flow_message_version": "3",
                                "flow_action": "navigate",
                                "flow_token" : "random_user_generated_token",
                                "flow_id"    : whatsapp_form_obj.flow_form_Id,
                                "flow_cta"   : "Not shown in draft mode",
                                "mode"       : "draft",
                                "flow_action_payload": {
                                    "screen": json_data.get('screens', [])[0].get('id'),
                                    "data": { "custom_variable": "custom_value" }
                                }
                            }
                        }
                    }
                }
        response = requests.post(url, json=payload, headers=headers).json()
        return JsonResponse(response, status=status.HTTP_200_OK)
    except (outlet_details.DoesNotExist,ProjectDetails.DoesNotExist,ProjectDetails.MultipleObjectsReturned,outlet_details.MultipleObjectsReturned,WhatsAppFlowForm.DoesNotExist,WhatsAppFlowForm.MultipleObjectsReturned) as e:
        if isinstance(e, outlet_details.DoesNotExist):
            return JsonResponse({"error": "Invalid API Key outlet details not found"}, status=404)
        elif isinstance(e, outlet_details.MultipleObjectsReturned):
                return JsonResponse({"error": "Multiple outlets found with the same API Key"}, status=400)
        elif isinstance(e, ProjectDetails.DoesNotExist):
            return JsonResponse({"error": "Project details not found"}, status=404)
        elif isinstance(e, ProjectDetails.MultipleObjectsReturned):
                return JsonResponse({"error": "Multiple projects found with the same API Key"}, status=400)
        elif isinstance(e, WhatsAppFlowForm.DoesNotExist):
                return JsonResponse({"error": "WhatsApp Flow Form details not found with given id"}, status=400)
        elif isinstance(e, WhatsAppFlowForm.MultipleObjectsReturned):
                return JsonResponse({"error": "Multiple WhatsApp Flow Form found with the given id"}, status=400)
    except Exception as e:
        print(str(e))
        print("======================== ERROR ==============================")
        return JsonResponse({"error": "Something went wrong!"}, status=500)
         

@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def update_whatsapp_flow_form_metadata(request):  
    try:
        outlet_api_key          = request.META.get('HTTP_API_KEY')
        project_api_key         = request.META.get('HTTP_WHATSAPP_PROJECT_KEY')
        whatsapp_form_id        = request.POST.get("form_id")
        name                    = request.POST.get("name")
        categories_list         = request.POST.getlist('categories_list')
        if outlet_api_key is None :
            return JsonResponse({"error": "outlet_api_key is missing"}, status=404)
        elif project_api_key is None :
            return JsonResponse({"error": "project_api_key is missing"}, status=404)
        elif whatsapp_form_id is None :
            return JsonResponse({"error": "whatsapp_form_id is missing"}, status=404)
        else:
            pass
        outlet_obj        = outlet_details.objects.get(api_key = outlet_api_key)
        project_obj       = ProjectDetails.objects.get(api_key = project_api_key)
        whatsapp_form_obj = WhatsAppFlowForm.objects.get(id    = whatsapp_form_id, project = project_obj,oulet = outlet_obj)
        url = f"https://backend.aisensy.com/direct-apis/t1/flows/{whatsapp_form_obj.flow_form_Id}"
        #url = f"https://backend.aisensy.com/direct-apis/t1/flows/{whatsapp_form_obj.flow_form_Id}/publish"
        headers = {
            'Accept'       : 'application/json',
            'Content-Type' : 'application/json',
            'Authorization': f'Bearer {project_obj.token}' 
        }
        payload = {
                "name": name,
                "categories": categories_list
            }
        response = requests.patch(url, json=payload, headers=headers).json()
        if response.get('success', False):
            whatsapp_form_obj.form_Name     = name
            whatsapp_form_obj.form_catagory = categories_list
            whatsapp_form_obj.save()
            return JsonResponse(response, status=status.HTTP_200_OK)
        else:
            return JsonResponse(response, status=status.HTTP_200_OK)

    except (outlet_details.DoesNotExist,ProjectDetails.DoesNotExist,ProjectDetails.MultipleObjectsReturned,outlet_details.MultipleObjectsReturned,WhatsAppFlowForm.DoesNotExist,WhatsAppFlowForm.MultipleObjectsReturned) as e:
        if isinstance(e, outlet_details.DoesNotExist):
            return JsonResponse({"error": "Invalid API Key outlet details not found"}, status=404)
        elif isinstance(e, outlet_details.MultipleObjectsReturned):
                return JsonResponse({"error": "Multiple outlets found with the same API Key"}, status=400)
        elif isinstance(e, ProjectDetails.DoesNotExist):
            return JsonResponse({"error": "Project details not found"}, status=404)
        elif isinstance(e, ProjectDetails.MultipleObjectsReturned):
                return JsonResponse({"error": "Multiple projects found with the same API Key"}, status=400)
        elif isinstance(e, WhatsAppFlowForm.DoesNotExist):
                return JsonResponse({"error": "WhatsApp Flow Form details not found with given id"}, status=400)
        elif isinstance(e, WhatsAppFlowForm.MultipleObjectsReturned):
                return JsonResponse({"error": "Multiple WhatsApp Flow Form found with the given id"}, status=400)
    except Exception as e:
        print(str(e))
        print("======================== ERROR ==============================")
        return JsonResponse({"error": "Something went wrong!"}, status=500)
            

@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def delete_whatsapp_flow_form(request):  
    try:
        outlet_api_key          = request.META.get('HTTP_API_KEY')
        project_api_key         = request.META.get('HTTP_WHATSAPP_PROJECT_KEY')
        whatsapp_form_id        = request.POST.get("form_id")
        if outlet_api_key is None :
            return JsonResponse({"error": "outlet_api_key is missing"}, status=404)
        elif project_api_key is None :
            return JsonResponse({"error": "project_api_key is missing"}, status=404)
        elif whatsapp_form_id is None :
            return JsonResponse({"error": "whatsapp_form_id is missing"}, status=404)
        else:
            pass
        outlet_obj        = outlet_details.objects.get(api_key = outlet_api_key)
        project_obj       = ProjectDetails.objects.get(api_key = project_api_key)
        whatsapp_form_obj = WhatsAppFlowForm.objects.get(id    = whatsapp_form_id, project = project_obj,oulet = outlet_obj)
        url = "https://backend.aisensy.com/direct-apis/t1/flows/{whatsapp_form_obj.flow_form_Id}"
        headers = {
            'Accept'       : 'application/json',
            'Content-Type' : 'application/json',
            'Authorization': f'Bearer {project_obj.token}' 
        }
        response = requests.delete(url, headers=headers).json()
        if response.get('success', False):
            whatsapp_form_obj.is_draft     = False
            whatsapp_form_obj.is_trash     = True
            whatsapp_form_obj.form_status  = "Trashed"
            whatsapp_form_obj.save()
            return JsonResponse(response, status=status.HTTP_200_OK)
        else:
            return JsonResponse(response, status=status.HTTP_200_OK)
    except (outlet_details.DoesNotExist,ProjectDetails.DoesNotExist,ProjectDetails.MultipleObjectsReturned,outlet_details.MultipleObjectsReturned,WhatsAppFlowForm.DoesNotExist,WhatsAppFlowForm.MultipleObjectsReturned) as e:
        if isinstance(e, outlet_details.DoesNotExist):
            return JsonResponse({"error": "Invalid API Key outlet details not found"}, status=404)
        elif isinstance(e, outlet_details.MultipleObjectsReturned):
                return JsonResponse({"error": "Multiple outlets found with the same API Key"}, status=400)
        elif isinstance(e, ProjectDetails.DoesNotExist):
            return JsonResponse({"error": "Project details not found"}, status=404)
        elif isinstance(e, ProjectDetails.MultipleObjectsReturned):
                return JsonResponse({"error": "Multiple projects found with the same API Key"}, status=400)
        elif isinstance(e, WhatsAppFlowForm.DoesNotExist):
                return JsonResponse({"error": "WhatsApp Flow Form details not found with given id"}, status=400)
        elif isinstance(e, WhatsAppFlowForm.MultipleObjectsReturned):
                return JsonResponse({"error": "Multiple WhatsApp Flow Form found with the given id"}, status=400)
    except Exception as e:
        print(str(e))
        print("======================== ERROR ==============================")
        return JsonResponse({"error": "Something went wrong!"}, status=500)


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def publish_whatsapp_flow_form(request):  
    try:
        outlet_api_key          = request.META.get('HTTP_API_KEY')
        project_api_key         = request.META.get('HTTP_WHATSAPP_PROJECT_KEY')
        whatsapp_form_id        = request.POST.get("form_id")
        if outlet_api_key is None :
            return JsonResponse({"error": "outlet_api_key is missing"}, status=404)
        elif project_api_key is None :
            return JsonResponse({"error": "project_api_key is missing"}, status=404)
        elif whatsapp_form_id is None :
            return JsonResponse({"error": "whatsapp_form_id is missing"}, status=404)
        else:
            pass
        outlet_obj        = outlet_details.objects.get(api_key = outlet_api_key)
        project_obj       = ProjectDetails.objects.get(api_key = project_api_key)
        whatsapp_form_obj = WhatsAppFlowForm.objects.get(id    = whatsapp_form_id, project = project_obj,outlet = outlet_obj)
        url = f"https://backend.aisensy.com/direct-apis/t1/flows/{whatsapp_form_obj.flow_form_Id}/publish"
        headers = {
            'Accept'       : 'application/json',
            'Content-Type' : 'application/json',
            'Authorization': f'Bearer {project_obj.token}' 
        }
        response = requests.post(url, headers=headers).json()
        if response.get('success', False):
            whatsapp_form_obj.is_draft     = False
            whatsapp_form_obj.is_published = True
            whatsapp_form_obj.form_status  = "Published"
            whatsapp_form_obj.save()
            return JsonResponse(response, status=status.HTTP_200_OK)
        else:
            return JsonResponse(response, status=status.HTTP_200_OK)

    except (outlet_details.DoesNotExist,ProjectDetails.DoesNotExist,ProjectDetails.MultipleObjectsReturned,outlet_details.MultipleObjectsReturned,WhatsAppFlowForm.DoesNotExist,WhatsAppFlowForm.MultipleObjectsReturned) as e:
        if isinstance(e, outlet_details.DoesNotExist):
            return JsonResponse({"error": "Invalid API Key outlet details not found"}, status=404)
        elif isinstance(e, outlet_details.MultipleObjectsReturned):
                return JsonResponse({"error": "Multiple outlets found with the same API Key"}, status=400)
        elif isinstance(e, ProjectDetails.DoesNotExist):
            return JsonResponse({"error": "Project details not found"}, status=404)
        elif isinstance(e, ProjectDetails.MultipleObjectsReturned):
                return JsonResponse({"error": "Multiple projects found with the same API Key"}, status=400)
        elif isinstance(e, WhatsAppFlowForm.DoesNotExist):
                return JsonResponse({"error": "WhatsApp Flow Form details not found with given id"}, status=400)
        elif isinstance(e, WhatsAppFlowForm.MultipleObjectsReturned):
                return JsonResponse({"error": "Multiple WhatsApp Flow Form found with the given id"}, status=400)
    except Exception as e:
        print(str(e))
        print("======================== ERROR ==============================")
        return JsonResponse({"error": "Something went wrong!"}, status=500)
            
          


def add_webhook(trigger,shopify_obj):
    webhook_url = f"https://{shopify_obj.shop}/admin/api/{SHOPIFY_API_YEAR}/webhooks.json" 
    headers = {
            'X-Shopify-Access-Token' : shopify_obj.access_token,
            'Content-Type': 'application/json',
            'accept': 'application/json'
        }
    payload ={  
        "webhook":{
            "topic":f"{trigger}",
            "address": f"https://api.demo.xircls.in/talk/shopify_webhook/" ,
            "format": "json"
        }
    }

    webhook_response = json.loads(requests.post(webhook_url, data = json.dumps(payload), headers = headers).text)
    return webhook_response

@csrf_exempt
def shopify_webhook(request):
    print(request,"===================================")
    data = request.body

    return HttpResponse(status=200)

@authentication_classes([])
@permission_classes([AllowAny])
class shopify_webhook_update(APIView):
    def post(self,request):
        shop = request.POST.get('shop')
        trigger = request.POST.get('trigger')
        shopify_obj = ShopifyXirclsApp.objects.get(shop=shop,app="whatsapp")
        response = add_webhook(trigger,shopify_obj)
        print("resonse = ",response)
        return JsonResponse({"success": True, "message": "webhook created successfully"})


from.models import ImageSave
@csrf_exempt
def upload_image(request):
    if request.method == 'POST' and request.FILES.get('image'):
        image = request.FILES['image']
        # Save the image to the model
        image_instance = ImageSave(file_data=image, filename=image.name)
        image_instance.save()

        # Construct the URL to the uploaded image
        uploaded_url = "https://api.demo.xircls.in/static"+image_instance.file_data.url

        return JsonResponse({'message': 'Image uploaded successfully', 'url': uploaded_url})

    return JsonResponse({'error': 'Invalid request'}, status=400)

@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def default_project(request):
    try:
        outlet_api_key          = request.META.get('HTTP_API_KEY')
        if outlet_api_key is None :
            return JsonResponse({"error": "outlet_api_key is missing"}, status=404)
        else:
            pass
        project_instance = ProjectDetails.objects.filter(outlet__api_key = outlet_api_key)
        project_instance.update(is_default=False)
        project_instance.filter(id=request.POST.get('project_id')).update(is_default = True)
        return JsonResponse({"message": "successfully set default"}, status=status.HTTP_200_OK)
    except (ProjectDetails.DoesNotExist,ProjectDetails.MultipleObjectsReturned) as e:
        if isinstance(e, ProjectDetails.DoesNotExist):
            return JsonResponse({"error": "Project details not found"}, status=404)
        elif isinstance(e, ProjectDetails.MultipleObjectsReturned):
                return JsonResponse({"error": "Multiple projects found with the same API Key"}, status=400)
    except Exception as e:
        print(str(e))
        print("======================== ERROR ==============================")
        return JsonResponse({"error": "Something went wrong!"}, status=500)


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def default_project(request):
    try:
        outlet_api_key          = request.META.get('HTTP_API_KEY')
        if outlet_api_key is None :
            return JsonResponse({"error": "outlet_api_key is missing"}, status=404)
        else:
            pass
        project_instance = ProjectDetails.objects.filter(outlet__api_key = outlet_api_key)
        project_instance.update(is_default=False)
        project_instance.filter(id=request.POST.get('project_id')).update(is_default = True)
        return JsonResponse({"message": "successfully set default"}, status=status.HTTP_200_OK)
    except (ProjectDetails.DoesNotExist,ProjectDetails.MultipleObjectsReturned) as e:
        if isinstance(e, ProjectDetails.DoesNotExist):
            return JsonResponse({"error": "Project details not found"}, status=404)
        elif isinstance(e, ProjectDetails.MultipleObjectsReturned):
                return JsonResponse({"error": "Multiple projects found with the same API Key"}, status=400)
    except Exception as e:
        print(str(e))
        print("======================== ERROR ==============================")
        return JsonResponse({"error": "Something went wrong!"}, status=500)


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def send_messages_parallel(request):
    try:
        template_id = request.POST.get('template_id', 609)
        template_instance = TemplateDetails.objects.get(id=template_id)
        coupon_variables = request.POST.get("coupon_variables", None)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
    
    try:
        outlet_obj = outlet_details.objects.get(api_key=request.META.get('HTTP_API_KEY'))
        project_obj = ProjectDetails.objects.get(api_key=request.META.get('HTTP_WHATSAPP_PROJECT_KEY'))
    except ProjectDetails.DoesNotExist:
        project_obj = template_instance.project

    wallet_obj = WhatsappWallet.objects.get(project=project_obj)
    wallet_dict = model_to_dict(wallet_obj)

    # if wallet_obj.subscription is None:
    #     return JsonResponse({"message": "Purchase Subscription", "success": False}, status=status.HTTP_200_OK)
    # if wallet_obj.subscription.end_date < timezone.now():
    #     return JsonResponse({"message": "Subscription is Expired", "success": False}, status=status.HTTP_200_OK)

    # try:
    #     contact_group_list = [int(x) for x in request.POST.get('contact_group_list').split(',')]
    # except:
    #     contact_group_list = [request.POST.get('contact_group_list')]

    customer_groups = ContactsGroup.objects.filter(id__in=[58])
    unique_contacts = set()
    for group in customer_groups:
        unique_contacts.update(group.contact.filter(is_active=True, is_opt_out=False))

    customer_list = list(unique_contacts)
    total_messages = len(customer_list)
    template_inst = json.loads(template_instance.payload)
    template_type = template_inst['category']
    per_message_cost = wallet_obj.deduction_plan.get(template_type)
    total_cost = total_messages * per_message_cost

    if total_cost > wallet_obj.balance:
        number_of_messages_possible = int(wallet_obj.balance / per_message_cost)
        return JsonResponse({'message': f'Insufficient funds, can only send {number_of_messages_possible} messages with present fund'}, safe=True, status=200)

    button_variables = request.POST.get('button_variables', None)
    msg_send = MessageSender(
        button_variables=button_variables,
        template_instance=template_instance,
        campaign_id=None
    )

    def send_messages_chunk(chunk):
        msg_send.send_messages(chunk)

    # Create a list with 150 elements, each containing the same customer_list
    customer_chunks = [customer_list for _ in range(150)]
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=150) as executor:
        futures = [executor.submit(send_messages_chunk, chunk) for chunk in customer_chunks]
        for future in futures:
            try:
                future.result()
            except Exception as e:
                return JsonResponse({"error": str(e)}, safe=False, status=500)

    return JsonResponse({'message': 'success'}, safe=True, status=200)







