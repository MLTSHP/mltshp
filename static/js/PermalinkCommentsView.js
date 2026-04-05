var PermalinkCommentsView = function ($root) {
    this.$root = $root;
    this.init();
    this.init_events();
};

$.extend(PermalinkCommentsView.prototype, {
    init: function () {
        this.$post_comment_body = $("#post-comment-body");
    },

    init_events: function () {
        this.$root.delegate(
            ".reply-to",
            "click",
            $.proxy(this.click_reply_to, this),
        );
        this.$root.delegate(
            ".delete",
            "click",
            $.proxy(this.click_delete, this),
        );
    },

    click_reply_to: function (ev) {
        var $target = $(ev.target);
        var $meta = $target.parent();
        var username = $meta.find(".username").html();
        var username_clean = username.replace(/[^a-zA-Z0-9_\-]+/g, "");
        var current_text = this.$post_comment_body.val();
        this.$post_comment_body.val(current_text + "@" + username_clean + " ");
        setCaret(this.$post_comment_body.get(0));
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
});
