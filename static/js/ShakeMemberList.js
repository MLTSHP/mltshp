var ShakeMemberList = function ($root) {
    this.$root = $root;
    this.init_events();
};

$.extend(ShakeMemberList.prototype, {
    init_events: function () {
        this.$root.delegate(
            ".remove-from-shake-button-link",
            "click",
            $.proxy(this.remove_from_shake, this),
        );
    },

    remove_from_shake: function (ev) {
        var $target = $(ev.target),
            $li = $target.parents("li"),
            $form = $target.next(),
            url = $form.attr("action");
        data = $form.serialize();

        if (
            confirm(
                "Are you sure you want to remove this user from a shake? If they have notifications on an email will be sent informing them of the change.",
            )
        ) {
            $.post(url, data, $.proxy(this.process_remove, $li));
        }
        return false;
    },

    process_remove: function (response) {
        this.remove();
    },
});
