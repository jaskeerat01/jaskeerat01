# GAME 7

## Level 1: API Reconnaissance & Object Enumeration
Research about github rest api and use that to find the details<br>
Hint:<a href="https://api.github.com/">Github</a>
<details>
<summary>View Solution</summary>
Soln Path: <a href="https://api.github.com/users/AlexanderBech">Github User Detail</a><br>
Password:<b>2300056</b>
</details>

## Level 2: Text Stream Processing & Automated Directory Fuzzing
Process the text file and use fuzzer to check the response code 
<details>
<summary>View Solution</summary>
Process it using the command: sed 's|http://inovace.eu/url/||' url.txt > output.txt<br>
Now use fuzzer to check it: ffuf -u 'http://inovace.eu/url/FUZZ' -w output.txt -r -mc 200 <br>
Correct Path: vkeb6uz6.html<br>
Password: <b>solution47</b>
</details>

## Level 3: Cryptographic Hash Analysis & De-hashing
hashcat and john the ripper could be used to crack it, while there are other online tools which are faster than these tools
<details>
<summary>View Solution</summary>
Go to <a href="https://crackstation.net">CrackStation</a><br>
Password: <b>games</b>
</details>

## Level 4: Breach Data Triage & Credential Intelligence
simply search on google and find it
<details>
<summary>View Solution</summary>
Most common passwords: <a href="https://fortune.com/2016/05/18/linkedin-breach-passwords-most-common/">Common Passwords</a><br>
Password: <b>sunshine</b>
</details>

## Level 5: Advanced Search Operators (Google Dorking) — Profile Targeting
Don't use the experience (years of experience increase every year) and city parameters in a google dork
<details>
<summary>View Solution</summary>
Dork Used: site:freelancer.com/u/ AND "Network+Engineer" AND "February 2017" <br>
Profile Link: <a href="https://www.freelancer.com/u/lawrence37">Freelancer</a><br>
Password: <b>lawrence37</b>
</details>

## Level 6: Advanced Search Operators (Google Dorking) — Asset Identification
Use the characterstics of the person for framing the google dork instead of using Austin in the dork
<details>
<summary>View Solution</summary>
Dork Used: site:airbnb.com/rooms/ "San Francisco" AND "14 years hosting" AND "outdoor enthusiast"<br>
Listing Link: <a href="https://www.airbnb.co.in/rooms/571142"> AirBnB </a><br>
Password: <b>adam</b>
</details>

## Level 7: Niche Domain Profiling & Identity Sourcing
Reverse search for the type of image processing and frame a google dork to find him
<details>
<summary>View Solution</summary>
Dork Used: site:stackoverflow.com/users/ "France" "hyperspectral image processing" "developer"<br>
Profile Link: <a href="https://stackoverflow.com/users/6093326/gwen">StackOverflow Profile </a><br>
Password: <b>6093326</b>
</details>

## Level 8: Programmatic Identity Resolution & API Querying
Use the previously used github rest api to find the username
<details>
<summary>View Solution</summary>
Link Used: https://api.github.com/user/2314988<br>
Checkout the login parameter of the returned JSON payload.<br>
Password: <b>vastrolorde</b>
</details>
