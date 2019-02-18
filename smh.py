#! python3

# This app is intended to scrape
# www.showmyhomework.co.uk and send a short
# SMS text summary using Twilio. Its most
# useful features are (hopefully) that it
# calculates a quick estimate of total effort
# (hours) required to complete all homework,
# and children/parents don't need to install
# a separate app on their phone, they just
# need to be able to receive SMS messages.

# Author: peter@southwestlondon.tv


import os
import subprocess
import sys
import threading
import time
import bs4
import pyAesCrypt
import pyautogui
import pyshorteners
from selenium import webdriver

pyautogui.FAILSAFE = True
url = r"https://www.showmyhomework.co.uk"


class Secret():
    """
    A file obscured* by AES ecnryption, typically containing credentials
    (tokens, passwords, config/user data etc.) formatted as regular
    Python data structures such as lists, dictionaries, strings, sets.
    This class provides a more secure and arguably easier way of
    importing and editing config data in Python without having to
    convert a different (plain text) formats such as JSON, YAML or TOML.

    Although primarily intended for importing .py files, the encrypt()
    and decrypt() methods should work on any file that needs to be
    obscured* and the edit() method should open any file with the
    specified 'editor' application.

    (*) I say 'obscured' because the AES password is generated in
    a convenient but insecure way, and could easily
    be guessed or cracked by someone with machine level access.
    The pyAesCrypt module was chosen for encryption due to its
    simplicity but this could easily be replaced with other custom
    security methods.
    """

    def __init__(self, filename="smh-credentials.py"):
        self.filename = filename
        self.aesname = filename+".aes"
        return

    def __str__(self):
        return("Original File: "+self.filename+"\tEncrypted File: "+self.aesname)

    def device_id(self):
        """
        For Windows, returns a device specific ID.
        For other operating systems, returns the MAC address
        """
        if sys.platform == "win32":
            return(subprocess.check_output('wmic csproduct get uuid').decode().split('\n')[1].strip())
        else:
            from uuid import getnode
            return (str(getnode()))

    def encrypt(self):
        """
        Converts any file to .aes using pyAesCrypt
        """
        if os.path.isfile(self.filename):
            # Use machine specific ID as password for AES
            pyAesCrypt.encryptFile(
                self.filename, self.aesname, self.device_id(), 64*1024)
            os.remove(self.filename)
        else:
            print("Original file", self.filename, "not found.")
        return

    def decrypt(self):
        """
        Converts any .aes file to its original form using pyAesCrypt
        """
        if os.path.isfile(self.aesname):
            # Use machine specific ID as password for AES
            pyAesCrypt.decryptFile(
                self.aesname, self.filename, self.device_id(), 64*1024)
            os.remove(self.aesname)
        else:
            print("Encrypted file", self.aesname, "not found.")
        return

    def edit(self):
        """
        Decrypt and open file in the specified editor.
        User is prompted manually to encrypt() the file again
        afterwards - nice to have feature would be to ensure
        this happens automatically.
        """
        self.decrypt()
        if sys.platform == "win32":
            editor = "notepad.exe"
            p = subprocess.Popen([editor, self.filename])
            prompt = "\nPress ENTER to re-encrypt " + \
                self.filename+" or any other key to quit: "
            i = input(prompt)
            if i == "":
                self.encrypt()
                p.terminate()
        else:
            print(
                "Sorry, Windows Notepad is that only editor I know how to launch just now...")
        # TODO: Add default text editors for OSX and Linus
        return

    def load(self):
        """
        Decrypt, import, then delete plain text (.py) version
        of encrypted Secret file.
        Method will fail if the Secret file is not importable
        into Python e.g. in JSON, YAML, TOML or INI format.

        In the main script, copy or import this Class and its
        methods, then initiate with:
        s = Secret().load()

        You can then access attributes of all Python objects in
        your Secret file as usual e.g. if the file contains:
        Twitter = {'id': '@swltv', 'password': '12345'}

        >>> s.Twitter["id"]
        will give: '@swltv'
        """
        import importlib
        self.decrypt()
        try:
            file = importlib.import_module(self.filename.split(".")[0])
        except:
            print("Unable to import", self.filename)
        self.encrypt()
        return (file)


class Homework:
    """A homework task on showmyhomework.co.uk"""
    count = 0
    task_list = []

    def __init__(self, url):
        self.url = url
        self.index = Homework.count
        Homework.count += 1
        Homework.task_list.append(self)
        self.tiny_url = ""
        while self.tiny_url == "":
            self.tiny_url = pyshorteners.Shortener('Tinyurl').short(self.url)[7:]
        print("http://"+self.tiny_url)

    def __str__(self):
        try:
            self.summary = "#"+str(self.index)+": " + \
                self.title+"\n"+self.tiny_url
            self.summary += "\n"+self.description+"\n"+self.info+"\n"
            self.summary += str(self.duration) + \
                " minutes : Issued "+self.issued+": Due "+self.due
            print(self.summary)
        except:
            print("***Check data/attributes***")
        return("")


def launch_showmyhomework():
    """Launch ShowMyHomework and login"""
    print("Contacting ShowMyHomework.co.uk...")
    global browser
    browser = webdriver.Chrome()
    index_url = r"https://www.showmyhomework.co.uk/todos/issued"
    browser.get(index_url)
    time.sleep(1)
    # pyautogui.hotkey("tab")
    # pyautogui.hotkey("tab")
    pyautogui.hotkey("tab")
    pyautogui.hotkey("tab")
    pyautogui.typewrite(secret.ShowMyHomework['school'])
    time.sleep(1)
    pyautogui.hotkey("enter")
    pyautogui.hotkey("tab")
    pyautogui.typewrite(secret.ShowMyHomework['id'])
    pyautogui.hotkey("tab")
    pyautogui.typewrite(secret.ShowMyHomework['password'])
    pyautogui.hotkey("tab")
    pyautogui.hotkey("tab")
    pyautogui.hotkey("tab")
    pyautogui.hotkey("enter")
    print("Login complete.")
    time.sleep(2)
    return


def get_task_index():
    """Create an index of unfinished homework tasks"""
    page = browser.page_source
    soup = bs4.BeautifulSoup(page, "html.parser")
    links = soup.select('h4 a')
    links = [x["href"] for x in links]
    # Show My Homework uses this format for links:
    # /homeworks/25797227 or /quizzes/26332980
    print("\nYou have", len(links), "homeworks outstanding:\n")
    urls = [url+str(link) for link in links]
    print("\n".join(urls))
    return(urls)


def initialise_tasks(urls):
    """Create list of task objects and fetch TinyURLs"""
    threads = []
    print("\nPreparing data and creating TinyURLs...\n")
    for url in urls:
        thread = threading.Thread(target=Homework, args=[url])
        thread.start()
        threads.append(thread)
    for thread in threads:
        thread.join()
    return


def get_task_info(homework):
    global browser
    try:
        browser.get(homework.url)
    except Exception as E:
        print("\n*** STAY CALM AND RUN THE SMH HELPER PROGRAMME AGAIN ***\n")
        print("Occasionally ShowMyHomework.co.uk isn't ready to talk to us...\n")
        browser.close()
    homework.title = ""
    while homework.title == "":
        # Wait for AJAX to populate the web page, including a proper title
        page = browser.page_source
        soup  = bs4.BeautifulSoup(page, "html.parser")
        try:
            homework.title = soup.find("h1", class_="main-header-title truncate-text").text.strip()
        except:
            pass
    homework.issued = soup.find("div", class_="homework-date issued-on").text.strip()
    homework.due = soup.find("div", class_="homework-date due-on").text.strip()
    homework.description = soup.find("p", class_="homework-description").text.strip()
    homework.info = soup.find("div", class_="well homework-information").text.strip()
    homework.subject = soup.find("div", class_="ember-view teacher-text __assignment-teacher-text__1067e").text.split("- ")[-1].strip()


def calculate_duration(homework):
    """Calculate or estimate duration (mins) for each task"""
    if "minutes" in homework.info:
        homework.duration = int(
            homework.info.split(" minute")[0].split(" ")[-1])
    elif "hour" in homework.info:
        homework.duration = int(homework.info.split(" hour")[
                                0].split(" ")[-1])*60
    else:
        # Some teachers use SMH as reminders e.g. school play rehearsals
        homework.duration = 0
    if "quizzes" in homework.url:
        # Quizzes don't have a duration by default
        # so using an "odd" number like 21 highlights the fact
        # the estimate hasn't actually been set by a teacher
        homework.title = homework.title.replace(
            'class="title"', '').split(",")[0].rstrip()
        homework.duration = 21


def loop_through_tasks():
    """Scrape details of each homework task/page"""
    print("\nGathering Homework details... Please be patient :)\n")
    for count, homework in enumerate(Homework.task_list):
        get_task_info(homework)
        calculate_duration(homework)
        print(f"\n*** {homework.subject.upper()}: {homework.title.upper()} ***")
        print(homework.description)
    print()
    return


def create_summary():
    """Calculate total duration of all homework tasks"""
    summary = ""
    total = 0
    for task in Homework.task_list:
        summary += "\n"+task.subject.upper() +": "
        summary += task.title + "\n"
        summary += f"{task.duration} mins "
        summary += "due"+task.due.split("Due on")[-1]
        summary += "\n"+task.tiny_url
        total += task.duration
    summary = "*SHOW MY HOMEWORK*\n"+str(len(Homework.task_list))+" tasks, " + \
        str(round(total/60, 1))+" hours effort"+summary
    print(summary)
    return(summary)


def send_SMS(msg):
    """Send an SMS text message to selected recipients"""
    from twilio.rest import Client
    account_sid = secret.Twilio['account sid']
    auth_token = secret.Twilio['auth token']
    twilio_number = secret.Twilio['number']
    print("\nUsing Twilio number: +"+str(twilio_number))
    client = Client(account_sid, auth_token)
    contacts = [x for x in enumerate(secret.contacts.items())]
    print("\nPlease select 0-9 recipients for SMS text message...")
    print("For example enter '02' for the 0th and 2nd contact in the list.\n")
    print([str(y[0])+": "+y[1][0] for y in contacts])
    recipients = input("> ").lower()
    print("\nSending SMS to:")
    print([contacts[int(x)][1][0] for x in recipients])
    i = input(
        "\n(S)end automatically, (C)onfirm each message, or ENTER for Test Mode): ").lower()
    # Format message
    if msg.startswith("#"):
        msg = msg.replace("\n", " : ")
    # Twilio maximum message size = 1600 characters
    msg = msg[:1600]
    for recipient in recipients:
        name, number = contacts[int(recipient)][1]
        # Hash out the following line while testing, to avoid embarassment!
        confirmed = "No"
        try:
            print("\nTo", name, ":")
            print(msg)
        except:
            print("Problem with data - maybe need to delete a header row?")
        if i == "c":
            confirmed = input(
                "\nEnter (Y) to proceed or any other key to skip: ").lower()
        if i == "s" or confirmed == "y":
            try:
                client.messages.create(
                    from_=twilio_number, to=number, body=str(msg))
                print("\nMessage sent to", name)
            except:
                print("\nSMS message failed - probably over 1600 character limit.")
            time.sleep(1)
    return


def main_menu():
    """Top level menu"""
    global secret
    secret = Secret().load()
    print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
    print("Welcome to the ShowMyHomework (SMH) helper by peter@southwestlondon.tv")
    print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n")
    print("You'll need a valid account with showmyhomework.co.uk and also")
    print("a (free) Twilio.com account. If it's your first time using this")
    print(
        "please select [E]dit from the menu below and add those details now.")
    i = input("""\nPress ENTER to send a quick homework summary to your phone contacts
    'T' to also open each task as a separate Tab in your Browser
    'E' to Edit your login details and contacts\n\n> """).lower()
    if i == "e":
        Secret().edit()
        return("No summary created; User data edited.")
    print()
    return(i)


def open_tabs(homework):
    """If selected, open all homework tasks in separate browser tabs"""
    javascript = f'window.open("{homework.url}","_blank");'
    browser.execute_script(javascript)

if __name__ == '__main__':
    menu_choice = "."
    while menu_choice not in ("t", "e", ""):
        menu_choice = main_menu()
    launch_showmyhomework()
    urls = get_task_index()
    initialise_tasks(urls)
    loop_through_tasks()
    message = create_summary()
    if menu_choice == "t":
        for homework in Homework.task_list[:-1]:
            # Last homework should already be open in the active tab
            thread = threading.Thread(target=open_tabs, args=[homework])
            thread.start()
    else:
        browser.close()
    send_SMS(message)
