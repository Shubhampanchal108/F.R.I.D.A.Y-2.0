import eel

eel.init("Frontend")

@eel.expose
def friday_reply(user_msg):
    print("User:", user_msg)

    # yaha tera AI logic aayega
    reply = f"Hello Shubhu 😄 You said: {user_msg}"
    return reply

eel.start("index.html", size=(2000, 2000))
