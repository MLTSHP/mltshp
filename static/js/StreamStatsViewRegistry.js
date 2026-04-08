/**
 * A singleton registry of StreamStatsView objects. These objects are created
 * one per post on a page, and contain logic and event handlers for stats and
 * comments of each individual post.
 */

const files_on_page = {};

const get_view = function (share_key) {
    return files_on_page[share_key];
};

var StreamStatsViewRegistry = {
    register: function (view) {
        files_on_page[view.share_key] = view;
    },

    refresh_likes: function (share_key) {
        var view = get_view(share_key);
        if (view !== undefined) {
            view.refresh_likes();
        }
    },

    refresh_saves: function (share_key) {
        var view = get_view(share_key);
        if (view !== undefined) {
            view.refresh_saves();
        }
    },
};

export { StreamStatsViewRegistry };
