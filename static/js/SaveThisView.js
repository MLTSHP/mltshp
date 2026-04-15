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
        const $saveThis = $(container);
        const $saveThisLink = $saveThis.find(".save-this-link");
        const $form = $saveThis.find("form");
        const $shakeIdInput = $saveThis.find(".shake-id-input");
        const $shakeSelector = $(
            "<div class='save-this-shake-selector save-this-shake-selector-loading'></div>",
        );

        // Per invocation functions that will close over the context dependent
        // variables defined above.
        function clickSaveThis(ev) {
            ev.stopPropagation();
            if ($saveThisLink.hasClass("save-this-link-multiple")) {
                showShakeSelector();
            } else {
                submitImageSave();
            }
            return false;
        }

        function clickChooseShake(ev) {
            ev.stopPropagation();
            const shakeId = ev.target.id.replace(/[^\d]+/, "");
            $shakeIdInput.val(shakeId);
            submitImageSave();
            return false;
        }

        function clickCloseSelector(ev) {
            ev.stopPropagation();
            $shakeSelector.remove();
        }

        async function showShakeSelector() {
            $saveThis.append($shakeSelector);
            $("body").one("click", (ev) => clickCloseSelector(ev));

            // Only query once per page.
            if (ShakesCache.fetch() !== false) {
                fetchAvailableShakes(ShakesCache.fetch());
            } else {
                const resp = await fetch("/account/shakes");
                const json = await resp.json();
                fetchAvailableShakes(json);
            }
        }

        function fetchAvailableShakes(response) {
            ShakesCache.store(response);
            let html = '<span class="close caret"></span><ul>';
            for (let i = 0; i < response["result"].length; i++) {
                html += `
                    <li>
                        <a class="shake-link" href="" id="save-this-shake-selector-${response["result"][i]["id"]}">
                            ${response["result"][i]["name"]}
                        </a>
                    </li>`;
            }
            html += "</ul>";
            $shakeSelector
                .removeClass("save-this-shake-selector-loading")
                .html(html);
        }

        async function submitImageSave(ev) {
            const url = $form.attr("action");
            const data = $form.serialize();
            const resp = await fetch(url, {
                method: "POST",
                body: new URLSearchParams(data),
            });
            const json = await resp.json();
            processImageSaveResponse(json);
        }

        function processImageSaveResponse(response) {
            if (response["share_key"]) {
                const count = response["count"];
                const shareKey = response["share_key"];
                const newShareKey = response["new_share_key"];
                const countString = toText(count, "Save");
                $("#save-count-amount-" + shareKey).html(countString);
                const output = `
                    <a href="/p/${newShareKey}" title="Saved It!">
                        <img width="29" height="22" src="/static/images/saved-this.svg">
                    </a>`;
                $shakeSelector.remove();
                $saveThis.html(output);
                SidebarStatsView.refreshSaves();
                StreamStatsViewRegistry.refreshSaves(shareKey);
            }
        }

        // Attach any event handlers.
        $saveThisLink.click((ev) => clickSaveThis(ev));
        $saveThis.delegate(".shake-link", "click", (ev) =>
            clickChooseShake(ev),
        );
        $saveThis.delegate(".close", "click", (ev) => clickCloseSelector(ev));
    },
};

export { SaveThisView };
