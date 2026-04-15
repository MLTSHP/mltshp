/**
 * A singleton registry of StreamStatsView objects. These objects are created
 * one per post on a page, and contain logic and event handlers for stats and
 * comments of each individual post.
 */

const filesOnPage = {};

const getView = function (shareKey) {
    return filesOnPage[shareKey];
};

const StreamStatsViewRegistry = {
    register: function (view) {
        filesOnPage[view.shareKey] = view;
    },

    refreshLikes: function (shareKey) {
        const view = getView(shareKey);
        if (view !== undefined) {
            view.refreshLikes();
        }
    },

    refreshSaves: function (shareKey) {
        const view = getView(shareKey);
        if (view !== undefined) {
            view.refreshSaves();
        }
    },
};

export { StreamStatsViewRegistry };
