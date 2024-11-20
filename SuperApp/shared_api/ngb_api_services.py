import requests 

class NGB_APIServices:
    BASE_URL = "https://ngb.mpwin.co.in:8700/update-notification-ngb" 

    @staticmethod
    def submit_notification_status_ngb_cc4(notification_data):
        try:
            response = requests.post(NGB_APIServices.BASE_URL, json=notification_data)
            response.raise_for_status() 
            return response.json()  
        except requests.exceptions.RequestException as e:
            print(f"NGB Response:- {e}")
            return None
    
    @staticmethod
    def submit_notification_status_ngb_ccb(notification_data):
        try:
            response = requests.post(NGB_APIServices.BASE_URL, json=notification_data)
            response.raise_for_status() 
            return response.json()  
        except requests.exceptions.RequestException as e:
            print(f"NGB Response:- {e}")
            return None    