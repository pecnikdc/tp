#!/usr/bin/Python

from datetime import datetime, timedelta
import requests, json, boto3
import os
import calendar

teetimesurl = {"South" : "https://foreupsoftware.com/index.php/api/booking/times?api_key=no_limits&booking_class=888&holes=18&schedule_id=1487&",
               "North" : "https://foreupsoftware.com/index.php/api/booking/times?api_key=no_limits&booking_class=888&holes=18&schedule_id=1468&"
            }
loginurl = "https://foreupsoftware.com/index.php/api/booking/users/login"

username = os.environ['username']
password = os.environ['password']

s3_bucket = "torrey-times"
#times = ["morning","midday","evening"]
times = eval(os.environ['times'])

#Sat 6 Sunday 7
#days = [ 6, 7]
days = eval(os.environ['days'])




def my_handler(event, context):

    resultsCombined = ""
    resultsSouth = {}
    resultsNorth = {}

    logincookie = login()
    resultsSouth = getTimes(logincookie,teetimesurl.get("South"),"south",times)
    str(resultsSouth).encode('ascii', 'ignore')
  
    resultsNorth = getTimes(logincookie,teetimesurl.get("North"),"north",times)
    #putS3("all", resultsNorth, "northkey")
    str(resultsNorth).encode('ascii', 'ignore')
    #print str(resultsNorth)
    #for i in resultsNorth:
        #print resultsNorth.values()

    #print results
    #print json.dumps(results)
    
    if ( len(resultsSouth) != 0):
        #print "results are greater 0 " + str(resultsSouth)
        #pubSNS(resultsSouth,"arn:aws:sns:us-west-2:584679212105:notifications")
        for k,v in resultsSouth.iteritems():
            #print "Tee Times for " + str(k) + " Times " + json.dumps(v)
            myDate = datetime.strptime(k, "%m-%d-%Y" )
            if myDate.weekday() in days :
                resultsCombined = resultsCombined +  "    Torrey Pines South Tee Times: " + str( calendar.day_name[myDate.weekday()])
                

                for k2,v2 in v.iteritems():
                    resultsCombined = resultsCombined +  "  " + str(k2) + " Spots: " + str(v2) + "    "
                    #print str(k2) + str(v2)

        #print resultsCombined

    if ( len(resultsNorth) != 0):
        for k,v in resultsNorth.iteritems():
            myDate = datetime.strptime(k, "%m-%d-%Y" )
            if myDate.weekday() in days :
                resultsCombined = resultsCombined +  "    Torrey Pines North Tee Times: " +  str( calendar.day_name[myDate.weekday()])

                for k2,v2 in v.iteritems():
                    resultsCombined = resultsCombined + "  " + str(k2) + " Spots: " + str(v2) + "    "
        
    if resultsCombined:
        resultsCombined = resultsCombined + "                                       http://foreupsoftware.com/index.php/booking/index/19347"
        pubSNS(resultsCombined,'arn:aws:sns:us-west-2:584679212105:notifications')


    checkUserNotifications("pecnikdc@gmail.com")
    json_times = json.loads(str(getBucketData("teetimes/north/all")))


def login():
    
    data = {"username" : username,
            "password" : password,
            "booking_class_id" : "888",
            "api_key" : "no_limits"  
           }

    r = requests.post(loginurl, data=data)

    token =  r.cookies.get("token")
    phpsession = r.cookies.get("PHPSESSID")
    cookie = {"token": token,
              "PHPSESSID" : phpsession
        }

    return cookie

def getTimes(cookie,courseurl,course,times):

    #times = ["morning","midday"]
    #times = teetimes
    headers = {"Api_key" : "no_limits"}

    #Start at minus one to get current day
    date = datetime.now() + timedelta(days=-1)

    count = 0
    results={}
    full_results = {}
    #Loops through the next 7 days for tee times
    while (count < 8):
        
        #teetimesday = courseurl
        date = date + timedelta(days=+1)
        date_formatted = date.strftime("%m-%d-%Y")

        weekno = date.isoweekday()
               
        count = count + 1
        results = {}
        days = 0

        json_day = {}

        while ( days < len(times)):

            teetimesday = courseurl
            teetimesday = teetimesday + "date=" + date_formatted + "&time=" + times[days]
            days = days + 1
            #print teetimesday

            t = requests.get(teetimesday, cookies=cookie, headers=headers)
            #print t.text
            value = str(t.text)
            #value = value.replace("[","")
            #value = value.replace("]","")
            data = json.loads(value)

            

            for datavalues in data:
                #print data
                #print "Course: " + datavalues['schedule_name'] + " Time: " + datavalues['time'] + " Spots: " + str(datavalues['available_spots'])
                json_day.update( 
                    { datavalues['time'] :  datavalues['available_spots'] }

                )
                #print "Spots: " + str(datavalues['available_spots'])
        
            #print data
            if ( len(data) != 0):
                #results.append(eval(str(data)))
                #full_results.append(eval(str(data)))
                results.update({date_formatted:str(data)})
                
                
                #putS3(date_formatted,t.text,course)

        if( len(results) != 0):
            putS3(date_formatted,str(results),course)
            full_results.update({date_formatted: json_day})
            #pubSNS(data,'arn:aws:sns:us-west-2:584679212105:notifications')
            #print("date is: " + str(data))
            #print("Full Results is: " + str(results))
        else:
            deleteS3(date_formatted,course)
        
        #print str(results)
    putS3("all",json.dumps(full_results),course)
    return full_results

def pubSNS(message,arn):

    client = boto3.client('sns')
    response = client.publish(
        TargetArn=arn,
        Message=json.dumps({'default': json.dumps(message)}),
        MessageStructure='json'
    )

def putS3(key,value,course):

    s3_client = boto3.client('s3')
    s3_client.put_object(
        Bucket=s3_bucket, 
        Key="teetimes/"+course+"/"+key,
        Body=value,
        ContentType='application/json')

def deleteS3(key,course):
    s3_client = boto3.client('s3')
    s3_client.delete_object(
        Bucket=s3_bucket, 
        Key="teetimes/"+course+"/"+key)

def checkUserNotifications(user):
    s3_client = boto3.client('s3')
    
    response = s3_client.get_object(
        Bucket=s3_bucket,
        Key="users/"+user,
        ResponseContentType='application/json')
    data=[]    
    data = response['Body'].read().decode('utf-8')
    json_data = eval(str(data))


def getBucketData(key):
    s3_client = boto3.client('s3')

    response = s3_client.get_object(
        Bucket=s3_bucket,
        Key=key,
        ResponseContentType='application/json')

    data=[]    
    data = response['Body'].read().decode('utf-8')

    return data

#my_handler("event", "one")
