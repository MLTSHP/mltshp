import { ShakesCache } from "./ShakesCache.js";

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

export { SaveThisView };
