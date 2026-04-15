import { setCaret } from "./common.js";

/**
 * Functionality associated with the stats and comments section of each post on
 * a list page e.g. https://mltshp.com/incoming,
 * https://mltshp.com/CurrentListening, or https://mltshp.com/user/LocalStain
 *
 * Attaches event handlers to "likes", "comments", and "saves" tabs, as well as
 * event handlers and processing for replaying, deleting, and adding commetns.
 * One instance created per post on the page, and managed by the global
 * StreamStatsViewRegistry module.
 */

class StreamStatsView {
    constructor($imageContentFooter) {
        this.$imageContentFooter = $imageContentFooter;
        this.shareKey = this.$imageContentFooter
            .attr("id")
            .replace("image-content-footer-", "");
        this.canSubmitComments = true;
        this.initDom();
        this.initEvents();
    }

    initDom() {
        this.$likesButton = this.$imageContentFooter.find(".likes");
        this.$savesButton = this.$imageContentFooter.find(".saves");
        this.$commentsButton = this.$imageContentFooter.find(".comments");
        this.$inlineDetails = this.$imageContentFooter.find(".inline-details");
        this.initCommentDom();
    }

    initCommentDom() {
        this.$postCommentInline = this.$inlineDetails.find(
            ".post-comment-inline",
        );
        this.$commentForm = this.$inlineDetails.find(".post-comment-form");
        this.$commentTextarea = this.$inlineDetails.find("textarea");
        this.$submitCommentButton = this.$inlineDetails.find(
            ".submit-comment-button",
        );
        this.$showMoreComments = this.$inlineDetails.find(
            ".show-more-comments",
        );
        this.$comment = this.$inlineDetails.find(".comment");
        this.$replyTo = this.$inlineDetails.find(".reply-to");
        this.$delete = this.$inlineDetails.find(".delete");
    }

    initEvents() {
        this.$likesButton.click((ev) => this.clickLike(ev));
        this.$savesButton.click((ev) => this.clickSaves(ev));
        this.$commentsButton.click((ev) => this.clickComments(ev));
        this.initCommentEvents();
    }

    initCommentEvents() {
        this.$commentTextarea.click((ev) => this.clickCommentTextarea(ev));
        this.$showMoreComments.click((ev) => this.clickMoreComments(ev));
        this.$replyTo.click((ev) => this.clickReplyTo(ev));
        this.$delete.click((ev) => this.clickDelete(ev));
        // Fix for Webkit bug where textarea looses focus incorrectly on mouseup.
        // http://code.google.com/p/chromium/issues/detail?id=4505
        this.$commentTextarea.mouseup(function (ev) {
            ev.preventDefault();
        });
        this.$commentForm.submit((ev) => this.submitComment(ev));
    }

    // Removes selected state from all tabs.
    clearTabSelection() {
        this.$likesButton.removeClass("selected");
        this.$savesButton.removeClass("selected");
        this.$commentsButton.removeClass("selected");
    }

    // Start the "loading" state transition.
    startLoading() {
        this.$inlineDetails.addClass("inline-details-loading").html("").show();
    }

    user_html(data) {
        let html = "";
        for (let i = 0; i < data.result.length; i++) {
            const result = data.result[i];
            const link =
                result["action"] == "save"
                    ? result["post_url"]
                    : `/user/${result["user_name"]}`;

            html += `
                <a href="${link}">
                    <img class="avatar--img" src="${result["user_profile_image_url"]}" height="20" width="20" alt="">
                    <span class="name">${result["user_name"]}</span>
                </a>
            `;
        }
        return html;
    }

    clickLike(ev) {
        ev.preventDefault();
        ev.stopPropagation();

        if (this.$likesButton.hasClass("selected")) {
            this.clearTabSelection();
            this.$inlineDetails.hide();
        }

        this.clearTabSelection();
        this.$likesButton.addClass("selected");
        this.startLoading();
        this.loadLikes();
    }

    async loadLikes() {
        const url = `/p/${this.shareKey}/likes`;
        const resp = await fetch(url);
        const json = await resp.json();
        this.processLikeResponse(json);
    }

    processLikeResponse(data) {
        const html = `<div class="user-saves-likes">${this.user_html(data)}</div>`;
        this.$inlineDetails.html(html);
    }

    clickSaves(ev) {
        ev.preventDefault();
        ev.stopPropagation();

        if (this.$savesButton.hasClass("selected")) {
            this.clearTabSelection();
            this.$inlineDetails.hide();
        }

        this.clearTabSelection();
        this.$savesButton.addClass("selected");
        this.startLoading();
        this.loadSaves();
    }

    async loadSaves() {
        const url = `/p/${this.shareKey}/saves`;
        const resp = await fetch(url);
        const json = await resp.json();
        this.processLikeResponse(json);
    }

    async clickComments(ev) {
        ev.preventDefault();
        ev.stopPropagation();

        if (this.$commentsButton.hasClass("selected")) {
            this.clearTabSelection();
            this.$inlineDetails.hide();
        }

        this.clearTabSelection();
        this.$commentsButton.addClass("selected");
        this.startLoading();
        const url = `/p/${this.shareKey}/quick-comments`;
        const resp = await fetch(url);
        const json = await resp.json();
        this.processCommentsResponse(json);
    }

    clickMoreComments(ev) {
        ev.preventDefault();
        ev.stopPropagation();

        this.$comment.show();
        this.$showMoreComments.hide();
    }

    processCommentsResponse(data) {
        this.canSubmitComments = true;
        if (data["result"] == "ok") {
            this.$commentsButton.find("a").html(data["count"]);
            this.$inlineDetails.html(data["html"]);
            this.initCommentDom();
            this.initCommentEvents();
        }
    }

    clickReplyTo(ev) {
        ev.preventDefault();
        ev.stopPropagation();

        this.clickCommentTextarea(ev);
        const username = $(ev.target)
            .parents(".comment")
            .find(".username")
            .html();
        const usernameClean = username.replace(/[^a-zA-Z0-9_\-]+/g, "");
        const currentText = this.$commentTextarea.val();
        this.$commentTextarea.val(currentText + "@" + usernameClean + " ");
        setCaret(this.$commentTextarea.get(0));
    }

    async clickDelete(ev) {
        ev.preventDefault();
        ev.stopPropagation();

        const $deleteForm = $(`#${ev.target.id}-form`),
            url = $deleteForm.attr("action"),
            data = $deleteForm.serialize();
        if (confirm("Are you sure you want to delete this?")) {
            const resp = await fetch(url, {
                method: "POST",
                body: new URLSearchParams(data),
            });
            const json = await resp.json();
            this.processCommentsResponse(json);
        }
    }

    async submitComment(ev) {
        ev.preventDefault();
        ev.stopPropagation();

        if (this.canSubmitComments === false) {
            return;
        }
        this.canSubmitComments = false;
        const url = this.$commentForm.attr("action");
        const data = this.$commentForm.serialize();
        const resp = await fetch(url, {
            method: "POST",
            body: new URLSearchParams(data),
        });
        const json = await resp.json();
        this.processCommentsResponse(json);
    }

    clickCommentTextarea(ev) {
        this.$postCommentInline.addClass("post-comment-inline-expanded");
        if (this.$commentTextarea.val().indexOf("Write a comment") === 0) {
            this.$commentTextarea.val("");
        }
        this.clickMoreComments(ev);
        this.$commentTextarea.css("min-height", "60px");
    }

    refreshLikes() {
        if (this.$likesButton.hasClass("selected")) {
            this.loadLikes();
        }
    }

    refreshSaves() {
        if (this.$savesButton.hasClass("selected")) {
            this.loadSaves();
        }
    }
}

export { StreamStatsView };
