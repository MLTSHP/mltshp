#!/usr/bin/env python

import argparse

from torndb import Connection
from tornado.options import options

from models import User


def main():
    parser = argparse.ArgumentParser(
        description='migrate a MLKSHK use to MLTSHP')
    parser.add_argument(
        'user', metavar='str', type=str,
        help='a MLKSHK username')
    args = parser.parse_args()

    user = User.get("name = %s and deleted <> 0", args.user)
    if user is not None:
        user.restore()
