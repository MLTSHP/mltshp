var RequestInvitation = function ($root) {
    this.$root = $root;
    this.init_dom();
    this.init_events();
};

$.extend(RequestInvitation.prototype, {
    init_dom: function () {
        this.$form = this.$root.find("form");
    },

    init_events: function () {
        this.$root.delegate(
            "form",
            "submit",
            $.proxy(this.submit_request, this),
        );
    },

    submit_request: function () {
        var url = this.$form.attr("action");
        var data = this.$form.serialize();
        $.post(url, data, $.proxy(this.process_response, this));
        return false;
    },

    process_response: function () {
        this.$root.html("<span>Ok! Request sent.</span>");
    },
});
