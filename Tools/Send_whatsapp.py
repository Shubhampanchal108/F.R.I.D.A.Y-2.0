import pywhatkit as kit
from datetime import datetime

Contact = {
    "shubham":"+9138248542",
    "mummy": "+919138248542"
}

whatsapp_tool = {
    "name": "send_whatsapp_message",
    "description": "Send a professional WhatsApp message to a saved contact using Friday Assistant",
    "parameters": {
        "type": "object",
        "properties": {
            "user_name": {
                "type": "string",
                "description": "Name of the contact saved in Friday contacts, e.g. Rahul, Mom"
            },
            "message": {
                "type": "string",
                "description": "Message content provided by the user. Friday will format it professionally."
            }
        },
        "required": ["user_name", "message"]
    }
}

def send_whatsapp_message(user_name: str, message: str):
    try:
        user_key = user_name.lower()

        # Contact exist check
        if user_key not in Contact:
            return f"❌ No contact saved with name {user_name}."

        phone_number = Contact[user_key]

        # Empty message check
        if not message or not message.strip():
            return "❌ Message cannot be empty."

        # Try sending message
        kit.sendwhatmsg(phone_number, message.strip(), datetime.now().hour, datetime.now().minute + 1)

        return f"✅ Message sent to {user_name}."

    except Exception as e:
        # Any failure (WhatsApp not installed, internet issue, etc.)
        return f"❌ Failed to send message to {user_name}. Error: {str(e)}"


print(send_whatsapp_message("mummy", "Hello How are you"))
