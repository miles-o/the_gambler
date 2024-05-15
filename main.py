import discord
import pandas as pd
import random
import asyncio
import ast


intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

balance = 0



class bet:
    def __init__(self, name, id, open, bets, options, pooled):
        self.name = name
        self.id = id
        self.options = options
        self.open = open
        self.bets = bets
        self.pooled = pooled


    def add_bets(self, msg, author):
        #check if user has account
        df = pd.read_csv("balances.csv")
        if author not in df['name'].values:
            return "No account open. Use $open account to open an account with a starting balance of $500"  
        author_index = df[df['name'] == author].index[0]
      
    
        try:
            #get variables from list
            amt = msg[1]
            #.lower so as to not worry about case
            option = msg[2].lower()
        except IndexError:
            return "Not all fields entered, place bet with bet amount and bet option e.g. $bet 50 heads"
        try:
            amt = int(amt)
        except:
            return "Bet amount not a number, place bet with bet amount and bet option e.g. $bet 50 heads"
        if amt < 0:
            return "Bet amount cannot be negative"

        if option not in self.options:
            space = " or "
            #have to do this weird thing in the f sting to print options nicely, taken from https://stackoverflow.com/questions/59956496/f-strings-formatter-including-for-loop-or-if-conditions
            return f'{option} is not an option in this bet, to place a bet please select from {space.join(f"{i}" for i in self.options)}.'
        #declare variable i to keep in correct scope
        i = 1
        #if user has already placed a bet
        if author in self.bets["better"]:
            #get index of user in the bets dictionary
            i = self.bets["better"].index(author)
            #check whether they are betting for the same option they did previously
            if option in self.bets["option"][i]:
                #take old amount and add new amount
                current_amt = self.bets["amt"][i]
                if df.loc[author_index, 'balance'] < current_amt + amt:
                    return f'Not enough in account. Bet a lower amount or take a loan. You have bet {current_amt} on {self.bets["option"][i]} so far.'
                self.bets["amt"][i] = current_amt + amt
            else:
                #if they tried to bet against themself cancel the bet
                return f'Cannot bet against youself, you currently have ${self.bets["amt"][i]} on {self.bets["option"][i]}. If you would like to increase your bet, place another bet for your current option to add money.'
        else:
            #if user hasnt placed a bet put all info into bets dictionary
            if df.loc[author_index, 'balance'] < amt:
                return "Not enough in account. Bet a lower amount, take a loan or declare bankruptcy."
            self.bets["better"].append(author)
            self.bets["amt"].append(amt)
            self.bets["option"].append(option)
            #grab index of new better
            i = self.bets["better"].index(author)
            #return confirmation string to post in chat
        return f'Bet placed! Current bet: ${self.bets["amt"][i]} on {self.bets["option"][i]}. Good luck!'
    
    
    
    def update_balances(self, winnings):
        df = pd.read_csv("balances.csv")

        i = 0
        num_of_betters = len(winnings["name"])
        
        #loop through all users
        while i < num_of_betters:
            #find user in balances.csv
            user_index = df[df['name'] == winnings["name"][i]].index[0]
            #take bet amount
            amount = winnings["balance"][i]
            #add amount
            df.loc[user_index, 'balance'] = df.loc[user_index, 'balance'] + amount
            i += 1
        #save to csv
        df.to_csv('balances.csv', mode='w', index=False, header=True)

        



    def pooled_bet_result(self, result):
        data = {}
        df = pd.DataFrame(data)
        i = 0
        num_of_winners = 0
        pooled_amount = 0
        #empty dictionary
        winnings = {
            "name": [],
            "balance": []
        }
        num_of_bets = len(self.bets["better"])
        #loop through betters
        while i < num_of_bets: 
            #add betters money to pooled amount
            pooled_amount = pooled_amount + self.bets["amt"][i]
            #if they won
            if self.bets["option"][i] == result:
                #add one to the amount of winners
                num_of_winners += 1
            i += 1
        #amount is the pooled amount split between winners
        i = 0
        try:
            amt = int(pooled_amount/num_of_winners)
        except ZeroDivisionError:
            amt = 0
        while i < num_of_bets:
            #add to winnings
            winnings["name"] += [self.bets["better"][i]]
            if self.bets["option"][i] == result:
                #if they won add pooled amount
                winnings["balance"].append(amt)
            #take away bet amount for everyone, if a winner amt should be more than bet amount
            winnings["balance"][i] = int(winnings["balance"][i]) - int(self.bets["amt"][i])
            i += 1
            #write to history
            data = {
                'id': [self.id],
                'name': [self.name],
                'type': [type(self).__name__],
                'options': [self.options],
                'winnings': [winnings]
            }
            # Make data frame of above dictionary
            df = pd.DataFrame(data)
            # append data frame to CSV file
        df.to_csv('bet_history.csv', mode='a', index=False, header=False)
        del df
        #delete bet from pending bets file
        df = pd.read_csv('pending_bets.csv')
        id_index = df[df['id'] == self.id].index[0]
        df = df.drop(df.index[id_index])
        df.to_csv('pending_bets.csv', mode='w', index=False, header=True)
        return winnings, result

    def non_pooled_bet_result(self, result):
        df = pd.read_csv("bet_history.csv")
        #simple random number for heads or tails
        i = 0
        winnings = {
            "name": [],
            "balance": []
        }
        num_of_bets = len(self.bets["better"])
        while i < num_of_bets:
            winnings["name"] += [self.bets["better"][i]]
            if self.bets["option"][i] == result:
                winnings["balance"] += [self.bets["amt"][i]]
            else:
                winnings["balance"] += [-abs(self.bets["amt"][i])]
            i += 1
            #write to history
            data = {
                'id': [self.id],
                'name': [self.name],
                'type': [type(self).__name__],
                'options': [self.options],
                'winnings': [winnings]
            }
            # Make data frame of above dictionary
            df = pd.DataFrame(data)
            # append data frame to CSV file
        df.to_csv('bet_history.csv', mode='a', index=False, header=False)
        del df
        #delete bet from unresulted bets file
        df = pd.read_csv('pending_bets.csv')
        id_index = df[df['id'] == self.id].index[0]
        df = df.drop(df.index[id_index])
        df.to_csv('pending_bets.csv', mode='w', index=False, header=True)
        return winnings, result


    def save_bet(self):
        df = pd.read_csv("bet_history.csv")
        data = {
            'name':[self.name],
            'id':[self.id],
            'open':[self.open],
            'bets':[self.bets],
            'options':[self.options],
            'pooled':[self.pooled]
        }
        df = pd.DataFrame(data)
        df.to_csv('pending_bets.csv', mode='a', index=False, header=False)
    
    def open_bet():
        #open bet from document and make active object
        print("not yet finished")



class coin_flip(bet):
    def __init__(self, name, id, open, bets, options, pooled):
        super().__init__(name, id, open, bets, options, pooled)
    
    def create_info(msg):
        df = pd.read_csv("bet_history.csv")
        #create bet id
        id = random.randint(0000, 9999)
        pooled = False
        #make sure no duplicate ids
        while id in df['id'].values:
            id = random.randint(0000, 9999)

        name = "coin flip"
        #find name and type
        i = 0
        length = len(msg)
        #loop through and look for "name:"
        while i < length:
            #check if theyve entered it twice
            if msg[i] == "name:" and name == "":
                name = msg[i + 1]
            elif msg[i] == "name:" and name != "":
                return f'Cannot include more than one name'
            i += 1
        i = 0
        #loop through and look for "options:"
        while i < length:
            #if they put it in tell em no
            if msg[i] == "options:":
                return "Coin flip does not take options, just write $create bet name: (name) type: coin flip"
            i += 1
        i = 0
        while i < length:
            #check if theyve entered it twice
            if msg[i] == "pooled:" and msg[i + 1].lower() == "true":
                pooled = True
            i += 1
        #insert variables into object and make empty dictionary for bets, options are already filled in in the coin flip
        proposed_bet = coin_flip(name, id, True, {
            "better": [],
            "amt": [],
            "option": []
        }, ["heads", "tails"], pooled)
        return proposed_bet

    def bet_result(self):
        df = pd.read_csv("bet_history.csv")
        #simple random number for heads or tails
        i = 0
        winnings = {
            "name": [],
            "balance": []
        }
        result = random.randint(0, 1)
        if result == 0:
            winner = "tails"
        else:
            winner = "heads"
        num_of_bets = len(self.bets["better"])
        while i < num_of_bets:
            winnings["name"] += [self.bets["better"][i]]
            if self.bets["option"][i] == winner:
                winnings["balance"] += [self.bets["amt"][i]]
            else:
                winnings["balance"] += [-abs(self.bets["amt"][i])]
            i += 1
            #write to history
            data = {
                'id': [self.id],
                'name': [self.name],
                'type': [type(self).__name__],
                'options': [self.options],
                'winnings': [winnings]
            }
            # Make data frame of above dictionary
            df = pd.DataFrame(data)
            # append data frame to CSV file
        df.to_csv('bet_history.csv', mode='a', index=False, header=False)
        return winnings, winner
                


class standard_bet(bet):
    def __init__(self, name, id, open, bets, options, pooled):
        super().__init__(name, id, open, bets, options, pooled)

    def create_info(msg):
        df = pd.read_csv("bet_history.csv")
        #create bet id
        id = random.randint(0000, 9999)
        #make sure no duplicate ids
        while id in df['id'].values:
            id = random.randint(0000, 9999)
        options = ["win", "lose"]
        name = "standard bet"
        options_index = 0
        pooled = True
        #find name and type
        i = 0
        length = len(msg)
        #loop through and look for "name:"
        while i < length:
            #check if theyve entered it twice
            if msg[i] == "name:":
                name = msg[i + 1]
            i += 1
        i = 0
        #loop through and look for "options:"
        while i < length:
            if msg[i] == "options:" and options_index == 0:
                options_index = i + 1
            elif msg[i] == "options:" and options_index != 0:
                return f'cannot include more than one "options:" field'
            i += 1
        i = 0
        while i < length:
            #check if theyve entered it twice
            if msg[i] == "pooled:" and msg[i + 1].lower() == "false":
                pooled = False
            i += 1
        if options_index != 0:
            options = []
            while options_index < length:
                options.append(msg[options_index])
                options_index += 1
            if len(options) < 2:
                return "Include at least 2 options"

        #insert variables into object and make empty dictionary for bets, options are already filled in in the coin flip
        proposed_bet = standard_bet(name, id, True, {
            "better": [],
            "amt": [],
            "option": []
        }, options, pooled)
        return proposed_bet
    
class overwatch(bet):
    def __init__(self, name, id, open, bets, options, pooled):
        super().__init__(name, id, open, bets, options, pooled)
    
    def create_info(msg):
        df = pd.read_csv("bet_history.csv")
        #create bet id
        id = random.randint(0000, 9999)
        pooled = True
        #make sure no duplicate ids
        while id in df['id'].values:
            id = random.randint(0000, 9999)
        options = ["win", "lose"]
        name = "overwatch"
        options_index = 0
        #find name and type
        i = 0
        length = len(msg)
        #loop through and look for "name:"
        while i < length:
            #check if theyve entered it twice
            if msg[i] == "name:" and name == "":
                name = msg[i + 1]
            elif msg[i] == "name:" and name != "":
                return f'Cannot include more than one name'
            i += 1
        i = 0
        #loop through and look for "options:"
        while i < length:
            if msg[i] == "options:" and options_index == 0:
                options_index = i + 1
            elif msg[i] == "options:" and options_index != 0:
                return f'cannot include more than one "options:" field'
            i += 1
        i = 0
        while i < length:
            #check if theyve entered it twice
            if msg[i] == "pooled:" and msg[i + 1].lower() == "false":
                pooled = False
            i += 1
        if options_index != 0:
            options = []
            while options_index < length:
                options.append(msg[options_index])
                options_index += 1
            if len(options) < 2:
                return "Include at least 2 options"

        #insert variables into object and make empty dictionary for bets, options are already filled in in the coin flip
        proposed_bet = overwatch(name, id, True, {
            "better": [],
            "amt": [],
            "option": []
        }, options, pooled)
        return proposed_bet
    




@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))
    
@client.event
async def on_message(message):
    if message.author == client.user:
        return
    
    #get author name to make everything else easier
    author = message.author.name

    #dont really need these as functions but its a pain in the ass to put them back, maybe later 
    def balance_response():
        #open the balances
        df = pd.read_csv("balances.csv")       
        #find the index that users name is in
        author_index = df[df['name'] == author].index[0]
        #get all info from that row
        balance = df.loc[author_index, 'balance']
        #debt is stored as all money user has taken out, not amount owed
        #but amount owed is displayed to user when they request their balance
        debt = int(df.loc[author_index, 'debt'])
        #return message
        return f'You have ${balance} and owe ${debt}'
    def open_account():
        #open balances
        df = pd.read_csv("balances.csv")
        #if authour already exists in name column
        if author in df['name'].values:
            #reply and cancel
            return "You already have an account open! Get out there and gamble some money!"
        else:
            #put users name in name section
            #add starting balance, starting balance is same for all players, can be changed in code right now
            #planning to add something so that everything can be reset and certain rules changed
            # a backup will be kept in case someone is evil >:)
            data = {
                'name': [author],
                'balance': [500],
                'debt': [0]
            }
            # Make data frame of above dictionary
            df = pd.DataFrame(data)
            # append data frame to CSV file
            df.to_csv('balances.csv', mode='a', index=False, header=False)
            #return message
            return f'Account opened! Starting balance is $500. Time to gamble.'
    def leaderboard():
        #open balances
        df = pd.read_csv("balances.csv")
        #sort by balance
        df = df.sort_values(by=['balance'], ascending=False)
        #find how many people there are
        values = df.shape[0] 
        #some blank variable to make it work
        i = 0
        leaderboard = ""
        #loop through all values
        while i < values:
            #find name and balance of player
            name = df.iloc[i, 0]
            balance = df.iloc[i, 1] - df.iloc[i, 2]
            #append to leaderboard with number next to name
            leaderboard = f'{leaderboard}#{i+1} {name}: ${balance}\n'
            i += 1
        #return leaderboard after finished
        return leaderboard 
          
    def take_loan(msg):
        #open balances
        df = pd.read_csv("balances.csv")
        #wheres wally that shit
        author_index = df[df['name'] == author].index[0]
        #split that shit
        amt = msg.split(" ")
        #take second word and make int should be a number 
        try:
            amt = int(amt[1])
        #if the user hasnt put in a number will return an error
        except ValueError:
            return "Loan amount not a number, please input a number to take out loan e.g. $loan 50"

        if amt < 0:
            return "Loan amount cannot be negative"


        loan_amt = df.loc[author_index, 'debt']
        if loan_amt > 5000:
            return "Can only have $5000 out at a time"
            
        #modify data
        df.loc[author_index, 'balance'] = df.loc[author_index, 'balance'] + amt
        df.loc[author_index, 'debt'] = df.loc[author_index, 'debt'] + int(1.1 * amt)
        #write data to csv
        df.to_csv('balances.csv', mode='w', index=False, header=True)
        #get balance
        balance = balance_response()
        return f"Loan approved. {balance}. Good luck!"
    
    def pay_loan(msg):
        df = pd.read_csv("balances.csv")

        author_index = df[df['name'] == author].index[0]
        #split that shit
        amt = msg.split(" ")
        #take second word and make int should be a number 
        try:
            amt = int(amt[2])
        #if the user hasnt put in a number will return an error
        except ValueError:
            return "Loan amount not a number, please input a number to take out loan e.g. $loan 50"
        if amt < 0:
            return "Loan amount cannot be negative"
        
        try:
            df.loc[author_index, 'balance'] = df.loc[author_index, 'balance'] - int(amt)
            if df.loc[author_index, 'balance'] < 0:
                return "Not enough in account. Try again"
            df.loc[author_index, 'debt'] = df.loc[author_index, 'debt'] - int(amt)
            df.to_csv('balances.csv', mode='w', index=False, header=True)

        except:
            return "error"
        balance = balance_response()
        return f'Paid. {balance}'

    
    def get_type(msg):
            types = ["standard", "coin flip", "overwatch"]
            bet_type = "standard"
            error = False

            #if type exists
            #loop through look for "type:"
            i = 0
            while i < len(msg):
                if msg[i].startswith("type:"):
                    #get rid of 'type:' text
                    type_index = i + 1
                    first_word = msg[type_index]
                    if first_word not in types: 
                        second_word = msg[type_index+1]
                        words = [first_word, second_word]
                        bet_type = ' '.join(words)
                    else:
                        bet_type = first_word
                    
                    #check if type exists, if not send error
                    if bet_type not in types:
                        error = True
                        return error, bet_type, f'error: bet type does not exist, please select from {types}'
                    else:
                        return error, bet_type, ""
                else:
                    i += 1
            return error, bet_type, ""
    
    def process_bankruptcy():
        df = pd.read_csv("balances.csv")
        #wheres wally that shit
        author_index = df[df['name'] == author].index[0]
        df.loc[author_index, 'balance'] = 50
        df.loc[author_index, 'debt'] = 0
        df.to_csv('balances.csv', mode='w', index=False, header=True)

    def bet_result(msg):
        df = pd.read_csv("pending_bets.csv")

        if len(msg) < 3:
            return "no result included"
        result = msg[1].lower()
        id = int(msg[2].lower())

        id_index = df[df['id'] == id].index[0]
        #name, id, open, bets, options, pooled
        name = df.loc[id_index, 'name']
        open = df.loc[id_index, 'open']
        bets = ast.literal_eval(df.loc[id_index, 'bets'])
        options = ast.literal_eval(df.loc[id_index, 'options'])
        pooled = df.loc[id_index, 'pooled']

        resulting_bet = bet(name, id, open, bets, options, pooled)
        if result not in resulting_bet.options:
            space = " or "
            return f'{result} is not an option in this bet, to close the bet please select from {space.join(f"{i}" for i in resulting_bet.options)}.'
            del resulting_bet
        else:
            if resulting_bet.pooled == True:
                winnings, winner = resulting_bet.pooled_bet_result(result)
            elif resulting_bet.pooled == False:
                winnings, winner = resulting_bet.non_pooled_bet_result(result)
            resulting_bet.update_balances(winnings)
            new_leaderboard = leaderboard()
            return f'Bet closed successfully. Winner: {winner}!\nUpdated leaderboard:\n{new_leaderboard}'
            del resulting_bet
    
    def get_pending_bets():
        df = pd.read_csv("pending_bets.csv")
        msg = ""
        num_bets = df.shape[0]
        i = 0
        while i < num_bets:
            name = df.loc[i, 'name']
            id = df.loc[i, 'id']
            open = df.loc[i, 'open']
            bets = ast.literal_eval(df.loc[i, 'bets'])
            options = ast.literal_eval(df.loc[i, 'options'])
            pooled = df.loc[i, 'pooled']
            space = " "
            bet_str = "\n"
            l = 0
            bets_amt = len(bets['better'])
            while l < bets_amt:
                better = bets['better'][l]
                bet = bets['amt'][l]
                option = bets['option'][l]
                bet_str = bet_str + f'- Name: {better} Bet: {bet} Option: {option}\n'
                l += 1
            msg = msg + f'Bet:\nName: {name} {id}\nOptions: \n{space.join(f"{i}" for i in options)}\nBets: {bet_str}Pooled: {pooled}\n\n'
            i += 1
        if msg == "":
            return "No bets currently pending"
        return msg

            
        
    #open account
    if message.content.startswith("$open account"):
        msg = open_account()
        await message.channel.send(msg)
        
    #check balance
    if message.content.startswith("$balance"):
        msg = balance_response()
        await message.channel.send(msg)
    #show leaderboard
    if message.content.startswith("$leaderboard"):
        msg = leaderboard()
        await message.channel.send(msg)
    #take loan
    if message.content.startswith("$loan"):
        #get message
        msg_content = message.content
        msg = take_loan(msg_content)
        await message.channel.send(msg)
    if message.content.startswith("$pay loan"):
        msg = message.content
        msg = pay_loan(msg)
        await message.channel.send(msg)

    if message.content.startswith("$declare bankruptcy"):
        await message.channel.send("Warning\nThis will reset your account to $50 but remove all debt\n\nConfirm? Y/n")

        #code taken from https://stackoverflow.com/questions/71198171/is-there-a-way-to-make-a-confirmation-in-discord-py

        def check(m): # checking if it's the same user and channel
            return m.author == message.author and m.channel == message.channel
        try: # waiting for message
            response = await client.wait_for('message', check=check, timeout=30.0) # timeout - how long bot waits for message (in seconds)
        except asyncio.TimeoutError: # returning after timeout
            await message.channel.send("Timeout. Declaration cancelled.")
            return
        # if response is different than yes / y - return
        if response.content.lower() not in ("yes", "y"): # lower() makes everything lowercase to also catch: YeS, YES etc.
            await message.channel.send("Declaration cancelled.")
            return
        process_bankruptcy()
        balance = balance_response()
        await message.channel.send(f'You have declared backruptcy. {balance}')

    if message.content.startswith("$gambling hotline"):
        await message.channel.send("If you or someone you know is impacted by gambling, help is available.\n\nTo access support now, call the Gambling Helpline on 1800 858 858 or visit the Gambling Help Online website gamblinghelponline.org.au for live chat support.")


    #create a bet
    if message.content.startswith("$create bet"):
        global current_bet
        #if a bet is currently open, dont let user create bet
        try:
            if current_bet.open == True:
                await message.channel.send("Another bet is currently open or awaiting a result. Only one bet at a time (for now)")
                return
        except NameError:
            msg = message.content
            msg = msg.split(" ")
            error, bet_type, error_msg = get_type(msg)
            if error == True:
                await message.channel.send(error_msg)
                return
            else:
                if bet_type == "standard":
                    proposed_bet = standard_bet.create_info(msg)
                    if isinstance(proposed_bet, str):
                        await message.channel.send(proposed_bet)
                        return
                    space = " "
                    await message.channel.send(f'Confirm info is correct: \nName: {proposed_bet.name} {proposed_bet.id}\nType: standard\nPooled: {proposed_bet.pooled}\nOptions:\n{space.join(f"{i}" for i in proposed_bet.options)}\nY/n')

                    #code taken from https://stackoverflow.com/questions/71198171/is-there-a-way-to-make-a-confirmation-in-discord-py

                    def check(m): # checking if it's the same user and channel
                        return m.author == message.author and m.channel == message.channel
                    try: # waiting for message
                        response = await client.wait_for('message', check=check, timeout=30.0) # timeout - how long bot waits for message (in seconds)
                    except asyncio.TimeoutError: # returning after timeout
                        await message.channel.send("Timeout. Bet cancelled.")
                        return
                    # if response is different than yes / y - return
                    if response.content.lower() not in ("yes", "y"): # lower() makes everything lowercase to also catch: YeS, YES etc.
                        await message.channel.send("Bet cancelled.")
                        return
                    current_bet = proposed_bet
                    await message.channel.send("Bet confirmed.")

                #should put these in class
                    

                elif bet_type == "coin flip":
                    proposed_bet = coin_flip.create_info(msg)
                    if isinstance(proposed_bet, str):
                        await message.channel.send(proposed_bet)
                        return
                    newline = "\n"
                    await message.channel.send(f'Confirm info is correct: \nName: {proposed_bet.name} {proposed_bet.id}\nType: coin flip\nOptions:\n{newline.join(f"{i}" for i in proposed_bet.options)}\nConfirm? Y/n')

                    #code taken from https://stackoverflow.com/questions/71198171/is-there-a-way-to-make-a-confirmation-in-discord-py

                    def check(m): # checking if it's the same user and channel
                        return m.author == message.author and m.channel == message.channel
                    try: # waiting for message
                        response = await client.wait_for('message', check=check, timeout=30.0) # timeout - how long bot waits for message (in seconds)
                    except asyncio.TimeoutError: # returning after timeout
                        await message.channel.send("Timeout. Bet cancelled.")
                        return
                    # if response is different than yes / y - return
                    if response.content.lower() not in ("yes", "y"): # lower() makes everything lowercase to also catch: YeS, YES etc.
                        await message.channel.send("Bet cancelled.")
                        return
                    current_bet = proposed_bet            
                    await message.channel.send("Bet confirmed.")

                elif bet_type == "overwatch":
                    proposed_bet = overwatch.create_info(msg)
                    if isinstance(proposed_bet, str):
                        await message.channel.send(proposed_bet)
                        return
                    newline = "\n"
                    await message.channel.send(f'Confirm info is correct: \nName: {proposed_bet.name} {proposed_bet.id}\nType: overwatch\nOptions:\n{newline.join(f"{i}" for i in proposed_bet.options)}\nY/n')

                    #code taken from https://stackoverflow.com/questions/71198171/is-there-a-way-to-make-a-confirmation-in-discord-py

                    def check(m): # checking if it's the same user and channel
                        return m.author == message.author and m.channel == message.channel
                    try: # waiting for message
                        response = await client.wait_for('message', check=check, timeout=30.0) # timeout - how long bot waits for message (in seconds)
                    except asyncio.TimeoutError: # returning after timeout
                        await message.channel.send("Timeout. Bet cancelled.")
                        return
                    # if response is different than yes / y - return
                    if response.content.lower() not in ("yes", "y"): # lower() makes everything lowercase to also catch: YeS, YES etc.
                        await message.channel.send("Bet cancelled.")
                        return
                    current_bet = proposed_bet
                    await message.channel.send("Bet confirmed.")

            

    if message.content.startswith("$close betting"):
        if current_bet.__class__ == coin_flip:
            winnings, winner = current_bet.bet_result()
            current_bet.update_balances(winnings)
            new_leaderboard = leaderboard()
            await message.channel.send(f'Coin flip done. Winner: {winner}!\nUpdated leaderboard:\n{new_leaderboard}')
            del current_bet
        else:
            current_bet.save_bet()
            await message.channel.send(f'Betting closed for {current_bet.name}. Awaiting result')
            del current_bet
            
    
    if message.content.startswith("$result"):
        msg = message.content
        msg = msg.split(" ")
        msg = bet_result(msg)
        await message.channel.send(msg)



    #bet on current bet
    if message.content.startswith("$bet"):
        msg = message.content
        msg = msg.split(" ")
        #check if a bet is running
        if current_bet.open == True:
            #add bets
            msg = current_bet.add_bets(msg, author)
            await message.channel.send(msg)
        else:
            await message.channel.send("No bets currently open, use $create bet to start a bet")

    #see info on current bet
    if message.content.startswith("$current bet"):
        bet_type = type(current_bet).__name__
        space = " "
        await message.channel.send(f'Current bet:\nName: {current_bet.name} {current_bet.id}\nType: {bet_type}\nOptions: \n{space.join(f"{i}" for i in current_bet.options)}\nPooled: {current_bet.pooled}')
    
    if message.content.startswith("$pending bets"):
        msg = get_pending_bets()
        await message.channel.send(msg)

    #help menu
    if message.content.startswith("$help"):
        await message.channel.send("$open account - Opens new account with starting balance of $500\n\n$balance - Check your current balance\n\n$leaderboard - Show leaderboard\n\n$create bet name: (name) type: (standard, coin flip, overwatch) pooled: (true, false) options: (option 1), (option 2), (option 3) etc.- Create a new bet\nWhen creating a bet you do not need to include name, type or options. You may include any of these fields, in any order. The default if you do not include a type the bet will be a standard bet. More info on standard options for bet types:\n\nStandard:\nName: standard bet\nOptions: Win, Lose\nPooled: true\n\nCoin flip\nName: coin flip\nOptions(cannot be changed): Heads, Tails\nPooled: False\n\nOverwatch:\nName: Overwatch\nOptions: win, lose\nPooled: true\n\n$current bet - View info on current bet\n\n$bet (amount) (option) - Place bet\n\n$close betting - Close betting\n\n$result (winning option) (bet id) - Choose winning option, make sure to include bet id, to view pending bets and find bet id use $pending bets\n\n$pending bets - view bets pending a result\n\n$loan (amount) - Take out a loan of up to $5000, 10% interest on loans\n\n$pay loan (amount) - Pay back your debt using account funds\n\n$declare bankruptcy - Reset account to $50 and remove all debt\n\n$gambling hotline - If you or someone you know is impacted by gambling, help is available.")

        
    

client.run("MTIzODUwNzAxNzE0MDgzMDI2MQ.GfZiJo.LzYb9JMsvYnoKUqPKZaDWUdoGyO5wOAro4QWIQ")