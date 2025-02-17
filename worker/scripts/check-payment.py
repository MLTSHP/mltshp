#!/usr/bin/env python3

import sys
import json
import models
from settings import settings
"""
Check if a user's subscription is current.
"""

NAME = "check-payment"

def main():
    users = models.User.all()
    for user in users:
        last_payments = models.PaymentLog.last_payments(count=1, user_id=user.id)
        if last_payments:
            lp = last_payments[0]
            ### TODO: this has not been converted to Stripe yet
            #details = b.get_subscription_details(SubscriptionId=lp.subscription_id)
            #if details.GetSubscriptionDetailsResult.SubscriptionStatus == 'Cancelled':
            #    user.is_paid = 0
            #    user.save()

    return json.dumps({'status':'finished', 'message':'Processed subscriptions.'})
