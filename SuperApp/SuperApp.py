import secrets
from flask import Flask, request, jsonify
from flask_pymongo import PyMongo
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_cors import CORS
import bcrypt
from ERP_APIServices import ERP_APIServices
from NGB_APIServices import NGB_APIServices
from MYDB_Trigger import MongoDBTrigger

app = Flask(__name__)

#Intialize trigger function for change.
trigger = MongoDBTrigger("mongodb://localhost:27017", "admin", "mpwz_notifylist_erp")

# Cross Origin allowing Configuration
CORS(app, resources={r"/*": {"origins": "*"}})

# MongoDB Configuration
app.config["MONGO_URI"] = "mongodb://localhost:27017/admin"
mongo = PyMongo(app)

# JWT Configuration
app.config['JWT_SECRET_KEY'] = secrets.token_hex()  
jwt = JWTManager(app)

@app.route('/', methods=['GET'])
def welcome_page():
   return ("  Welcome MPWZ ADMIN "), 400

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

# @app.route('/set_common_password', methods=['PUT'])
# @jwt_required()
# def set_common_password():
#     # Get the common password
#     common_password = "123456"
#     # Hash the common password
#     hashed_password = bcrypt.hashpw(common_password.encode('utf-8'), bcrypt.gensalt())

#     # Update the password for all users in the collection
#     result = mongo.db.mpwz_users_access_locations.update_many(
#         {},  # Empty filter to match all documents
#         {"$set": {"password": hashed_password}}
#     )

#     # Check how many users were modified
#     if result.modified_count > 0:
#         return jsonify({"msg": f"Password set to '123456' for {result.modified_count} users."}), 200
#     else:
#         return jsonify({"msg": "No users found or password unchanged."}), 404
    
@app.route('/set_user_password', methods=['PUT'])
@jwt_required()
def set_user_password():
    # Get the data from the request
    data = request.get_json()
    username = data.get("username")
    new_password = data.get("new_password")

    if not username or not new_password:
        return jsonify({"msg": "Username and new password are required."}), 400

    # Hash the new password
    hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())

    # Update the password for the specified user in the database
    result = mongo.db.mpwz_users_access_locations.update_one(
        {"username": username},
        {"$set": {"password": hashed_password}}
    )

    # Check if the user was found and the password was updated
    if result.modified_count > 0:
        return jsonify({"msg": f"Password for user '{username}' changed successfully!"}), 200
    else:
        return jsonify({"msg": f"User  '{username}' not found or password unchanged."}), 404 

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

@app.route('/action-history-erp', methods=['GET', 'POST'])
@jwt_required()
def action_history_erp():
    current_user = get_jwt_identity()
    username = current_user['username']

    if request.method == 'GET':
        # Handle GET request to fetch action history
        action_history_records = mongo.db.action_history_erp.find(
            {"erp_notify_to_id": username},  
            {"_id": 0}
        )
        # Convert cursor to a list
        action_history_list = list(action_history_records)

        if action_history_list:
            return jsonify(action_history_list), 200
        else:
            return jsonify({"msg": "No action history found."}), 404

    elif request.method == 'POST':
        # Handle POST request to insert action history
        data = request.json

        required_fields = ["erp_action_datetime", "erp_app_id", "erp_notify_details", 
                           "erp_notify_from_id", "erp_notify_from_name", 
                           "erp_notify_refsys_id", "erp_notify_remark", 
                           "erp_notify_to_id", "erp_notify_to_name", 
                           "erp_sequence_no", "mpwz_id"]

        if not all(field in data for field in required_fields):
            return jsonify({"error": "Missing fields"}), 400

        data['erp_notify_from_id'] = username  

        # Insert the new record into MongoDB
        mongo.db.action_history_erp.insert_one(data)
        
        return jsonify(data), 201

@app.route('/action-history-ngb', methods=['GET', 'POST'])
@jwt_required()
def action_history_ngb():
    current_user = get_jwt_identity()
    username = current_user['username']

    if request.method == 'GET':
        action_history_records = mongo.db.action_history_ngb.find(
            {"ngb_notify_to_id": username},  
            {"_id": 0}
        )
        # Convert cursor to a list
        action_history_list = list(action_history_records)

        if action_history_list:
            return jsonify(action_history_list), 200
        else:
            return jsonify({"msg": "No action history found."}), 404

    elif request.method == 'POST':
        data = request.json
        # Validate the data (basic validation)
        required_fields = ["mpwz_id", "ngb_action_datetime", "ngb_app_id", 
                           "ngb_notify_details", "ngb_notify_from_id", 
                           "ngb_notify_from_name", "ngb_notify_refsys_id", 
                           "ngb_notify_remark", "ngb_notify_to_id", 
                           "ngb_notify_to_name", "ngb_sequence_no"]
        
        if not all(field in data for field in required_fields):
            return jsonify({"error": "Missing fields"}), 400
        
        data['ngb_notify_from_id'] = username  
        mongo.db.action_history_ngb.insert_one(data)
        
        # Return the newly created record with a 201 status code
        return jsonify(data), 201

@app.route('/my-request-history-erp', methods=['GET'])
@jwt_required()
def my_action_history_erp():
    current_user = get_jwt_identity()
    username = current_user['username']
    print(username)
    action_history_records = mongo.db.action_history_erp.find(
          {"erp_notify_from_id": username},  
          {"_id": 0}
    )
    # Convert cursor to a list
    action_history_list = list(action_history_records)

    if action_history_list:
        return jsonify(action_history_list), 200
    else:
        return jsonify({"msg": "No action history found."}), 404

@app.route('/my-request-history-ngb', methods=['GET'])
@jwt_required()
def my_action_history_ngb():
    current_user = get_jwt_identity()
    username = current_user['username']
    print(username)
    action_history_records = mongo.db.action_history_ngb.find(
          {"ngb_notify_from_id": username},  
          {"_id": 0}
    )
    # Convert cursor to a list
    action_history_list = list(action_history_records)

    if action_history_list:
        return jsonify(action_history_list), 200
    else:
        return jsonify({"msg": "No action history found."}), 404

@app.route('/pending-notify-erp', methods=['GET'])
@jwt_required()
def pending_notification_erp():
    current_user = get_jwt_identity()
    username = current_user['username']
    action_history_records = mongo.db.mpwz_notifylist_erp.find(
          {"erp_notify_to_id": username},  
          {"_id": 0}
    )
    # Convert cursor to a list
    action_history_list = list(action_history_records)

    if action_history_list:
        return jsonify(action_history_list), 200
    else:
        return jsonify({"msg": "No action history found."}), 404
    
@app.route('/pending-notify-ngb', methods=['GET'])
@jwt_required()
def pending_notification_ngb():
    current_user = get_jwt_identity()
    username = current_user['username']
    print(username)
    action_history_records = mongo.db.mpwz_notifylist_ngb.find(
          {"ngb_notify_to_id": username},  
          {"_id": 0}
    )
    # Convert cursor to a list
    action_history_list = list(action_history_records)

    if action_history_list:
        return jsonify(action_history_list), 200
    else:
        return jsonify({"msg": "No action history found."}), 404  
    
@app.route('/update-ngb-notify-status-inhouse', methods=['POST'])
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

@app.route('/update-erp-notify-status-inhouse', methods=['POST'])
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
        remote_response = ERP_APIServices.submit_notification_status_erp(notification_data)
    
    if remote_response:
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
    else:
        return jsonify({"msg": "Failed to send notification status to ERP server."}), 500
 
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
    trigger.start_watching()  # Start watching
    app.run(debug=False)