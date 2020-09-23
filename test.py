import pickle

msg = "asdf\n"
msg_buffer = ""

msg_buffer = msg.rstrip() + "\n\n \n\n" + msg.rstrip()


for line in msg_buffer.split():
    print(line)

