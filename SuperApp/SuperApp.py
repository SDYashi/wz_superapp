import secrets
import datetime
import json
import hashlib
from flask import Flask, request, jsonify
from flask_pymongo import PyMongo
from flask_jwt_extended import JWTManager,create_access_token, jwt_required, get_jwt_identity,get_jwt
from flask_cors import CORS
import bcrypt
from shared_api import ngb_postapi_services
from shared_api.erp_postapi_services import erp_apiservices
from shared_api.ngb_postapi_services import ngb_apiservices
from myservices.my_sequence_generator import SequenceGenerator
from myservices.my_services_logs import my_services

app = Flask(__name__)

# intialize all class's for use app 
seq_gen = SequenceGenerator("admin")
log_entry_event = my_services()

# cross origin allow for applications
CORS(app, resources={r"/*": {"origins": "*"}})

# mongo database's configuration informations
app.config["MONGO_URI"] = "mongodb://localhost:27017/admin"
mongo = PyMongo(app)

# jwt token configuration
app.config['JWT_SECRET_KEY'] ='ashfkjdshfkjdshgflsdkijghsdjlkgdhi' # secrets.token_hex()  
app.config['JWT_ACCESS_TOKEN_EXPIRES']=datetime.timedelta(days=25)
jwt = JWTManager(app)

# this api is only for admin single time purpose where application pushed on server
# @app.route('/set_common_password', methods=['PUT'])
# def set_common_password():
#     # Get the common password
#     common_password = "123456"
#     common_status = "PENDING"

#     # Hash the common password
#     # hashed_password = bcrypt.hashpw(common_password.encode('utf-8'), bcrypt.gensalt())
#     # Update the password for all users in the collection
#     # result = mongo.db.mpwz_users.update_many(
#     #     {}, 
#     #     {"$set": {"password": hashed_password}}
#     # )

#     # Check how many users were modified
#     # if result.modified_count > 0:
#     #     return jsonify({"msg": f"Password set to '123456' for {result.modified_count} users."}), 200
#     # else:
#     #     return jsonify({"msg": "No users found or password unchanged."}), 404
    
#     # Update the password for all users in the collection
#     result1 = mongo.db.mpwz_notifylist.update_many(
#         {}, 
#         {"$set": {"notify_status": common_status}}
#     )
    
#     if result1.modified_count > 0:
#         return jsonify({"msg": f"notify_status set to {common_status} for {result1.modified_count} users."}), 200
#     else:
#         return jsonify({"msg": "No Change  in Notification stats."}), 404

@app.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        username = data.get("username") 
        password = data.get("password")  
        # Retrieve the user from the database
        user = mongo.db.mpwz_users.find_one({"username": username}) 

        if user:
            stored_hashed_password = user['password']

            # Check if the password is correct using bcrypt
            if bcrypt.checkpw(password.encode('utf-8'), stored_hashed_password):
                access_token = create_access_token(identity={"username": username})                
                request_data = username
                response_data = {"status": "success", "message": "Logged in successfully", "BearerToken": access_token}
                log_entry_event.log_api_call(request_data, response_data)

                return jsonify(access_token=access_token), 200            
            else:
                return jsonify({"msg": f"Failed login attempt for user: {username}"}), 401
        else:
            return jsonify({"msg": "Invalid username or password"}), 401             

    except Exception as error:
        return jsonify({"msg": "An error occurred while processing your request", "error": str(error)}), 500

@app.route('/change_password', methods=['PUT'])
@jwt_required()
def change_password():
    try:
        current_user = get_jwt_identity()
        username = current_user['username']
        data = request.get_json()
        # Validate input
        new_password = data.get("new_password")
        if not new_password:
            return jsonify({"msg": "New password is required"}), 400
        # Hash the new password
        hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
        # Update the password in the database
        response = mongo.db.mpwz_users.update_one({"username": username}, {"$set": {"password": hashed_password}})
        if response.modified_count == 0:
            return jsonify({"msg": "No changes made, password may be the same as the current one"}), 400
        response_data = {
            "msg": "Password Changed successfully",
            "BearrToken": username,
            "current_api": request.full_path,
            "client_ip": request.remote_addr,
            "action_by": username,
            "action_at": datetime.datetime.now().isoformat()
        }
        log_entry_event.log_api_call(data, response_data)
        return jsonify({"msg": "Password changed successfully!"}), 200
    except Exception as error:
        return jsonify({"msg": f"An error occurred while changing the password. Please try again later {str(error)}."}), 500

@app.route('/userprofile', methods=['GET'])
@jwt_required()
def view_profile():
    try:
        current_user = get_jwt_identity()
        username = current_user['username']
        request_data = {}

        # Retrieve the user profile from the database
        user = mongo.db.mpwz_users.find_one({"employee_number": username}, {"_id": 0})

        if user:
            for key, value in user.items():
                if isinstance(value, bytes):
                    user[key] = base64.b64encode(value).decode('utf-8')  

            request_data['current_api'] = request.full_path
            request_data['client_ip'] = request.remote_addr
            user['action_by']=username
            user['action_at']=datetime.datetime.now().isoformat()

            response_data = {
                "msg": "User Profile loaded successfully",
                "BearrToken": user,
                "action_by": username,
                "action_at": datetime.datetime.now().isoformat()
            }

            # Log the API call
            log_entry_event.log_api_call(request_data, response_data)
            return jsonify(user), 200
        else:
            return jsonify({"msg": "User not found in records"}), 404

    except Exception as e:
        return jsonify({"msg": f"An error occurred while retrieving the user profile. Please try again later. {str(e)}"}), 500

@app.route('/notify-status', methods=['GET', 'POST'])
@jwt_required()
def notify_status():
    try:
        current_user = get_jwt_identity()
        username = current_user['username']
        request_data = {}
        if request.method == 'GET':
            statuses = list(mongo.db.mpwz_notify_status.find())
            if statuses:
                response_statuses = []
                for status in statuses:
                    # Creating new dictionary to remove _id from response
                    status_response = {key: value for key, value in status.items() if key != '_id'}
                    status_response['action_by'] = username
                    status_response['action_at'] = datetime.datetime.now().isoformat()
                    response_statuses.append(status_response)

                    # Make log entry in table   
                    request_data['current_api'] = request.full_path
                    request_data['client_ip'] = request.remote_addr
                    response_data = {"msg": "User  Profile loaded successfully", "BearrToken": response_statuses}                     
                    log_entry_event.log_api_call(request_data, response_data)

                return jsonify({"statuses": response_statuses}), 200
            else:
                return jsonify({"statuses": "No status added by mpwz admin"}), 404

        elif request.method == 'POST':
            data = request.get_json()
            if 'status' not in data:
                return jsonify({"msg": "Status is required"}), 400 

            myseq_mpwz_id = seq_gen.get_next_sequence('mpwz_notify_status')   
            new_status = {
                "mpwz_id": myseq_mpwz_id,
                "status": data['status'],
                "action_by": username,
                "action_at": datetime.datetime.now().isoformat()
            } 
            result = mongo.db.mpwz_notify_status.insert_one(new_status)
            if result:
                new_status['_id'] = str(result.inserted_id)  
                new_status['server_response'] = "New status added successfully"  
                # Make log entry in table        
                request_data = data 
                request_data['current_api'] = request.full_path
                request_data['client_ip'] = request.remote_addr
                response_data = {"msg": "New Status Added successfully", "BearrToken": new_status}                     
                log_entry_event.log_api_call(request_data, response_data)
                return jsonify(new_status), 201
            else:
                return jsonify({"msg": "Error while adding new status into database"}), 500
        else:
            return jsonify({"msg": "Invalid request encountered at server."}), 400

    except Exception as e:
        return jsonify({"msg": f"An error occurred while processing the request. Please try again later. {str(e)}"}), 500

@app.route('/notify-integrated-app', methods=['GET', 'POST'])
@jwt_required()
def notify_integrated_applist():
    try:
        current_user = get_jwt_identity()
        username = current_user['username']

        if request.method == 'GET':
            statuses = list(mongo.db.mpwz_integrated_app.find())
            if statuses:
                response_statuses = []
                for status in statuses:
                    # Creating new dictionary to remove _id from response
                    status_response = {key: value for key, value in status.items() if key != '_id'}
                    status_response['action_by'] = username
                    status_response['action_at'] = datetime.datetime.now().isoformat()
                    response_statuses.append(status_response)

                    # Make log entry in table        
                    request_data = current_user
                    request_data['current_api'] = request.full_path
                    request_data['client_ip'] = request.remote_addr
                    response_data = {"msg": "New App integrated successfully", "BearrToken": response_statuses}                     
                    log_entry_event.log_api_call(request_data, response_data)

                return jsonify({"app_name_list": response_statuses}), 200
            else:
                return jsonify({"msg": "No apps added by mpwz admin"}), 404

        elif request.method == 'POST':
            data = request.get_json()
            if 'app_name' not in data:
                return jsonify({"msg": "app_name is required"}), 400

            mpwz_id_sequenceno = seq_gen.get_next_sequence('mpwz_integrated_app')
            app_name_list = {
                "mpwz_id": mpwz_id_sequenceno,
                "app_name": data['app_name'],
                "action_by": username,
                "action_at": datetime.datetime.now().isoformat()
            }

            result = mongo.db.mpwz_integrated_app.insert_one(app_name_list)
            if result:
                app_name_list['_id'] = str(result.inserted_id)
                app_name_list['server_response'] = "New app integration info added successfully"

                # Make log entry in table        
                request_data = data
                request_data['current_api'] = request.full_path
                request_data['client_ip'] = request.remote_addr
                response_data = {"msg": "New App integrated successfully", "BearrToken": app_name_list}                     
                log_entry_event.log_api_call(request_data, response_data)
                return jsonify({"app_name_list": app_name_list}), 201
            else:
                return jsonify({"msg": "Unable to add new app details in the system, try again..."}), 500
        else:
            return jsonify({"msg": "Invalid request encountered at server."}), 400

    except Exception as e:
        return jsonify({"msg": f"An error occurred while processing the request. Please try again later. {str(e)}"}), 500
 
@app.route('/action-history', methods=['GET', 'POST'])
@jwt_required()
def action_history():
    try:
        current_user = get_jwt_identity()
        username = current_user['username']
        application_type = request.args.get('application_type')

        if request.method == 'GET':
            if application_type:
                action_history_records = list(mongo.db.mpwz_user_action_history.find(
                    {
                        "$and": [
                            {"app_source": application_type},
                            {
                                "$or": [
                                    {"notify_to_id": username},
                                    {"notify_from_id": username}
                                ]
                            }
                        ]
                    },
                    {"_id": 0}
                ))

                if action_history_records:
                    response_statuses = []
                    for status in action_history_records:
                        # Creating new dictionary to remove _id from response
                        status_response = {key: value for key, value in status.items() if key != '_id'}
                        status_response['action_by'] = username
                        status_response['action_at'] = datetime.datetime.now().isoformat()
                        response_statuses.append(status_response)
                        # Log entry in table  
                        request_data = current_user
                        request_data['current_api'] = request.full_path
                        request_data['client_ip'] = request.remote_addr
                        response_data = {"msg": "Action History loaded successfully", "BearrToken": response_statuses}
                        log_entry_event.log_api_call(request_data, response_data)

                    return jsonify({"action_history": response_statuses}), 200
                else:
                    return jsonify({"msg": "No action history found."}), 404
            else:
                return jsonify({"msg": "Application is not integrated with us, please contact admin"}), 400

        elif request.method == 'POST':
            data = request.json
            if application_type:
                required_fields = [
                    "action_datetime", "app_id", "notify_details",
                    "notify_from_id", "notify_from_name",
                    "notify_refsys_id", "notify_remark",
                    "notify_to_id", "notify_to_name", "mpwz_id"
                ]

                if not all(field in data for field in required_fields):
                    return jsonify({"msg": "Missing required fields"}), 400

                mpwz_id_actionhistory = seq_gen.get_next_sequence('mpwz_user_action_history')
                data['sequence_no'] = str(data['mpwz_id'])
                data['mpwz_id'] = str(mpwz_id_actionhistory)
                data['notify_from_id'] = username
                data['action_by'] = username
                data['action_at'] = datetime.datetime.now().isoformat()

                response = mongo.db.action_history_erp.insert_one(data)
                if response:
                    data['_id'] = str(response.inserted_id)                    
                    # Log entry in table        
                    request_data = data
                    request_data['current_api'] = request.full_path
                    request_data['client_ip'] = request.remote_addr
                    response_data = {"msg": "Action History updated successfully", "BearrToken": current_user}
                    log_entry_event.log_api_call(request_data, response_data)

                    return jsonify({"msg": f"Action history updated successfully, mpwz_id: {mpwz_id_actionhistory}"}), 200
                else:
                    return jsonify({"msg": "Failed to update action history logs"}), 400
            else:
                return jsonify({"msg": "Invalid request encountered at server."}), 400
    except Exception as e:
        return jsonify({"msg": f"An error occurred while processing the request. Please try again later.{str(e)}"}), 500

@app.route('/my-request-notify-count', methods=['GET'])
@jwt_required()
def my_request_notification_count():
    try:
        current_user = get_jwt_identity()
        username = current_user['username']
        notification_status = request.args.get('notification_status')

        # Initialize response data
        response_data = {
            'username': username,
            'total_pending_count': 0,
            'app_notifications_count': {}
        }

        match_stage = {
            'notify_from_id': username
        }

        if notification_status:
            match_stage['notify_status'] = notification_status

        pipeline = [
            {
                '$match': match_stage
            },
            {
                '$group': {
                    '_id': {
                        'app_source': '$app_source',
                        'notify_status': '$notify_status'
                    },
                    'count': {'$sum': 1}
                }
            }
        ]

        notification_counts = mongo.db.mpwz_notifylist.aggregate(pipeline)

        # Process the aggregation results
        for doc in notification_counts:
            app_source = doc['_id']['app_source']
            notify_status = doc['_id']['notify_status']

            if app_source not in response_data['app_notifications_count']:
                response_data['app_notifications_count'][app_source] = {}

            response_data['app_notifications_count'][app_source][notify_status] = doc['count']
            response_data['total_pending_count'] += doc['count']

        # Log the response data
        request_data = current_user
        request_data['current_api'] = request.full_path
        request_data['client_ip'] = request.remote_addr
        log_entry_event.log_api_call(request_data, response_data)

        return jsonify(response_data), 200

    except Exception as e:
        return jsonify({"msg": f"An error occurred while processing the request. Please try again later.{str(e)}"}), 500

@app.route('/my-request-notify-list', methods=['GET'])
@jwt_required()
def my_request_notification_list():
    try:
        current_user = get_jwt_identity()
        username = current_user['username']
        application_type = request.args.get('application_type')
        notification_status = request.args.get('notification_status')

        # Check if the application type exists
        app_exists = mongo.db.mpwz_integrated_app.find_one({"app_name": application_type})
        if not app_exists:
            return jsonify({"msg": "Application type does not exist."}), 400 

        # Initialize response data
        response_data = {
            'username': username,
            'notifications': []
        }
        # Build the query for filters
        query = {
            'app_source': application_type,
            'notify_from_id': username,
            'notify_status':notification_status
        }

        # if notification_status:
        #     query['notify_status'] = notification_status

        # Fetching notifications by query
        notifications = mongo.db.mpwz_notifylist.find(query)

        # Process notifications
        for notification in notifications:
            notification_copy = notification.copy()  
            notification_copy.pop('_id', None)  
            response_data['notifications'].append(notification_copy)

        # Log the notification list retrieval
        request_data = current_user
        request_data['current_api'] = request.full_path
        request_data['client_ip'] = request.remote_addr
        log_entry_event.log_api_call(request_data, {"msg": "My request info list loaded successfully", "BearrToken": response_data['notifications']})

        if not response_data['notifications']:
            return jsonify({"msg": "No notifications found."}), 404

        return jsonify(response_data), 200

    except Exception as e:
        return jsonify({"msg": f"An error occurred while processing the request. Please try again later. {str(e)}"}), 500

@app.route('/pending-notify-count', methods=['GET'])
@jwt_required()
def pending_notification_count():
    try:
        current_user = get_jwt_identity()
        username = current_user['username'] 
        notification_status = request.args.get('notification_status')

        # Initialize response data
        response_data = {
            'username': username,
            'total_pending_count': 0,
            'app_notifications_count': {}
        }
        
        # Build the match stage based on whether notification_status is provided
        match_stage = {
            'notify_to_id': username
        }
        
        if notification_status:
            match_stage['notify_status'] = notification_status

        pipeline = [
            {
                '$match': match_stage
            },
            {
                '$group': {
                    '_id': {
                        'app_source': '$app_source',
                        'notify_status': '$notify_status'
                    },
                    'count': {'$sum': 1}
                }
            }
        ] 
        
        notification_counts = mongo.db.mpwz_notifylist.aggregate(pipeline)
        
        for doc in notification_counts:
            app_source = doc['_id']['app_source']
            notify_status = doc['_id']['notify_status']
            
            if app_source not in response_data['app_notifications_count']:
                response_data['app_notifications_count'][app_source] = {}

            response_data['app_notifications_count'][app_source][notify_status] = doc['count']
            response_data['total_pending_count'] += doc['count']

        # Log the response statuses
        if notification_counts:
            response_statuses = []
            for status in notification_counts:
                status_response1 = {key: value for key, value in status.items() if key != '_id'}  
                status_response1['action_by'] = username
                status_response1['action_at'] = datetime.datetime.now().isoformat()
                response_statuses.append(status_response1)
                
                # Make logs entry in table  
                request_data = current_user
                request_data['current_api'] = request.full_path
                request_data['client_ip'] = request.remote_addr
                response_data = {"msg": "action pending info count loaded successfully", "BearrToken": response_statuses}
                log_entry_event.log_api_call(request_data, response_data)       
        else:
            return jsonify({"msg": "Failed to update pending request for action logs"}), 400     

        return jsonify(response_data), 200

    except Exception as e:
        return jsonify({"msg": "An error occurred while processing your request", "error": str(e)}), 500
    
@app.route('/pending-notify-list', methods=['GET'])
@jwt_required()
def pending_notification_list():
    try:
        current_user = get_jwt_identity()
        username = current_user['username']
        application_type = request.args.get('application_type')
        notification_status = request.args.get('notification_status')

        # Check if the application type exists
        app_exists = mongo.db.mpwz_integrated_app.find_one({"app_name": application_type})
        if not app_exists:
            return jsonify({"msg": "application type does not exist."}), 400  

        # response_data = {
        #     'username': username,
        #     'notifications': []
        # }
        response_data=[]
        
        query = {
            'app_source': application_type,  
            'notify_to_id': username,
            'notify_status':notification_status
        }

        # if notification_status:
        #     query['notify_status'] = notification_status

        # Fetch data using query
        notifications = mongo.db.mpwz_notifylist.find(query)
        unique_button_names = mongo.db.mpwz_buttons.distinct('button_name')

        for notification in notifications:
            notification_copy = notification.copy()  
            notification_copy.pop('_id', None) 
            notification_copy['buttons'] = unique_button_names  
            response_data.append(notification_copy) 
            # response_data['notifications'].append(notification_copy) 

        # Log the response statuses
        # if response_data['notifications']:
        if response_data:
            response_statuses = []
            # for notification in response_data['notifications']:
            for notification in response_data:
                status_response1 = {key: value for key, value in notification.items()}  
                status_response1['action_by'] = username
                status_response1['action_at'] = datetime.datetime.now().isoformat()
                response_statuses.append(status_response1)

                # Make logs entry in table  
                request_data = current_user
                request_data['current_api'] = request.full_path
                request_data['client_ip'] = request.remote_addr
                log_entry_event.log_api_call(request_data, {"msg": "action pending info list loaded successfully", "BearrToken": response_statuses})       
        else:
            return jsonify({"msg": "No pending notifications found."}), 404 

        return jsonify(response_data), 200

    except Exception as e:
        return jsonify({"msg": "An error occurred while processing your request", "error": str(e)}), 500
     
@app.route('/update-notify-inhouse-app', methods=['POST'])
@jwt_required()
def update_notify_status_inhouse_app():
    try:
        current_user = get_jwt_identity()
        data = request.get_json()
        remote_response = ""
        username = current_user['username']
        app_source = request.args.get('app_source')
        app_exists = mongo.db.mpwz_integrated_app.find_one({"app_name": app_source})
        if not app_exists:
            return jsonify({"msg": "Requesting application is not integrated with our server."}), 400
        required_fields = ["mpwz_id", "app_source", "app_source_appid", "notify_status", "notify_refsys_id", "notify_to_id", "notify_from_id","notify_type"]

        for field in required_fields:
            if field not in data:
                return jsonify({"msg": f"{field} is required"}), 400

        notify_to_id = data["notify_to_id"]
        if notify_to_id != username:
            return jsonify({"msg": "You are not authorized to update this notification status."}), 403

        if app_source == 'ngb':
            ngb_user_details = mongo.db.mpwz_notifylist.find_one({
                "app_source": app_source,
                "mpwz_id": data["mpwz_id"],
                "notify_refsys_id": data['notify_refsys_id']
            })

            if ngb_user_details is None:
                return jsonify({"msg": "Notification details not found in databaase"}), 404

            if ngb_user_details.get("notify_type") == "CC4":
                shared_api_data = {
                    "id": ngb_user_details["notify_refsys_id"],
                    "locationCode": ngb_user_details["locationCode"],
                    "approver": ngb_user_details["approver"],
                    "billId": ngb_user_details["billId"],
                    "billCorrectionProfileInitiatorId": ngb_user_details["billCorrectionProfileInitiatorId"],
                    "status": data["notify_status"],
                    "remark": ngb_user_details["remark"],
                    "updatedBy": ngb_user_details["updatedBy"],
                    "updatedOn": ngb_user_details["updatedOn"]
                }
                remote_response = ngb_postapi_services.notify_ngb_toupdate_cc4status(shared_api_data)

            elif ngb_user_details.get("notify_type") == "CCB":
                shared_api_data = {
                    "postingDate": ngb_user_details["postingDate"],
                    "amount": ngb_user_details["amount"],
                    "code": ngb_user_details["code"],
                    "ccbRegisterNo": ngb_user_details["ccbRegisterNo"],
                    "remark": ngb_user_details["remark"],
                    "consumerNo": ngb_user_details["consumerNo"],
                }
                remote_response = ngb_postapi_services.notify_ngb_toupdate_ccbstatus(shared_api_data)
            else:
                return jsonify({"msg": "Notification Type is not allowed to push data to NGB."}), 400

        elif app_source == 'erp':

            return jsonify({"msg": "Notification Type is not allowed to push data to ERP."}), 400

        else:
            return jsonify({"msg": f"Something went wrong while verifying remote servers: {app_source}"}), 200

        if remote_response is not None and remote_response.status_code == 200:
            # Prepare the update query
            update_query = {
                "notify_status": data["notify_status"],
                "notify_refsys_response": remote_response,
                "notify_status_updatedon": datetime.datetime.now().isoformat(),
            }

            # Find the document and update it
            result = mongo.db.mpwz_notifylist.update_one(
                {"mpwz_id": data["mpwz_id"], "notify_to_id": data["notify_to_id"]},
                {"$set": update_query}            )

            if result.modified_count > 0:
                response_statuses = []
                for status in result:
                    status_response1 = {key: value for key, value in status.items() if key != '_id'}
                    status_response1['action_by'] = username
                    status_response1['action_at'] = datetime.datetime.now().isoformat()
                    response_statuses.append(status_response1)

                # Make logs entry in table
                request_data = username
                request_data['current_api'] = request.full_path
                request_data['client_ip'] = request.remote_addr
                response_data = {"msg": "Notification updated in in-house server successfully", "Bear Token": response_statuses}
                log_entry_event.log_api_call(request_data, response_data)
                return jsonify({"msg": f"Notification status updated successfully. {result.modified_count}"}), 200
            else:
                return jsonify({"msg": f"Something went wrong while updating Notification in own servers: {app_source}"}), 400
        else:
            return jsonify({"msg": f"Something went wrong while updating Notification into remote servers: {app_source}"}), 200
    except Exception as e:
        return jsonify({"msg": f"Something went wrong while processing request in primary stage {str(e)}"}), 500
     
## Extenal API for Get Data from Remote Servers ##
@app.route('/shared-call/api/ngb/post-notify-list', methods=['POST'])
@jwt_required()
def create_notification_from_ngb():
    current_user = get_jwt_identity()
    data = request.get_json() 
    username = current_user['username']     
    application_type = request.args.get('app_source')    
    app_request_type = request.args.get('app_request_type')

    print(f"requesting data for {app_request_type} and request comming from {application_type}")   

    app_exists = mongo.db.mpwz_integrated_app.find_one({"app_name": application_type})
    if not app_exists:
        return jsonify({"msg": "requesting application is not integrated with our server."}), 400 
    else: 

        required_fields_map = {
            "CC4": ["id", "locationCode", "approver", "billId", "billCorrectionProfileInitiatorId", "status", "remark", "updatedBy", "updatedOn"],
            "CCB": ["id", "postingDate", "amount", "code", "ccbRegisterNo", "remark", "consumerNo"]
        }
        # Check if the data_type exists in the required fields map
        if app_request_type in required_fields_map:
            required_fields = required_fields_map[app_request_type]
            for field in required_fields:
                if field not in data:
                    return jsonify({"msg": f"{field} is required for {app_request_type}."}), 400
        else:
            return jsonify({"msg": f"Invalid data type: {app_request_type}."}), 400  
        
        existing_record = mongo.db.mpwz_notifylist.find_one({"notify_refsys_id": data["notify_refsys_id"]})
        if existing_record:      
            return jsonify({"msg": "Records with notify_refsys_id already existed in database."}), 400
        else:  
            # Generate sequence number for mpwz_id
            mpwz_id_sequenceno = seq_gen.get_next_sequence('mpwz_notifylist')
            if mpwz_id_sequenceno:  
                if app_request_type=="CC4":
                    data['mpwz_id'] = mpwz_id_sequenceno
                    data['app_source'] = "ngb"
                    data['app_source_appid'] = data['app_source_appid']
                    data['notify_status'] = data['notify_status']
                    data['notify_refsys_id'] = data['notify_refsys_id']
                    data['notify_to_id'] = data['notify_to_id']
                    data['notify_from_id'] = data['notify_from_id']
                    data['notify_to_name'] = data['notify_to_name']
                    data['notify_from_name'] = data['notify_from_name']
                else:
                    data['mpwz_id'] = mpwz_id_sequenceno
                    data['app_source'] = "ngb"
                    data['app_source_appid'] = data['app_source_appid']
                    data['notify_status'] = data['notify_status']
                    data['notify_refsys_id'] = data['notify_refsys_id']
                    data['notify_to_id'] = data['notify_to_id']
                    data['notify_from_id'] = data['notify_from_id']
                    data['notify_to_name'] = data['notify_to_name']
                    data['notify_from_name'] = data['notify_from_name']
            try:
                result = mongo.db.mpwz_notifylist.insert_one(data)
                if result:
                    response_status = {
                        "mpwz_id": data["mpwz_id"],
                        "action_by": username,
                        "action_at": datetime.datetime.now().isoformat()
                    }
                    request_data = current_user
                    response_data = {
                        "status": "success", 
                        "msg": f"Data inserted successfully from source {application_type} id:--{str(result.inserted_id)}",
                        "BearerToken": response_status
                    }
                    # Log adding logs i9nto db
                    log_entry_event.log_api_call(request_data, response_data)
                    return jsonify({"msg": "Data inserted successfully", "id": str(result.inserted_id)}), 200
                else:
                    seq_gen.reset_sequence('mpwz_notifylist_erp')
                    return jsonify({"msg": "Failed to insert data from remote server logs"}), 400 
                
            except Exception as errors:
                seq_gen.reset_sequence('mpwz_notifylist_erp')
                return jsonify({"msg": f"Failed to insert data: {str(errors)}"}), 500

@app.route('/shared-call/api/erp/post-notify-list', methods=['POST'])
@jwt_required()
def create_notification_from_erp():
    current_user = get_jwt_identity()
    data = request.get_json() 
    username = current_user['username']     
    application_type = request.args.get('app_source')    
    app_request_type = request.args.get('app_request_type') 
    
    print(f"requesting data for {app_request_type} and request comming from {application_type}")   

    app_exists = mongo.db.mpwz_integrated_app.find_one({"app_name": application_type})
    if not app_exists:
        return jsonify({"msg": "requesting application is not integrated with our server."}), 400 
    else: 
        required_fields_map = {
            "LEAVE": ["id", "locationCode", "approver", "billId", "billCorrectionProfileInitiatorId", "status", "remark", "updatedBy", "updatedOn"],
            "PROJECT": ["id", "locationCode", "approver", "billId", "billCorrectionProfileInitiatorId", "status", "remark", "updatedBy", "updatedOn"],
            "TADA": ["id", "locationCode", "approver", "billId", "billCorrectionProfileInitiatorId", "status", "remark", "updatedBy", "updatedOn"],
            "BILL": ["id", "locationCode", "approver", "billId", "billCorrectionProfileInitiatorId", "status", "remark", "updatedBy", "updatedOn"]
        }
        # Check if the data_type exists in the required fields map
        if app_request_type in required_fields_map:
            required_fields = required_fields_map[app_request_type]
            for field in required_fields:
                if field not in data:
                    return jsonify({"msg": f"{field} is required for {app_request_type}."}), 400
        else:
            return jsonify({"msg": f"Invalid data type: {app_request_type}."}), 400  
        
        existing_record = mongo.db.mpwz_notifylist.find_one({"notify_refsys_id": data["notify_refsys_id"]})
        if existing_record:      
            return jsonify({"msg": "Records with notify_refsys_id already existed in database."}), 400
        else:  
            # Generate sequence number for mpwz_id
            mpwz_id_sequenceno = seq_gen.get_next_sequence('mpwz_notifylist')
            if mpwz_id_sequenceno:
                    data['mpwz_id'] = mpwz_id_sequenceno
                    data['app_source'] = "ngb"
                    data['app_source_appid'] = data['app_source_appid']
                    data['notify_status'] = data['notify_status']
                    data['notify_refsys_id'] = data['notify_refsys_id']
                    data['notify_to_id'] = data['notify_to_id']
                    data['notify_from_id'] = data['notify_from_id']
                    data['notify_to_name'] = data['notify_to_name']
                    data['notify_from_name'] = data['notify_from_name']
                    data['app_request_type'] = data['app_request_type']
            try:
                result = mongo.db.mpwz_notifylist.insert_one(data)
                if result:
                    response_status = {
                        "mpwz_id": data["mpwz_id"],
                        "action_by": username,
                        "action_at": datetime.datetime.now().isoformat()
                    }
                    request_data = current_user
                    response_data = {
                        "status": "success", 
                        "msg": f"Data inserted successfully from source {application_type} id:--{str(result.inserted_id)}",
                        "BearerToken": response_status
                    }
                    # Log adding logs i9nto db
                    log_entry_event.log_api_call(request_data, response_data)
                    return jsonify({"msg": "Data inserted successfully", "id": str(result.inserted_id)}), 200
                else:
                    seq_gen.reset_sequence('mpwz_notifylist')
                    return jsonify({"msg": "Failed to insert data from remote server logs"}), 400 
                
            except Exception as errors:
                seq_gen.reset_sequence('mpwz_notifylist')
                return jsonify({"msg": f"Failed to insert data: {str(errors)}"}), 500

# this api is only for testng purpose
@app.route('/shared-call/api/ngb/post-notify-list-test', methods=['POST'])
def create_notification_testing():
    data = request.get_json() 
    try:
        data_type = data['code']
        if data_type:        
            request_type ="CCB"
        else:
            request_type="CC4"

        if request_type=="CC4":
            myseq_mpwz_id = seq_gen.get_next_sequence('mpwz_notify_status') 
            data['mpwz_id'] = myseq_mpwz_id
            data['app_source'] = "ngb"
            data['app_source_appid'] = data['approvalStatus']
            data['notify_status'] = data['approvalStatus']
            data['notify_refsys_id'] = data['approvalStatus']
            data['notify_to_id'] = data['approvalStatus']
            data['notify_from_id'] = data['approvalStatus']
            data['notify_to_name'] = data['approvalStatus']
            data['notify_from_name'] = data['approvalStatus']
        else:
            myseq_mpwz_id = seq_gen.get_next_sequence('mpwz_notify_status') 
            data['mpwz_id'] = myseq_mpwz_id
            data['app_source'] = "ngb"
            data['app_source_appid'] = data['approvalStatus']
            data['notify_status'] = data['approvalStatus']
            data['notify_refsys_id'] = data['approvalStatus']
            data['notify_to_id'] = data['approvalStatus']
            data['notify_from_id'] = data['approvalStatus']
            data['notify_to_name'] = data['approvalStatus']
            data['notify_from_name'] = data['approvalStatus']

    except Exception as e:
           return jsonify({"error new": str(e)}), 500
    
    # Insert the data into MongoDB
    try:
        mongo.db.mpwz_notifylist.insert_one(data)
        return jsonify({"message": "Data inserted successfully"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # app.run(debug=False)
    app.run(host='0.0.0.0', port=8000,debug=False)