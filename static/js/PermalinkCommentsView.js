import { setCaret } from "./common.js";

/**
 * Functionality associated with replying to or deleting a comment from a
 * permalink page e.g. https://mltshp.com/p/1RNJS#post-comment
 *
 * Attaches event handlers to "reply" and "delete" (if owned by the current
 * user) links on each existing comment. Only initialised if the
 * #post-comment-body has some children.
 */

let $root;
let $post_comment_body;

const PermalinkCommentsView = {
    addEvents: function ($image_comments_permalink) {
        $root = $image_comments_permalink;
        $post_comment_body = $("#post-comment-body");

        $root.delegate(".reply-to", "click", (ev) =>
            PermalinkCommentsView.click_reply_to(ev),
        );
        $root.delegate(".delete", "click", (ev) =>
            PermalinkCommentsView.click_delete(ev),
        );
    },

    click_reply_to: function (ev) {
        var $target = $(ev.target);
        var $meta = $target.parent();
        var username = $meta.find(".username").html();
        var username_clean = username.replace(/[^a-zA-Z0-9_\-]+/g, "");
        var current_text = $post_comment_body.val();
        $post_comment_body.val(current_text + "@" + username_clean + " ");
        setCaret($post_comment_body.get(0));
        window.location.hash = "post-comment";
        return false;
    },

    click_delete: function (ev) {
        var $delete_form = $("#" + ev.target.id + "-form");
        if (confirm("Are you sure you want to delete this?")) {
            $delete_form.submit();
        }
        return false;
    },
};

export { PermalinkCommentsView };
