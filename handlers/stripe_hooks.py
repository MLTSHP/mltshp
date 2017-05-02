import datetime

from tornado.options import options

from base import BaseHandler
from models import User, PaymentLog

import json
import postmark
import stripe


class StripeWebhook(BaseHandler):
    def check_xsrf_cookie(self):
        return

    def post(self):
        # type of message is passed through "type" parameter
        json_response = json.loads(self.request.body)
        body_str = json.dumps(json_response).replace("\n","\\n")

        stripe_customer_id = None
        period_start = None
        period_end = None
        checkout_id = None
        status = None
        subscription_id = None
        charge_id = None
        amount = 0
        operation = None

        evt = stripe.convert_to_stripe_object(json_response,
            options.stripe_secret_key, None)

        if evt.type == 'invoice.payment_failed':
            # subscription failed to be paid due to a problem
            # with the member's credit card or something
            # for now, just email hello@mltshp.com about this
            stripe_customer_id = evt.data.object.customer

            subscriber = User.get("stripe_customer_id=%s and deleted=0",
                stripe_customer_id)

            if subscriber and options.postmark_api_key:
                pm = postmark.PMMail(
                    api_key=options.postmark_api_key,
                    sender="hello@mltshp.com", to="hello@mltshp.com",
                    subject="%s has a subscription failure" % (subscriber.display_name()),
                    text_body="Subscription ID: %s\nBuyer Name:%s\nBuyer Email:%s\nUser ID:%s\n" %
                    (subscription_id, subscriber.display_name(),
                     subscriber.email, subscriber.id))
                pm.send()

            return self.finish("OK")

        elif evt.type == 'customer.subscription.created':
            # important properties
            #   customer - should be recorded already in account.stripe_customer_id
            #   current_period_start
            #   current_period_end
            #   plan.id (mltshp-annual)
            stripe_customer_id = evt.data.object.customer
            period_start = evt.data.object.current_period_start
            period_end = evt.data.object.current_period_end
            checkout_id = evt.data.object.id
            status = "subscribed" # evt.type
            operation = "subscribe"
            subscription_id = evt.data.object.id
            amount = evt.data.object.plan.amount

        elif evt.type == "customer.subscription.deleted":
            stripe_customer_id = evt.data.object.customer
            period_start = evt.data.object.current_period_start
            period_end = evt.data.object.current_period_end
            status = "canceled" # evt.type
            operation = "cancel"
            subscription_id = evt.data.object.id

        elif evt.type == 'invoice.payment_succeeded':
            #   customer
            #   date
            #   lines.subscriptions[0].plan.id
            #       period.start
            #       period.end
            #   total
            line_items = [item for item in evt.data.object.lines.data
                if item.type == "subscription" and
                   item.plan.id in ("mltshp-double", "mltshp-single")]
            if line_items:
                line_item = line_items[0]
                stripe_customer_id = evt.data.object.customer
                period_start = line_item.period.start
                period_end = line_item.period.end
                checkout_id = evt.data.object.id
                status = "payment" # evt.type
                operation = "pay"
                subscription_id = evt.data.object.subscription
                charge_id = evt.data.object.charge
                amount = evt.data.object.total

        else:
            # unsupported event type; just ignore it
            return self.finish("OK")

        subscriber = None
        if stripe_customer_id:
            subscriber = User.get("stripe_customer_id=%s and deleted=0",
                stripe_customer_id)

        if subscriber is None:
            # raise an exception for this...
            #raise Exception("failed to locate user for stripe_customer_id %s"
            #    % stripe_customer_id)
            return self.finish("OK")

        #create a payment log record
        amount = "USD %0.2f" % (amount / 100.0)
        pl = PaymentLog(
            user_id                   = subscriber.id,
            status                    = status,
            reference_id              = checkout_id,
            transaction_id            = charge_id,
            operation                 = operation,
            transaction_date          = datetime.datetime.fromtimestamp(period_start).strftime("%Y-%m-%d %H:%M:%S"),
            next_transaction_date     = datetime.datetime.fromtimestamp(period_end).strftime("%Y-%m-%d %H:%M:%S"),
            buyer_email               = subscriber.email,
            buyer_name                = subscriber.display_name(),
            recipient_email           = "hello@mltshp.com",
            recipient_name            = "MLTSHP, Inc.",
            payment_reason            = "MLTSHP Paid Account",
            transaction_serial_number = 1,
            subscription_id           = subscription_id,
            payment_method            = 'CC',
            transaction_amount        = amount,
            processor                 = PaymentLog.STRIPE
        )
        pl.save()

        if evt.type == "customer.subscription.deleted":
            subscriber.is_paid = 0
        else:
            subscriber.is_paid = 1
        subscriber.save()

        return self.finish("OK")
