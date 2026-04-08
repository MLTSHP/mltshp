/**
 * Functionality to update the statistics (views, saves, likes) in the sidebar
 * of a user page e.g. https://mltshp.com/user/epski
 *
 * Populates latest values from a backend API call on page load. Unsure why not
 * just server side generated.
 */

function format(str_num) {
    return Number.parseInt(str_num).toLocaleString();
}

function formatBrief(str_num) {
    // Format number in a way that won't need excessive space to
    // display. Abbreviate with suffixes and limit to one
    // decimal place.

    const n = parseInt(str_num, 10);

    // Handle garbage input (somewhat) gracefully.
    if (Number.isNaN(n)) {
        return "0";
    }

    // Anything up to and including 9,999 return verbatim as
    // we've got four characters minimum to play with.
    if (n < 10000) {
        return n.toLocaleString();
    }

    const suffixes = [
        { threshold: 1e12, suffix: "T" },
        { threshold: 1e9, suffix: "B" },
        { threshold: 1e6, suffix: "M" },
        { threshold: 1e3, suffix: "K" },
    ];

    for (const { threshold, suffix } of suffixes) {
        // Iterate until we find a suffix that can handle this
        // value.
        if (n >= threshold) {
            // Truncate to 1 decimal place.
            const truncated = Math.floor((n / threshold) * 10) / 10;

            // If the decimal part is 0 trim it.
            if (truncated % 1 === 0) {
                return truncated.toFixed(0) + suffix;
            } else {
                return truncated.toFixed(1) + suffix;
            }
        }
    }

    return n.toLocaleString();
}

var $root;

const UserCounts = {
    populate: function ($user_counts) {
        $root = $user_counts;
        var name = $root.attr("name");

        function display_results(result) {
            if ("views" in result) {
                $root
                    .find(".views")
                    .attr("title", format(result["views"]) + " views")
                    .find(".num")
                    .html(formatBrief(result["views"]));
                $root
                    .find(".saves")
                    .attr("title", format(result["saves"]) + " saves")
                    .find(".num")
                    .html(formatBrief(result["saves"]));
                $root
                    .find(".likes")
                    .attr("title", format(result["likes"]) + " likes")
                    .find(".num")
                    .html(formatBrief(result["likes"]));
            }
        }

        $.get(
            "/user/" + name + "/counts",
            (result) => display_results(result),
            "json",
        );
    },
};

export { UserCounts };
