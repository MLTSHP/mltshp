const DEFAULT_IMAGE_STATS = { save_count: 0, like_count: 0 };

var SidebarStatsView = (function (scope) {
    // if we aren't on a permalink page, just expose a dummy public API
    if ($(scope).length == 0) {
        return {
            init: function () {},
            refresh_likes: function () {},
            refresh_saves: function () {},
        };
    }

    const image_stats = { ...DEFAULT_IMAGE_STATS };
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
                var result = response["result"][i];
                var link;
                if (result["action"] == "save") {
                    // for saves, we link to the saved post
                    link = result["post_url"];
                } else {
                    link = "/user/" + result["user_name"];
                }
                html += '<div class="user-action">';
                html += '<a class="icon" href="' + link + '">';
                html +=
                    '<img class="avatar--img" src="' +
                    result["user_profile_image_url"] +
                    '" height="20" width="20" alt=""></a>';
                html +=
                    '<a class="name" href="' +
                    link +
                    '">' +
                    result["user_name"] +
                    "</a>";
                html +=
                    '<span class="date">' +
                    result["posted_at_friendly"] +
                    "</span>";
                html += "</div>";
            }
            $content.removeClass("loading").html(html);
        },
    };
})("#sidebar-stats");

export { SidebarStatsView };
