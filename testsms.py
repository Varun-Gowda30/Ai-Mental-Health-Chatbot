import requests
import gpsloc as g
def process(msg,mob,mob1):
    
    mobile=mob+","+mob1
    url = "https://www.fast2sms.com/dev/bulkV2"

    querystring = {"authorization":"zlPm5TXA86EZGwc7pKyoDnQt0IC9OqsNR2ghYafk3ujBre4JUHlQoZuF8iUR3bWAHnEeM2mhXjKzq5Ok","sender_id":"TXTIND","message":str(msg),"route":"v3","numbers":str(mobile)}

    headers = {
        'cache-control': "no-cache"
    }

    response = requests.request("GET", url, headers=headers, params=querystring)

    print(response.text)
##loc=g.get_loc()
##aa="eswar"
##msg=aa+"didn't wear the Helmet in the location "+"https://www.google.co.in/maps/place/"+loc+" Pay Rs.2000/- fine to BTP"
#process(msg,"9844641410","9902752525")
