/**
 * Functionality associated with the edit shake members list, found on each
 * shake page e.g. https://mltshp.com/AMearworm
 *
 * Attaches an event handler to each person in the list, allowing them to be
 * removed as a member by the shake owner.
 */

function process_remove(elem) {
    // li element of this user in the list.
    elem.remove();
}

const ShakeMemberList = {
    attachEvents: function ($root) {
        // Per invocation functions that will close over the context dependent
        // variable defined above.
        function remove_from_shake(ev) {
            var $target = $(ev.target),
                $li = $target.parents("li"),
                $form = $target.next(),
                url = $form.attr("action");
            const data = $form.serialize();

            if (
                confirm(
                    "Are you sure you want to remove this user from a shake? If they have notifications on an email will be sent informing them of the change.",
                )
            ) {
                $.post(url, data, () => process_remove($li));
            }
            return false;
        }

        // Attach any event handlers.
        $root.delegate(".remove-from-shake-button-link", "click", (ev) =>
            remove_from_shake(ev),
        );
    },
};

export { ShakeMemberList };
