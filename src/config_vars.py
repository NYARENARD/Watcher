import os

class_vars = {
    "token" : os.getenv("TOKEN"),
    "prefix" : os.getenv("PREFIX"),
    "logchannel" : os.getenv("LOGCHANNEL"),
    "ttv_channels" : os.getenv("TTVCHANNELS"),
    "nickname" : os.getenv("NICKNAME"),
    "ttv_token" : os.getenv("TTVTOKEN")
}