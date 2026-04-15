import { applyHoverForVideo } from "./common.js";

/**
 * Functionality associated with NSFW covers. Called on to attach event
 * handlers to any posts that the server has generated a NSFW cover for.
 */

const NSFWCover = {
    attachEvents($root) {
        // Per invocation functions that will close over the context dependent
        // variables defined above.
        function clickShowImage(ev) {
            var location = document.location,
                basePath = location.protocol + "//" + location.host,
                filePath = $(ev.target).attr("href");
            // Going to leave this as a jquery get rather than migrate to fetch
            // right away. The two implementations behave differently and only
            // the existing method seems to work with /services/oembed
            $.get(
                basePath +
                    "/services/oembed?include_embed=1&url=" +
                    escape(basePath + filePath),
                (resp) => loadImage(resp),
                "json",
            );
            return false;
        }

        function loadImage(response) {
            var parent = $root.parent(),
                parentHeight = parent.height();

            if (response["type"] === "photo") {
                parent
                    .css("min-height", parentHeight + "px")
                    .html(
                        '<img class="unsized" src="' + response["url"] + '">',
                    );
            } else if (response["embed_html"]) {
                parent
                    .css("min-height", parentHeight + "px")
                    .html(
                        '<div class="data-wrapper">' +
                            response["embed_html"] +
                            "</div>",
                    );
            } else if (response["type"] === "video") {
                var content = parent
                    .css("min-height", parentHeight + "px")
                    .html(
                        response["html"].replace(
                            /<source /g,
                            '<source onerror="fallbackImage(this)" ',
                        ),
                    );
                applyHoverForVideo(content.find("video.autoplay"));
            }
        }

        // Attach any event handlers.
        $root.delegate("a", "click", (ev) => clickShowImage(ev));
    },
};

export { NSFWCover };
