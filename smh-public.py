#! python3

# This app is intended to scrape
# www.showmyhomework.com and send a short
# SMS text summary using Twilio. It's most
# useful feature is (hopefully) that it
# calculates a quick estimate of total effort
# (hours) required to complete the homework.

# Author: peter@southwestlondon.tv

import time
import os
import webbrowser
import bs4
import pyautogui
pyautogui.FAILSAFE = True
from selenium import webdriver

# Base URL for individual homework pages on showmyhomework.com
url=r"https://www.showmyhomework.co.uk"

class Homework:
    """
    A single homework assignement on showmyhomework.com
    """
    count=0

    def __init__(self, id):
        # Show My Homework website ID uses format /homeworks/25797227
        # or /quizzes/26332980
        self.id=id
        self.index=Homework.count
        self.url=url+id
        Homework.count+=1
        
    def open(self):
        webbrowser.open(self.url)

    def parse(self,tags):
        result=str(self.soup.select(tags))
        result=result.replace("\n","")
        unwanted=["p","strong","ul","div","u","ol"]
        for u in unwanted:
            result=result.replace("<"+u+">","")
            result=result.replace("</"+u+">","")
        replacements={"<li>":"\n",
                      "\xa0":"\n",
                      "<h1":"",
                      "</h1>":"",
                      "[":"",
                      "]":"",
                       'class="main-header-title truncate-text">':"",
                       'p class="homework-description"':"",
                       "</li>":"",
                       'div class="well homework-information"':"",
                      'div class="homework-date issued-on"':"",
                      'div class="homework-date due-on"':"",
                      "!-- --":"",
                      "<":"",
                      ">":"",
                      "\t":"",
                      "br":"\n",
                      "Set on ":"",
                      "Due on ":"",
                      "Important information":"",
                      }
        for key in replacements:
            result=result.replace(key,replacements[key])
        result=result.strip(" ")
        result=result.strip("\n")
        return(result)

    def __str__(self):
        try:
            self.summary="#"+str(self.index)+": "+self.title+"\n"+self.url
            self.summary+="\n"+self.description+"\n"+self.info+"\n"
            self.summary+=str(self.duration)+" minutes : Issued "+self.issued+": Due "+self.due
            print(self.summary)
        except:
            print("***Check data/attributes***")
        return("")

def smh():
    i=input("Press ENTER for defaults, or T to open in Tabs: ")
    print("Contacting Show My Home Work...")
    global browser
    browser=webdriver.Chrome()
    index_url=r"https://www.showmyhomework.co.uk/todos/issued"
    browser.get(index_url)
    time.sleep(2)
    pyautogui.hotkey("tab")
    pyautogui.hotkey("tab")
    pyautogui.hotkey("tab")
    pyautogui.hotkey("tab")
    # Fields are currently hard-coded into this app
    # What is a better way of setting this up once
    # regardless of operating system?
    #
    # Replace this with first keyword in school name
    pyautogui.typewrite("my_school_keyword")
    time.sleep(2)
    pyautogui.hotkey("enter")
    pyautogui.hotkey("tab")
    # Replace this email with registered SMH email address
    pyautogui.typewrite("child@email_address.example")   
    pyautogui.hotkey("tab")
    # Replace this with SMH password
    pyautogui.typewrite("SMH_password")
    pyautogui.hotkey("tab")
    pyautogui.hotkey("tab")
    pyautogui.hotkey("tab")
    pyautogui.hotkey("enter")
    print("Login complete.")
    time.sleep(2)

    # CREATE INDEX OF OUTSTANDING HOMEWORK
    todo=[]
    # todo will be the master list of Homework objects
    page = browser.page_source
    soup = bs4.BeautifulSoup(page,"html.parser")
    links=soup.select('h4 a')
    links=[x["href"] for x in links]
    print("\nYou have",len(links),"homeworks outstanding:\n")
    for link in links:
        new_homework=Homework(link)
        todo+=[new_homework]
    urls="\n".join([url+str(link) for link in links])
    print(urls)               
    return(urls,todo,i)

def smh_pages(todo,i):
    print("\nGathering Homework details...\n")
    
    for homework in todo:
        browser.get(homework.url)
        time.sleep(1.5)        
        page = browser.page_source
        soup = bs4.BeautifulSoup(page,"html.parser")
        # SOUP - for debugging and extracting further data
        homework.soup=soup
        # TITLE
        homework.title=homework.parse("h1")
        # ISSUED
        homework.issued=homework.parse("div.homework-date.issued-on")
        # DUE
        homework.due=homework.parse("div.homework-date.due-on")
        # DESCRIPTION
        homework.description=homework.parse("p.homework-description")
        # INFO
        homework.info=homework.parse("div.well.homework-information")
        # DURATION
        if "minutes" in homework.info:
            homework.duration=int(homework.info.split(" minute")[0].split(" ")[-1])
        elif "hour" in homework.info:
            homework.duration=int(homework.info.split(" hour")[0].split(" ")[-1])*60
        else:
            # Some teachers use SMH as reminders e.g. school play rehearsals
            homework.duration=0
        if "quizzes" in homework.id:
            # Quizzes don't have a duration by default
            # so using an "odd" number like 21 highlights the fact
            # the estimate hasn't actually been set by a teacher
            homework.title=homework.title.replace('class="title"','').split(",")[0].rstrip()
            homework.duration=21
        print(homework)
        if i.lower()=="t":
            webbrowser.open(homework.url)   
    return()

def duration(todo):
    summary=""
    total=0
    for t in todo:
        summary+="\n"+str(t.duration)+" mins: "
        summary+=t.title
        summary+=": "+t.due+"\n"
        summary+=t.url[8:]
        total+=t.duration
    summary="SMH: "+str(len(todo))+" tasks "+str(round(total/60,1))+" hours effort"+summary
    print(summary)
    return(summary)

def _load_twilio_config():
    # This currently works on Windows 10 where the relevant
    # environment variables have been setup manually.
    # A typical user wouldn't know how to do this so if there's 
    # an off the shelf library for setting this up once, perhaps
    # as part of a single "Twilio signup" routine, that would be
    # a big enhancement.
    global account_sid, auth_token, twilio_number
    account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
    print(account_sid)
    auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
    print(auth_token)
    twilio_number = os.environ.get('TWILIO_NUMBER')
    print(twilio_number)

    if not all([account_sid, auth_token, twilio_number]):
        print(NOT_CONFIGURED_MESSAGE)
        quit()
    else:
        print("Twilio credentials verified.\n")
        global client
        from twilio.rest import Client
        client = Client(account_sid, auth_token)
        return (twilio_number, account_sid, auth_token, client)

def _confirm_tokens():
    twilio_number, account_sid, auth_token, client=_load_twilio_config()
    print("\n")
    print(account_sid, auth_token, sep='\n')
    print("Using Twilio number: +"+str(twilio_number),sep="")
    print("\n")
    return()

def SEND_SMS(msg):
    if msg.startswith("#"):
        msg=msg.replace("\n"," : ")
    _load_twilio_config()
   
    # Replace mobile phoen numbers here
    contacts={"Mum":"+447991000000",
              "Dad":"+447991000000",
              "Child":"+447991000000",}
    i=input("Send to (M)um, (D)ad and/or (C)hild? ").lower()
    recipients=[]
    # Hash out the following recipients as required
    if "m" in i:
        recipients+=["Mum"]
    if "d" in i:
        recipients+=["Dad"]
    if "c" in i:
        recipients+=["Child"]
    print("Sending SMS to:")
    print("\n".join(recipients))
    i=input("\n(S)end automatically, (C)onfirm each message, or ENTER for Test Mode):").lower()
    for recipient in recipients:        
        name=recipient
        number=contacts[recipient]
        # Hash out the following line while testing, to avoid embarassment!
        confirmed="No"
        try:
            print("\nTo",name,":")
            print(msg)
        except:
            print("Problem with data - maybe need to delete a header row?")
        if i=="c":
            confirmed=input("\nEnter (Y) to proceed or any other key to skip: ").lower()
        if i=="s" or confirmed=="y":
            client.messages.create(from_=twilio_number, to=number, body=str(msg))
            print("\nMessage sent to",name)
            time.sleep(1)   
    return

# Main Program

def main():
    urls,todo,i=smh()
    smh_pages(todo,i)
    summary=duration(todo)
    SEND_SMS(summary)

if __name__ == '__main__':
    summary=main()