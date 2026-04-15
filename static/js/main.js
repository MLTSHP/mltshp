/* For now the core JS behavior needed accross the site */

import { InviteMember } from "./InviteMember.js";
import { NewPostPanel } from "./NewPostPanel.js";
import { NotificationInvitationContainer } from "./NotificationInvitationContainer.js";
import { NSFWCover } from "./NSFWCover.js";
import { PermalinkCommentsView } from "./PermalinkCommentsView.js";
import { RecommendedShakeCategory } from "./RecommendedShakeCategory.js";
import { RequestInvitation } from "./RequestInvitation.js";
import { SaveThisView } from "./SaveThisView.js";
import { ShakeMemberList } from "./ShakeMemberList.js";
import { SidebarStatsView } from "./SidebarStatsView.js";
import { StreamStatsView } from "./StreamStatsView.js";
import { StreamStatsViewRegistry } from "./StreamStatsViewRegistry.js";
import { UserCounts } from "./UserCounts.js";
import { applyHoverForVideo, toText } from "./common.js";

NewPostPanel.attachEvents();
InviteMember.attachEvents();

function screenReaderFocus(el) {
    el.setAttribute("tabindex", "0");
    el.blur();
    el.focus();
}

$(".save-this").each(function () {
    SaveThisView.attachEvents(this);
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

// TODO this could probably be a CSS :hover
$(".image-edit-title").hover(
    function () {
        $(this).addClass("image-edit-title-hover");
    },
    function () {
        $(this).removeClass("image-edit-title-hover");
    },
);

$(".image-edit-title").click(async (ev) => {
    const $label = $(ev.currentTarget);
    const $container = $label.closest(".image-title");
    const url = $container.find("form").attr("action");

    const resp = await fetch(url);
    const json = await resp.json();

    if ("title_raw" in json) {
        $label.hide();
        const $input = $container.find(".title-input");
        $input.val(json["title_raw"]);
        $label.next(".image-edit-title-form").addClass("is-active");
        screenReaderFocus($input[0]);
    }
});

$(".image-edit-title-form").submit(async (ev) => {
    ev.preventDefault();
    ev.stopPropagation();

    const $form = $(ev.currentTarget);
    const data = $form.serialize();
    const url = $form.attr("action");
    const resp = await fetch(url, {
        method: "POST",
        body: new URLSearchParams(data),
    });
    const json = await resp.json();
    if ("title" in json && "title_raw" in json) {
        const $container = $form.closest(".image-title");
        $container.find(".image-edit-title").html(json["title"]).show();
        $container.find(".title-input").val(json["title_raw"]);
        $container.find(".image-edit-title-form").removeClass("is-active");
        if (json["title_raw"] === "") {
            $container
                .find(".the-title")
                .html("click here to edit title")
                .show();
            $container.find(".the-title").addClass("the-title-blank");
        } else {
            $container.find(".the-title").removeClass("the-title-blank");
        }
    }
});

// Inline editing of the description.
$(".description-edit-form").submit(async (ev) => {
    ev.preventDefault();
    ev.stopPropagation();

    const $form = $(ev.currentTarget);
    const data = $form.serialize();
    const url = $form.attr("action");
    const resp = await fetch(url, {
        method: "POST",
        body: new URLSearchParams(data),
    });
    const json = await resp.json();

    console.log(json);

    if ("description" in json && "description_raw" in json) {
        const $container = $form.closest(".description-edit");
        $container.find("textarea").val(json["description_raw"]);
        $container.find(".description-edit-form").hide();
        if (json["description"]) {
            $container
                .find(".the-description")
                .html(json["description"])
                .show();
            $container
                .find(".the-description")
                .removeClass("the-description-blank");
        } else {
            $container
                .find(".the-description")
                .html("click here to edit description")
                .show();
            $container
                .find(".the-description")
                .addClass("the-description-blank");
        }
    }
});

// TODO this could probably be a CSS :hover
$(".description-edit .the-description").hover(
    function () {
        $(this).addClass("the-description-hover");
    },
    function () {
        $(this).removeClass("the-description-hover");
    },
);

$(".description-edit .the-description").click(async (ev) => {
    const $label = $(ev.currentTarget);
    const $container = $label.closest(".description-edit");
    const url = $container.find("form").attr("action");
    const resp = await fetch(url);
    const json = await resp.json();

    if ("description_raw" in json) {
        $label.hide();
        const $textarea = $container.find(".description-edit-textarea");
        $textarea.val(json["description_raw"]);
        $label.next(".description-edit-form").show();
        screenReaderFocus($textarea[0]);
    }
});

$(".description-edit .cancel").click(function () {
    $(this).closest(".description-edit").find(".the-description").show();
    $(this).closest(".description-edit-form").hide();
    return false;
});

// Inline editing of the alt text.
$(".alt-text-edit-form").submit(async (ev) => {
    ev.preventDefault();
    ev.stopPropagation();

    const $form = $(ev.currentTarget);
    const data = $form.serialize();
    const url = $form.attr("action");
    const resp = await fetch(url, {
        method: "POST",
        body: new URLSearchParams(data),
    });
    const json = await resp.json();
    if ("alt_text" in json && "alt_text_raw" in json) {
        var $container = $form.closest(".alt-text-edit");
        if (json["alt_text"]) {
            $container
                .removeClass("alt-text--blank")
                .find(".the-alt-text")
                .html(json["alt_text"]);
        } else {
            $container
                .addClass("alt-text--blank")
                .find(".the-alt-text")
                .html("add some alt text");
        }
        $container
            .removeClass("alt-text--hidden")
            .removeClass("alt-text--editing")
            .find("textarea")
            .val(json["alt_text_raw"]);
        screenReaderFocus($container.find(".the-alt-text")[0]);
    }
});

// TODO this could probably be a CSS :hover
$(".alt-text-edit .the-alt-text").hover(
    function () {
        $(this).addClass("the-alt-text-hover");
    },
    function () {
        $(this).removeClass("the-alt-text-hover");
    },
);

$(".alt-text-edit .the-alt-text").click(async (ev) => {
    const $label = $(ev.currentTarget);
    const $container = $label.closest(".alt-text-edit");
    const url = $container.find("form").attr("action");
    const resp = await fetch(url);
    const json = await resp.json();

    if ("alt_text_raw" in json) {
        $label.closest(".alt-text-edit").addClass("alt-text--editing");
        const $textarea = $container.find(".alt-text-edit-textarea");
        $textarea.val(json["alt_text_raw"]);
        screenReaderFocus($textarea[0]);
    }
});

$(".alt-text-edit .cancel").click(function () {
    $(this)
        .closest(".alt-text-edit")
        .removeClass("alt-text--hidden")
        .removeClass("alt-text--editing");
    return false;
});

$(".alt-text-toggle").click(function () {
    let $alt = $(this).closest(".alt-text");
    $alt.toggleClass("alt-text--hidden");
    if (!$alt.hasClass("alt-text--hidden")) {
        screenReaderFocus($alt.find(".the-alt-text")[0]);
    }
});

$(".delete-from-shakes-form").click(function () {
    return confirm("Are you sure you want to remove it?");
});

/* Like / Unlike button */
$(".like-button, .unlike-button").click(async (ev) => {
    ev.preventDefault();
    ev.stopPropagation();

    const $form = $(ev.currentTarget).parents("form");
    const $buttons = $form.children("button");
    const url = $form.attr("action");
    const data = $form.serialize() + "&json=1"; // TODO json suffix required?
    const resp = await fetch(url, {
        method: "POST",
        body: new URLSearchParams(data),
    });
    const json = await resp.json();

    if (json["error"]) {
        return;
    }

    const count = json["count"];
    const shareKey = json["share_key"];
    const countString = toText(count, "Like");
    $("#like-count-amount-" + shareKey).html(countString);
    if (json["like"] === true) {
        $form.attr("action", `/p/${shareKey}/unlike`);
    } else {
        $form.attr("action", `/p/${shareKey}/like`);
    }
    $buttons.toggleClass("is-active");
    SidebarStatsView.refreshLikes();
    StreamStatsViewRegistry.refreshLikes(shareKey);
});

SidebarStatsView.init("#sidebar-stats");

$(".image-content").each(function () {
    const $image_content = $(this),
        $image_footer = $image_content.find(".image-content-footer"),
        $nsfw_cover = $image_content.find(".nsfw-cover");
    const stream_stats_view = new StreamStatsView($image_footer);
    StreamStatsViewRegistry.register(stream_stats_view);
    if ($nsfw_cover.length > 0) {
        NSFWCover.attachEvents($nsfw_cover);
    }
});

applyHoverForVideo($(".image-content video.autoplay"));

/* Open / close notification boxes */
$(document).on("click", ".notification-block-hd", function () {
    $(this).next().toggle();
});

/* User follow module */
$(document).on("click", ".user-follow .submit-form", async (ev) => {
    ev.preventDefault();
    ev.stopPropagation();

    const $button = $(ev.currentTarget);
    const $container = $(button).parents(".user-follow");
    const $form = $container.find("form");
    const url = $form.attr("action");
    const data = $form.serialize() + "&json=1"; // TODO json suffix required?
    const resp = await fetch(url, {
        method: "POST",
        body: URLSearchParams(data),
    });
    const json = await resp.json();

    if (json["error"]) {
        return false;
    }

    if (json["subscription_status"] == true) {
        $form.attr("action", url.replace("subscribe", "unsubscribe"));
        $button
            .text("- Unfollow")
            .addClass("btn-warning")
            .removeClass("btn-secondary");
    } else {
        $form.attr("action", url.replace("unsubscribe", "subscribe"));
        $button
            .text("+ Follow")
            .addClass("btn-secondary")
            .removeClass("btn-warning");
    }
});

$(document).on("click", ".notification-close", async (ev) => {
    ev.preventDefault();
    ev.stopPropagation();

    const $button = $(ev.currentTarget);
    const $notification = $button.parent(".notification");
    const $notificationBlock = $button.parents(".notification-block");
    const $notificationBlockHd = $notificationBlock.find(
        ".notification-block-hd",
    );
    const id = $button.attr("id").replace(/[^\d]+/, "");
    const url = `/account/clear-notification?type=single&id=${id}`;
    // TODO data should be sent as body for POST?
    const resp = await fetch(url, { method: "POST" });

    $notification.remove();
    const html = $notificationBlockHd.html();
    const count = html.replace(/[^\d]+/, "");
    var newCount = parseInt(count, 10) - 1;
    if (newCount == 0) {
        $notificationBlockHd.html("You have 0 new followers");
        $notificationBlock.find(".clear-all").remove();
    } else {
        $notificationBlockHd.html(html.replace(/[\d]+/, newCount));
    }
});

$(document).on("click", ".notification-block .clear-all a", async (ev) => {
    ev.preventDefault();
    ev.stopPropagation();

    const $link = $(ev.currentTarget);
    const url = $link.attr("href");
    const $notificationBlock = $link.parents(".notification-block");
    const resp = await fetch(url, { method: "POST" });
    const json = await resp.json();

    if (json["error"]) {
        return false;
    }

    $notificationBlock.find(".notification-block-hd").html(resp["response"]);
    $notificationBlock.find(".notification-block-bd").html("").toggle();

    return false;
});

/* Notification block: invitations: */
$(document).on("submit", "#notifcation-block-invitations form", async (ev) => {
    ev.preventDefault();
    ev.stopPropagation();

    const $form = $(ev.currentTarget);
    const data = $form.serialize();
    const url = $form.attr("action");
    const resp = await fetch(url, {
        method: "POST",
        body: new URLSearchParams(data),
    });
    const json = await resp.json();

    if (json["error"]) {
        $form.find(".main-message").html(`<p>${response["error"]}</p>`);
    } else {
        if (json["count"] == 0) {
            $form.find("input").hide();
            $("#invitation-count-text").html(`${json["count"]} invitations`);
            $form.find(".main-message").html("<p>Thanks!</p>");
        } else {
            const invitation_text =
                json["count"] == 1 ? "invitation" : "invitations";
            $("#invitation-count-text").html(
                `${json["count"]} ${invitation_text}`,
            );
            $form.find(".main-message").html(json["message"]);
            $("#email_address").val("");
        }
    }
});

/* Notification block: shake invitations: */
$(document).on(
    "submit",
    "#notifcation-block-shakeinvitation form",
    async (ev) => {
        ev.preventDefault();
        ev.stopPropagation();

        const $form = $(ev.currentTarget);
        const data = $form.serialize();
        const url = $form.attr("action");
        const $block = $form.parents(".notification");
        const $header = $(
            "#notifcation-block-shakeinvitation .notification-block-hd",
        );
        const resp = await fetch(url, {
            method: "POST",
            body: new URLSearchParams(data),
        });
        const json = await resp.json();

        if (!json["error"]) {
            $block.remove();
            // we update the header differently when presenting only one
            // invitation on the shake page itself.
            if ($header.hasClass("invitation-single")) {
                $header.html("Got it.");
            } else {
                const invitationText =
                    json["count"] == 1 ? "invitation" : "invitations";
                $header.html(`${json["count"]} new shake ${invitationText}`);
            }
        }
    },
);

const initNotificationInvitationRequest = function () {
    const $notificationInvitationRequest = $(
        "#notification-block-invitation-request",
    );
    if ($notificationInvitationRequest.length > 0) {
        NotificationInvitationContainer.populate(
            $notificationInvitationRequest,
        );
    }
};
initNotificationInvitationRequest();

// Expand all notifications.
$("#notification-block-aggregate").click(function () {
    $(this).find(".notification-block-hd").html("Loading...");
    $.get("/account/quick-notifications", function (response) {
        $("#notification-block-aggregate").hide().after(response);
        initNotificationInvitationRequest();
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
const $siteNav = $("#site-nav");
let siteNavExpanded = false;
$("#site-nav .site-nav--toggle").click(function (event) {
    event.stopPropagation();
    if (siteNavExpanded == false) {
        siteNavExpanded = true;
        $siteNav.addClass("is-expanded");
        $("body").one("click", function () {
            $siteNav.removeClass("is-expanded");
            siteNavExpanded = false;
        });
    } else {
        $siteNav.removeClass("is-expanded");
        $("body").unbind("click");
        siteNavExpanded = false;
    }
});

$("#site-nav .site-nav--list").click(function (event) {
    event.stopPropagation();
});

/* Choose a shake dropdown */
const $chooseAShake = $("#choose-a-shake");
let shakeExpanded = false;
$("#choose-a-shake .choose-a-shake--toggle").click(function (event) {
    event.stopPropagation();
    if (shakeExpanded == false) {
        shakeExpanded = true;
        $chooseAShake.addClass("is-expanded");
        $("body").one("click", function () {
            $chooseAShake.removeClass("is-expanded");
            shakeExpanded = false;
        });
    } else {
        $chooseAShake.removeClass("is-expanded");
        $("body").unbind("click");
        shakeExpanded = false;
    }
});

$("#choose-a-shake .choose-a-shake--dropdown").click(function (event) {
    event.stopPropagation();
});

/* Conversations - mute this button */
$(".mute-this-conversation").click(async (ev) => {
    ev.preventDefault();
    ev.stopPropagation();

    const $button = $(ev.currentTarget);
    const $form = $button.next(".mute-this-conversation-form");
    const url = $form.attr("action");
    const data = $form.serialize();
    const $conversation = $button.parents(".conversation");
    await fetch(url, { method: "POST", body: new URLSearchParams(data) });
    $conversation.fadeOut("slow");
});

const $imageCommentsPermalink = $("#image-comments-permalink");
if ($imageCommentsPermalink.length > 0) {
    PermalinkCommentsView.addEvents($imageCommentsPermalink);
}

$("#nsfw-filter-button a").click(function () {
    $(this).parents("form").submit();
    return false;
});

$("#apps .disconnect").click(async (ev) => {
    ev.preventDefault();
    ev.stopPropagation();

    if (confirm("Are you sure you want to disconnect this app?")) {
        const $button = $(ev.currentTarget);
        const $form = $button.parent().next("form");
        const url = $form.attr("action");
        const data = $form.serialize();
        const parent = $button.parents("li");
        await fetch(url, { method: "POST", body: new URLSearchParams(data) });
        parent.hide("slow");
    }
});

// Tools: Recommended group shakes
if ($("#shake-categories").length > 0) {
    $("#shake-categories .shake-category").each(function () {
        RecommendedShakeCategory.attachEvents(this);
    });
}

// Shake Page - change image.
// TODO this could probably be a CSS :hover
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

// TODO this could probably be a CSS :hover
$(".shake-edit-title").hover(
    function () {
        $(this).addClass("shake-edit-title-hover");
    },
    function () {
        $(this).removeClass("shake-edit-title-hover");
    },
);

$(".shake-edit-title").click(async (ev) => {
    const $label = $(ev.currentTarget);
    const $container = $label.closest(".shake-details");
    const url = $container.find("form").attr("action");
    const resp = await fetch(url);
    const json = await resp.json();

    if ("title_raw" in json) {
        $label.hide();
        $container.find(".shake-edit-title-input").val(json["title_raw"]);
        $label.next(".shake-edit-title-form").show();
    }
});

$(".shake-edit-title-form").submit(async (ev) => {
    ev.preventDefault();
    ev.stopPropagation();

    const $form = $(ev.currentTarget);
    const data = $form.serialize();
    const url = $form.attr("action");
    const resp = await fetch(url, {
        method: "POST",
        body: new URLSearchParams(data),
    });
    const json = await resp.json();

    if ("title" in json && "title_raw" in json) {
        const $container = $form.closest(".shake-details");
        $container.find(".shake-edit-title").html(json["title"]).show();
        $container.find(".shake-edit-title-input").val(json["title_raw"]);
        $container.find(".shake-edit-title-form").hide();
    }
});

// Shake Page: Edit Description
$(".shake-edit-description-form .cancel").click((ev) => {
    const $form = $(ev.currentTarget);
    $form.parents(".shake-details").find(".shake-edit-description").show();
    $form.closest(".shake-edit-description-form").hide();
    return false;
});

// TODO this could probably be a CSS :hover
$(".shake-edit-description").hover(
    function () {
        $(this).addClass("shake-edit-description-hover");
    },
    function () {
        $(this).removeClass("shake-edit-description-hover");
    },
);

$(".shake-edit-description").click(async (ev) => {
    const $label = $(ev.currentTarget);
    // Form is sibling of label, so find the enclosing container ...
    const $container = $label.closest(".shake-details");

    // ... then navigate down to the form
    const url = $container.find("form").attr("action");
    const resp = await fetch(url);
    const json = await resp.json();

    if ("description_raw" in json) {
        $label.hide();
        $container
            .find(".shake-edit-description-input")
            .val(json["description_raw"]);
        $label.next(".shake-edit-description-form").show();
    }
});

$(".shake-edit-description-form").submit(async (ev) => {
    ev.preventDefault();
    ev.stopPropagation();

    const $form = $(ev.currentTarget);
    const data = $form.serialize();
    const url = $form.attr("action");

    const resp = await fetch(url, {
        method: "POST",
        body: new URLSearchParams(data),
    });
    const json = await resp.json();
    if ("description" in json && "description_raw" in json) {
        const $container = $form.closest(".shake-details");
        $container
            .find(".shake-edit-description")
            .html(json["description"])
            .show();
        $container
            .find(".shake-edit-description-input")
            .val(json["description_raw"]);
        $container.find(".shake-edit-description-form").hide();
    }
});

const $userCountsPanel = $("#user-counts");
if ($userCountsPanel.length > 0) {
    UserCounts.populate($userCountsPanel);
}

/* Shake Page: Request invitation to join shake */
const $requestInvitationPanel = $("#request-invitation");
if ($requestInvitationPanel.length > 0) {
    RequestInvitation.attachEvents($requestInvitationPanel);
}

// Button to remove user from shake membership.
$(".remove-from-shake").click(function () {
    $form = $(this).find("form").submit();
    return false;
});

//make incoming clickable (I know.)
$(".incoming-header").click(function () {
    document.location = `${document.location.protocol}//${document.location.host}/incoming`;
});

/* Shake Page: Remove Members From Shake */
const $shakeMembersList = $("#shake-members-list");
if ($shakeMembersList.length > 0) {
    ShakeMemberList.attachEvents($shakeMembersList);
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
