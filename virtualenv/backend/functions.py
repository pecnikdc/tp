#!/usr/bin/Python

from datetime import datetime, timedelta
import requests, json, boto3

teetimesurl = {"South" : "https://foreupsoftware.com/index.php/api/booking/times?api_key=no_limits&booking_class=888&holes=18&schedule_id=1487&",
               "North" : "https://foreupsoftware.com/index.php/api/booking/times?api_key=no_limits&booking_class=888&holes=18&schedule_id=1468&"
            }
loginurl = "https://foreupsoftware.com/index.php/api/booking/users/login"
username = "pecnikdc@gmail.com"
password = "sw14aau"


s3_bucket = "torrey-times"
times = ["morning"] #,"midday"]
#Sat 6 Sunday 7
days = [ 6, 7]

def my_handler(event, context):

    logincookie = login()
    resultsSouth = getTimes(logincookie,teetimesurl.get("South"),"south",times)
    print str(resultsSouth)
    #for i in resultsSouth:
        #print resultsSouth.values()
    resultsNorth = getTimes(logincookie,teetimesurl.get("North"),"north",times)
    print str(resultsNorth)
    #for i in resultsNorth:
        #print resultsNorth.values()

    #print results
    #print json.dumps(results)
    if ( len(resultsSouth) != 0):
        pubSNS(resultsSouth,"arn:aws:sns:us-west-2:584679212105:notifications")

    if ( len(resultsNorth) != 0):
        pubSNS(resultsNorth,"arn:aws:sns:us-west-2:584679212105:notifications")

    checkUserNotifications("pecnikdc@gmail.com")

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
    results=[]
    #Loops through the next 7 days for tee times
    while (count < 8):
        
        teetimesday = courseurl
        date = date + timedelta(days=+1)
        date_formatted = date.strftime("%m-%d-%Y")

        weekno = date.isoweekday()
        print "Weekday is " + str(weekno)
               
        count = count + 1
        results = []
        days = 0
        print( str(weekno==6))
        
        if(weekno == 6 or weekno == 7):
            print "Sat or Sunday checking times"

            while ( days < len(times)):

                teetimesday = teetimesday + "date=" + date_formatted + "&time=" + times[days]
                days = days + 1

                t = requests.get(teetimesday, cookies=cookie, headers=headers)
                #print t.text
                value = str(t.text)
                value.replace("[","")
                value.replace("]","")
                data = json.loads(value)
                #print data
        
                #print data
                if ( len(data) != 0):
                    results.append(data)
                
                    #putS3(date_formatted,t.text,course)

        if( len(results) != 0):
            putS3(date_formatted,str(results),course)
            pubSNS(data,'arn:aws:sns:us-west-2:584679212105:notifications')
        else:
            deleteS3(date_formatted,course)
        
        #print str(results)

    return results

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
    print data[1]