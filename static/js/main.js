/* For now the core JS behavior needed accross the site */

$(document).ready(function () {
    var NewPostPanel = (function () {
        var panel_expanded = false;

        var $new_post_panel;
        var $new_post_panel_inner;
        var $new_post_button;
        var $save_video_form;
        var $save_video_form_button;
        var $post_video_form;
        var $post_video_form_button;

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
            $save_video_form_button = $(
                "#new-post-panel .save-video-form .btn",
            );
            $post_video_form = $("#new-post-panel .post-video-form");
            $post_video_form_button = $(
                "#new-post-panel .post-video-form .btn",
            );
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
                that = this;
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

    var to_text = function (num, base) {
        return num == 1
            ? num + " " + "<span>" + base + "</span>"
            : num + " " + "<span>" + base + "s" + "</span>";
    };

    var ShakesCache = {
        fetch: function () {
            if (this.result !== undefined) {
                return this.result;
            } else {
                return false;
            }
        },

        store: function (result) {
            this.result = result;
        },
    };

    var SaveThisView = function (container) {
        this.$save_this = $(container);
        this.init();
    };

    $.extend(SaveThisView.prototype, {
        init: function () {
            this.init_dom();
            this.init_events();
        },

        init_dom: function () {
            this.$save_this_link = this.$save_this.find(".save-this-link");
            this.$form = this.$save_this.find("form");
            this.$shake_id_input = this.$save_this.find(".shake-id-input");
            this.$shake_selector = $(
                "<div class='save-this-shake-selector save-this-shake-selector-loading'></div>",
            );
        },

        init_events: function () {
            this.$save_this_link.click($.proxy(this.click_save_this, this));
            this.$save_this.delegate(
                ".shake-link",
                "click",
                $.proxy(this.click_choose_shake, this),
            );
            this.$save_this.delegate(
                ".close",
                "click",
                $.proxy(this.click_close_selector, this),
            );
        },

        click_save_this: function (ev) {
            ev.stopPropagation();
            if (this.$save_this_link.hasClass("save-this-link-multiple")) {
                this.show_shake_selector();
            } else {
                this.submit_image_save();
            }
            return false;
        },

        click_choose_shake: function (ev) {
            ev.stopPropagation();
            var shake_id = ev.target.id.replace(/[^\d]+/, "");
            this.$shake_id_input.val(shake_id);
            this.submit_image_save();
            return false;
        },

        click_close_selector: function (ev) {
            ev.stopPropagation();
            this.$shake_selector.remove();
        },

        show_shake_selector: function () {
            this.$save_this.append(this.$shake_selector);
            $("body").one("click", $.proxy(this.click_close_selector, this));

            // Only query once per page.
            if (ShakesCache.fetch() !== false) {
                this.fetch_available_shakes(ShakesCache.fetch());
            } else {
                $.get(
                    "/account/shakes",
                    $.proxy(this.fetch_available_shakes, this),
                    "json",
                );
            }
        },

        fetch_available_shakes: function (response) {
            ShakesCache.store(response);
            var html = '<span class="close caret"></span><ul>';
            for (var i = 0; i < response["result"].length; i++) {
                html +=
                    '<li><a class="shake-link" href="" id="save-this-shake-selector-' +
                    response["result"][i]["id"] +
                    '">' +
                    response["result"][i]["name"] +
                    "</a></li>";
            }
            html += "</ul>";
            this.$shake_selector
                .removeClass("save-this-shake-selector-loading")
                .html(html);
        },

        submit_image_save: function (ev) {
            var url = this.$form.attr("action");
            var data = this.$form.serialize();
            $.post(
                url,
                data,
                $.proxy(this.process_image_save_response, this),
                "json",
            );
        },

        process_image_save_response: function (response) {
            if (response["share_key"]) {
                var count = response["count"];
                var share_key = response["share_key"];
                var new_share_key = response["new_share_key"];
                var count_string = to_text(count, "Save");
                $("#save-count-amount-" + share_key).html(count_string);
                var output =
                    '<a href="/p/' +
                    new_share_key +
                    '" title="Saved It!"><img width="29" height="22" src="/static/images/saved-this.svg"></a>';
                this.$shake_selector.remove();
                this.$save_this.html(output);
                SidebarStatsView.refresh_saves();
                StreamStatsViewRegistry.refresh_saves(share_key);
            } else {
                return false;
            }
        },
    });

    function screen_reader_focus(el) {
        el.setAttribute("tabindex", "0");
        el.blur();
        el.focus();
    }

    $(".save-this").each(function () {
        var save_this_view = new SaveThisView(this);
    });

    // when we hit enter on a form, we want to submit it
    // even though we don't have an type="submit" input
    // available, since we're using a styled button.
    $sign_in_form = $("#sign-in-form");
    $("input", $sign_in_form).keydown(function (e) {
        if (e.keyCode == 13) {
            $sign_in_form.submit();
            return false;
        }
    });

    $(".btn", $sign_in_form).click(function () {
        $sign_in_form.submit();
        return false;
    });

    // Prompt user to confirm before flagging something as NSFW.
    $("#flag-image-permalink").click(function () {
        return confirm("Are you sure you want to flag this as NSFW?");
    });

    // Prompt user to confirm before quitting a shake.
    $("#quit-shake-page").click(function () {
        return confirm(
            "Are you sure you want to quit this shake?\n(If you are following this shake you will also have to unfollow with the button above.)",
        );
    });

    // Prompt user to confirm before deleting a sharedfile.
    $("#delete-post-text").click(function () {
        return confirm("Are you sure you want to delete this post?");
    });

    // Inline editing of the title.
    $(".image-edit-title-form .cancel").click(function () {
        $(this).closest(".image-title").find(".image-edit-title").show();
        $(this).closest(".image-edit-title-form").removeClass("is-active");
        return false;
    });

    $(".image-edit-title").hover(
        function () {
            $(this).addClass("image-edit-title-hover");
        },
        function () {
            $(this).removeClass("image-edit-title-hover");
        },
    );

    $(".image-edit-title").click(function () {
        var $title_container = $(this).closest(".image-title");
        var url = $title_container.find("form").attr("action");
        var that = this;

        $.get(
            url,
            function (result) {
                if ("title_raw" in result) {
                    $(that).hide();
                    $title_container
                        .find(".title-input")
                        .val(result["title_raw"]);
                    $(that)
                        .next(".image-edit-title-form")
                        .addClass("is-active");
                }
            },
            "json",
        );
    });

    $(".image-edit-title-form").submit(function () {
        var data = $(this).serialize();
        var url = $(this).attr("action");
        var that = this;
        $.post(
            url,
            data,
            function (result) {
                if ("title" in result && "title_raw" in result) {
                    var $title_container = $(that).closest(".image-title");
                    $title_container
                        .find(".image-edit-title")
                        .html(result["title"])
                        .show();
                    $title_container
                        .find(".title-input")
                        .val(result["title_raw"]);
                    $title_container
                        .find(".image-edit-title-form")
                        .removeClass("is-active");
                }
            },
            "json",
        );
        return false;
    });

    // Inline editing of the description.
    $(".description-edit-form").submit(function () {
        var data = $(this).serialize();
        var url = $(this).attr("action");
        var that = this;
        $.post(
            url,
            data,
            function (result) {
                if ("description" in result && "description_raw" in result) {
                    var $description_container =
                        $(that).closest(".description-edit");
                    $description_container
                        .find("textarea")
                        .val(result["description_raw"]);
                    $description_container
                        .find(".description-edit-form")
                        .hide();
                    if (result["description"]) {
                        $description_container
                            .find(".the-description")
                            .html(result["description"])
                            .show();
                        $description_container
                            .find(".the-description")
                            .removeClass("the-description-blank");
                    } else {
                        $description_container
                            .find(".the-description")
                            .html("click here to edit description")
                            .show();
                        $description_container
                            .find(".the-description")
                            .addClass("the-description-blank");
                    }
                }
            },
            "json",
        );
        return false;
    });

    $(".description-edit .the-description").hover(
        function () {
            $(this).addClass("the-description-hover");
        },
        function () {
            $(this).removeClass("the-description-hover");
        },
    );

    $(".description-edit .the-description").click(function () {
        var $description_container = $(this).closest(".description-edit");
        var url = $description_container.find("form").attr("action");
        var that = this;
        $.get(
            url,
            function (result) {
                if ("description_raw" in result) {
                    $(that).hide();
                    let $textarea = $description_container.find(
                        ".description-edit-textarea",
                    );
                    $textarea.val(result["description_raw"]);
                    $(that).next(".description-edit-form").show();
                    screen_reader_focus($textarea[0]);
                }
            },
            "json",
        );
    });

    $(".description-edit .cancel").click(function () {
        $(this).closest(".description-edit").find(".the-description").show();
        $(this).closest(".description-edit-form").hide();
        return false;
    });

    // Inline editing of the alt text.
    $(".alt-text-edit-form").submit(function () {
        var data = $(this).serialize();
        var url = $(this).attr("action");
        var that = this;
        $.post(
            url,
            data,
            function (result) {
                if ("alt_text" in result && "alt_text_raw" in result) {
                    var $alt_text_container = $(that).closest(".alt-text-edit");
                    if (result["alt_text"]) {
                        $alt_text_container.removeClass("alt-text--blank");
                        $alt_text_container
                            .find(".the-alt-text")
                            .html(result["alt_text"]);
                    } else {
                        $alt_text_container.addClass("alt-text--blank");
                        $alt_text_container
                            .find(".the-alt-text")
                            .html("add some alt text");
                    }
                    $alt_text_container.removeClass("alt-text--hidden");
                    $alt_text_container.removeClass("alt-text--editing");
                    $alt_text_container
                        .find("textarea")
                        .val(result["alt_text_raw"]);
                    screen_reader_focus(
                        $alt_text_container.find(".the-alt-text")[0],
                    );
                }
            },
            "json",
        );
        return false;
    });

    $(".alt-text-edit .the-alt-text").hover(
        function () {
            $(this).addClass("the-alt-text-hover");
        },
        function () {
            $(this).removeClass("the-alt-text-hover");
        },
    );

    $(".alt-text-edit .the-alt-text").click(function () {
        var $alt_text_container = $(this).closest(".alt-text-edit");
        var url = $alt_text_container.find("form").attr("action");
        var that = this;
        $.get(
            url,
            function (result) {
                if ("alt_text_raw" in result) {
                    $(that)
                        .closest(".alt-text-edit")
                        .addClass("alt-text--editing");
                    let $textarea = $alt_text_container.find(
                        ".alt-text-edit-textarea",
                    );
                    $textarea.val(result["alt_text_raw"]);
                    screen_reader_focus($textarea[0]);
                }
            },
            "json",
        );
    });

    $(".alt-text-edit .cancel").click(function () {
        $(this).closest(".alt-text-edit").removeClass("alt-text--hidden");
        $(this).closest(".alt-text-edit").removeClass("alt-text--editing");
        return false;
    });

    $(".alt-text-toggle").click(function () {
        let $alt = $(this).closest(".alt-text");
        $alt.toggleClass("alt-text--hidden");
        if (!$alt.hasClass("alt-text--hidden")) {
            screen_reader_focus($alt.find(".the-alt-text")[0]);
        }
    });

    $(".delete-from-shakes-form").click(function () {
        return confirm("Are you sure you want to remove it?");
    });

    /* Like / Unlike button */
    $(".like-button, .unlike-button").click(function () {
        var to_text = function (num, base) {
            return num == 1
                ? num + " " + "<span>" + base + "</span>"
                : num + " " + "<span>" + base + "s" + "</span>";
        };

        var $form = $(this).parents("form");
        var $buttons = $form.children("button");
        var url = $form.attr("action");
        var data = $form.serialize() + "&json=1";

        $.post(
            url,
            data,
            function (response) {
                if (response["error"]) {
                    return false;
                } else {
                    var count = response["count"];
                    var share_key = response["share_key"];
                    var count_string = to_text(count, "Like");
                    $("#like-count-amount-" + share_key).html(count_string);
                    if (response["like"] === true) {
                        $form.attr("action", "/p/" + share_key + "/unlike");
                    } else {
                        $form.attr("action", "/p/" + share_key + "/like");
                    }
                    $buttons.toggleClass("is-active");
                    SidebarStatsView.refresh_likes();
                    StreamStatsViewRegistry.refresh_likes(share_key);
                }
            },
            "json",
        );
        return false;
    });

    var ImageStats = function () {
        return {
            save_count: 0,
            like_count: 0,
        };
    };

    var SidebarStatsView = (function (scope) {
        // if we aren't on a permalink page, just expose a dummy public API
        if ($(scope).length == 0) {
            return {
                init: function () {},
                refresh_likes: function () {},
                refresh_saves: function () {},
            };
        }

        var image_stats = new ImageStats();
        $save_count = $(".save-count", scope);
        $like_count = $(".like-count", scope);
        image_stats.save_count = parseInt($save_count.html(), 10);
        image_stats.like_count = parseInt($like_count.html(), 10);

        var $save_button = $(".sidebar-stats-saves", scope);
        var $like_button = $(".sidebar-stats-hearts", scope);
        var $content = $(".sidebar-stats-content", scope);

        var saves_expanded = false;
        var likes_expanded = false;

        return {
            init: function () {
                if (image_stats.save_count > 0) {
                    this.bind_saves();
                } else {
                    this.unbind_saves();
                }
                if (image_stats.like_count > 0) {
                    this.bind_likes();
                    this.toggle_likes();
                } else {
                    this.unbind_likes();
                }
            },

            refresh_likes: function () {
                $like_count = $(".like-count", scope);
                image_stats.like_count = parseInt($like_count.html(), 10);
                if (likes_expanded) {
                    this.get_likes();
                }
                if (image_stats.like_count > 0) {
                    this.bind_likes();
                } else {
                    likes_expanded = false;
                    this.unbind_likes();
                }
            },

            refresh_saves: function () {
                $save_count = $(".save-count", scope);
                image_stats.save_count = parseInt($save_count.html(), 10);
                if (saves_expanded) {
                    this.get_saves();
                }
                if (image_stats.save_count > 0) {
                    this.bind_saves();
                } else {
                    saves_expanded = false;
                    this.unbind_saves();
                }
            },

            bind_saves: function () {
                $save_button.unbind("click");
                $save_button.addClass("enable-cursor");
                $save_button.click(function () {
                    SidebarStatsView.toggle_saves();
                });
            },

            unbind_saves: function () {
                $save_button.removeClass("enable-cursor");
                $save_button.unbind("click");
                this.collapse();
            },

            bind_likes: function () {
                $like_button.unbind("click");
                $like_button.addClass("enable-cursor");
                $like_button.click(function () {
                    SidebarStatsView.toggle_likes();
                });
            },

            unbind_likes: function () {
                $like_button.removeClass("enable-cursor");
                $like_button.unbind("click");
                this.collapse();
            },

            toggle_saves: function () {
                likes_expanded = false;
                saves_expanded = !saves_expanded;
                if (saves_expanded) {
                    $like_button.removeClass("selected");
                    $content.addClass("loading").show();
                    $save_button.addClass("selected");
                    this.get_saves();
                } else {
                    this.collapse();
                }
            },

            get_saves: function () {
                $.get(
                    document.location.pathname + "/saves",
                    function (response) {
                        if (response["result"]) {
                            SidebarStatsView.process_save(response);
                        }
                    },
                    "json",
                );
            },

            toggle_likes: function () {
                saves_expanded = false;
                likes_expanded = !likes_expanded;
                if (likes_expanded) {
                    $save_button.removeClass("selected");
                    $content.addClass("loading").show();
                    $like_button.addClass("selected");
                    this.get_likes();
                } else {
                    this.collapse();
                }
            },

            get_likes: function () {
                $.get(
                    document.location.pathname + "/likes",
                    function (response) {
                        if (response["result"]) {
                            SidebarStatsView.process_like(response);
                        }
                    },
                    "json",
                );
            },

            process_save: function (response) {
                if (response["count"] == 0) {
                    this.disable_saves();
                } else {
                    $save_count.html(this.to_text(response["count"], "Save"));
                    this.render_content(response);
                }
            },

            process_like: function (response) {
                if (response["count"] == 0) {
                    this.unbind_likes();
                } else {
                    $like_count.html(this.to_text(response["count"], "Like"));
                    this.render_content(response);
                }
            },

            to_text: function (num, base) {
                return num == 1
                    ? num + " " + "<span>" + base + "</span>"
                    : num + " " + "<span>" + base + "s" + "</span>";
            },

            collapse: function (repsponse) {
                $like_button.removeClass("selected");
                $save_button.removeClass("selected");
                $content.hide();
            },

            render_content: function (response) {
                var html = "";
                for (var i = 0, len = response["result"].length; i < len; i++) {
                    html += '<div class="user-action">';
                    html +=
                        '<a class="icon" href="/user/' +
                        response["result"][i]["user_name"] +
                        '">';
                    html +=
                        '<img class="avatar--img" src="' +
                        response["result"][i]["user_profile_image_url"] +
                        '" height="20" width="20" alt=""></a>';
                    html +=
                        '<a href="/user/' +
                        response["result"][i]["user_name"] +
                        '" class="name">' +
                        response["result"][i]["user_name"] +
                        "</a>";
                    html +=
                        '<span class="date">' +
                        response["result"][i]["posted_at_friendly"] +
                        "</span>";
                    html += "</div>";
                }
                $content.removeClass("loading").html(html);
            },
        };
    })("#sidebar-stats");
    SidebarStatsView.init();

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
            this.$comments_button =
                this.$image_content_footer.find(".comments");
            this.$inline_details =
                this.$image_content_footer.find(".inline-details");
            this.init_comment_dom();
        },

        init_comment_dom: function () {
            this.$post_comment_inline = this.$inline_details.find(
                ".post-comment-inline",
            );
            this.$comment_form =
                this.$inline_details.find(".post-comment-form");
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
            this.$show_more_comments.click(
                $.proxy(this.click_more_comments, this),
            );
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
            this.$inline_details
                .addClass("inline-details-loading")
                .html("")
                .show();
        },

        user_html: function (data) {
            var html = "";
            for (var i = 0; i < data.result.length; i++) {
                html +=
                    '<a href="/user/' +
                    data.result[i]["user_name"] +
                    '">' +
                    '<img class="avatar--img" src="' +
                    data.result[i]["user_profile_image_url"] +
                    '" height="20" width="20" alt="">' +
                    '<span class="name">' +
                    data.result[i]["user_name"] +
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
                '<div class="user-saves-likes">' +
                this.user_html(data) +
                "</div>";
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
            this.$comment_textarea.val(
                current_text + "@" + username_clean + " ",
            );
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

    var StreamStatsViewRegistry = {
        files_on_page: {},
        register: function (view) {
            this.files_on_page[view.share_key] = view;
        },
        refresh_likes: function (share_key) {
            view = this.get_view(share_key);
            if (view !== undefined) {
                view.refresh_likes();
            }
        },
        refresh_saves: function (share_key) {
            view = this.get_view(share_key);
            if (view !== undefined) {
                view.refresh_saves();
            }
        },
        get_view: function (share_key) {
            return this.files_on_page[share_key];
        },
    };

    function apply_hover_for_video(sel) {
        sel.hover(function () {
            if (this.hasAttribute("controls")) {
                this.removeAttribute("controls");
            } else {
                this.setAttribute("controls", "controls");
            }
        });
    }

    var NSFWCover = function ($root) {
        this.$root = $root;
        this.init();
    };

    $.extend(NSFWCover.prototype, {
        init: function () {
            this.$root.delegate(
                "a",
                "click",
                $.proxy(this.click_show_image, this),
            );
        },

        click_show_image: function (ev) {
            var location = document.location,
                host = location.host,
                protocol = location.protocol,
                base_path = location.protocol + "//" + location.host,
                file_path = $(ev.target).attr("href");
            $.get(
                base_path +
                    "/services/oembed?include_embed=1&url=" +
                    escape(base_path + file_path),
                $.proxy(this.load_image, this),
                "json",
            );
            return false;
        },

        load_image: function (response) {
            var parent = this.$root.parent(),
                parent_height = parent.height();

            if (response["type"] === "photo") {
                parent
                    .css("min-height", parent_height + "px")
                    .html(
                        '<img class="unsized" src="' + response["url"] + '">',
                    );
            } else if (response["embed_html"]) {
                parent
                    .css("min-height", parent_height + "px")
                    .html(
                        '<div class="data-wrapper">' +
                            response["embed_html"] +
                            "</div>",
                    );
            } else if (response["type"] === "video") {
                var content = parent
                    .css("min-height", parent_height + "px")
                    .html(
                        response["html"].replace(
                            /<source /g,
                            '<source onerror="fallbackImage(this)" ',
                        ),
                    );
                apply_hover_for_video(content.find("video.autoplay"));
            }
        },
    });

    $(".image-content").each(function () {
        var $image_content = $(this),
            $image_footer = $image_content.find(".image-content-footer"),
            $nsfw_cover = $image_content.find(".nsfw-cover");
        var stream_stats_view = new StreamStatsView($image_footer);
        StreamStatsViewRegistry.register(stream_stats_view);
        var nsfw_cover = new NSFWCover($nsfw_cover);
    });

    apply_hover_for_video($(".image-content video.autoplay"));

    /* Open / close notification boxes */
    $(".notification-block-hd").live("click", function () {
        $(this).next().toggle();
    });

    /* User follow module */
    $(".user-follow .submit-form").live("click", function () {
        var $container = $(this).parents(".user-follow");
        var $form = $container.find("form");
        var url = $form.attr("action");
        var data = $form.serialize() + "&json=1";
        var that = this;
        $.post(
            url,
            data,
            function (response) {
                if (response["error"]) {
                    return false;
                } else {
                    if (response["subscription_status"] == true) {
                        $form.attr(
                            "action",
                            url.replace("subscribe", "unsubscribe"),
                        );
                        $(that)
                            .text("- Unfollow")
                            .addClass("btn-warning")
                            .removeClass("btn-secondary");
                    } else {
                        $form.attr(
                            "action",
                            url.replace("unsubscribe", "subscribe"),
                        );
                        $(that)
                            .text("+ Follow")
                            .addClass("btn-secondary")
                            .removeClass("btn-warning");
                    }
                }
            },
            "json",
        );
        return false;
    });

    $(".notification-close").live("click", function () {
        $notification = $(this).parent(".notification");
        var $notification_block = $(this).parents(".notification-block");
        var $notification_block_hd = $notification_block.find(
            ".notification-block-hd",
        );
        var id = $(this)
            .attr("id")
            .replace(/[^\d]+/, "");
        $.post(
            "/account/clear-notification" + "?type=single&id=" + id,
            {},
            function (response) {
                $notification.remove();
                var html = $notification_block_hd.html();
                var count = html.replace(/[^\d]+/, "");
                var new_count = parseInt(count, 10) - 1;
                if (new_count == 0) {
                    $notification_block_hd.html("You have 0 new followers");
                    $notification_block.find(".clear-all").remove();
                } else {
                    $notification_block_hd.html(
                        html.replace(/[\d]+/, new_count),
                    );
                }
            },
            "json",
        );
        return false;
    });

    $(".notification-block .clear-all a").live("click", function () {
        var url = $(this).attr("href");
        var $notification_block = $(this).parents(".notification-block");
        $.post(
            url,
            {},
            function (response) {
                if (response["error"]) {
                    return false;
                } else {
                    $notification_block
                        .find(".notification-block-hd")
                        .html(response["response"]);
                    $notification_block
                        .find(".notification-block-bd")
                        .html("")
                        .toggle();
                }
            },
            "json",
        );

        return false;
    });

    /* Notification block: invitations: */
    $("#notifcation-block-invitations form").live("submit", function () {
        var data = $(this).serialize();
        var url = $(this).attr("action");

        var that = this;
        $.post(
            url,
            data,
            function (response) {
                if (response["error"]) {
                    $(that)
                        .find(".main-message")
                        .html("<p>" + response["error"] + "</p>");
                } else {
                    if (response["count"] == 0) {
                        $(that).find("input").hide();
                        $("#invitation-count-text").html(
                            response["count"] + " invitations",
                        );
                        $(that).find(".main-message").html("<p>Thanks!</p>");
                    } else {
                        var invitation_text =
                            response["count"] == 1
                                ? "invitation"
                                : "invitations";
                        $("#invitation-count-text").html(
                            response["count"] + " " + invitation_text,
                        );
                        $(that).find(".main-message").html(response["message"]);
                        $("#email_address").val("");
                    }
                }
            },
            "json",
        );

        return false;
    });

    /* Notification block: shake invitations: */
    $("#notifcation-block-shakeinvitation form").live("submit", function () {
        var data = $(this).serialize();
        var url = $(this).attr("action");
        var $block = $(this).parents(".notification");
        var $header = $(
            "#notifcation-block-shakeinvitation .notification-block-hd",
        );

        var that = this;
        $.post(
            url,
            data,
            function (response) {
                if (!response["error"]) {
                    $block.remove();
                    // we update the header differently when presenting only one
                    // invitation on the shake page itself.
                    if ($header.hasClass("invitation-single")) {
                        $header.html("Got it.");
                    } else {
                        var invitation_text =
                            response["count"] == 1
                                ? "invitation"
                                : "invitations";
                        $header.html(
                            response["count"] + " new shake " + invitation_text,
                        );
                    }
                }
            },
            "json",
        );

        return false;
    });

    var NotificationInvitationContainer = function ($root) {
        this.$root = $root;
        this.init();
    };

    $.extend(NotificationInvitationContainer.prototype, {
        init: function () {
            this.$hd = this.$root.find(".notification-block-hd");
            this.$bd = this.$root.find(".notification-block-bd");
            this.on_shake_page = this.$hd.hasClass("on-shake-page");
            var that = this;
            this.$root.find(".notification").each(function () {
                var new_invitation_request = new NotificationInvitationRequest(
                    $(this),
                    that,
                );
            });
        },

        update_count: function (count) {
            if (!this.on_shake_page) {
                var request_text = count == 1 ? " request" : " requests";
                var html = count + request_text + " to join a shake";
                this.$hd.html(html);
            } else {
                this.$hd.html("Got it!");
            }
        },
    });

    var NotificationInvitationRequest = function ($root, container) {
        this.$root = $root;
        this.container = container;
        this.init_dom();
        this.init_events();
    };

    $.extend(NotificationInvitationRequest.prototype, {
        init_dom: function () {
            this.$form = this.$root.find("form");
            this.$form_approve_invitation = this.$root.find(
                ".approve-invitation",
            );
            this.$form_decline_invitation = this.$root.find(
                ".decline-invitation",
            );
        },

        init_events: function () {
            this.$root.delegate(
                ".approve-invitation",
                "submit",
                $.proxy(this.submit_approve_invitation, this),
            );
            this.$root.delegate(
                ".decline-invitation",
                "submit",
                $.proxy(this.submit_decline_invitation, this),
            );
        },

        submit_approve_invitation: function (ev) {
            ev.preventDefault();
            this.submit_form(this.$form_approve_invitation);
        },

        submit_decline_invitation: function (ev) {
            ev.preventDefault();
            this.submit_form(this.$form_decline_invitation);
        },

        submit_form: function ($form) {
            var url = $form.attr("action");
            var data = $form.serialize();
            $.post(url, data, $.proxy(this.clear_notification, this), "json");
        },

        clear_notification: function (response) {
            if (response["status"] == "ok") {
                this.$root.remove();
                this.container.update_count(response["count"]);
            }
        },
    });

    var init_notification_invitation_request = function () {
        $notification_invitation_request = $(
            "#notification-block-invitation-request",
        );
        if ($notification_invitation_request.length > 0) {
            var invitation_requests = new NotificationInvitationContainer(
                $notification_invitation_request,
            );
        }
    };
    init_notification_invitation_request();

    // Expand all notifications.
    $("#notification-block-aggregate").click(function () {
        $(this).find(".notification-block-hd").html("Loading...");
        $.get("/account/quick-notifications", function (response) {
            $("#notification-block-aggregate").hide().after(response);
            init_notification_invitation_request();
        });
    });

    /* Action Button in a Fun Form, should submit the form (exception here
       for a button with a g-recaptcha class which has a separate event
       handler). */
    $(".field-submit .btn:not(.g-recaptcha)").click(function () {
        $(this).closest("form").submit();
        return false;
    });

    /* Site Nav dropdown */
    $site_nav = $("#site-nav");
    var site_nav_expanded = false;
    $("#site-nav .site-nav--toggle").click(function (event) {
        event.stopPropagation();
        if (site_nav_expanded == false) {
            site_nav_expanded = true;
            $site_nav.addClass("is-expanded");
            $("body").one("click", function () {
                $site_nav.removeClass("is-expanded");
                site_nav_expanded = false;
            });
        } else {
            $site_nav.removeClass("is-expanded");
            $("body").unbind("click");
            site_nav_expanded = false;
        }
    });

    $("#site-nav .site-nav--list").click(function (event) {
        event.stopPropagation();
    });

    /* Choose a shake dropdown */
    $choose_a_shake = $("#choose-a-shake");
    var shake_expanded = false;
    $("#choose-a-shake .choose-a-shake--toggle").click(function (event) {
        event.stopPropagation();
        if (shake_expanded == false) {
            shake_expanded = true;
            $choose_a_shake.addClass("is-expanded");
            $("body").one("click", function () {
                $choose_a_shake.removeClass("is-expanded");
                shake_expanded = false;
            });
        } else {
            $choose_a_shake.removeClass("is-expanded");
            $("body").unbind("click");
            shake_expanded = false;
        }
    });

    $("#choose-a-shake .choose-a-shake--dropdown").click(function (event) {
        event.stopPropagation();
    });

    /* Conversations - mute this button */
    $(".mute-this-conversation").click(function () {
        var $form = $(this).next(".mute-this-conversation-form");
        var url = $form.attr("action");
        var data = $form.serialize();
        var $conversation = $(this).parents(".conversation");
        $.post(url, data, function () {
            $conversation.fadeOut("slow");
        });
        return false;
    });

    // http://stackoverflow.com/questions/1125292/how-to-move-cursor-to-end-of-contenteditable-entity
    function setCaret(el) {
        ctrl = el;
        pos = ctrl.value.length;
        if (ctrl.setSelectionRange) {
            ctrl.focus();
            ctrl.setSelectionRange(pos, pos);
        } else if (ctrl.createTextRange) {
            var range = ctrl.createTextRange();
            range.collapse(true);
            range.moveEnd("character", pos);
            range.moveStart("character", pos);
            range.select();
        }
    }

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
            this.$post_comment_body.val(
                current_text + "@" + username_clean + " ",
            );
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

    var $image_comments_permalink = $("#image-comments-permalink");
    if ($image_comments_permalink.length > 0) {
        var new_comment = new PermalinkCommentsView($image_comments_permalink);
    }

    $("#nsfw-filter-button a").click(function () {
        $(this).parents("form").submit();
        return false;
    });

    $("#apps .disconnect").click(function () {
        if (confirm("Are you sure you want to disconnect this app?")) {
            var $form = $(this).parent().next("form");
            var url = $form.attr("action");
            var data = $form.serialize();
            var parent = $(this).parents("li");
            $.post(
                url,
                data,
                function (response) {
                    parent.hide("slow");
                },
                "ajax",
            );
            return false;
        } else {
            return false;
        }
    });

    // Tools: Find People / Shakes
    if ($("#content-find-people-body").length > 0) {
        $("#content-find-people-body").load(
            "/tools/find-shakes/quick-fetch-twitter",
        );
        $("#refresh-friends a").live("click", function () {
            $("#content-find-people-body").load(
                "/tools/find-shakes/quick-fetch-twitter?refresh=1",
            );
            return false;
        });
    }

    // Tools: Recommended group shakes
    if ($("#shake-categories").length > 0) {
        var RecommendedShakeCategory = function (root) {
            this.root = root;
            this.$root = $(root);
            this.fetched = false;
            this.init_events();
        };

        $.extend(RecommendedShakeCategory.prototype, {
            init_events: function () {
                this.$toggle = this.$root.find(".shake-category-toggle");
                this.$body = this.$root.find(".shake-category-body");
                this.$toggle.click($.proxy(this.click_toggle, this));
            },

            click_toggle: function () {
                if (!this.fetched) {
                    var url =
                        "/tools/find-shakes/quick-fetch-category/" +
                        this.$toggle.attr("href").replace("#", "");
                    $.get(url, $.proxy(this.populate_results, this));
                } else {
                    this.toggle();
                }
                return false;
            },

            populate_results: function (results) {
                this.fetched = true;
                this.$body.html(results);
                this.toggle();
            },

            toggle: function (result) {
                this.$root.toggleClass("shake-category-selected");
            },
        });

        $("#shake-categories .shake-category").each(function () {
            var new_category = new RecommendedShakeCategory(this);
        });
    }

    // Shake Page - change image.
    $("#shake-image-edit").hover(
        function () {
            $(this).addClass("shake-image-hover");
        },
        function () {
            $(this).removeClass("shake-image-hover");
        },
    );

    // Shake Page: choosing file to upload.
    $("#shake-image-edit input").change(function () {
        $(this).closest("form").submit();
    });

    // Shake Page: inline editing title & description:
    $(".shake-edit-title-form .cancel").click(function () {
        $(this).parents(".shake-details").find(".shake-edit-title").show();
        $(this).closest(".shake-edit-title-form").hide();
        return false;
    });

    $(".shake-edit-title").hover(
        function () {
            $(this).addClass("shake-edit-title-hover");
        },
        function () {
            $(this).removeClass("shake-edit-title-hover");
        },
    );

    $(".shake-edit-title").click(function () {
        var $title_container = $(this).closest(".shake-details");
        var url = $title_container.find("form").attr("action");
        var that = this;

        $.get(
            url,
            function (result) {
                if ("title_raw" in result) {
                    $(that).hide();
                    $title_container
                        .find(".shake-edit-title-input")
                        .val(result["title_raw"]);
                    $(that).next(".shake-edit-title-form").show();
                }
            },
            "json",
        );
    });

    $(".shake-edit-title-form").submit(function () {
        var data = $(this).serialize();
        var url = $(this).attr("action");
        var that = this;
        $.post(
            url,
            data,
            function (result) {
                if ("title" in result && "title_raw" in result) {
                    var $title_container = $(that).closest(".shake-details");
                    $title_container
                        .find(".shake-edit-title")
                        .html(result["title"])
                        .show();
                    $title_container
                        .find(".shake-edit-title-input")
                        .val(result["title_raw"]);
                    $title_container.find(".shake-edit-title-form").hide();
                }
            },
            "json",
        );
        return false;
    });

    // Shake Page: Edit Description
    $(".shake-edit-description-form .cancel").click(function () {
        $(this)
            .parents(".shake-details")
            .find(".shake-edit-description")
            .show();
        $(this).closest(".shake-edit-description-form").hide();
        return false;
    });

    $(".shake-edit-description").hover(
        function () {
            $(this).addClass("shake-edit-description-hover");
        },
        function () {
            $(this).removeClass("shake-edit-description-hover");
        },
    );

    $(".shake-edit-description").click(function () {
        var $title_container = $(this).closest(".shake-details");
        var url = $title_container.find("form").attr("action");
        var that = this;

        $.get(
            url,
            function (result) {
                if ("description_raw" in result) {
                    $(that).hide();
                    $title_container
                        .find(".shake-edit-description-input")
                        .val(result["description_raw"]);
                    $(that).next(".shake-edit-description-form").show();
                }
            },
            "json",
        );
    });

    $(".shake-edit-description-form").submit(function () {
        var data = $(this).serialize();
        var url = $(this).attr("action");
        var that = this;
        $.post(
            url,
            data,
            function (result) {
                if ("description" in result && "description_raw" in result) {
                    var $title_container = $(that).closest(".shake-details");
                    $title_container
                        .find(".shake-edit-description")
                        .html(result["description"])
                        .show();
                    $title_container
                        .find(".shake-edit-description-input")
                        .val(result["description_raw"]);
                    $title_container
                        .find(".shake-edit-description-form")
                        .hide();
                }
            },
            "json",
        );
        return false;
    });

    var $user_counts = $("#user-counts");
    if ($user_counts.length > 0) {
        var UserCounts = (function () {
            var $root = $user_counts,
                name = $root.attr("name");
            $.get(
                "/user/" + name + "/counts",
                function (result) {
                    UserCounts.display_results(result);
                },
                "json",
            );

            return {
                display_results: function (result) {
                    if ("views" in result) {
                        $root
                            .find(".views .num")
                            .html(UserCounts.format(result["views"]));
                        $root
                            .find(".saves .num")
                            .html(UserCounts.format(result["saves"]));
                        $root
                            .find(".likes .num")
                            .html(UserCounts.format(result["likes"]));
                    }
                },
                format: function (str_num) {
                    var rgx = /(\d+)(\d{3})/;
                    str_num = "" + str_num;
                    while (rgx.test(str_num)) {
                        str_num = str_num.replace(rgx, "$1" + "," + "$2");
                    }
                    return str_num;
                },
            };
        })();
    }

    /* Shake Page: Request invitation to shake */
    var RequestInvitation = function ($root) {
        this.$root = $root;
        this.init_dom();
        this.init_events();
    };

    $.extend(RequestInvitation.prototype, {
        init_dom: function () {
            this.$form = this.$root.find("form");
        },

        init_events: function () {
            this.$root.delegate(
                "form",
                "submit",
                $.proxy(this.submit_request, this),
            );
        },

        submit_request: function () {
            var url = this.$form.attr("action");
            var data = this.$form.serialize();
            $.post(url, data, $.proxy(this.process_response, this));
            return false;
        },

        process_response: function () {
            this.$root.html("<span>Ok! Request sent.</span>");
        },
    });

    var $request_invitation = $("#request-invitation");
    if ($request_invitation.length > 0) {
        request_invitation = new RequestInvitation($request_invitation);
    }

    // Button to remove from shake.
    $(".remove-from-shake").click(function () {
        $form = $(this).find("form").submit();
        return false;
    });

    //make incoming clickable (I know.)
    $(".incoming-header").click(function () {
        document.location =
            document.location.protocol +
            "//" +
            document.location.host +
            "/incoming";
    });

    // Invite Member widget for the Shake administrator.
    var InviteMember = (function () {
        var $main_module = $("#shake-invite-member");
        var $input_field = $main_module.find(".input-text");
        var $invite_button = $main_module.find(".invite-button");
        var $shake_results = $main_module.find(".shake-results");
        var $form = $main_module.find("form");
        var $title = $main_module.find("h3");
        var search_results = [];
        var last_search = "";

        $input_field.keyup(function (ev) {
            InviteMember.search_names(ev);
        });

        $form.submit(function (ev) {
            return InviteMember.submit_form();
        });

        $shake_results.click(function (ev) {
            InviteMember.select_user($(ev.target).text());
        });

        $invite_button.click(function () {
            InviteMember.send_invite();
            return false;
        });

        return {
            search_names: function () {
                if ($input_field.val() == "") {
                    this.clear_results();
                    this.clear_input();
                    return false;
                }

                // don't search again if field hasn't changed.
                if ($input_field.val() == last_search) {
                    return false;
                }

                last_search = $input_field.val();
                var data = $form.serialize();
                var that = this;
                $.post(
                    "/account/quick_name_search",
                    data,
                    function (response) {
                        if ("users" in response) {
                            that.update_results(response["users"]);
                        }
                    },
                    "json",
                );
            },

            update_results: function (users) {
                search_results = users;
                if (search_results.length == 0) {
                    this.clear_results();
                } else {
                    this.render_results();
                }
            },

            render_results: function () {
                $shake_results.html("").show();
                for (var i = 0; i < search_results.length; i++) {
                    $shake_results.append(
                        '<li><img src="' +
                            search_results[i].profile_image_url +
                            '" width="24" height="24"><span>' +
                            search_results[i].name +
                            "</span></li>",
                    );
                }
            },

            select_user: function (user_name) {
                this.clear_results();
                $input_field.val(user_name);
                $invite_button.removeAttr("disabled");
            },

            submit_form: function (ev) {
                if (
                    search_results.length == 1 &&
                    search_results[0].name == $input_field.val()
                ) {
                    this.select_user(search_results[0].name);
                    this.send_invite();
                    this.clear_results();
                }
                return false;
            },

            clear_results: function () {
                last_search = "";
                $shake_results.hide().html("");
            },

            clear_input: function () {
                $input_field.val("");
                $invite_button.attr("disabled", "disabled");
            },

            send_invite: function () {
                if ($invite_button.disabled) {
                    return false;
                } else {
                    var url = $form.attr("action");
                    var data = $form.serialize();
                    $.post(
                        url,
                        data,
                        function () {
                            InviteMember.data_sent();
                            return false;
                        },
                        "json",
                    );
                    return false;
                }
            },

            data_sent: function () {
                $title.html("Your invitation has been sent");
                this.clear_input();
                this.clear_results();
            },
        };
    })();

    /* Shake Page: Remove Members From Shake */
    var ShakeMemberList = function ($root) {
        this.$root = $root;
        this.init_events();
    };

    $.extend(ShakeMemberList.prototype, {
        init_events: function () {
            this.$root.delegate(
                ".remove-from-shake-button-link",
                "click",
                $.proxy(this.remove_from_shake, this),
            );
        },

        remove_from_shake: function (ev) {
            var $target = $(ev.target),
                $li = $target.parents("li"),
                $form = $target.next(),
                url = $form.attr("action");
            data = $form.serialize();

            if (
                confirm(
                    "Are you sure you want to remove this user from a shake? If they have notifications on an email will be sent informing them of the change.",
                )
            ) {
                $.post(url, data, $.proxy(this.process_remove, $li));
            }
            return false;
        },

        process_remove: function (response) {
            this.remove();
        },
    });

    var $shake_member_list = $("#shake-members-list");
    if ($shake_member_list.length > 0) {
        var shake_member_list = new ShakeMemberList($shake_member_list);
    }

    // support for dismissable "Vote" banner;
    // cookie naturally expires the day after the election
    var alertVote = $("#alert-vote");
    var alertVoteCookieVal = "dismiss-alert-vote=1";
    var alertVoteExpires = new Date("2024-11-06T00:00:00");
    if (
        document.cookie.indexOf(alertVoteCookieVal) === -1 &&
        new Date() < alertVoteExpires
    ) {
        alertVote.css({ display: "block" });
        alertVote.find("button").click(function () {
            document.cookie = [
                alertVoteCookieVal,
                "expires=" + alertVoteExpires.toGMTString(),
                "path=/",
            ].join("; ");
            alertVote.css({ display: "none" });
        });
    }
});
