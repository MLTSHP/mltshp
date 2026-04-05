var NotificationInvitationRequest = function ($root, container) {
    this.$root = $root;
    this.container = container;
    this.init_dom();
    this.init_events();
};

$.extend(NotificationInvitationRequest.prototype, {
    init_dom: function () {
        this.$form = this.$root.find("form");
        this.$form_approve_invitation = this.$root.find(".approve-invitation");
        this.$form_decline_invitation = this.$root.find(".decline-invitation");
    },

    init_events: function () {
        this.$root.delegate(
            ".approve-invitation",
            "submit",
            $.proxy(this.submit_approve_invitation, this),
        );
        this.$root.delegate(
            ".decline-invitation",
            "submit",
            $.proxy(this.submit_decline_invitation, this),
        );
    },

    submit_approve_invitation: function (ev) {
        ev.preventDefault();
        this.submit_form(this.$form_approve_invitation);
    },

    submit_decline_invitation: function (ev) {
        ev.preventDefault();
        this.submit_form(this.$form_decline_invitation);
    },

    submit_form: function ($form) {
        var url = $form.attr("action");
        var data = $form.serialize();
        $.post(url, data, $.proxy(this.clear_notification, this), "json");
    },

    clear_notification: function (response) {
        if (response["status"] == "ok") {
            this.$root.remove();
            this.container.update_count(response["count"]);
        }
    },
});
