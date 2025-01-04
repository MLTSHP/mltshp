import re

import tornado.web
from tornado import escape
from tornado.options import options
from .base import BaseHandler, require_membership
import lib.utilities

from models import sharedfile, user

MAX_PER_PAGE = 10


class SearchHandler(BaseHandler):
    @tornado.web.authenticated
    @require_membership
    def get(self, base36_id=None):
        self.set_header("Cache-Control", "private")

        # This handler supports several modes of search, influenced by
        # special search terms, or the "context" query parameter, which
        # is another way to convey the search mode (used by contextual
        # forms). The following terms are recognized:
        # * in:<shakename>: <shakename> is a shake identifier, the keyword
        #       supplied on shake creation and used for the URL path to the
        #       shake. This can also be one of the following special names:
        #       mine, likes, friends, popular.
        # * from:<username>: <username> is the login name of any MLTSHP
        #       user.
        # When search words are combined with one or both of these special
        # terms, the search is constrained to that context. The "likes" and
        # "friends" context does not support a username filter at this time.

        before_id = None
        if base36_id:
            before_id = lib.utilities.base36decode(base36_id)

        current_user_obj = self.get_current_user_object()
        q = self.get_argument("q", "")
        context = self.get_argument("context", "")
        if context:
            q = q + " " + context

        user_join_clause = ""
        shake_join_clause = ""
        parent_where_clause = "AND sharedfile.parent_id=0 AND sharedfile.original_id=0"
        likes_shake = False
        friend_shake = False

        terms = q.split(" ")
        new_terms = []
        for term in terms:
            term = lib.utilities.clean_search_term(term)
            if term.lower().startswith("from:"):
                parent_where_clause = ""
                user_name = term.split(":", 1)[1]
                if re.match("^[a-zA-Z0-9_-]+$", user_name):
                    user_join_clause = "JOIN user ON user.deleted=0 AND user.id=sharedfile.user_id AND user.name='%s'" % user_name
            elif term.lower().startswith("in:"):
                # include matches within this shake, regardless of whether the
                # post was 'original' or not.
                parent_where_clause = ""
                shake_name = term.split(":", 1)[1]
                if re.match("^[a-zA-Z0-9-]+$", shake_name):
                    if shake_name == "mine":
                        shake_type = "user"
                        shake_field = "user_id"
                        shake_ident = current_user_obj.id
                    elif shake_name == "likes":
                        likes_shake = True
                        continue
                    elif shake_name == "friends":
                        friend_shake = True
                        continue
                    elif shake_name == "popular":
                        best_of_user = user.User.get("name=%s and deleted=0", options.best_of_user_name)
                        shake_ident = best_of_user.id
                        shake_type = "user"
                        shake_field = "user_id"
                    else:
                        shake_type = "group"
                        shake_field = "name"
                        shake_ident = shake_name

                    shake_join_clause = """
                        JOIN shakesharedfile
                            ON shakesharedfile.deleted=0
                            AND shakesharedfile.sharedfile_id=sharedfile.id
                        JOIN shake
                            ON shake.id=shakesharedfile.shake_id
                            AND shake.deleted=0
                            AND shake.type='%s'
                            AND shake.%s='%s'""" % (shake_type, shake_field, shake_ident)

            elif term.startswith("*"):
                self.add_error("q", "You cannot begin a search term with the * character")
            else:
                new_terms.append(term)
        query_str = " ".join(new_terms)

        sharedfiles = []
        newer_link = None
        older_link = None

        if query_str:
            if friend_shake:
                sharedfiles = current_user_obj.sharedfiles_from_subscriptions(
                    per_page=MAX_PER_PAGE+1, q=query_str, before_id=before_id)
                if len(sharedfiles) > MAX_PER_PAGE:
                    sharedfiles = sharedfiles[0:MAX_PER_PAGE]
                    older_link = "/search/before/%s?q=%s" % (sharedfiles[-1].share_key, escape.url_escape(q))
            elif likes_shake:
                sharedfiles = current_user_obj.likes(before_id=before_id,
                    per_page=MAX_PER_PAGE+1, q=q)
                if len(sharedfiles) > MAX_PER_PAGE:
                    sharedfiles = sharedfiles[0:MAX_PER_PAGE]
                    older_link = "/search/before/%d?q=%s" % (sharedfiles[-1].favorite_id, escape.url_escape(q))
            else:
                offset = int(self.get_argument("offset", "0"))
                sql = """SELECT sharedfile.*
                    FROM sharedfile
                    %s
                    %s
                    WHERE sharedfile.deleted=0
                        %s
                        AND MATCH (sharedfile.title, sharedfile.description, sharedfile.alt_text)
                        AGAINST (%%s in boolean mode)
                    ORDER BY sharedfile.created_at DESC LIMIT %%s,%%s""" % (
                        user_join_clause, shake_join_clause, parent_where_clause)
                sharedfiles = sharedfile.Sharedfile.object_query(
                    sql,
                    query_str, offset, MAX_PER_PAGE + 1)
                if offset > 0:
                    newer_link = "/search?q=%s&offset=%d" % (escape.url_escape(q), max(offset - MAX_PER_PAGE, 0))
                if len(sharedfiles) > MAX_PER_PAGE:
                    older_link = "/search?q=%s&offset=%d" % (escape.url_escape(q), offset + MAX_PER_PAGE)
                    sharedfiles = sharedfiles[0:MAX_PER_PAGE]

        return self.render("search/search.html",
            current_user_obj=current_user_obj,
            sharedfiles=sharedfiles, q=q,
            older_link=older_link, newer_link=newer_link)
