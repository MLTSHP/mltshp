# -*- coding: utf-8 -*-
import os
import datetime
import json
import sys

import test.base
from models import User, PaymentLog
from mock import patch, Mock
import stripe
from tornado.options import options


### TBD for Stripe ###

class PaymentTests(test.base.BaseAsyncTestCase):
    def setUp(self):
        super(PaymentTests, self).setUp()
        self.user = User(name='admin', email='admin@mltshp.com', email_confirmed=1)
        self.user.set_password('asdfasdf')
        self.user.save()
        self.sign_in("admin", "asdfasdf")

    def test_no_subscription_sees_subscription_button(self):
        response = self.fetch_url("/account/settings")
        self.assertTrue(response.body.find('upgrade to a paid account') > 0)

    def test_subscriber_sees_subscription(self):
        self.user.is_paid = 1
        self.user.save()
        response = self.fetch_url('/account/settings')
        self.assertTrue(response.body.find('Your last 3 payments or credits:') > 0)

    def test_subcription_webhook_sets_paid_status(self):
        self.user.stripe_customer_id = "cus_AHgKQnggJErzEA"
        self.user.save()
        self.assertEqual(self.user.is_paid, 0)

        # taken from a test stripe event
        # https://dashboard.stripe.com/test/events/evt_5RHqA5yR9E0tT9
        body = """
        {
          "id": "evt_AHgKCfFWDluL5M",
          "object": "event",
          "api_version": "2016-03-07",
          "created": 1489464527,
          "data": {
            "object": {
              "id": "sub_AHgKKr2ibwOoYX",
              "object": "subscription",
              "application_fee_percent": null,
              "cancel_at_period_end": false,
              "canceled_at": null,
              "created": 1489464525,
              "current_period_end": 1521000525,
              "current_period_start": 1489464525,
              "customer": "cus_AHgKQnggJErzEA",
              "discount": null,
              "ended_at": null,
              "items": {
                "object": "list",
                "data": [
                  {
                    "id": "si_09x6xl05bkKHOGRciwBEl4OQ",
                    "object": "subscription_item",
                    "created": 1489464526,
                    "plan": {
                      "id": "mltshp-annual",
                      "object": "plan",
                      "amount": 2400,
                      "created": 1458774515,
                      "currency": "usd",
                      "interval": "year",
                      "interval_count": 1,
                      "livemode": true,
                      "metadata": {},
                      "name": "MLTSHP Pro",
                      "statement_descriptor": null,
                      "trial_period_days": null
                    },
                    "quantity": 1
                  }
                ],
                "has_more": false,
                "total_count": 1,
                "url": "/v1/subscription_items?subscription=sub_AHgKKr2ibwOoYX"
              },
              "livemode": true,
              "metadata": {},
              "plan": {
                "id": "mltshp-annual",
                "object": "plan",
                "amount": 2400,
                "created": 1458774515,
                "currency": "usd",
                "interval": "year",
                "interval_count": 1,
                "livemode": true,
                "metadata": {},
                "name": "MLTSHP Pro",
                "statement_descriptor": null,
                "trial_period_days": null
              },
              "quantity": 1,
              "start": 1489464525,
              "status": "active",
              "tax_percent": null,
              "trial_end": null,
              "trial_start": null
            }
          },
          "livemode": true,
          "pending_webhooks": 3,
          "request": "req_AHgKUz1FyfX7XJ",
          "type": "customer.subscription.created"
        }
        """
        response = self.fetch("/webhooks/stripe", method="POST", body=body)
        self.assertEquals(response.body, "OK")

        user = User.get(self.user.id)
        self.assertEqual(user.is_paid, 1)

    def test_subscription_creation(self):
        # test for POST to /account/subscribe with stripe.js info
        # creates a subscription transaction through stripe and
        # sets account to paid.
        # need to mock stripe.Customer.retrieve and
        # customer.subscriptions.create(), subscription.delete()
        pass

    def test_cancel_handler_clears_paid_status(self):
        self.user.is_paid = 1
        self.user.stripe_customer_id = "fake"
        self.user.save()

        pl = PaymentLog(
            processor=PaymentLog.STRIPE,
            user_id=self.user.id,
            status="payment",
            subscription_id="fake-sub",
            transaction_serial_number=1)
        pl.save()

        # stub out the underlying stripe things
        fake_plan = Mock()
        fake_plan.id = options.stripe_annual_plan_id

        fake_subscription = Mock()
        fake_subscription.id = "fake-sub"
        fake_subscription.status = "active"
        fake_subscription.plan = fake_plan
        fake_subscription.current_period_start = 1489464525
        fake_subscription.current_period_end = 1521000525
        fake_subscription.delete.return_value = None

        customer = stripe.Customer(id=self.user.stripe_customer_id)
        customer.subscriptions = Mock()
        customer.subscriptions.data = [ fake_subscription ]
        customer.subscriptions.retrieve.return_value = fake_subscription

        with patch("stripe.Customer") as CustomerMock:
            CustomerMock.retrieve.return_value = customer
            response = self.post_url("/account/payment/cancel", {})

        user = User.get(self.user.id)
        self.assertEqual(user.is_paid, 0)

#    def test_return_sets_account_to_paid(self):
#    def test_invalid_return_doesnt_set_to_paid_and_errors(self):
#    def test_sending_PI_correctly_saves(self):
#    def test_sending_PS_correctly_saves_and_sets_paid(self):
#    def test_sending_subscription_successful(self):
#    def test_sending_subscription_cancelled(self):
#    def test_sending_bad_to_process_fails(self):
