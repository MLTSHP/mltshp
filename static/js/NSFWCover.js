var NSFWCover = function ($root) {
    this.$root = $root;
    this.init();
};

$.extend(NSFWCover.prototype, {
    init: function () {
        this.$root.delegate("a", "click", $.proxy(this.click_show_image, this));
    },

    click_show_image: function (ev) {
        var location = document.location,
            host = location.host,
            protocol = location.protocol,
            base_path = location.protocol + "//" + location.host,
            file_path = $(ev.target).attr("href");
        $.get(
            base_path +
                "/services/oembed?include_embed=1&url=" +
                escape(base_path + file_path),
            $.proxy(this.load_image, this),
            "json",
        );
        return false;
    },

    load_image: function (response) {
        var parent = this.$root.parent(),
            parent_height = parent.height();

        if (response["type"] === "photo") {
            parent
                .css("min-height", parent_height + "px")
                .html('<img class="unsized" src="' + response["url"] + '">');
        } else if (response["embed_html"]) {
            parent
                .css("min-height", parent_height + "px")
                .html(
                    '<div class="data-wrapper">' +
                        response["embed_html"] +
                        "</div>",
                );
        } else if (response["type"] === "video") {
            var content = parent
                .css("min-height", parent_height + "px")
                .html(
                    response["html"].replace(
                        /<source /g,
                        '<source onerror="fallbackImage(this)" ',
                    ),
                );
            apply_hover_for_video(content.find("video.autoplay"));
        }
    },
});

export { NSFWCover };
