#Stock trading bot for Discord
#created by SJ Wilkins IV, 05/17/2020
#Current version: 0.2

import sys
sys.dont_write_bytecode = True

from yahoo_fin import stock_info as si
from yahoo_fin import options as op
import os
import pickle as pk
from enum import Enum
import numpy as np
import datetime

import discord
from dotenv import load_dotenv

try:
    import main as tt
except:
    print("Unable to load Trump Twitter module")

#INITIALIZATION STUFF--------------------------------------------------
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')
ADMIN = os.getenv('DISCORD_ADMIN')
SUGGEST = os.getenv('DISCORD_SUGGESTIONS')

#GLOBAL VARIABLES------------------------------------------------------
allUsers = []           #list of all User objects
startMoney = 1000000    #amount of money each user starts with
adminCmds = True        #whether or not to allow admin commands
optBuys = 100           #how many options are bought at a time (default 100)
curDate = ""            #the current date
dateFormat = '%Y-%m-%d' #format used for the date

#Pre written outputs---------------------------------------------------
badError = "You shouldn't see this error, if you do shit is fucked. Let SJ know"
commands = ["--help", "--addme <name>", "--info <ticker>", "--buy <stock/calls/puts> <ticker> <amount> <*strike*> <*YYYY-MM-DD*>", "--sell <stock/calls/puts> <ticker> <amount> <*strike*> <*YYYY-MM-DD*>", "--summary <name>", "--history <name>", "--leaderboard", "--suggest <your suggestion to admin>"]
listOfCommands = "List of commands: \n" + "\n".join(commands)
badInputResponse = "Incorrect input for command, type --help for full command list"
marketCloseResp = "Pools closed. No trading now. You must live with your poor choices until the market reopens."

#Stuff for options trading
    #name = 0
    #strike = 2
    #cost = 3

#info in users---------------------------------------------------------
    #name:      actual name (i.e. Sean)
    #uName:     discord username (i.e. Minimojobot)
    #rank:      current rank in group
    #curMoney:  how much money they have in their profile
    #curVal:    how much their entire portfolio is worth right now
    #curStocks: stocks currently in their portfolio (ticker->amount) or ('type:ticker:strike:date'->amount)
    #tradeHist: trade history (ticker->(trade type, amount))

#TODO
'''
    - add timestamps to events
    - add ability to trade options
    - add log file
'''
#Returns the stock price for given ticker
def getStockPrice(ticker):
    try:
        return si.get_live_price(ticker)
    except:
        return "Failed to load current stock price for " + ticker + ". Transaction cancelled."

#Returns true if the given ticker is one that is tracked, False otherwise
def verifyStockTicker(ticker):
    try:
        si.get_live_price(ticker)
    except:
        return False
    return True

#Saves user data to pickle file
def saveUserData(user):
    user.updateInfo()
    try:
        with open(user.name + '.pkl', 'wb') as uf:
            pk.dump(user.name, uf)
            pk.dump(user.uName, uf)
            pk.dump(user.rank, uf)
            pk.dump(user.curMoney, uf)
            pk.dump(user.curVal, uf)
            pk.dump(user.curStocks, uf)
            pk.dump(user.tradeHist, uf)
    except:
        print("ERROR:saveUserData: unable to save data for " + str(user.name))

#Returns option table with the given parameters
def getOptTable(_type, _ticker, _date):
    try:
        return op.get_options_chain(_ticker, _date)[_type].to_numpy()
    except:
        return "Unable to load options chain for the requested data, please check your inputs"

#Returns the cost for an option in a table with the given strike price
def getOptCost(_optTable, _strikePrice):
    for row in _optTable:
        if row[2] == _strikePrice:
            return float(row[3])
    return "Unable to load cost of requested option, please check your inputs"

#Returns if a given string is in valid date format
def validDate(_date):
    try:
        if _date == datetime.datetime.strptime(_date, dateFormat).strftime(dateFormat): return True
    except:
        return False

#Returns value of option
def getOptVal(_type, _ticker, _strike):
    rawVal = float(getStockPrice(_ticker)) - _strike
    if _type == 'puts':
        rawVal *= -1
    if rawVal > 0:
        return rawVal * optBuys
    else:
        return 0

class User:
    #Initializes user, loads existing data if it exists
    def __init__(self, _name, _uName = None):
        if os.path.exists(_name):
            print("Loading file")
            with open(_name, 'rb') as uf:
                self.name = pk.load(uf)
                self.uName = pk.load(uf)
                self.rank = pk.load(uf)
                self.curMoney = pk.load(uf)
                self.curVal = pk.load(uf)
                self.curStocks = pk.load(uf)
                self.tradeHist = pk.load(uf)
        else:
            print("Creating new user")
            self.name = _name
            self.uName = _uName
            self.rank = -1
            self.curMoney = startMoney
            self.curVal = -1
            self.curStocks = {}
            self.tradeHist = []
            saveUserData(self)
    
    #Updates the users curVal variable
    def updateInfo(self):
        self.curVal = self.curMoney
        for stock in self.curStocks:
            if ':' not in stock:
                self.curVal += getStockPrice(stock) * self.curStocks[stock]
            else:
                optInfo = stock.split(':')
                try:
                    optTable = getOptTable(optInfo[0], optInfo[1], optInfo[3])
                    if type(optTable) == str:
                        raise Exception("Unable to load optTable")
                    optCost = getOptCost(optTable, optInfo[2])
                    if type(optCost) == str:
                        raise Exception("Unable to load optCost")
                    self.curVal += optCost * optBuys * self.curStocks[stock]
                except:
                    self.curVal += getOptVal(optInfo[0], optInfo[1], float(optInfo[2])) * self.curStocks[stock]
        if self.curVal <= 0:
            print("WARNING:updateInfo: " + str(self.name) + " has negative value -> " + str(self.curVal))
    
    #Attempts to issue buy command
    def buyStock(self, _ticker, _amount):
        if not verifyStockTicker(_ticker):
            return "Stock ticker not recognized"
        curPrice = getStockPrice(_ticker)
        if self.curMoney < curPrice * _amount:
            return str(self.name) + " is a broke ass bitch and can't afford " + str(_amount) + " of " + str(_ticker)
        self.curMoney -= curPrice * _amount
        if _ticker in self.curStocks:
            self.curStocks[_ticker] += _amount
        else:
            self.curStocks[_ticker] = _amount
        self.tradeHist.append({'type': 'buy', 'ticker': _ticker, 'amount': _amount, 'price': curPrice})
        saveUserData(self)
        return str(self.name) + " successfully purchased " + str(_amount) + " of " + _ticker

    #Attempts to issue sell command
    def sellStock(self, _ticker, _amount):
        if not verifyStockTicker(_ticker):
            return "Stock ticker not recognized"
        curPrice = getStockPrice(_ticker)
        if _ticker not in self.curStocks or self.curStocks[_ticker] < _amount:
            return str(self.name) + " is a dumbass who doesn't own " + str(_amount) + " of " + _ticker + " to sell"
        self.curMoney += curPrice * _amount
        self.curStocks[_ticker] -= _amount
        if self.curStocks[_ticker] == 0:
            del self.curStocks[_ticker]
        self.tradeHist.append({'type': 'sell', 'ticker': _ticker, 'amount': _amount, 'price': curPrice})
        saveUserData(self)
        return str(self.name) + " successfully sold " + str(_amount) + " of " + _ticker
    
    #Prints summary for user
    def getSummary(self):
        self.updateInfo()
        output = ""
        output += "Summary for " + self.name + " (" + self.uName + "):\n"
        output += "Current cash:\t\t\t$" + str(round(self.curMoney, 2)) + "\n"
        output += "Current net worth:\t$" + str(round(self.curVal, 2)) + "\n"
        output += "Current holdings:\n"
        for stock in self.curStocks:
            if ':' not in stock:
                output += "\t" + str(stock) + ":" + " " * (5 - len(str(stock))) + str(self.curStocks[stock]) + " at $" + str(round(getStockPrice(stock), 2)) + " ea.\n"
            else:
                optInfo = stock.split(':')
                output += "\t" + optInfo[0] + " " + optInfo[1] + ", x" + str(self.curStocks[stock]) + " at $" + optInfo[2] + ", exp:" + optInfo[3] + "\n"
        return output

    #Updates the users rank
    def setRank(self, _rank):
        self.rank = _rank
        saveUserData(self)

    #Prints full trading history for user
    def getTradeHist(self):
        output = ""
        output += "Trade history for " + self.name + " (" + self.uName + "):\n"
        for i in reversed(range(len(self.tradeHist))):
            output += "\t" + self.tradeHist[i]['type'] + " - " + self.tradeHist[i]['ticker'] + " - " + str(self.tradeHist[i]['amount']) + " - $" + str(round(self.tradeHist[i]['price'], 2))
            if 'strike' in self.tradeHist[i]:
                output += " - strk:" + str(self.tradeHist[i]['strike']) + " - exp:" + str(self.tradeHist[i]['date'])
            output += "\n"
        return output

    #Attempts to buy options
    def buyOptions(self, _type, _ticker, _date, _strike, _numBuys):
        optTable = getOptTable(_type, _ticker, _date)
        if type(optTable) == str:
            return optTable
        optCost = getOptCost(optTable, _strike)
        if type(optCost) == str:
            return optCost
        if self.curMoney < optBuys * optCost * _numBuys:
            return str(self.name) + " is a broke ass bitch and can't afford " + str(_numBuys) + " " + str(_type)[:-1] + " options of " + str(_ticker) + " expiring " + _date
        self.curMoney -= optBuys * optCost * _numBuys
        if str(_type + ':' + _ticker + ':' + str(_strike) + ':' + _date) in self.curStocks:
            self.curStocks[str(_type + ':' + _ticker + ':' + str(_strike) + ':' + _date)] += _numBuys
        else:
            self.curStocks[str(_type + ':' + _ticker + ':' + str(_strike) + ':' + _date)] = _numBuys
        self.tradeHist.append({'type': 'buy:' + _type, 'ticker': _ticker, 'amount': _numBuys, 'price': optCost, 'strike': _strike, 'date': _date})
        saveUserData(self)
        return str(self.name) + " successfully purchased " + str(_numBuys) + " " + str(_type)  + " of " + _ticker
    
    #Attempts to sell options
    def sellOptions(self, _type, _ticker, _date, _strike, _numSells):
        #('type:ticker:strike:date'->amount)
        hashKey = _type + ':' + _ticker + ':' + str(_strike) + ':' + _date
        if hashKey not in self.curStocks or self.curStocks[hashKey] < _numSells:
            return str(self.name) + " is a dumbass who doesn't own enough " + _type + " of " + _ticker + " expiring on " + _date + " at strike price $" + str(_strike) + " to sell"
        optTable = getOptTable(_type, _ticker, _date)
        if type(optTable) == str:
            return optTable
        optCost = getOptCost(optTable, _strike)
        if type(optCost) == str:
            return optCost
        self.curMoney += optCost * optBuys * _numSells
        self.curStocks[hashKey] -= _numSells
        if self.curStocks[hashKey] == 0:
            del self.curStocks[hashKey]
        self.tradeHist.append({'type': 'sell' + _type, 'ticker': _ticker, 'amount': _numSells, 'price': optCost, 'strike': _strike, 'date': _date})
        saveUserData(self)
        return str(self.name) + " successfully sold " + str(_numSells) + " " + str(_type)  + " of " + _ticker

    #Checks if options have expires and calculate the return appropriately
    def expOpts(self):
        tempDict = {}
        for opt in self.curStocks:
            if ':' in opt:
                optInfo = opt.split(':')
                if datetime.datetime.strptime(optInfo[3], dateFormat) < datetime.datetime.strptime(curDate, dateFormat):
                    price = getOptVal(optInfo[0], optInfo[1], float(optInfo[2])) * self.curStocks[opt]
                    self.curMoney += price
                    self.tradeHist.append({'type':'exp:' + optInfo[0], 'ticker': optInfo[1], 'amount': self.curStocks[opt], 'price': price, 'strike': optInfo[2], 'date': optInfo[3]})
                    print(self.name + " had an option expire")
                else:
                    tempDict[opt] = self.curStocks[opt]
            else:
                tempDict[opt] = self.curStocks[opt]
        self.curStocks = tempDict
        saveUserData(self)

#Prints info about a stock
def getStockInfo(_ticker):
    if not verifyStockTicker(_ticker):
        return "Stock ticker not recognized"
    return "Current price for " + _ticker + ": " + str(round(getStockPrice(_ticker), 2))

#Creates new user
def createUser(_name, _uName):
    name = _name.strip()
    uName = _uName

    for user in allUsers:
        if user.uName == uName:
            return "Account already created, ready to accept commands"
        if user.name == name:
            return "Name already in use, please select another"

    try:
        allUsers.append(User(name, uName))
        return "New user added successfully"
    except:
        print("ERROR:createUser: oof")
        return badError

#Updates the rank for all users
def updateRanks():
    global allUsers
    for user in allUsers:
        user.updateInfo()
    allUsers = sorted(allUsers, key = lambda u: u.curVal, reverse=True)
    for i in range(len(allUsers)):
        allUsers[i].setRank(i + 1)
        saveUserData(allUsers[i])

#Prints leaderboard for users
def getLeaderboard():
    updateRanks()
    output = ""
    for user in allUsers:
        output += str(user.rank)+ ": " + user.name + "" + " " * (10 - len(user.name)) + "$" + str(round(user.curVal, 2)) + "\n"
    return output

#Does initial data loading and preparing on boot
def startService():
    global curDate
    curDate = datetime.datetime.today().strftime(dateFormat)
    try:
        allFiles = os.listdir()
        for f in allFiles:
            if f.endswith('.pkl'):
                allUsers.append(User(f))
        print("Users loaded successfully")
    except:
        print("Unable to load users")
    if not os.path.exists(SUGGEST):
        cFile = open(SUGGEST, 'w')
        cFile.write("Suggestions sent to admin:\n")
        cFile.close()
        print("Created suggestion file")
    try:
        print("Trying to expire contracts")
        expireOpt()
    except:
        print("Error expiring options")

#Get index of user from uName
def getUserIndex(_uName):
    for i in range(len(allUsers)):
        if allUsers[i].uName == _uName or allUsers[i].name == _uName:
            return i
    print("ERROR:getUserIndex: user not found in database")
    return "error: User not found in database"

#ADMIN ONLY - resets the files in the program
def resetFiles():
    try:
        allFiles = os.listdir()
        for f in allFiles:
            if f.endswith('.pkl'):
                os.remove(f)
    except:
        print("Failed to reset files, aborting")
        exit()
    startService()
    for i in range(len(allUsers)):
        del allUsers[0]
    if len(allUsers) != 0:
        return "Error in reseting data"
    return "Bot reset successfully"

#Logs suggestions to a file to be read by the admin later
def logSuggestion(auth, sug):
    try:
        sugFile = open(SUGGEST, 'a')
        sugFile.write("<" + auth + ">: " + sug.strip() + "\n")
        sugFile.close()
    except:
        print("Error logging suggestion to file")
        return "Error logging suggestion to file, try again or contact admin"
    return "Successfully logged suggestion by " + auth + " to file"

#Calculate expired options
def expireOpt():
    #check if it's a new day
    curDate = datetime.datetime.today().strftime('%Y-%m-%d')
    for user in allUsers:
        user.expOpts()

#Returns true if market is open, false otherwise
def canTrade():
    curWeekday = datetime.datetime.today().weekday()
    time = (int(datetime.datetime.now().strftime('%H')) * 100) + int(datetime.datetime.now().strftime('%M'))
    if curWeekday < 5 and time >= 830 and time < 1500:
        return True
    else:
        return False


#HANDLE INPUT FROM DISCORD------------------------------------------------
    #Input options:
    '''
    --addme <name>
    --info <ticker>
    --buy <stock/calls/puts> <ticker> <amount> <strike*> <YYYY-MM-DD*>
    --sell <stock/calls/puts> <ticker> <amount> <strike*> <YYYY-MM-DD*>
    --summary <name>
    --history <name>
    --leaderboard
    '''

def handleDiscord(_author, _command):
    try:
        author = str(_author)
        cmds = str(_command).split()
    except:
        print("ERROR:handleDiscord: error converting input\n\t" + str(_author) + "\n\t" + str(_command))
        return badError
    
    #Check if attempting to trade after hours
    if not canTrade() and (cmds[0] == '--buy' or cmds[0] == '--sell'):
        return marketCloseResp

    #ADMIN COMMANDS - No input checking so make sure you do it right
    if adminCmds:
        if author == ADMIN:
            if cmds[0] == "--createAcct":   #--createAcct <name> <user name>
                return "ADMIN: " + createUser(cmds[1], cmds[2])
            if cmds[-1:][0] == "PROXY":     #--<cmd> <args...> <user name> PROXY
                author = cmds[-2:-1][0]
                cmds = cmds[:-2]
            if cmds[0] == "--reset":        #--reset
                return resetFiles()

    #GENERAL COMMANDS
    if cmds[0] == "--help":
        return listOfCommands
    elif cmds[0] == "--addme":
        if len(cmds) < 2: return badInputResponse
        return createUser(cmds[1], author)
    elif cmds[0] == "--info":
        if len(cmds) < 2: return badInputResponse
        return getStockInfo(cmds[1])
    elif cmds[0] == '--buy':
        if len(cmds) < 4: return badInputResponse
        userI = getUserIndex(author)
        if type(userI) is not int: return userI
        if cmds[1] == 'stock' and len(cmds) == 4:
            try: return allUsers[userI].buyStock(cmds[2], int(cmds[3]))
            except: return badInputResponse
        elif (cmds[1] == 'puts' or cmds[1] == 'calls') and len(cmds) == 6:
            try: return allUsers[userI].buyOptions(cmds[1], cmds[2], cmds[5], float(cmds[4]), int(cmds[3]))
            except: return badError
        else: return badError
    elif cmds[0] == '--sell':
        if len(cmds) < 4: return badInputResponse
        userI = getUserIndex(author)
        if type(userI) is not int: return userI
        if cmds[1] == 'stock' and len(cmds) == 4:
            try: return allUsers[userI].sellStock(cmds[2], int(cmds[3]))
            except: return badInputResponse 
        elif (cmds[1] == 'puts' or cmds[1] == 'calls') and len(cmds) == 6:
            try: return allUsers[userI].sellOptions(cmds[1], cmds[2], cmds[5], float(cmds[4]), int(cmds[3]))
            except: return badError
        else: return badError
    elif cmds[0] == "--summary":
        if len(cmds) == 1: userI = getUserIndex(author)
        else: userI = getUserIndex(cmds[1])
        if type(userI) is not int: return userI
        return allUsers[userI].getSummary()
    elif cmds[0] == "--history":
        if len(cmds) == 1: userI = getUserIndex(author)
        else: userI = getUserIndex(cmds[1])
        if type(userI) is not int: return userI
        return allUsers[userI].getTradeHist()
    elif cmds[0] == "--leaderboard":
        return getLeaderboard()
    elif cmds[0] == "--suggest":
        if len(cmds) < 2: return badInputResponse
        return logSuggestion(author, cmds[1])
    elif cmds[0] == "--searchTrumpTweets" and len(cmds) > 1:
        return tt.searchTweet(" ".join(cmds[1:]))
    else:
        return listOfCommands

#DISCORD CODE--------------------------------------------------------------
client = discord.Client()

@client.event
async def on_ready():
    startService()
    print("Bot loaded successfully")

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    elif len(str(message.content)) >= 2 and str(message.content)[:2] == "--":
        await message.channel.send(handleDiscord(message.author, message.content))

client.run(TOKEN)