from datetime import datetime

def get_date_with_day():
    try:
        today = datetime.now()
        formatted_date = today.strftime("%Y-%m-%d")  
        day_name = today.strftime("%A")              

        return {
            "status": "success",
            "action": "get_date_with_day",
            "message": "Current date with day fetched",
            "date": formatted_date,
            "day": day_name,
            "formatted": f"{formatted_date} ({day_name})"
        }

    except Exception as e:
        return {
            "status": "error",
            "code": "DATE_DAY_FETCH_FAILED",
            "message": str(e)
        }

def get_current_time():
    try:
        now = datetime.now()
        formatted_time = now.strftime("%H:%M:%S") 
        return {
            "status": "success",
            "action": "get_current_time",
            "message": "Current time fetched",
            "time": formatted_time
        }
    except Exception as e:
        return {
            "status": "error",
            "code": "TIME_FETCH_FAILED",
            "message": str(e)
        }
