var NotificationInvitationContainer = function ($root) {
    this.$root = $root;
    this.init();
};

$.extend(NotificationInvitationContainer.prototype, {
    init: function () {
        this.$hd = this.$root.find(".notification-block-hd");
        this.$bd = this.$root.find(".notification-block-bd");
        this.on_shake_page = this.$hd.hasClass("on-shake-page");
        var that = this;
        this.$root.find(".notification").each(function () {
            var new_invitation_request = new NotificationInvitationRequest(
                $(this),
                that,
            );
        });
    },

    update_count: function (count) {
        if (!this.on_shake_page) {
            var request_text = count == 1 ? " request" : " requests";
            var html = count + request_text + " to join a shake";
            this.$hd.html(html);
        } else {
            this.$hd.html("Got it!");
        }
    },
});
