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
let $postCommentBody;

const PermalinkCommentsView = {
    addEvents: function ($imageCommentsPermalink) {
        $root = $imageCommentsPermalink;
        $postCommentBody = $("#post-comment-body");

        $root.delegate(".reply-to", "click", (ev) =>
            PermalinkCommentsView.clickReplyTo(ev),
        );
        $root.delegate(".delete", "click", (ev) =>
            PermalinkCommentsView.clickDelete(ev),
        );
    },

    clickReplyTo: function (ev) {
        const $target = $(ev.target);
        const $meta = $target.parent();
        const username = $meta.find(".username").html();
        const usernameClean = username.replace(/[^a-zA-Z0-9_\-]+/g, "");
        const currentText = $postCommentBody.val();
        $postCommentBody.val(currentText + "@" + usernameClean + " ");
        setCaret($postCommentBody.get(0));
        window.location.hash = "post-comment";
        return false;
    },

    clickDelete: function (ev) {
        const $deleteForm = $("#" + ev.target.id + "-form");
        if (confirm("Are you sure you want to delete this?")) {
            $deleteForm.submit();
        }
        return false;
    },
};

export { PermalinkCommentsView };
