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

import time
import os
import sys
import webbrowser
import subprocess
import bs4
import threading
import pyautogui
import pyAesCrypt
import pyshorteners

pyautogui.FAILSAFE = True
from selenium import webdriver

# Base URL for individual homework pages on showmyhomework.co.uk
url = r"https://www.showmyhomework.co.uk"


class Secret:
    """
    A file obscured* by AES ecnryption, typically containing credentials
    (tokens, passwords, config/user data etc.) formatted as regular
    Python data structures such as lists, dictionaries, strings, sets.
    This class provides a more secure and arguably easier way of
    importing and editing config data in Python without having to
    convert between different (plain text) formats such as JSON, YAML or TOML.

    In the main script, copy or import this Class and its methods,
    then initiate with:
    secret = Secret().load()

    You can then access attributes of all Python objects in
    your Secret file as usual with "dot" notation e.g. if the file contains:
    Twitter = {'id': '@swltv', 'password': '12345'}

    >>> secret.Twitter["id"]
    will give: '@swltv'
    
    Although primarily intended for importing .py files, the encrypt()
    and decrypt() methods should work on any file that needs to be
    obscured* and the edit() method should open any file with the 
    specified 'editor' application.

    (*) I say 'obscured' because the AES password is generated in
    a convenient but insecure way, not by the user, and could easily
    be guessed or cracked by someone with machine level access.
    The pyAesCrypt module was chosen for encryption due to its
    simplicity but this could easily be replaced with other custom
    security methods.
    """

    def __init__(self, filename="smh-credentials.py"):
        # TODO: allow for Secret files which aren't in same directory as this script
        # e.g. using sys.path.append
        self.filename = filename
        self.aesname = filename + ".aes"
        return

    def __str__(self):
        return "Original File: " + self.filename + "\tEncrypted File: " + self.aesname

    def device_id(self):
        """
        For Windows, returns a device specific ID.
        For other operating systems, returns the MAC address
        """
        if sys.platform == "win32":
            return (
                subprocess.check_output("wmic csproduct get uuid")
                .decode()
                .split("\n")[1]
                .strip()
            )
        else:
            from uuid import getnode

            return str(getnode())

    def encrypt(self):
        """
        Converts any file to .aes using pyAesCrypt
        """
        if os.path.isfile(self.filename):
            # Use machine specific ID as password for AES
            pyAesCrypt.encryptFile(
                self.filename, self.aesname, self.device_id(), 64 * 1024
            )
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
                self.aesname, self.filename, self.device_id(), 64 * 1024
            )
            os.remove(self.aesname)
        else:
            print("Encrypted file", self.aesname, "not found.")
        return

    def edit(self):
        """
        Decrypt and open file in the specified editor.
        User is prompted manually to encrypt() the file again
        afterwards - "nice to have" future feature would be
        to ensure this happens automatically.
        """
        self.decrypt()
        if sys.platform == "win32":
            editor = "notepad.exe"
            p = subprocess.Popen([editor, self.filename])
            prompt = (
                "\nPress ENTER to re-encrypt "
                + self.filename
                + " or any other key to quit: "
            )
            i = input(prompt)
            if i == "":
                self.encrypt()
                p.terminate()
        else:
            print(
                "Sorry, Windows Notepad is that only editor I know how to launch just now..."
            )
        # TODO: Add default text editors for OSX and Linux
        return

    def load(self):
        """
        Decrypt, import, then delete plain text (.py) version
        of encrypted Secret file.
        Method will fail if the Secret file is not importable
        into Python i.e. not a valid .py file.
        """
        import importlib

        self.decrypt()
        try:
            file = importlib.import_module(self.filename.split(".")[0])
        except:
            print("Unable to import", self.filename)
        self.encrypt()
        return file


class Homework:
    """A homework task on showmyhomework.co.uk"""

    count = 0

    def __init__(self, id):
        # Show My Homework website ID uses format:
        # /homeworks/25797227 or
        # /quizzes/26332980
        self.id = id
        self.index = Homework.count
        self.url = url + id
        self.tiny_url = pyshorteners.Shortener("Tinyurl").short(self.url)[7:]
        Homework.count += 1

    def open(self):
        webbrowser.open(self.url)

    def parse(self, tags):
        result = str(self.soup.select(tags))
        result = result.replace("\n", "")
        unwanted = ["p", "strong", "ul", "div", "u", "ol"]
        for u in unwanted:
            result = result.replace("<" + u + ">", "")
            result = result.replace("</" + u + ">", "")
        replacements = {
            "<li>": "\n",
            "\xa0": "\n",
            "<h1": "",
            "</h1>": "",
            "[": "",
            "]": "",
            'class="main-header-title truncate-text">': "",
            'p class="homework-description"': "",
            "</li>": "",
            'div class="well homework-information"': "",
            'div class="homework-date issued-on"': "",
            'div class="homework-date due-on"': "",
            "!-- --": "",
            "<": "",
            ">": "",
            "\t": "",
            "br": "\n",
            "Set on ": "",
            "Due on ": "",
            "Important information": "",
        }
        for key in replacements:
            result = result.replace(key, replacements[key])
        result = result.strip(" ")
        result = result.strip("\n")
        return result

    def __str__(self):
        try:
            self.summary = (
                "#" + str(self.index) + ": " + self.title + "\n" + self.tiny_url
            )
            self.summary += "\n" + self.description + "\n" + self.info + "\n"
            self.summary += (
                str(self.duration)
                + " minutes : Issued "
                + self.issued
                + ": Due "
                + self.due
            )
            print(self.summary)
        except:
            print("***Check data/attributes***")
        return ""


def launch_smh():
    """Launch ShowMyHomework and get index of outstanding tasks"""
    print("Contacting ShowMyHomework.co.uk and generating TinyURL links...")
    global browser
    browser = webdriver.Chrome()
    index_url = r"https://www.showmyhomework.co.uk/todos/issued"
    browser.get(index_url)
    time.sleep(1)
    pyautogui.hotkey("tab")
    pyautogui.hotkey("tab")
    pyautogui.hotkey("tab")
    pyautogui.hotkey("tab")
    pyautogui.typewrite(secret.ShowMyHomework["school"])
    time.sleep(1)
    pyautogui.hotkey("enter")
    pyautogui.hotkey("tab")
    pyautogui.typewrite(secret.ShowMyHomework["id"])
    pyautogui.hotkey("tab")
    pyautogui.typewrite(secret.ShowMyHomework["password"])
    pyautogui.hotkey("tab")
    pyautogui.hotkey("tab")
    pyautogui.hotkey("tab")
    pyautogui.hotkey("enter")
    print("Login complete.")
    time.sleep(2)
    return


def get_smh_tasks():
    """Create an index of unfinished homework tasks"""
    todo = []
    # 'todo' will hold a master list of Homework instances
    page = browser.page_source
    soup = bs4.BeautifulSoup(page, "html.parser")
    links = soup.select("h4 a")
    links = [x["href"] for x in links]
    print("\nYou have", len(links), "homeworks outstanding:\n")
    for link in links:
        new_homework = Homework(link)
        todo += [new_homework]
    urls = "\n".join([url + str(link) for link in links])
    print(urls)
    return (urls, todo)


def smh_pages(todo, i):
    """Scrape details of each homework task/page"""
    print("\nGathering Homework details...\n")
    # TODO: scrape as parallel processes to speed up the process
    for homework in todo:
        browser.get(homework.url)
        time.sleep(2)
        page = browser.page_source
        soup = bs4.BeautifulSoup(page, "html.parser")
        # SOUP - for debugging and extracting further data
        homework.soup = soup
        # TITLE
        homework.title = homework.parse("h1")
        # ISSUED
        homework.issued = homework.parse("div.homework-date.issued-on")
        # DUE
        homework.due = homework.parse("div.homework-date.due-on")
        # DESCRIPTION
        homework.description = homework.parse("p.homework-description")
        # INFO
        homework.info = homework.parse("div.well.homework-information")
        # DURATION
        if "minutes" in homework.info:
            homework.duration = int(homework.info.split(" minute")[0].split(" ")[-1])
        elif "hour" in homework.info:
            homework.duration = int(homework.info.split(" hour")[0].split(" ")[-1]) * 60
        else:
            # Some teachers use SMH as reminders e.g. school play rehearsals
            homework.duration = 0
        if "quizzes" in homework.id:
            # Quizzes don't have a duration by default
            # so using an "odd" number like 21 highlights the fact
            # the estimate hasn't actually been set by a teacher
            homework.title = (
                homework.title.replace('class="title"', "").split(",")[0].rstrip()
            )
            homework.duration = 21
        print(homework)
        if i.lower() == "t":
            webbrowser.open(homework.url)
    return


def duration(todo):
    """Calculate total duration of all homework tasks"""
    summary = ""
    total = 0
    for t in todo:
        summary += "\n" + str(t.duration) + " mins: "
        summary += t.title
        summary += ": " + t.due + "\n"
        summary += t.tiny_url
        total += t.duration
    summary = (
        "SMH: "
        + str(len(todo))
        + " tasks "
        + str(round(total / 60, 1))
        + " hours effort"
        + summary
    )
    print(summary)
    return summary


def send_SMS(msg):
    """Send an SMS text message to selected recipients"""
    from twilio.rest import Client

    account_sid = secret.Twilio["account sid"]
    auth_token = secret.Twilio["auth token"]
    twilio_number = secret.Twilio["number"]
    print("\nUsing Twilio number: +" + str(twilio_number))
    client = Client(account_sid, auth_token)
    contacts = [x for x in enumerate(secret.contacts.items())]
    print("\nPlease select 0-9 recipients for SMS text message...")
    print("For example enter '02' for the 0th and 2nd contact in the list.\n")
    print([str(y[0]) + ": " + y[1][0] for y in contacts])
    recipients = input("> ").lower()
    print("\nSending SMS to:")
    print([contacts[int(x)][1][0] for x in recipients])
    i = input(
        "\n(S)end automatically, (C)onfirm each message, or ENTER for Test Mode): "
    ).lower()
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
                "\nEnter (Y) to proceed or any other key to skip: "
            ).lower()
        if i == "s" or confirmed == "y":
            try:
                client.messages.create(from_=twilio_number, to=number, body=str(msg))
                print("\nMessage sent to", name)
            except:
                print("\nSMS message failed - probably over 1600 character limit.")
            time.sleep(1)
    return


# Main Program


def main():
    # Load configuration data
    global secret
    secret = Secret().load()
    # Top level menu
    print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
    print("Welcome to the ShowMyHomework (SMH) helper by peter@southwestlondon.tv")
    print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n")
    print("You'll need a valid account with showmyhomework.co.uk and also")
    print("a (free) Twilio.com account. If it's your first time using this")
    print("please select [E]dit from the menu below and add those details now.")
    i = input(
        """\nPress ENTER to send a quick homework summary to your phone contacts
    'T' to also open each task as a separate Tab in your Browser
    'E' to Edit your login details and contacts\n\n> """
    )
    if i.lower() == "e":
        Secret().edit()
        return "No summary created; User data edited."
    # Logon to ShowMyHomework using Secret credentials
    launch_smh()
    # Get list of outstanding homework tasks
    urls, todo = get_smh_tasks()
    # Scrape individual pages, one for each task
    smh_pages(todo, i)
    # Create a summary message
    summary = duration(todo)
    # Send summary message to mobile phone contacts
    send_SMS(summary)
    return summary


if __name__ == "__main__":
    summary = main()
