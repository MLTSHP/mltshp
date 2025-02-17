from datetime import timedelta
import tornado.httpclient
from lib.utilities import utcnow

import test.base
import test.factories
from models import Promotion, Voucher, Shake, PaymentLog


class VoucherTests(test.base.BaseAsyncTestCase):
    def setUp(self):
        super(VoucherTests, self).setUp()
        self.admin = test.factories.user()
        self.sign_in("admin", "password")

        self.shake = Shake(user_id=self.admin.id, name='promotion-shake',
            title='Promotion Shake', type='group')
        self.shake.save()
        self.expired_promotion = Promotion(name="Expired Promotion",
            membership_months=60,
            expires_at=utcnow() - timedelta(seconds=50),
            promotion_shake_id=0)
        self.expired_promotion.save()
        self.promotion = Promotion(name="Unit Test Sale",
            membership_months=60, promotion_shake_id=self.shake.id,
            expires_at=utcnow() + timedelta(seconds=60*60*24*365))
        self.promotion.save()

        self.used_voucher = Voucher(offered_by_user_id=0, promotion_id=self.promotion.id,
            voucher_key="abc123")
        # apply_to_user saves the voucher object (because it touches the
        # claimed_by_user_id and dates) and also the user object (by
        # updating the is_paid status)
        self.used_voucher.apply_to_user(self.admin)

        self.unused_voucher = Voucher(offered_by_user_id=0, claimed_by_user_id=0,
            promotion_id=self.promotion.id, voucher_key="unclaimed")
        self.unused_voucher.save()

        tornado.httpclient.HTTPClient()

    def test_create_account_has_code_field(self):
        """
        Create account page should display the discount
        code field for new user registration.
        """
        self.sign_out()
        response = self.fetch_url("/create-account")
        self.assertEqual(200, response.code)
        self.assertIn("Discount code:", response.body)

    def test_create_account_with_bad_voucher(self):
        """
        Submitting an invalid discount code should result in an error.
        """
        self.sign_out()
        arguments = self._valid_arguments()
        arguments["key"] = "ABCDEFGHIJKL"
        response = self.post_url("/create-account", arguments=arguments)
        self.assertEqual(200, response.code)
        self.assertIn("Invalid discount code", response.body)

    def test_create_account_with_unrecognized_voucher(self):
        """
        Submitting an invalid discount code should result in an error.
        """
        self.sign_out()
        arguments = self._valid_arguments()
        arguments["key"] = "foobar"
        response = self.post_url("/create-account", arguments=arguments)
        self.assertEqual(200, response.code)
        self.assertIn("Invalid discount code", response.body)

    def test_create_account_with_good_voucher(self):
        """
        Submitting a valid discount code should create an account
        with appropriate credit applied.
        """
        self.sign_out()
        arguments = self._valid_arguments()
        arguments["key"] = "unclaimed"
        # this will create the account, but the redirect doesn't
        # carry forward the session info, so sign in separately
        # then verify the confirm-account page displays with a greeting
        self.post_url("/create-account", arguments=arguments)
        self.sign_in(arguments["name"], arguments["password"])
        response = self.fetch_url("/confirm-account")
        self.assertIn(
            ("Hello, <span class=\"user-name\">%s</span>!" % arguments["name"]), response.body)
        response = self.fetch_url("/account/settings")
        self.assertIn("5 Years", response.body)

    def test_settings_page_with_credit(self):
        """
        Validate that our test user account is showing a 5 year
        credit on their account settings.
        """
        response = self.fetch_url("/account/settings")
        self.assertIn("5 Years", response.body)

    def test_redeem_page_with_pro_user(self):
        """
        A pro member shouldn't have access to the redeem page.
        """
        response = self.fetch_url("/account/redeem")
        self.assertNotIn("Redeem a Coupon", response.body)

    def test_redeem_voucher_with_bad_voucher(self):
        self.sign_out()
        user = test.factories.user(name="free_user", email="free_user@mltshp.com", is_paid=0)
        self.sign_in(user.name, "password")
        response = self.fetch_url("/account/settings")
        # verify this account is currently free
        self.assertIn("You are currently using a free account.", response.body)

        arguments = {
            "key": "abc123"
        }
        response = self.post_url("/account/redeem", arguments)
        self.assertIn("Invalid", response.body)

    def test_redeem_voucher_with_good_voucher(self):
        self.sign_out()
        user = test.factories.user(name="free_user", email="free_user@mltshp.com")
        user.is_paid = 0
        user.save()
        self.sign_in(user.name, "password")
        response = self.fetch_url("/account/settings")
        # verify this account is currently free
        self.assertIn("You are currently using a free account.", response.body)

        arguments = {
            "key": "unclaimed"
        }
        # this will post and redirect to the settings page which should
        # then reflect that we are a paid user with 5 years of credit
        response = self.post_url("/account/redeem", arguments)
        self.assertIn("5 Years", response.body)

        payments = PaymentLog.where("user_id=%s", user.id)
        self.assertEqual(len(payments), 1)
        self.assertEqual(payments[0].operation, "redeem")
        self.assertEqual(payments[0].status, "credit")
        self.assertEqual(payments[0].reference_id, str(self.promotion.id))
        self.assertEqual(payments[0].transaction_id, arguments['key'])
        self.assertEqual(payments[0].buyer_email, user.email)
        self.assertEqual(payments[0].buyer_name, user.name)
        # self.assertEqual(payments[0].next_transaction_date, )

        voucher = Voucher.get("claimed_by_user_id=%s", user.id)
        self.assertEqual(voucher.promotion_id, self.promotion.id)
        self.assertEqual(voucher.claimed_by_user_id, user.id)
        self.assertEqual(voucher.offered_by_user_id, self.admin.id)

    def test_active_promotion_list(self):
        promotions = Promotion.active()
        self.assertEqual(len(promotions), 1)
        self.assertEqual(promotions[0].id, self.promotion.id)

    def _valid_arguments(self):
        return {
            "name" : "valid_user",
            "password" : "asdfasdf",
            "password_again" : "asdfasdf",
            "email" : "valid_user@mltshp.com",
            "_skip_recaptcha_test_only" : True,
        }
