import secrets
from flask import Flask, request, jsonify
from flask_pymongo import PyMongo
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_cors import CORS
import bcrypt
from SuperApp.kafka import init_kafka_app
from SuperApp.shared_api.erp_api_services import ERP_APIServices
from SuperApp.shared_api.ngb_api_services import NGB_APIServices



app = Flask(__name__)

# Register Kafka Blueprint with the app
init_kafka_app(app)

# Cross Origin allowing Configuration
CORS(app, resources={r"/*": {"origins": "*"}})

# MongoDB Configuration
app.config["MONGO_URI"] = "mongodb://localhost:27017/admin"
mongo = PyMongo(app)

# JWT Configuration
app.config['JWT_SECRET_KEY'] = secrets.token_hex()  
jwt = JWTManager(app)

@app.route('/login', methods=['POST'])
def login():
        data = request.get_json()
        username = data.get("username") 
        password = data.get("password")
    
        # Fetch user from the correct collection
        user = mongo.db.mpwz_users_access_locations.find_one({"username": username})
    
    
        if user:
            # Ensure that the password is encoded to bytes
            if bcrypt.checkpw(password.encode('utf-8'), user['password']):
                access_token = create_access_token(identity={"username": username})
                return jsonify(access_token=access_token), 200
            else:
                return jsonify({"msg": f"Failed login attempt for user: {username}"}), 401
        else:
            # return jsonify({"msg": f"User  not found: {username}"}), 401
            return jsonify({"msg": "Invalid username or password"}), 401   

# Change Password
@app.route('/change_password', methods=['PUT'])
@jwt_required()
def change_password():
    current_user = get_jwt_identity()
    data = request.get_json()
    # print(data) 
    new_password = data.get("new_password").encode('utf-8')    
    hashed_password = bcrypt.hashpw(new_password, bcrypt.gensalt())
    mongo.db.mpwz_users_access_locations.update_one({"username": current_user['username']}, {"$set": {"password": hashed_password}})    
    return jsonify({"msg": "Password changed successfully!"}), 200

@app.route('/userprofile', methods=['GET'])
@jwt_required()
def profile():
    current_user = get_jwt_identity()
    username = current_user['username']
    user = mongo.db.mpwz_users_access_locations.find_one({"username": username}, {"_id": 0, "password": 0})  # Exclude password

    if user:
        return jsonify(user), 200
    else:
        return jsonify({"msg": "User  not found"}), 404

@app.route('/action-history', methods=['GET', 'POST'])
@jwt_required()
def action_history():
    current_user = get_jwt_identity()
    username = current_user['username']
    application_type = request.args.get('application_type')  # Get the application type from query parameters

    if request.method == 'GET':
        if application_type == 'erp':
            action_history_records = mongo.db.action_history_erp.find(
               {
                    "$or": [
                        {"erp_notify_to_id": username},
                        {"erp_notify_from_id": username}
                    ]
                },
                {"_id": 0}
            )
            action_history_list = list(action_history_records)
        elif application_type == 'ngb':
            action_history_records = mongo.db.action_history_ngb.find(
                {
                    "$or": [
                        {"ngb_notify_to_id": username},
                        {"ngb_notify_from_id": username}
                    ]
                },
                {"_id": 0}
            )
            action_history_list = list(action_history_records)
        else:
            return jsonify({"error": "Invalid application type"}), 400

        if action_history_list:
            return jsonify(action_history_list), 200
        else:
            return jsonify({"msg": "No action history found."}), 404

    elif request.method == 'POST':
        data = request.json

        if application_type == 'erp':
            required_fields = ["erp_action_datetime", "erp_app_id", "erp_notify_details", 
                               "erp_notify_from_id", "erp_notify_from_name", 
                               "erp_notify_refsys_id", "erp_notify_remark", 
                               "erp_notify_to_id", "erp_notify_to_name", 
                               "erp_sequence_no", "mpwz_id"]

            if not all(field in data for field in required_fields):
                return jsonify({"error": "Missing fields"}), 400

            data['erp_notify_from_id'] = username  
            mongo.db.action_history_erp.insert_one(data)
            return jsonify(data), 201

        elif application_type == 'ngb':
            required_fields = ["mpwz_id", "ngb_action_datetime", "ngb_app_id", 
                               "ngb_notify_details", "ngb_notify_from_id", 
                               "ngb_notify_from_name", "ngb_notify_refsys_id", 
                               "ngb_notify_remark", "ngb_notify_to_id", 
                               "ngb_notify_to_name", "ngb_sequence_no"]
            
            if not all(field in data for field in required_fields):
                return jsonify({"error": "Missing fields"}), 400
            
            data['ngb_notify_from_id'] = username  
            mongo.db.action_history_ngb.insert_one(data)
            return jsonify(data), 201

        else:
            return jsonify({"error": "Invalid application type"}), 400

@app.route('/my-request-notify-list', methods=['GET'])
@jwt_required()
def my_request_notification_list():
    current_user = get_jwt_identity()
    username = current_user['username']
    application_type = request.args.get('application_type')
    notification_status = request.args.get('notification_status')  # Optional parameter

    valid_application_types = ['erp', 'ngb']
    response_data = {
        'username': username,
        'notifications': []
    }

    try:
        # Initialize lists for each application type
        erp_notifications = []
        ngb_notifications = []

        # If application_type is provided and valid
        if application_type:
            if application_type not in valid_application_types:
                return jsonify({"msg": "Invalid application type specified."}), 400

            # Build the query filter based on the application type
            if application_type == 'erp':
                query_filter = {"erp_notify_from_id": username}
                if notification_status:
                    query_filter["erp_notify_status"] = notification_status  # Filter by status if provided
                action_history_records = mongo.db.mpwz_notifylist_erp.find(query_filter, {"_id": 0})
                erp_notifications = list(action_history_records)

            elif application_type == 'ngb':
                query_filter = {"ngb_notify_from_id": username}
                if notification_status:
                    query_filter["ngb_notify_status"] = notification_status  # Filter by status if provided
                action_history_records = mongo.db.mpwz_notifylist_ngb.find(query_filter, {"_id": 0})
                ngb_notifications = list(action_history_records)

        # If no application_type is provided, query both collections
        else:
            # Query ERP notifications
            query_filter_erp = {"erp_notify_from_id": username}
            if notification_status:
                query_filter_erp["erp_notify_status"] = notification_status  # Filter by status if provided
            action_history_records_erp = mongo.db.mpwz_notifylist_erp.find(query_filter_erp, {"_id": 0})
            erp_notifications = list(action_history_records_erp)

            # Query NGB notifications
            query_filter_ngb = {"ngb_notify_from_id": username}
            if notification_status:
                query_filter_ngb["ngb_notify_status"] = notification_status  # Filter by status if provided
            action_history_records_ngb = mongo.db.mpwz_notifylist_ngb.find(query_filter_ngb, {"_id": 0})
            ngb_notifications = list(action_history_records_ngb)

        # Add notifications for ERP if any
        if erp_notifications:
            response_data['notifications'].append({
                "application_name": "erp",
                "pending_count": len(erp_notifications),
                "notification": erp_notifications
            })

        # Add notifications for NGB if any
        if ngb_notifications:
            response_data['notifications'].append({
                "application_name": "ngb",
                "pending_count": len(ngb_notifications),
                "notification": ngb_notifications
            })

        # If no notifications were found, notify the user
        if not response_data['notifications']:
            response_data['msg'] = "No notifications found."

    except Exception as e:
        return jsonify({"msg": "Error retrieving notifications.", "error": str(e)}), 500

    return jsonify(response_data), 200

@app.route('/my-request-notify-count', methods=['GET'])
@jwt_required()
def my_request_notification_count():
    current_user = get_jwt_identity()
    username = current_user['username']
    application_type = request.args.get('application_type')
    notification_status = request.args.get('notification_status')

    valid_application_types = ['erp', 'ngb']
    total_pending_count = 0
    response_data = {
        'username': username,
        'total_pending_count': 0,
        'notification_status': []
    }

    try:
        # Initialize pending counts for each application type
        erp_pending_count = 0
        ngb_pending_count = 0

        # If application_type is provided and valid
        if application_type:
            if application_type not in valid_application_types:
                return jsonify({"msg": "Invalid application type specified."}), 400

            # Build the query filter based on the application type
            if application_type == 'erp':
                query_filter = {"erp_notify_from_id": username}
                if notification_status:
                    query_filter["erp_notify_status"] = notification_status
                action_history_records = mongo.db.mpwz_notifylist_erp.find(query_filter, {"_id": 0})
                action_history_list = list(action_history_records)
                erp_pending_count = len(action_history_list)

            elif application_type == 'ngb':
                query_filter = {"ngb_notify_from_id": username}
                if notification_status:
                    query_filter["ngb_notify_status"] = notification_status
                action_history_records = mongo.db.mpwz_notifylist_ngb.find(query_filter, {"_id": 0})
                action_history_list = list(action_history_records)
                ngb_pending_count = len(action_history_list)

        # If no application_type is provided, query both collections
        else:
            # Query ERP notifications
            query_filter_erp = {"erp_notify_from_id": username}
            if notification_status:
                query_filter_erp["erp_notify_status"] = notification_status
            action_history_records_erp = mongo.db.mpwz_notifylist_erp.find(query_filter_erp, {"_id": 0})
            erp_pending_count = len(list(action_history_records_erp))

            # Query NGB notifications
            query_filter_ngb = {"ngb_notify_from_id": username}
            if notification_status:
                query_filter_ngb["ngb_notify_status"] = notification_status
            action_history_records_ngb = mongo.db.mpwz_notifylist_ngb.find(query_filter_ngb, {"_id": 0})
            ngb_pending_count = len(list(action_history_records_ngb))

        # Calculate total pending count
        total_pending_count = erp_pending_count + ngb_pending_count

        # Prepare response data
        response_data['total_pending_count'] = total_pending_count

        # Add notification status for each application
        if erp_pending_count > 0:
            response_data['notification_status'].append({
                "pending_count": erp_pending_count,
                "application_name": "erp"
            })
        if ngb_pending_count > 0:
            response_data['notification_status'].append({
                "pending_count": ngb_pending_count,
                "application_name": "ngb"
            })

    except Exception as e:
        return jsonify({"msg": "Error retrieving notifications.", "error": str(e)}), 500

    return jsonify(response_data), 200

@app.route('/pending-notify-list', methods=['GET'])
@jwt_required()
def pending_notification_list():
    current_user = get_jwt_identity()
    username = current_user['username']
    application_type = request.args.get('application_type')
    notification_status = request.args.get('notification_status')

    valid_application_types = ['erp', 'ngb']
    response_data = {
        'username': username,
        'notifications': []
    }

    try:
        # Initialize the lists to hold notifications
        erp_notifications = []
        ngb_notifications = []

        # If application_type is provided and valid
        if application_type:
            if application_type not in valid_application_types:
                return jsonify({"msg": "Invalid application type specified."}), 400

            # Build the query filter based on the application type
            if application_type == 'erp':
                query_filter = {"erp_notify_to_id": username}
                if notification_status:
                    query_filter["erp_notify_status"] = notification_status
                action_history_records = mongo.db.mpwz_notifylist_erp.find(query_filter, {"_id": 0})
                erp_notifications = list(action_history_records)

            elif application_type == 'ngb':
                query_filter = {"ngb_notify_to_id": username}
                if notification_status:
                    query_filter["ngb_notify_status"] = notification_status
                action_history_records = mongo.db.mpwz_notifylist_ngb.find(query_filter, {"_id": 0})
                ngb_notifications = list(action_history_records)

        # If no application_type is provided, query both collections
        else:
            # Query ERP notifications
            query_filter_erp = {"erp_notify_to_id": username}
            if notification_status:
                query_filter_erp["erp_notify_status"] = notification_status
            action_history_records_erp = mongo.db.mpwz_notifylist_erp.find(query_filter_erp, {"_id": 0})
            erp_notifications = list(action_history_records_erp)

            # Query NGB notifications
            query_filter_ngb = {"ngb_notify_to_id": username}
            if notification_status:
                query_filter_ngb["ngb_notify_status"] = notification_status
            action_history_records_ngb = mongo.db.mpwz_notifylist_ngb.find(query_filter_ngb, {"_id": 0})
            ngb_notifications = list(action_history_records_ngb)

        # Add notifications to response
        if erp_notifications:
            response_data['notifications'].append({
                "application_name": "erp",
                "notification": erp_notifications
            })
        if ngb_notifications:
            response_data['notifications'].append({
                "application_name": "ngb",
                "notification": ngb_notifications
            })

    except Exception as e:
        return jsonify({"msg": "Error retrieving notifications.", "error": str(e)}), 500

    return jsonify(response_data), 200

@app.route('/pending-notify-count', methods=['GET'])
@jwt_required()
def pending_notification_count():
    current_user = get_jwt_identity()
    username = current_user['username']
    application_type = request.args.get('application_type')
    notification_status = request.args.get('notification_status')

    valid_application_types = ['erp', 'ngb']
    total_pending_count = 0
    response_data = {
        'username': username,
        'total_pending_count': 0,
        'notification_status': []
    }

    try:
        # Initialize pending counts for each application type
        erp_pending_count = 0
        ngb_pending_count = 0

        # If application_type is provided and valid
        if application_type:
            if application_type not in valid_application_types:
                return jsonify({"msg": "Invalid application type specified."}), 400

            # Build the query filter based on the application type
            if application_type == 'erp':
                query_filter = {"erp_notify_to_id": username}
                if notification_status:
                    query_filter["erp_notify_status"] = notification_status
                action_history_records = mongo.db.mpwz_notifylist_erp.find(query_filter, {"_id": 0})
                action_history_list = list(action_history_records)
                erp_pending_count = len(action_history_list)

            elif application_type == 'ngb':
                query_filter = {"ngb_notify_to_id": username}
                if notification_status:
                    query_filter["ngb_notify_status"] = notification_status
                action_history_records = mongo.db.mpwz_notifylist_ngb.find(query_filter, {"_id": 0})
                action_history_list = list(action_history_records)
                ngb_pending_count = len(action_history_list)

        # If no application_type is provided, query both collections
        else:
            # Query ERP notifications
            query_filter_erp = {"erp_notify_to_id": username}
            if notification_status:
                query_filter_erp["erp_notify_status"] = notification_status
            action_history_records_erp = mongo.db.mpwz_notifylist_erp.find(query_filter_erp, {"_id": 0})
            erp_pending_count = len(list(action_history_records_erp))

            # Query NGB notifications
            query_filter_ngb = {"ngb_notify_to_id": username}
            if notification_status:
                query_filter_ngb["ngb_notify_status"] = notification_status
            action_history_records_ngb = mongo.db.mpwz_notifylist_ngb.find(query_filter_ngb, {"_id": 0})
            ngb_pending_count = len(list(action_history_records_ngb))

        # Calculate total pending count
        total_pending_count = erp_pending_count + ngb_pending_count

        # Prepare response data
        response_data['total_pending_count'] = total_pending_count

        # Add notification status for each application
        if erp_pending_count > 0:
            response_data['notification_status'].append({
                "pending_count": erp_pending_count,
                "application_name": "erp"
            })
        if ngb_pending_count > 0:
            response_data['notification_status'].append({
                "pending_count": ngb_pending_count,
                "application_name": "ngb"
            })

    except Exception as e:
        return jsonify({"msg": "Error retrieving notifications.", "error": str(e)}), 500

    return jsonify(response_data), 200
    
@app.route('/update-notify-ngb', methods=['POST'])
@jwt_required()
def update_ngb_notify_status():
    current_user = get_jwt_identity()
    username = current_user['username']    
    # Get data from the request
    data = request.get_json()    
    # Validate required fields
    required_fields = [
        "mpwz_id", "ngb_app_id", "ngb_notify_status", "ngb_notify_to_id"
    ]
    
    for field in required_fields:
        if field not in data:
            return jsonify({"msg": f"{field} is required."}), 400
        
    # Validate if ngb_notify_to_id matches the current user
    ngb_notify_to_id = data["ngb_notify_to_id"]
    if ngb_notify_to_id != username:
        return jsonify({"msg": "You are not authorized to update this notification status."}), 403
    else:
         
        # Prepare data for remote server submission
        notification_data = {
            "mpwz_id": data["mpwz_id"],
            "ngb_app_id": data["ngb_app_id"],
            "ngb_notify_status": data["ngb_notify_status"],
            "ngb_notify_status_updatedon": data.get("ngb_notify_status_updatedon", "now"),
            "ngb_notify_to_id": data["ngb_notify_to_id"]
        }
        
        # Call the NotificationAPI to submit the notification status to the remote server
        remote_response = NGB_APIServices.submit_notification_status_ngb_ccb(notification_data)

        if remote_response:
            # Prepare the update query
            update_query = {
                "ngb_notify_status": data["ngb_notify_status"],
                "ngb_notify_status_updatedon": data.get("ngb_notify_status_updatedon", "now"),         
            }        
            # Find the document and update it
            result = mongo.db.mpwz_notifylist_ngb.update_one(
                {"mpwz_id": data["mpwz_id"], "ngb_notify_to_id": data["ngb_notify_to_id"]},
                {"$set": update_query}
            )
            if result.modified_count > 0:
                return jsonify({"msg": "Notification status updated successfully."}), 200
            else:
                return jsonify({"msg": "No records updated. Please check data."}), 404
        else:
            return jsonify({"msg": "Failed to Send Notification Status to NGB Server."}), 500   

@app.route('/update-notify-erp', methods=['POST'])
@jwt_required()
def update_erp_notify_status():
    current_user = get_jwt_identity()
    username = current_user['username']    
    # Get data from the request
    data = request.get_json()    
    # Validate required fields
    required_fields = [
        "mpwz_id", "erp_app_id", "erp_notify_status", "erp_notify_to_id"
    ]
    
    for field in required_fields:
        if field not in data:
            return jsonify({"msg": f"{field} is required."}), 400
        
    # Validate if erp_notify_to_id matches the current user
    erp_notify_to_id = data["erp_notify_to_id"]
    if erp_notify_to_id != username:
        return jsonify({"msg": "You are not authorized to update this notification status."}), 403
    else:
        # Prepare data for remote server submission
        notification_data = {
            "mpwz_id": data["mpwz_id"],
            "erp_app_id": data["erp_app_id"],
            "erp_notify_status": data["erp_notify_status"],
            "erp_notify_status_updatedon": data.get("erp_notify_status_updatedon", "now"),
            "erp_notify_to_id": data["erp_notify_to_id"]
        }
        
        # Call the NotificationAPI to submit the notification status to the remote server
        # remote_response = ERP_APIServices.submit_notification_status_erp(notification_data)
    
    
    # if remote_response:
        # Prepare the update query
        update_query = {
            "erp_notify_status": data["erp_notify_status"],
            "erp_notify_status_updatedon": notification_data["erp_notify_status_updatedon"],
        }
        
        # Find the document and update it
        result = mongo.db.mpwz_notifylist_erp.update_one(
            {"mpwz_id": data["mpwz_id"], "erp_notify_to_id": data["erp_notify_to_id"]},
            {"$set": update_query}
        )       
        
        if result.modified_count > 0:
            return jsonify({"msg": "Notification status updated successfully."}), 200
        else:
            return jsonify({"msg": "Notification status not updated. Please try again."}), 404
    # else:
    #     return jsonify({"msg": "Failed to send notification status to ERP server."}), 500
 
@app.route('/notify-status', methods=['GET'])
def get_notification_status():
    # Standard notification statuses
    statuses = {
        "statuses": [
            {"id": 1, "status": "Approved"},
            {"id": 2, "status": "Rejected"},
            {"id": 3, "status": "Pending"},
            {"id": 4, "status": "Reassigned"}
        ]
    }

    return jsonify(statuses)


if __name__ == '__main__':
    # trigger.start_watching()  
    app.run(debug=False)