import requests 

class ERP_APIServices:
    BASE_URL = "https://prodserv.mpwin.co.in:8700/update-notification-erp" 

    @staticmethod
    def submit_notification_status_erp(notification_data):
        try:
            response = requests.post(ERP_APIServices.BASE_URL, json=notification_data)
            response.raise_for_status() 
            return response.json()  
        except requests.exceptions.RequestException as e:
            print(f"ERP Response:- {e}")
            return None