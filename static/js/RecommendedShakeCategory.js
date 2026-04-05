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
