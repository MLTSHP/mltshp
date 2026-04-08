const NSFWCover = {
    attachEvents($root) {
        // Per invocation functions that will close over the context dependent
        // variables defined above.
        function click_show_image(ev) {
            var location = document.location,
                host = location.host,
                protocol = location.protocol,
                base_path = location.protocol + "//" + location.host,
                file_path = $(ev.target).attr("href");
            $.get(
                base_path +
                    "/services/oembed?include_embed=1&url=" +
                    escape(base_path + file_path),
                (resp) => load_image(resp),
                "json",
            );
            return false;
        }

        function load_image(response) {
            var parent = $root.parent(),
                parent_height = parent.height();

            if (response["type"] === "photo") {
                parent
                    .css("min-height", parent_height + "px")
                    .html(
                        '<img class="unsized" src="' + response["url"] + '">',
                    );
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
        }

        // Attach any event handlers.
        $root.delegate("a", "click", (ev) => click_show_image(ev));
    },
};

export { NSFWCover };
