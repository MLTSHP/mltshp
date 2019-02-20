from base import BaseHandler

import postmark

import hashlib
import time
import hashlib
import random
from lib.utilities import email_re


class HAProxyHandler(BaseHandler):
    def get(self):
        return self.write("OK")

class HeartbeatHandler(BaseHandler):
    def check_xsrf_cookie(self):
        pass
    def get(self):
        response = """{
        "description":null,
        "verified":false,
        "profile_use_background_image":true,
        "profile_background_color":"C0DEED",
        "url":null,
        "follow_request_sent":false,
        "lang":"en",
        "profile_background_image_url":"http:\/\/s.twimg.com\/a\/1289607957\/images\/themes\/theme1\/bg.png",
        "created_at":"Sun May 03 17:29:18 +0000 2009",
        "profile_text_color":"333333",
        "location":null,
        "notifications":false,
        "profile_background_tile":false,
        "profile_link_color":"0084B4",
        "id_str":"37458155",
        "listed_count":0,
        "following":false,
        "followers_count":7,
        "statuses_count":70,
        "profile_sidebar_fill_color":"DDEEF6",
        "protected":false,
        "show_all_inline_media":false,
        "friends_count":2,
        "profile_image_url":"http:\/\/s.twimg.com\/a\/1289518607\/images\/default_profile_0_normal.png",
        "name":"Drop Cash",
        "contributors_enabled":false,
        "time_zone":"Alaska",
        "favourites_count":0,"profile_sidebar_border_color":"C0DEED",
        "id":555,"geo_enabled":false,"utc_offset":-32400,"screen_name":"mltshp"}"""
        return self.write(response)

    def post(self):
        return self.write("OK")

class FAQHandler(BaseHandler):
    def check_xsrf_cookie(self):
        pass

    def get(self):
        return self.render("misc/faq.html")

    def post(self):
        return self.redirect('/account/subscribe')

class ComingSoonHandler(BaseHandler):
    def get(self):
        return self.render("misc/coming-soon.html")

class WebmasterToolsHandler(BaseHandler):
    def get(self):
        return self.render("misc/googlead81c5d028a3e443.html")

class StyleguideHandler(BaseHandler):
    def get(self):
        return self.render("misc/styleguide.html")

class TermsOfUseHandler(BaseHandler):
    def get(self):
        return self.render("misc/terms-of-use.html")

class CodeOfConductHandler(BaseHandler):
    def get(self):
        return self.render("misc/code-of-conduct.html")

class PromoHandler(BaseHandler):
    def get(self):
        ads = [
            {
               'img': '/static/promos/merch/1.jpg',
               'link': 'https://teespring.com/stores/mltshp-store',
               'text': '',
            },
            {
               'img': '/static/promos/merch/2.jpg',
               'link': 'https://teespring.com/stores/mltshp-store',
               'text': '',
            },
            {
               'img': '/static/promos/merch/3.jpg',
               'link': 'https://teespring.com/stores/mltshp-store',
               'text': '',
            },
            {
               'img': '/static/promos/merch/4.jpg',
               'link': 'https://teespring.com/stores/mltshp-store',
               'text': '',
            },
            {
               'img': '/static/promos/merch/5.jpg',
               'link': 'https://teespring.com/stores/mltshp-store',
               'text': '',
            },
            {
               'img': '/static/promos/merch/6.jpg',
               'link': 'https://teespring.com/stores/mltshp-store',
               'text': '',
            },
            {
               'img': '/static/promos/merch/7.jpg',
               'link': 'https://teespring.com/stores/mltshp-store',
               'text': '',
            },
            {
               'img': '/static/promos/merch/8.jpg',
               'link': 'https://teespring.com/stores/mltshp-store',
               'text': '',
            },
            {
               'img': '/static/promos/merch/9.jpg',
               'link': 'https://teespring.com/stores/mltshp-store',
               'text': '',
            },
            {
               'img': '/static/promos/merch/10.jpg',
               'link': 'https://teespring.com/stores/mltshp-store',
               'text': '',
            },
            {
               'img': '/static/promos/merch/11.jpg',
               'link': 'https://teespring.com/stores/mltshp-store',
               'text': '',
            },
            {
               'img': '/static/promos/merch/12.jpg',
               'link': 'https://teespring.com/stores/mltshp-store',
               'text': '',
            },
        ]
        banner = random.choice(ads)
        return self.render("misc/promo.html", banner = banner)

