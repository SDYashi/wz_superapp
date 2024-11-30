from flask import jsonify
import requests 

class ngb_apiservices:
    
    @staticmethod
    def notify_ngb_toupdate_cc4status(data):
        try:
            response = requests.post("https://ngb.mpwin.co.in:8700/update-notification-ngb", json=data)
            response.raise_for_status() 
            return response.json()  
        except requests.exceptions.RequestException as error_response:
            print(f"ERP Response:- {error_response}")
            return jsonify({"msg": f"Failed to connect NGB Server Due to Error:{error_response}"}), 401
        
    @staticmethod    
    def notify_ngb_toupdate_ccbstatus(data):
        try:
            response = requests.post("https://ngb.mpwin.co.in:8700/update-notification-ngb", json=data)
            response.raise_for_status() 
            return response.json()  
        except requests.exceptions.RequestException as error_response:
            print(f"ERP Response:- {error_response}")
            return jsonify({"msg": f"Failed to connect NGB Server Due to Error:{error_response}"}), 401
        
    @staticmethod
    def notify_ngb_togetdate_cc4status(data):
        try:
            response = requests.get("https://ngb.mpwin.co.in:8700/get-notification-ngb", json=data)
            response.raise_for_status() 
            return response.json()  
        except requests.exceptions.RequestException as error_response:
            print(f"ERP Response:- {error_response}")
            return jsonify({"msg": f"Failed to connect NGB Server Due to Error:{error_response}"}), 401    
        
    @staticmethod
    def notify_ngb_togetdate_ccbstatus(data):
        try:
            response = requests.get("https://ngb.mpwin.co.in:8700/get-notification-ngb", json=data)
            response.raise_for_status() 
            return response.json()  
        except requests.exceptions.RequestException as error_response:
            print(f"ERP Response:- {error_response}")
            return jsonify({"msg": f"Failed to connect NGB Server Due to Error:{error_response}"}), 401    