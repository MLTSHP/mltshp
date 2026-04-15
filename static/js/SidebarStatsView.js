import { toText } from "./common.js";

/**
 * Funcionality associated with the stats shown in the sidebar of a permalink
 * page e.g. https://mltshp.com/p/1RNNC
 *
 * Defines and attaches event handlers.
 */
const DEFAULT_IMAGE_STATS = { saveCount: 0, likeCount: 0 };

let scope;

const imageStats = { ...DEFAULT_IMAGE_STATS };

// Initialise these once init() has been called with a valid scope. If never
// initialised, never referred to.
let $saveCount;
let $likeCount;

let $saveButton;
let $likeButton;
let $content;

let savesExpanded;
let likesExpanded;

// if we aren't on a permalink page, just expose a dummy public API
function noScope() {
    return scope === undefined || $(scope).length === 0;
}

const SidebarStatsView = {
    init: function (_scope) {
        scope = _scope;

        if (noScope()) {
            return;
        }

        // Set all these now that we have been provided a meaningful scope.
        $saveCount = $(".save-count", scope);
        $likeCount = $(".like-count", scope);
        imageStats.saveCount = parseInt($saveCount.html(), 10);
        imageStats.likeCount = parseInt($likeCount.html(), 10);

        $saveButton = $(".sidebar-stats-saves", scope);
        $likeButton = $(".sidebar-stats-hearts", scope);
        $content = $(".sidebar-stats-content", scope);

        savesExpanded = false;
        likesExpanded = false;

        if (imageStats.saveCount > 0) {
            this.bindSaves();
        } else {
            this.unbindSaves();
        }
        if (imageStats.likeCount > 0) {
            this.bindLikes();
            this.toggleLikes();
        } else {
            this.unbindLikes();
        }
    },

    refreshLikes: function () {
        if (noScope()) {
            return;
        }

        $likeCount = $(".like-count", scope);
        imageStats.likeCount = parseInt($likeCount.html(), 10);
        if (likesExpanded) {
            this.getLikes();
        }
        if (imageStats.likeCount > 0) {
            this.bindLikes();
        } else {
            likesExpanded = false;
            this.unbindLikes();
        }
    },

    refreshSaves: async function () {
        if (noScope()) {
            return;
        }

        $saveCount = $(".save-count", scope);
        imageStats.saveCount = parseInt($saveCount.html(), 10);
        if (savesExpanded) {
            await this.getSaves();
        }
        if (imageStats.saveCount > 0) {
            this.bindSaves();
        } else {
            savesExpanded = false;
            this.unbindSaves();
        }
    },

    bindSaves: function () {
        $saveButton.unbind("click");
        $saveButton.addClass("enable-cursor");
        $saveButton.click(function () {
            SidebarStatsView.toggleSaves();
        });
    },

    unbindSaves: function () {
        $saveButton.removeClass("enable-cursor");
        $saveButton.unbind("click");
        this.collapse();
    },

    bindLikes: function () {
        $likeButton.unbind("click");
        $likeButton.addClass("enable-cursor");
        $likeButton.click(function () {
            SidebarStatsView.toggleLikes();
        });
    },

    unbindLikes: function () {
        $likeButton.removeClass("enable-cursor");
        $likeButton.unbind("click");
        this.collapse();
    },

    toggleSaves: function () {
        likesExpanded = false;
        savesExpanded = !savesExpanded;
        if (savesExpanded) {
            $likeButton.removeClass("selected");
            $content.addClass("loading").show();
            $saveButton.addClass("selected");
            this.getSaves();
        } else {
            this.collapse();
        }
    },

    getSaves: async function () {
        const resp = await fetch(`${document.location.pathname}/saves`);
        const json = await resp.json();
        if (response["result"]) {
            SidebarStatsView.processSave(json);
        }
    },

    toggleLikes: function () {
        savesExpanded = false;
        likesExpanded = !likesExpanded;
        if (likesExpanded) {
            $saveButton.removeClass("selected");
            $content.addClass("loading").show();
            $likeButton.addClass("selected");
            this.getLikes();
        } else {
            this.collapse();
        }
    },

    getLikes: async function () {
        const resp = await fetch(document.location.pathname + "/likes");
        const json = await resp.json();
        if (json["result"]) {
            SidebarStatsView.processLike(json);
        }
    },

    processSave: function (response) {
        if (response["count"] == 0) {
            this.disable_saves();
        } else {
            $saveCount.html(toText(response["count"], "Save"));
            this.renderContent(response);
        }
    },

    processLike: function (response) {
        if (response["count"] == 0) {
            this.unbindLikes();
        } else {
            $likeCount.html(toText(response["count"], "Like"));
            this.renderContent(response);
        }
    },

    collapse: function (repsponse) {
        $likeButton.removeClass("selected");
        $saveButton.removeClass("selected");
        $content.hide();
    },

    renderContent: function (response) {
        var html = "";
        for (var i = 0, len = response["result"].length; i < len; i++) {
            var result = response["result"][i];
            var link;
            if (result["action"] == "save") {
                // for saves, we link to the saved post
                link = result["post_url"];
            } else {
                link = `/user/${result["user_name"]}`;
            }
            html += `
                <div class="user-action">
                    <a class="icon" href="${link}">
                        <img class="avatar--img" src="${result["user_profile_image_url"]}" height="20" width="20" alt="">
                    </a>
                    <a class="name" href="${link}">${result["user_name"]}</a>
                    <span class="date">${result["posted_at_friendly"]}</span>
                </div>
            `;
        }
        $content.removeClass("loading").html(html);
    },
};

export { SidebarStatsView };
