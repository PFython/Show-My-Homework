# Show My Homework

This app is designed to send a short task summary by SMS text (using Twilio) to parents and/or child using www.showmyhomework.co.uk ("SMH").  Although a mobile app exists for SMH, not all school children have access to it on their (or their parents') phones, and in any case the key thing it doesn't tell parents is the total estimated effort remaining for all outstanding homework tasks.

It's a simple enough app and my first ever "public" project on Github.  I'm currently looking for a mentor or mentors to help guide me on my journey from having a functional but amateur/hacked together app and putting the necessary bells and whistles on it to make it "production ready" i.e. packaged up nicely so that users can just pick it up and use it, without any knowledge of Python, setting up Twilio, environment variables, tokens etc.

At the time of writing the key improvements I know I need to make include:

1) Login details, Contact Names and Contact Phone Numbers are stored in a "credentials" file which needs to be edited with a text editor by the user.  Nice to have would be an easy menu/form to update the details instead.
2) The script doesn't "just run" - Python itself and a couple of dependencies need to be installed first.
3) Twilio tokens and phone number are stored in a "credentials" file which needs to be edited with a text editor by the user.  Nice to have would be an easy menu/form to update the details instead.
4) There's no user-friendly "signup" facility for people who don't already have a Twilio account.
5) It relies on pyautogui and webbrowser rather than a "proper" API.
6) There are no tests!
7) This is all there is by way of documentation!

As well as achieving the end goal which is to create a nicely packaged and shareable tool that other parents can just pickup (probably download from a more "mainstream" website than Github), I think this very journey of getting from where the code is currently at ("functional but amateur/hacked") to that state with the minimum effort is worth documenting, perhaps even as a tutorial.  I know there are many Python newbies like myself who have got to the point of creating something useful, albeit in a vacuum, and are frankly a bit daunted by all the extra learning and steps they have to go through to actually start sharing the tool with end users, or indeed with other friendly Pythonistas who can help improve the quality, security, readability etc. of the code itself.

So... all comments and offers of a guiding hand would be awesome and greatly appreciated, not just for me and this particular app, but for other newbies wanting to take this universal Next Step.

Many thanks,
peter@southwestlondon.tv
