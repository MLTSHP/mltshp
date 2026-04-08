import { ShakesCache } from "./ShakesCache.js";
import { SidebarStatsView } from "./SidebarStatsView.js";
import { StreamStatsViewRegistry } from "./StreamStatsViewRegistry.js";
import { toText } from "./common.js";

/**
 * Functionality related to the "save this" button on posts. Sets up event
 * handlers for responding to buttons, dynamically generating and displaying
 * the drop down box to select shakes from, and handles submitting the save.
 *
 * Although a global module the attachEvents function is called once per post,
 * passing per post context as a parameter.
 */

const SaveThisView = {
    attachEvents: function (container) {
        const $save_this = $(container);
        const $save_this_link = $save_this.find(".save-this-link");
        const $form = $save_this.find("form");
        const $shake_id_input = $save_this.find(".shake-id-input");
        const $shake_selector = $(
            "<div class='save-this-shake-selector save-this-shake-selector-loading'></div>",
        );

        // Per invocation functions that will close over the context dependent
        // variables defined above.
        function click_save_this(ev) {
            ev.stopPropagation();
            if ($save_this_link.hasClass("save-this-link-multiple")) {
                show_shake_selector();
            } else {
                submit_image_save();
            }
            return false;
        }

        function click_choose_shake(ev) {
            ev.stopPropagation();
            var shake_id = ev.target.id.replace(/[^\d]+/, "");
            $shake_id_input.val(shake_id);
            submit_image_save();
            return false;
        }

        function click_close_selector(ev) {
            ev.stopPropagation();
            $shake_selector.remove();
        }

        function show_shake_selector() {
            $save_this.append($shake_selector);
            $("body").one("click", (ev) => click_close_selector(ev));

            // Only query once per page.
            if (ShakesCache.fetch() !== false) {
                fetch_available_shakes(ShakesCache.fetch());
            } else {
                $.get(
                    "/account/shakes",
                    (resp) => fetch_available_shakes(resp),
                    "json",
                );
            }
        }

        function fetch_available_shakes(response) {
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
            $shake_selector
                .removeClass("save-this-shake-selector-loading")
                .html(html);
        }

        function submit_image_save(ev) {
            var url = $form.attr("action");
            var data = $form.serialize();
            $.post(
                url,
                data,
                (resp) => process_image_save_response(resp),
                "json",
            );
        }

        function process_image_save_response(response) {
            if (response["share_key"]) {
                var count = response["count"];
                var share_key = response["share_key"];
                var new_share_key = response["new_share_key"];
                var count_string = toText(count, "Save");
                $("#save-count-amount-" + share_key).html(count_string);
                var output =
                    '<a href="/p/' +
                    new_share_key +
                    '" title="Saved It!"><img width="29" height="22" src="/static/images/saved-this.svg"></a>';
                $shake_selector.remove();
                $save_this.html(output);
                SidebarStatsView.refresh_saves();
                StreamStatsViewRegistry.refresh_saves(share_key);
            } else {
                return false;
            }
        }

        // Attach any event handlers.
        $save_this_link.click((ev) => click_save_this(ev));
        $save_this.delegate(".shake-link", "click", (ev) =>
            click_choose_shake(ev),
        );
        $save_this.delegate(".close", "click", (ev) =>
            click_close_selector(ev),
        );
    },
};

export { SaveThisView };
