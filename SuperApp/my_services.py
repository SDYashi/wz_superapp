import datetime


class MY_APIServices:
    def __init__(self):
        self.api_call_history = []

    def log_api_call(self, request_data, response_data):
        # Create a log entry
        log_entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "request": request_data,
            "response": response_data
        }
        self.api_call_history.append(log_entry)
        
        # Print only the most recent API call
        print("Most Recent API Call:")
        print(log_entry)