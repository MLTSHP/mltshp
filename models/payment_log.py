from lib.flyingcow import Model, Property
from tornado.options import options

from datetime import datetime


class PaymentLog(Model):
    user_id                   = Property()
    status                    = Property()
    reference_id              = Property()
    transaction_id            = Property()
    operation                 = Property()
    transaction_date          = Property()
    next_transaction_date     = Property()
    buyer_email               = Property()
    buyer_name                = Property()
    recipient_email           = Property()
    recipient_name            = Property()
    payment_reason            = Property()
    transaction_serial_number = Property()
    subscription_id           = Property()
    payment_method            = Property()
    transaction_amount        = Property()
    processor                 = Property(default=0)
    created_at                = Property()
    updated_at                = Property()

    #AMAZON  = 0
    #TUGBOAT = 1
    VOUCHER = 2
    STRIPE  = 3

    def save(self, *args, **kwargs):
        if options.readonly:
            self.add_error('_', 'Site is read-only.')
            return False

        self._set_dates()
        return super(PaymentLog, self).save(*args, **kwargs)

    def _set_dates(self):
        """
        Sets the created_at and updated_at fields. This should be something
        a subclass of Property that takes care of this during the save cycle.
        """
        if self.id is None or self.created_at is None:
            self.created_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        self.updated_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

    @staticmethod
    def last_payments(count=3, user_id=None):
        """
        Grabs the last <<count>> payments sorted by id.
        """
        if not user_id:
            return []
        if count <= 0:
            return []
            
        return PaymentLog.where('user_id = %s AND status IN (%s, %s) ORDER BY id desc LIMIT %s',
             user_id, 'payment', 'credit', count)
