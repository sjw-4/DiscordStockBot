import schedule
import time
import discordStonksBot as dsb
import subprocess

subprocess.call("discordStonksBot.py", shell=True)

schedule.every().day.at("00:01").do(dsb.expireOpt)

while True:
    schedule.run_pending()
    time.sleep(60)