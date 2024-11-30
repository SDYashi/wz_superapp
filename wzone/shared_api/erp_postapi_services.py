from flask import jsonify
import requests 

class erp_apiservices:

    @staticmethod
    def notify_erp_toupdate_status(data):
        try:
            response = requests.post("https://prodserv.mpwin.co.in:8700/update-notification-erp", json=data)
            response.raise_for_status() 
            return response.json()  
        except requests.exceptions.RequestException as error_response:
            print(f"ERP Response:- {error_response}")
            return jsonify({"msg": f"Failed to connect ERP Server Due to Error:{error_response}"}), 401
        
    @staticmethod
    def notify_erp_togetdate_status(data):
        try:
            response = requests.get("https://prodserv.mpwin.co.in:8700/get-notification-erp", json=data)
            response.raise_for_status() 
            return response.json()  
        except requests.exceptions.RequestException as error_response:
            print(f"ERP Response:- {error_response}")
            return jsonify({"msg": f"Failed to connect ERP Server Due to Error:{error_response}"}), 401    
        
    @staticmethod
    def erp_dologin_token(data):
        try:
            response = requests.post("https://prodserv.mpwin.co.in:8700/login-erp", json=data)
            response.raise_for_status() 
            return response.json()  
        except requests.exceptions.RequestException as error_response:
            print(f"ERP Response:- {error_response}")
            return jsonify({"msg": f"Failed to connect ERP Server Due to Error:{error_response}"}), 401    