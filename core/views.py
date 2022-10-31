
from genericpath import exists
from django.shortcuts import render
from rest_framework.views import APIView
from . models import *
from rest_framework.response import Response
from . serializer import *
import time as t
import json
import AWSIoTPythonSDK.MQTTLib as AWSIoTPyMQTT
from awscrt import mqtt
import pandas as pd
import datetime 
from datetime import datetime, timedelta
from django.utils import timezone
import pytz
from time import gmtime, strftime
from django.db.models.functions import Now
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# Create your views here.
ENDPOINT = "a1a20cagimrnhk-ats.iot.us-east-1.amazonaws.com"
CLIENT_ID = "esp_py"
PATH_TO_CERTIFICATE = "https://github.com/Sw-427/Iot/blob/master/certs/54850eb2147a8454d87ec3a8798350e4c8444c9037015a330f6ade69028baf41-certificate.pem.crt"
PATH_TO_PRIVATE_KEY = "certs/54850eb2147a8454d87ec3a8798350e4c8444c9037015a330f6ade69028baf41-private.pem.key"
PATH_TO_AMAZON_ROOT_CA_1 = "certs/AmazonRootCA1 (1).pem"
MESSAGE = "Hello World"
TOPIC = "ESP32/pub"
RANGE = 20
myAWSIoTMQTTClient = AWSIoTPyMQTT.AWSIoTMQTTClient(CLIENT_ID)
myAWSIoTMQTTClient.configureEndpoint(ENDPOINT, 8883)
myAWSIoTMQTTClient.configureCredentials(PATH_TO_AMAZON_ROOT_CA_1, PATH_TO_PRIVATE_KEY, PATH_TO_CERTIFICATE)

myAWSIoTMQTTClient.connect()

def mtn(x):
    months = {
        'jan':1,
        'feb':2,
        'mar':3,
        'apr':4,
        'may':5,
        'jun':6,
        'jul':7,
        'aug':8,
        'sep':9,
        'oct':10,
        'nov':11,
        'dec':12
        }
    a = x.strip()[:3].lower()
    try:
        ez = months[a]
        return(ez)
    except:
        raise ValueError('Not a month')

def refresh(client, userdata, message):
    global uids,time,dataq
    payload = message.payload.decode("utf-8")
    payload = json.loads(payload)
    uids = payload['UID']


    apple = iot.objects.filter(uid=uids)
    if apple.exists():
        for a in apple:
            if a.outdate == a.indate:
                iot.objects.filter(pk=a.id).update(outdate = Now())
    else:
        b = iot(uid=uids)
        b.save()    
    print(payload)
    
def slot():
    count = 0
    apple = iot.objects.all()
    if apple.exists():
        for a in apple:
            if a.outdate == a.indate:
                count = count + 1
    return count
myAWSIoTMQTTClient.subscribe("esp32/pub",1,refresh)

class ReactView(APIView):
	def get(self, request):
		detail = [ {"uid": detail.uid,"intime": detail.indate,"outtime": detail.outdate}
		for detail in iot.objects.all() if detail.outdate is not detail.indate]
		return Response(detail)

class slots(APIView):
    def get(self, request):
        return Response({'count':slot()})
    
class analytics(APIView):
    def get(self, request):
        qs = iot.objects.all()
        global x
        con = 0
        x = NULL
        for i in qs:
            if i.outdate != i.indate:
                con = con +1
                if x is NULL:
                    x =  i.outdate - i.indate
                else:
                    x = x + i.outdate - i.indate
                i.indate = i.indate.strftime("%H:%M:%S")
                i.outdate = i.outdate.strftime("%H:%M:%S")
        try:
            avg = x/con
        except:
            avg = 0
        df = convert_to_dataframe(qs, fields=['uid','indate','outdate'])
        
        df['diff'] = [datetime.strptime(az['outdate'], "%H:%M:%S") - datetime.strptime(az['indate'], "%H:%M:%S") for ind, az in df.iterrows() ]
        
        df['indate'] = [(timedelta(seconds=19800) + datetime.strptime(az['indate'], "%H:%M:%S")).strftime("%H:%M:%S") for ind, az in df.iterrows() ]
        print(df)
        plt.plot(df['indate'], df['diff'])
        plt.xlabel('Time of Entry')
        # naming the y axis
        plt.ylabel('Time of stay')
        plt.title('Time vs Entry')
        plt.savefig('foo.png')
        
        data = {
            "avgtime":avg
        }
        
        return Response(data)



def convert_to_dataframe(qs, fields=None, index=None):
    '''
    ::param qs is an QuerySet from Django
    ::fields is a list of field names from the Model of the QuerySet
    ::index is the preferred index column we want our dataframe to be set to

    Using the methods from above, we can easily build a dataframe
    from this data.
    '''
    lookup_fields = get_lookup_fields(qs.model, fields=fields)
    index_col = None
    if index in lookup_fields:
        index_col = index
    elif "id" in lookup_fields:
        index_col = 'id'
    values = qs_to_dataset(qs, fields=fields)
    df = pd.DataFrame.from_records(values, columns=lookup_fields, index=index_col)
    return df

def get_model_field_names(model, ignore_fields=['content_object']):
    '''
    ::param model is a Django model class
    ::param ignore_fields is a list of field names to ignore by default
    This method gets all model field names (as strings) and returns a list 
    of them ignoring the ones we know don't work (like the 'content_object' field)
    '''
    model_fields = model._meta.get_fields()
    model_field_names = list(set([f.name for f in model_fields if f.name not in ignore_fields]))
    return model_field_names


def get_lookup_fields(model, fields=None):
    '''
    ::param model is a Django model class
    ::param fields is a list of field name strings.
    This method compares the lookups we want vs the lookups
    that are available. It ignores the unavailable fields we passed.
    '''
    model_field_names = get_model_field_names(model)
    if fields is not None:
        '''
        we'll iterate through all the passed field_names
        and verify they are valid by only including the valid ones
        '''
        lookup_fields = []
        for x in fields:
            if "__" in x:
                # the __ is for ForeignKey lookups
                lookup_fields.append(x)
            elif x in model_field_names:
                lookup_fields.append(x)
    else:
        '''
        No field names were passed, use the default model fields
        '''
        lookup_fields = model_field_names
    return lookup_fields

def qs_to_dataset(qs, fields=None):
    '''
    ::param qs is any Django queryset
    ::param fields is a list of field name strings, ignoring non-model field names
    This method is the final step, simply calling the fields we formed on the queryset
    and turning it into a list of dictionaries with key/value pairs.
    '''

    lookup_fields = get_lookup_fields(qs.model, fields=fields)
    a = list(qs.values(*lookup_fields))
    for i in a:
        i["indate"] = i["indate"].strftime("%H:%M:%S")
        i["outdate"] = i["outdate"].strftime("%H:%M:%S")
    return a
