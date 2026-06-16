def write_log(msg):
    f = open("log.txt", "w")
    f.write(msg)
    f.close()
