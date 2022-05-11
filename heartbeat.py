#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
from clint.textui import colored, puts
from datetime import datetime
from os import path
from time import time
import pickle
import sys

class HeartbeatInterval(object):
    """Date interval."""

    def __init__(self, days = 0, hours = 0, minutes = 0, seconds = 0):
        self.days = days
        self.hours = days
        self.minutes = minutes
        self.seconds = seconds
        self.formats = {
            "days": "%d days",
            "hours": "%d hours",
            "minutes": "%d minutes",
            "seconds": "%d seconds",
        }

    def __str__(self):
        """Represent the interval as a string."""

        return self.as_string()

    def format_count(self, count, single, plural):
        """Format the count."""

        unit = single if count == 1 else plural

        return "%d %s" % (count, unit)

    def as_days(self, parts):
        """Represent the interval in days."""

        parts.append(self.format_count(self.days, "day", "days"))
        self.as_hours(parts)

        return parts

    def as_hours(self, parts):
        """Represent the interval in hours."""

        parts.append(self.format_count(self.hours, "hour", "hours"))
        self.as_minutes(parts)

        return parts

    def as_minutes(self, parts):
        """Represent the interval in minutes."""

        parts.append(self.format_count(self.minutes, "minute", "minutes"))
        self.as_seconds(parts)

        return parts

    def as_seconds(self, parts):
        """Represent the interval in seconds."""

        parts.append(self.format_count(self.seconds, "second", "seconds"))

        return parts

    def as_string(self):
        """Represent the interval as a string."""

        parts = []

        if self.days > 0:
            parts = self.as_days(parts)
        elif self.hours > 0:
            parts = self.as_hours(parts)
        elif self.minutes > 0:
            parts = self.as_minutes(parts)
        else:
            parts = self.as_seconds(parts)

        if len(parts) > 2:
            first = parts[:-1]
            second = parts[-1]
            return "%s and %s" % (", ".join(first), second)
        else:
            return ", ".join(parts)

class HeartbeatResource(object):
    """Context Manager for the heartbeat class."""

    def __enter__(self):
        self.hb = Heartbeat()
        return self.hb

    def __exit__(self, exc_type, exc_value, traceback):
        self.hb.cleanup()

class Heartbeat(object):
    """Tracks the last time actions were performed."""

    def __init__(self):
        self.actions = {}
        self.action_path = path.expanduser("/opt/heartbeats")
        self.actions_updated = False
        self.load()

    def add(self, name, data):
        """Add a new heartbeat."""

        self.actions[name] = {
            "last_beat": None,
            "data": data
        }

        self.actions_updated = True

    def remove(self, name):
        """Remove a heartbeat."""
        try:
            del self.actions[name]
            self.save()
        except KeyError:
            print("Invalid heartbeat")

    def load(self):
        """Load the actions in from last time."""

        try:
            with open(self.action_path, mode="rb") as f:
                self.actions = pickle.load(f)
        except (EOFError, FileNotFoundError):
            pass

    def cleanup(self):
        """Ran at shutdown."""

        if self.actions_updated:
            self.save()

    def save(self):
        """Save the actions to file."""

        try:
            with open(self.action_path, mode="wb") as f:
                pickle.dump(self.actions, f)
        except PermissionError:
            sys.exit("Could not save changes to disk.  Ensure %s can be written to." % self.action_path)

    def get_status(self, action):
        """Return the status of an action."""

        last_beat = self.get_last_beat(action)

        if last_beat:
            diff = datetime.now() - datetime.fromtimestamp(last_beat)
            return "%s was last done %s ago" % (action, self.format_diff(diff))
        else:
            return "%s has never been done" % action

    def get_last_beat(self, action):
        """Return the last time an action was performed."""

        try:
            return self.actions[action]["last_beat"]
        except KeyError:
            pass

    def get_actions(self):
        """Return every action."""

        return self.actions

    def get_action(self, action):
        """Return the data for an action."""

        try:
            return self.actions[action]
        except KeyError:
            pass

    def log_action(self, action):
        """Log that an action took place."""

        try:
            self.actions[action]["last_beat"] = time()
        except KeyError:
            print("Invalid heartbeat")
            return False

        self.actions_updated = True
        return True

class HeartbeatStatus(object):

    def __init__(self, hb):
        self.hb = hb
        self.now = datetime.now()

    def show(self):
        """Show the status of the heartbeats."""
        heartbeat_statuses = self.get_statuses()

        if len(heartbeat_statuses):
            puts(colored.yellow("Heartbeats"))
            puts(colored.yellow("==========\n"))

            for heartbeat in heartbeat_statuses:
                print("* %s" % heartbeat_statuses[heartbeat])

    def get_statuses(self):
        """Return the status of every beat."""
        actions = self.hb.get_actions()
        lines = {}

        for action in actions:
            line = self.get_status(actions[action])
            if line:
                lines[action] = line

        return lines

    def get_status(self, heartbeat):
        """Return the status of a beat."""

        last_beat = heartbeat["last_beat"]
        leniency = heartbeat["data"]["leniency"]
        last_line = heartbeat["data"]["last_line"]
        never_line = heartbeat["data"]["never_line"]
        line = None

        if last_beat:
            diff = self.now - datetime.fromtimestamp(last_beat)
            if leniency and diff.total_seconds() > leniency:
                line = colored.red(last_line % self.format_diff(diff))
        else:
            line = colored.red(never_line)

        return line

    def format_diff(self, delta):
        """Format a timedelta."""

        interval = HeartbeatInterval()
        interval.days = delta.days
        interval.hours, remainder = divmod(delta.seconds, 60 * 60)
        interval.minutes, interval.seconds = divmod(remainder, 60)

        return interval

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--motd", action="store_true")
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--add", action="store_true")
    parser.add_argument("--remove", action="store")
    parser.add_argument("--ping")
    args = parser.parse_args()

    if args.motd:
        with HeartbeatResource() as hb:
            HeartbeatStatus(hb).show()
    elif args.add:
        code = input("Code: ")
        data = {}
        data["last_line"] = input("Last line: ")
        data["never_line"] = input("Never line: ")

        try:
            data["leniency"] = int(input("Leniency (seconds): "))
        except ValueError:
            data["leniency"] = None

        with HeartbeatResource() as hb:
            hb.add(code, data)
    elif args.remove:
        Heartbeat().remove(args.remove)
    elif args.ping:
        with HeartbeatResource() as hb:
            hb.log_action(args.ping)
    elif args.list:
        for action in Heartbeat().get_actions():
            print(action)
    else:
        parser.print_help()

if __name__ == "__main__" and sys.stdout.isatty():
    main()
