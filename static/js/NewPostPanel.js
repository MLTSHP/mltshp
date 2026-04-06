var NewPostPanel = (function () {
    var panel_expanded = false;

    var $new_post_panel;
    var $new_post_panel_inner;
    var $new_post_button;
    var $save_video_form;
    var $save_video_form_button;
    var $post_video_form;
    var $post_video_form_button;
    let $upload_image_input;
    let $link_to_video;
    let $video_shake_id;
    let $shake_selector;

    var init_dom = function () {
        $new_post_panel = $("#new-post-panel");
        $new_post_panel_inner = $("#new-post-panel .new-post-panel--inner");
        $new_post_button = $("#new-post-button");
        // upload image
        $upload_image_input = $("#upload-image-input");
        // link to video
        $link_to_video = $("#link-to-video");
        $video_shake_id = $("#video-shake-id");
        // video preview screen
        $save_video_form = $("#new-post-panel .save-video-form");
        $save_video_form_button = $("#new-post-panel .save-video-form .btn");
        $post_video_form = $("#new-post-panel .post-video-form");
        $post_video_form_button = $("#new-post-panel .post-video-form .btn");
        // shake selector
        $shake_selector = $(".shake-selector");
    };
    init_dom();

    $new_post_button.click(function () {
        NewPostPanel.load_new_post();
        return false;
    });

    // We don't want click event on panel to bubble up to body
    // since a click to body closes the panel.
    $new_post_panel.click(function (ev) {
        ev.stopPropagation();
    });

    // The events that are inside the panel that we want to initialize
    // when the panel loads.  These are the events that are subject
    // to change depending on content that is loaded.
    var init_events = function () {
        $link_to_video.click(function () {
            NewPostPanel.load_post_video();
            return false;
        });

        $save_video_form_button.click(function (e) {
            NewPostPanel.submit_save_video();
            return false;
        });

        $post_video_form_button.click(function (e) {
            NewPostPanel.submit_post_video();
            return false;
        });

        $upload_image_input.change(function () {
            $(this).closest("form").submit();
        });

        $shake_selector.click(NewPostPanel.toggle_shake_selector);
        $shake_selector.find("ul a").click(NewPostPanel.choose_shake);
    };

    var remove_events = function () {
        $save_video_form_button.unbind();
        $post_video_form_button.unbind();
        $shake_selector.unbind();
        $link_to_video.unbind();
    };

    return {
        toggle_shake_selector: function (ev) {
            $(this).toggleClass("is-active").find("ul").toggle();
            ev.stopPropagation();
            ev.preventDefault();
        },
        // Sets the text of the shake to the chosen one and
        // sets a hidden input field with the proper shake id.
        choose_shake: function () {
            var $shake_selector = $(this).parents(".shake-selector");
            var $selected_shake = $shake_selector.find(".green");
            var $selected_shake_input = $shake_selector.find("input");
            var name = $(this).html();
            var id = $(this)
                .attr("id")
                .replace(/[^0-9]+/, "");
            $selected_shake.html(name);
            $selected_shake_input.val(id);
        },
        load_new_post: function () {
            var url = "/tools/new-post";
            var that = this;
            $.get(url, function (response) {
                that.refresh_panel(response);
                that.expand_panel();
            });
            return false;
        },
        load_post_video: function () {
            if ($video_shake_id.length > 0) {
                var shake_suffix = "?shake_id=" + $video_shake_id.val();
            } else {
                var shake_suffix = "";
            }
            var url = "/tools/save-video" + shake_suffix;
            var that = this;
            $.get(url, function (response) {
                that.refresh_panel(response);
                that.expand_panel();
            });
        },
        expand_panel: function () {
            panel_expanded = true;
            $new_post_panel.slideDown();
            var that = this;
            $("body").one("click", $.proxy(this.close_panel, this));
            // we want to hide anything with a video since we can't
            // overlap things like youtube embeds, which is an iframe
            // that has an absolutely positioned flash element inside.
            $(".the-image iframe").each(function () {
                $(this).parent().css("height", $(this).height());
                $(this).parent().css("width", $(this).width());
                $(this).hide();
            });
        },
        close_panel: function () {
            panel_expanded = false;
            $new_post_panel.hide();
            remove_events();
            // show the videos again.
            $(".the-image iframe").show();
        },
        submit_save_video: function () {
            var url = $save_video_form.attr("action");
            var data = $save_video_form.serialize();
            var that = this;
            $.get(url, data, function (response) {
                that.refresh_panel(response);
            });
        },
        submit_post_video: function () {
            var url = $post_video_form.attr("action");
            var data = $post_video_form.serialize();
            var that = this;
            $post_video_form_button
                .unbind("click")
                .find("span")
                .html("Posting...");
            $.post(
                url,
                data,
                function (response) {
                    document.location =
                        document.location.protocol +
                        "//" +
                        document.location.host +
                        response["path"];
                },
                "json",
            );
        },
        refresh_panel: function (response) {
            $new_post_panel_inner.html(response);
            $new_post_panel_inner.html();
            remove_events();
            init_dom();
            init_events();
        },
    };
})();

export { NewPostPanel };
