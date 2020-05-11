# DiscordStockBot
Bot in Python3 that can be connected to discord to allow a server to trade stocks with fake money and track the leader board. Currently a work in progress
I use this for my friends so some of the language in the messages may not be appropriate for all audiences

To use:
1) Follow the steps to "authenticate" the bot with Discord, here is the link I used https://realpython.com/how-to-make-a-discord-bot-python/
2) Create a file called ".env", include the following but adjust as needed for your implementation  
  #.env  
  DISCORD_TOKEN=                    #PUT YOUR TOKEN HERE, follow above link for details  
  DISCORD_GUILD=                    #Put the name of your server/guild you want the bot in  
  DISCORD_ADMIN=                    #your Discord username, allows you to enter admin commands  
  DISCORD_SUGGEESTIONS=suggest.txt  #you can rename the file whatever you'd like  
3) Make sure the necessary packages are installed (using pip3)
  - yahoo_fin
  - pandas
  - discord.py
  - requests_html
  - python-dotenv
4) run with "python3 runBot.py", I ran on Linux (Ubuntu) so I can't guarentee anything on Windows or Mac

The list of commands are in the file, I tried to keep things organized but you know how it goes. This is a few day project, so have fairly low expectations going in

Future plans:
  - Add log file for debugging after errors
  - Add timestamps
  - Add more admin commands (ie. set start money, etc)
