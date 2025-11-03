# htbcli
Simple cli to interact with HTB seasonal boxes

# requirements
Before starting, you need to generate an API token on HTB to be able to use the cli. Simply go to My profile -> profile settings and create an app token. Then ensure that the env variable HTB_API_TOKEN contains your token and the setup will be complete

export HTB_API_TOKEN=eyJ...

# commands
There aren't a lot of commands available but see below the examples of the commands

# list

this allows you to list all seasonal machines in the current season

```
python3 htbcli.py list

Name                 id     os                  
----------------------------------------------
Expressway           736    Linux               
Imagery              751    Linux               
DarkZero             754    Windows             
Signed               775    Windows             
Hercules             778    Windows             
Conversor            787    Linux               
Giveback             796    Linux      
```

# info

this allows you to get the description of the machine which is helpful when they give you creds for assumed breach scenarios

```
python3 htbcli.py info --machine DarkZero

Description: As is common in real life pentests, you will start the DarkZero box with credentials for the following account john.w / RFulUtONCOL!
```

# start

this allows to launch a machine. It will wait until it gets a valid ip address before returning it

```
python3 htbcli.py start --machine Giveback

Found machine 'Giveback' with ID 796.
Do you want to start 'Giveback'? (y/n): y
Machine 796 start request sent successfully.
Waiting for machine to finish spawning...
Machine is ready! (id=796, name=Giveback, ip=10.129.127.168)
Final machine IP: 10.129.127.168
```

# stop

this allows to terminate a machine

```
python3 htbcli.py stop --machine Giveback

Machine 796 stop request sent successfully.
```

# flag

this allows to submit a flag for the current running machine

```
python3 htbcli.py flag --submit_flag flag

```
