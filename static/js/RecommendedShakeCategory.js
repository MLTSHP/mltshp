/**
 * Functionality associated with the shake categories accordian control on the
 * find shakes page e.g. https://mltshp.com/tools/find-shakes
 *
 * Adds event listener to toggle category open and closed, and load shakes from
 * the server upon first opening of a category.
 */

const RecommendedShakeCategory = {
    attachEvents: function (root) {
        const $root = $(root);
        const $toggle = $root.find(".shake-category-toggle");
        const $body = $root.find(".shake-category-body");

        let fetched = false;

        // Per invocation functions that will close over the context dependent
        // variables defined above.
        async function clickToggle() {
            if (!fetched) {
                const url =
                    "/tools/find-shakes/quick-fetch-category/" +
                    $toggle.attr("href").replace("#", "");

                const resp = await fetch(url);
                populateResults(await resp.text());
            } else {
                toggle();
            }
            return false;
        }

        function populateResults(results) {
            fetched = true;
            $body.html(results);
            toggle();
        }

        function toggle(result) {
            $root.toggleClass("shake-category-selected");
        }

        // Attach any event handlers.
        $toggle.click(() => clickToggle());
    },
};

export { RecommendedShakeCategory };
