/* For now the core JS behavior needed accross the site */

import { SaveThisView } from "./SaveThisView.js";
import { SidebarStatsView } from "./SidebarStatsView.js";
import { StreamStatsView } from "./StreamStatsView.js";
import { StreamStatsViewRegistry } from "./StreamStatsViewRegistry.js";
import { NSFWCover } from "./NSFWCover.js";
import { NewPostPanel } from "./NewPostPanel.js";
import { InviteMember } from "./InviteMember.js";
import { UserCounts } from "./UserCounts.js";

var to_text = function (num, base) {
    return num == 1
        ? num + " " + "<span>" + base + "</span>"
        : num + " " + "<span>" + base + "s" + "</span>";
};

function screen_reader_focus(el) {
    el.setAttribute("tabindex", "0");
    el.blur();
    el.focus();
}

$(".save-this").each(function () {
    var save_this_view = new SaveThisView(this);
});

// when we hit enter on a form, we want to submit it even though we don't have
// an type="submit" input available, since we're using a styled button.
const $sign_in_form = $("#sign-in-form");
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
                $title_container.find(".title-input").val(result["title_raw"]);
                var $input = $title_container.find(".title-input");
                $(that).next(".image-edit-title-form").addClass("is-active");
                screen_reader_focus($input[0]);
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
                $title_container.find(".title-input").val(result["title_raw"]);
                $title_container
                    .find(".image-edit-title-form")
                    .removeClass("is-active");
                if (result["title_raw"] === "") {
                    $title_container
                        .find(".the-title")
                        .html("click here to edit title")
                        .show();
                    $title_container
                        .find(".the-title")
                        .addClass("the-title-blank");
                } else {
                    $title_container
                        .find(".the-title")
                        .removeClass("the-title-blank");
                }
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
                $description_container.find(".description-edit-form").hide();
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
                $(that).closest(".alt-text-edit").addClass("alt-text--editing");
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

SidebarStatsView.init();

function apply_hover_for_video(sel) {
    sel.hover(function () {
        if (this.hasAttribute("controls")) {
            this.removeAttribute("controls");
        } else {
            this.setAttribute("controls", "controls");
        }
    });
}

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
$(document).on("click", ".notification-block-hd", function () {
    $(this).next().toggle();
});

/* User follow module */
$(document).on("click", ".user-follow .submit-form", function () {
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

$(document).on("click", ".notification-close", function () {
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
                $notification_block_hd.html(html.replace(/[\d]+/, new_count));
            }
        },
        "json",
    );
    return false;
});

$(document).on("click", ".notification-block .clear-all a", function () {
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
$(document).on("submit", "#notifcation-block-invitations form", function () {
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
                        response["count"] == 1 ? "invitation" : "invitations";
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
$(document).on(
    "submit",
    "#notifcation-block-shakeinvitation form",
    function () {
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
    },
);

var init_notification_invitation_request = function () {
    const $notification_invitation_request = $(
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
const $site_nav = $("#site-nav");
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
const $choose_a_shake = $("#choose-a-shake");
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

// Tools: Recommended group shakes
if ($("#shake-categories").length > 0) {
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
    $(this).parents(".shake-details").find(".shake-edit-description").show();
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
                $title_container.find(".shake-edit-description-form").hide();
            }
        },
        "json",
    );
    return false;
});

var $user_counts = $("#user-counts");
if ($user_counts.length > 0) {
    UserCounts.populate($user_counts);
}

/* Shake Page: Request invitation to shake */
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

/* Shake Page: Remove Members From Shake */
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

// Support for sticky site header
const $siteHeader = $(".site-header");
if ($siteHeader.length > 0) {
    let lastScrollY = window.scrollY;
    const scrollHandler = () => {
        if (!$siteHeader.hasClass("docked")) {
            if (window.scrollY > 120) {
                $siteHeader.addClass("docked");
            }
        } else {
            if (window.scrollY <= 120) {
                $siteHeader.removeClass("docked visible hidden");
            }
        }
        if ($siteHeader.hasClass("docked")) {
            const isVisible = $siteHeader.hasClass("visible");
            if (!isVisible && window.scrollY < lastScrollY) {
                // triggering delta can be 1px
                $siteHeader.addClass("visible");
                $siteHeader.removeClass("hidden");
            } else if (isVisible && window.scrollY > lastScrollY + 20) {
                // triggering delta must be ~20px
                $siteHeader.removeClass("visible");
                $siteHeader.addClass("hidden");
            }
        }
        lastScrollY = window.scrollY;
    };
    $(window).on("scroll", scrollHandler);
}
