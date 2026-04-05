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
