import secrets
import datetime
import json
import hashlib
from flask import Flask, request, jsonify
from flask_pymongo import PyMongo
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_cors import CORS
import bcrypt
from shared_api.erp_postapi_services import erp_apiservices
from shared_api.ngb_postapi_services import ngb_apiservices
from myservices.my_sequence_generator import SequenceGenerator
from myservices.my_services import my_services

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
app.config['JWT_SECRET_KEY'] = secrets.token_hex()  
app.config['JWT_ACCESS_TOKEN_EXPIRES']=datetime.timedelta(hours=1)
jwt = JWTManager(app)

@app.route('/login', methods=['POST'])
def login():
        data = request.get_json()
        username = data.get("username") 
        password = data.get("password")  
        user = mongo.db.mpwz_users_credentials.find_one({"username": username}) 
        if user:
            if bcrypt.checkpw(password.encode('utf-8'), user['password']):
                access_token = create_access_token(identity={"username": username})
                data = request.json
                json_string = json.dumps(data, sort_keys=True) 
                hash_object = hashlib.sha256(json_string.encode())
                request_data = hash_object.hexdigest()
                response_data = {"status": "success", "message": "Logged in successfully","BearrToken":access_token}
                log_entry_event.log_api_call(request_data,response_data)
                return jsonify(access_token=access_token), 200            
            else:
                return jsonify({"msg": f"Failed login attempt for user: {username}"}), 401
        else:
            return jsonify({"msg": "Invalid username or password"}), 401   

@app.route('/change_password', methods=['PUT'])
@jwt_required()
def change_password():
    current_user = get_jwt_identity()
    username = current_user['username']
    data = request.get_json()
    new_password = data.get("new_password").encode('utf-8')    
    hashed_password = bcrypt.hashpw(new_password, bcrypt.gensalt())
    response=mongo.db.mpwz_users_credentials.update_one({"username": current_user['username']}, {"$set": {"password": hashed_password}}) 
    if response:
        request_data = request.json
        response_data = {"status": "success", "message": "Password Changed successfully","BearrToken":current_user}
        response_data['action_by']=username
        response_data['action_at']= datetime.datetime.now().isoformat()    
        log_entry_event.log_api_call(request_data,response_data)
    else:
        return jsonify({"msg": "Failed to update password change logs"}), 400       
    return jsonify({"msg": "Password changed successfully!"}), 200

@app.route('/userprofile', methods=['GET'])
@jwt_required()
def profile():
    current_user = get_jwt_identity()
    username = current_user['username']
    user = mongo.db.mpwz_users_credentials.find_one({"username": username}, {"_id": 0, "password": 0})  
    if user:          
        user['action_by']=username
        user['action_at']=  datetime.datetime.now().isoformat()       
        request_data = request.json
        response_data = {"status": "success", "message": "User Profile load successfully","BearrToken":user}
        log_entry_event.log_api_call(request_data,response_data)
        return jsonify({"userinfo":user}), 200
    else:
        return jsonify({"msg": "user not found in records"}), 404

@app.route('/notify-status', methods=['GET', 'POST'])
@jwt_required()
def notify_status():    
    current_user = get_jwt_identity()
    username = current_user['username']
    if request.method == 'GET':
        statuses = list(mongo.db.mpwz_notify_status.find())
        if statuses:
            response_statuses = []
            for status in statuses:
                # Creating new dictionary for remove _id from response
                status_response = {key: value for key, value in status.items() if key != '_id'}
                status_response['action_by']=username
                status_response['action_at']= datetime.datetime.now().isoformat()
                response_statuses.append(status_response)
                #make logs entry in table        
                request_data = request.json
                response_data = {"status": "success", "message": "User Profile load successfully","BearrToken":response_statuses}                     
                log_entry_event.log_api_call(request_data,response_data)
            return jsonify({"statuses": response_statuses})
        else:
            return jsonify({"statuses": "no status added by mpwz admin"})
    elif request.method == 'POST':
        data = request.get_json()
        if 'status' not in data:
            return jsonify({"msg": "status is required"}), 400
        
        new_status = {
            "mpwz_id":seq_gen.get_next_sequence('mpwz_notify_status'),
            "status": data['status'],
            "action_by":username,
            "action_at": datetime.datetime.now().isoformat()
        } 
        result = mongo.db.mpwz_notify_status.insert_one(new_status)
        new_status['_id'] = str(result.inserted_id)  
        new_status['server_response'] = "new status added successfully"         
        #make logs entry in table        
        request_data = request.json
        response_data = {"status": "success", "message": "New Status Added successfully","BearrToken":new_status}                     
        log_entry_event.log_api_call(request_data,response_data)
        return jsonify(new_status), 201
    else:
         return jsonify({"msg": "invalid request incountered at server.."}), 400

@app.route('/notify-integrated-app', methods=['GET', 'POST'])
@jwt_required()
def notify_integrated_applist():      
    current_user = get_jwt_identity()
    username = current_user['username']
    if request.method == 'GET':
        statuses = list(mongo.db.mpwz_integrated_app.find())  
        if statuses:
            response_statuses = []
            for status in statuses:
                # Creating new dictionary for remove _id from response
                status_response = {key: value for key, value in status.items() if key != '_id'}                
                status_response['action_by']=username
                status_response['action_at']= datetime.datetime.now().isoformat()
                response_statuses.append(status_response)
                #make logs entry in table        
                request_data = request.json
                response_data = {"status": "success", "message": "New App integred successfully","BearrToken":response_statuses}                     
                log_entry_event.log_api_call(request_data,response_data)
            return jsonify({"app_name_list": response_statuses})
        else:
            return jsonify({"msg": "no apps added by mpwz admin"})
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
            app_name_list['server_response'] = "new app integration info added successfully"               
            #make logs entry in table        
            request_data = request.json
            response_data = {"status": "success", "message": "New App integred successfully","BearrToken":app_name_list}                     
            log_entry_event.log_api_call(request_data,response_data)
            return jsonify({"app_name_list":app_name_list}), 200
        else:
             return jsonify({"msg": "unable to add new app details in system, try again..."}), 400
    else:
         return jsonify({"msg": "invalid request incountered at server.."}), 400

@app.route('/action-history', methods=['GET', 'POST'])
@jwt_required()
def action_history():
    current_user = get_jwt_identity()
    username = current_user['username']
    application_type = request.args.get('application_type') 
    if request.method == 'GET':            
        if application_type:    
            action_history_records = mongo.db.mpwz_user_action_history.find(
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
            )
            if action_history_records:  
                response_statuses = []
                for status in action_history_records:
                    # Creating new dictionary for remove _id from response
                    status_response = {key: value for key, value in status.items() if key != '_id'}                
                    status_response['action_by']=username
                    status_response['action_at']= datetime.datetime.now().isoformat()
                    response_statuses.append(status_response)
                    print("response_code:--",response_statuses)
                    #make logs entry in table  
                    request_data = request.json
                    response_data = {"status": "success", "message": "Action History load successfully","BearrToken":response_statuses}
                    log_entry_event.log_api_call(request_data,response_data)
                return jsonify({"action_history": response_statuses}), 200
            else:
                return jsonify({"msg": "No action history found."}), 404
        else:
            return jsonify({"msg": "application is not intergrated with us, please contact admin"}), 400

    elif request.method == 'POST':
        data = request.json
        if application_type:
            required_fields = ["action_datetime", "app_id", "notify_details", 
                               "notify_from_id", "notify_from_name", 
                               "notify_refsys_id", "notify_remark", 
                               "notify_to_id", "notify_to_name", "mpwz_id"]

            if not all(field in data for field in required_fields):
                return jsonify({"msg": f"Missing fields"}), 400
            else:

                mpwz_id_actionhistory=seq_gen.get_next_sequence('mpwz_user_action_history')
                data['sequence_no']= str(data['mpwz_id'])
                data['mpwz_id']=str(mpwz_id_actionhistory)
                data['notify_from_id'] = username                       
                data['action_by']=username
                data['action_at']=  datetime.datetime.now().isoformat()  
                response = mongo.db.action_history_erp.insert_one(data)
                if response:
                    data['_id'] = str(response.inserted_id)              
                    request_data = data
                    response_data = {"status": "success", "message": "Action History Updated successfully","BearrToken":current_user}
                    log_entry_event.log_api_call(request_data,response_data)
                else:
                    return jsonify({"msg": "Failed to update action history logs"}), 400    
            return jsonify({"msg": f"action history updated successfully mpwz_id:-{mpwz_id_actionhistory}"}), 200      
        else:
         return jsonify({"msg": "invalid request incountered at server.."}), 400

@app.route('/my-request-notify-count', methods=['GET'])
@jwt_required()
def my_request_notification_count():
    current_user = get_jwt_identity()
    username = current_user['username'] 
    notification_status = request.args.get('notification_status') 
    # Initialize response data
    response_data = {
        'username': username,
        'total_pending_count': 0,
        'app_notifications_count': {}
    }

    pipeline = [
        {
            '$match': {
                'notify_status': notification_status,  
                'notify_from_id': username
            }
        },
        {
            '$group': {
                '_id': '$app_source', #group by data
                'count': {'$sum': 1}  
            }
        }
    ]
    notification_counts = mongo.db.mpwz_notifylist.aggregate(pipeline)
    # add the response data
    for doc in notification_counts:
        response_data['app_notifications_count'][doc['_id']] = doc['count']
        response_data['total_pending_count'] += doc['count']  
    return jsonify(response_data), 200

@app.route('/my-request-notify-list', methods=['GET'])
@jwt_required()
def my_request_notification_list():
    current_user = get_jwt_identity()
    username = current_user['username']
    application_type = request.args.get('application_type')
    notification_status = request.args.get('notification_status')

    app_exists = mongo.db.mpwz_integrated_app.find_one({"app_name": application_type})
    if not app_exists:
        return jsonify({"msg": "application type does not exist."}), 400  

    # Initialize response data
    response_data = {
        'username': username,
        'notifications': []
    }

    # Build the query for filters
    query = {
        'app_source': application_type,  
        'notify_status': notification_status,
        'notify_from_id': username
    }   

    # # Use $or functions for add notify_to_id for search
    # query = {
    #     '$or': [
    #         {'notify_from_id': username},
    #         {'notify_to_id': username}
    #     ]
    # }

    # Fetch notifications based on  query
    notifications = mongo.db.mpwz_notifylist.find(query)

    for notification in notifications:
        notification_copy = notification.copy()  # copy of the notification
        notification_copy.pop('_id', None)  
        response_data['notifications'].append(notification_copy) 
    return jsonify( response_data), 200

@app.route('/pending-notify-count', methods=['GET'])
@jwt_required()
def pending_notification_count():
    current_user = get_jwt_identity()
    username = current_user['username'] 
    notification_status = request.args.get('notification_status')

    # Initialize response data
    response_data = {
        'username': username,
        'total_pending_count': 0,
        'app_notifications_count': {}
    }
    pipeline = [
        {
            '$match': {
                'notify_status': notification_status,  
                'notify_to_id': username
            }
        },
        {
            '$group': {
                '_id': '$app_source', 
                'count': {'$sum': 1}  
            }
        }
    ]
    notification_counts = mongo.db.mpwz_notifylist.aggregate(pipeline)
    # add the response data
    for doc in notification_counts:
        response_data['app_notifications_count'][doc['_id']] = doc['count']
        response_data['total_pending_count'] += doc['count']  
    return jsonify(response_data), 200

@app.route('/pending-notify-list', methods=['GET'])
@jwt_required()
def pending_notification_list():
    current_user = get_jwt_identity()
    username = current_user['username']
    application_type = request.args.get('application_type')
    notification_status = request.args.get('notification_status')

    app_exists = mongo.db.mpwz_integrated_app.find_one({"app_name": application_type})
    if not app_exists:
        return jsonify({"msg": "application type does not exist."}), 400  

    # Initialize response data
    response_data = {
        'username': username,
        'notifications': []
    }

    # Build the query for filters
    query = {
        'app_source': application_type,  
        'notify_status': notification_status,
        'notify_to_id': username
    }

    # Fetch notifications based on  query
    notifications = mongo.db.mpwz_notifylist.find(query)

    for notification in notifications:
        notification_copy = notification.copy()  # copy of the notification
        notification_copy.pop('_id', None)  
        response_data['notifications'].append(notification_copy) 
    return jsonify( response_data), 200


@app.route('/update-notify-inhouse', methods=['POST'])
@jwt_required()
def update_notify_status():
    current_user = get_jwt_identity()
    username = current_user['username']    
    # Get data from the request
    data = request.get_json()    
    # Validate required fields
    required_fields = [
        "mpwz_id", "app_id", "notify_status", "notify_to_id","notify_from_id"
    ]
    
    for field in required_fields:
        if field not in data:
            return jsonify({"msg": f"{field} is required."}), 400
        
    # Validate if notify_to_id matches the current user
    notify_to_id = data["notify_to_id"]
    if notify_to_id != username:
        return jsonify({"msg": "You are not authorized to update this notification status."}), 403
    else:
         
        # Prepare data for remote server submission
        notification_data = {
            "mpwz_id": data["mpwz_id"],
            "app_id": data["app_id"],
            "notify_status": data["notify_status"],
            "notify_status_updatedon": data.get("notify_status_updatedon", "now"),
            "notify_to_id": data["notify_to_id"],
            "notify_from_id": data["notify_from_id"]
        }
        
        # Call the NotificationAPI to submit the notification status to the remote server
        remote_response = APIServices.submit_notification_status_ccb(notification_data)

        if remote_response:
            # Prepare the update query
            update_query = {
                "notify_status": data["notify_status"],
                "notify_status_updatedon": data.get("notify_status_updatedon", "now"),         
            }        
            # Find the document and update it
            result = mongo.db.mpwz_notifylist_ngb.update_one(
                {"mpwz_id": data["mpwz_id"], "notify_to_id": data["notify_to_id"]},
                {"$set": update_query}
            )
            if result.modified_count > 0:
                return jsonify({"msg": "Notification status updated successfully."}), 200
            else:
                return jsonify({"msg": "No records updated. Please check data."}), 404
        else:
            return jsonify({"msg": "Failed to Send Notification Status to NGB Server."}), 500   


## Extenal API for Remote Servers ##
@app.route('/api/erp-notify', methods=['POST'])
def create_notification_from_erp():
    required_fields = [
        "app_id",
        "notify_status",
        "notify_refsys_id",
        "notify_from_id",
        "notify_from_name",
        "notify_to_id",
        "notify_to_name",
        "notify_title",
        "notify_description",
        "notify_comments",
        "notify_notes",
        "notify_intiatedby",
        "notify_datetime",   
    ]

    # Check if all required fields are provided
    for field in required_fields:
        if field not in request.json:
            return jsonify({"msg": f"{field} is required"}), 400

    # Generate sequence number for mpwz_id
    mpwz_id_sequenceno = seq_gen.get_next_sequence('mpwz_notifylist_erp')

    # Extract the data from the incoming request
    data = {
        "mpwz_id": mpwz_id_sequenceno,
        "app_id": request.json["app_id"],
        "notify_status": request.json["notify_status"],
        "notify_refsys_id": request.json["notify_refsys_id"],
        "notify_from_id": request.json["notify_from_id"],
        "notify_from_name": request.json["notify_from_name"],
        "notify_to_id": request.json["notify_to_id"],
        "notify_to_name": request.json["notify_to_name"],
        "notify_title": request.json["notify_title"],
        "notify_description": request.json["notify_description"],
        "notify_comments": request.json["notify_comments"],
        "notify_notes": request.json["notify_notes"],
        "notify_intiatedby": request.json["notify_intiatedby"],
        "notify_datetime": request.json["notify_datetime"]
    }

    # Checking notify_refsys_id already exists in the collection
    existing_record = mongo.db.mpwz_notifylist_erp.find_one({"notify_refsys_id": data["notify_refsys_id"]})

    if existing_record:      
        return jsonify({"msg": "Record with this notify_refsys_id already exists."}), 400
  
    try:
        result = mongo.db.mpwz_notifylist_erp.insert_one(request.json)
        return jsonify({"message": "Data inserted successfully", "id": str(result.inserted_id)}), 200
    except Exception as e:
        return jsonify({"msg": f"Failed to insert data: {str(e)}"}), 500



if __name__ == '__main__':
    app.run(debug=False)