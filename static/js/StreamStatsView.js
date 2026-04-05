var StreamStatsView = function ($image_content_footer) {
    this.$image_content_footer = $image_content_footer;
    this.share_key = this.$image_content_footer
        .attr("id")
        .replace("image-content-footer-", "");
    this.can_submit_comments = true;
    this.init_dom();
    this.init_events();
};

$.extend(StreamStatsView.prototype, {
    init_dom: function () {
        this.$likes_button = this.$image_content_footer.find(".likes");
        this.$saves_button = this.$image_content_footer.find(".saves");
        this.$comments_button = this.$image_content_footer.find(".comments");
        this.$inline_details =
            this.$image_content_footer.find(".inline-details");
        this.init_comment_dom();
    },

    init_comment_dom: function () {
        this.$post_comment_inline = this.$inline_details.find(
            ".post-comment-inline",
        );
        this.$comment_form = this.$inline_details.find(".post-comment-form");
        this.$comment_textarea = this.$inline_details.find("textarea");
        this.$submit_comment_button = this.$inline_details.find(
            ".submit-comment-button",
        );
        this.$show_more_comments = this.$inline_details.find(
            ".show-more-comments",
        );
        this.$comment = this.$inline_details.find(".comment");
        this.$reply_to = this.$inline_details.find(".reply-to");
        this.$delete = this.$inline_details.find(".delete");
    },

    init_events: function () {
        this.$likes_button.click($.proxy(this.click_like, this));
        this.$saves_button.click($.proxy(this.click_saves, this));
        this.$comments_button.click($.proxy(this.click_comments, this));
        this.init_comment_events();
    },

    init_comment_events: function () {
        this.$comment_textarea.click(
            $.proxy(this.click_comment_textarea, this),
        );
        this.$show_more_comments.click($.proxy(this.click_more_comments, this));
        this.$reply_to.click($.proxy(this.click_reply_to, this));
        this.$delete.click($.proxy(this.click_delete, this));
        // Fix for Webkit bug where textarea looses focus incorrectly on mouseup.
        // http://code.google.com/p/chromium/issues/detail?id=4505
        this.$comment_textarea.mouseup(function (e) {
            e.preventDefault();
        });
        this.$comment_form.submit($.proxy(this.submit_comment, this));
    },

    // Removes selected state from all tabs.
    clear_tab_selection: function () {
        this.$likes_button.removeClass("selected");
        this.$saves_button.removeClass("selected");
        this.$comments_button.removeClass("selected");
    },

    // Start the "loading" state transition.
    start_loading: function () {
        this.$inline_details.addClass("inline-details-loading").html("").show();
    },

    user_html: function (data) {
        var html = "";
        for (var i = 0; i < data.result.length; i++) {
            var result = data.result[i];
            var link;
            if (result["action"] == "save") {
                link = result["post_url"];
            } else {
                link = "/user/" + result["user_name"];
            }
            html +=
                '<a href="' +
                link +
                '">' +
                '<img class="avatar--img" src="' +
                result["user_profile_image_url"] +
                '" height="20" width="20" alt="">' +
                '<span class="name">' +
                result["user_name"] +
                "</span></a>";
        }
        return html;
    },

    click_like: function () {
        if (this.$likes_button.hasClass("selected")) {
            this.clear_tab_selection();
            this.$inline_details.hide();
            return false;
        }
        this.clear_tab_selection();
        this.$likes_button.addClass("selected");
        this.start_loading();
        this.load_likes();
        return false;
    },

    load_likes: function () {
        var url = "/p/" + this.share_key + "/likes";
        $.get(url, $.proxy(this.process_like_response, this), "json");
    },

    process_like_response: function (data) {
        var html =
            '<div class="user-saves-likes">' + this.user_html(data) + "</div>";
        this.$inline_details.html(html);
    },

    click_saves: function () {
        if (this.$saves_button.hasClass("selected")) {
            this.clear_tab_selection();
            this.$inline_details.hide();
            return false;
        }

        this.clear_tab_selection();
        this.$saves_button.addClass("selected");
        this.start_loading();
        this.load_saves();
        return false;
    },

    load_saves: function () {
        var url = "/p/" + this.share_key + "/saves";
        $.get(url, $.proxy(this.process_like_response, this), "json");
    },

    click_comments: function () {
        if (this.$comments_button.hasClass("selected")) {
            this.clear_tab_selection();
            this.$inline_details.hide();
            return false;
        }

        this.clear_tab_selection();
        this.$comments_button.addClass("selected");
        this.start_loading();
        var url = "/p/" + this.share_key + "/quick-comments";
        $.get(url, $.proxy(this.process_comments_response, this), "json");
        return false;
    },

    click_more_comments: function () {
        this.$comment.show();
        this.$show_more_comments.hide();
        return false;
    },

    process_comments_response: function (data) {
        this.can_submit_comments = true;
        if (data["result"] == "ok") {
            this.$comments_button.find("a").html(data["count"]);
            this.$inline_details.html(data["html"]);
            this.init_comment_dom();
            this.init_comment_events();
        }
    },

    click_reply_to: function (ev) {
        this.click_comment_textarea();
        var username = $(ev.target)
            .parents(".comment")
            .find(".username")
            .html();
        var username_clean = username.replace(/[^a-zA-Z0-9_\-]+/g, "");
        var current_text = this.$comment_textarea.val();
        this.$comment_textarea.val(current_text + "@" + username_clean + " ");
        setCaret(this.$comment_textarea.get(0));
        return false;
    },

    click_delete: function (ev) {
        var $delete_form = $("#" + ev.target.id + "-form"),
            url = $delete_form.attr("action"),
            data = $delete_form.serialize();
        if (confirm("Are you sure you want to delete this?")) {
            $.post(
                url,
                data,
                $.proxy(this.process_comments_response, this),
                "json",
            );
        }
        return false;
    },

    submit_comment: function () {
        if (this.can_submit_comments === false) {
            return false;
        }
        this.can_submit_comments = false;
        var url = this.$comment_form.attr("action");
        var data = this.$comment_form.serialize();
        $.post(
            url,
            data,
            $.proxy(this.process_comments_response, this),
            "json",
        );
        return false;
    },

    click_comment_textarea: function (e) {
        this.$post_comment_inline.addClass("post-comment-inline-expanded");
        if (this.$comment_textarea.val().indexOf("Write a comment") === 0) {
            this.$comment_textarea.val("");
        }
        this.click_more_comments();
        this.$comment_textarea.css("min-height", "60px");
    },

    refresh_likes: function () {
        if (this.$likes_button.hasClass("selected")) {
            this.load_likes();
        }
    },

    refresh_saves: function () {
        if (this.$saves_button.hasClass("selected")) {
            this.load_saves();
        }
    },
});
