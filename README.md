# Heartbeat

A simple script for tracking when something was last done and displaying a summary in your terminal as a MOTD.

```
usage: heartbeat.py [-h] [--motd] [--list] [--add] [--remove REMOVE] [--ping PING]

optional arguments:
  -h, --help       show this help message and exit
  --motd
  --list
  --add
  --remove REMOVE
  --ping PING
```

## Adding heartbeats

Adding a new heartbeat that expects to be ran at least once an hour:

```
> ./heartbeat.py --add

Code: example-heartbeat
Last line: Example heartbeat last called %s ago
Never line: Example heartbeat never called
Leniency (seconds): 3600
```

## Running a heartbeat

```
> ./heartbeat.py --ping example-heartbeat
```

## Displaying your heartbeats

Heartbeats can be shown manually or displayed whenever you open a new terminal:

```
> ./heartbeat.py --motd

Heartbeats
==========

* Example heartbeat last called 1 day, 2 hours, 3 minutes and 4 seconds ago
```

