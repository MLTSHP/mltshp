/**
 * Functionality for "Invite A New Member" form shown in the sidebar of a shake
 * the current user is an editor of. Lets the user type in a few characters, see
 * an autocompleted list of matching usernames to pick from, and finally sends
 * an invitation via the backend.
 */

// Invite Member widget for the Shake administrator.
var $main_module = $("#shake-invite-member");
var $input_field = $main_module.find(".input-text");
var $invite_button = $main_module.find(".invite-button");
var $shake_results = $main_module.find(".shake-results");
var $form = $main_module.find("form");
var $title = $main_module.find("h3");
var search_results = [];
var last_search = "";

const InviteMember = {
    attachEvents: function () {
        $input_field.keyup((ev) => this.search_names(ev));
        $form.submit((ev) => this.submit_form());
        $shake_results.click((ev) => this.select_user($(ev.target).text()));
        $invite_button.click(() => {
            this.send_invite();
            return false;
        });
    },

    search_names: function () {
        if ($input_field.val() == "") {
            this.clear_results();
            this.clear_input();
            return false;
        }

        // don't search again if field hasn't changed.
        if ($input_field.val() == last_search) {
            return false;
        }

        last_search = $input_field.val();
        var data = $form.serialize();
        $.post(
            "/account/quick_name_search",
            data,
            (response) => {
                if ("users" in response) {
                    this.update_results(response["users"]);
                }
            },
            "json",
        );
    },

    update_results: function (users) {
        search_results = users;
        if (search_results.length == 0) {
            this.clear_results();
        } else {
            this.render_results();
        }
    },

    render_results: function () {
        $shake_results.html("").show();
        for (var i = 0; i < search_results.length; i++) {
            $shake_results.append(
                '<li><img src="' +
                    search_results[i].profile_image_url +
                    '" width="24" height="24"><span>' +
                    search_results[i].name +
                    "</span></li>",
            );
        }
    },

    select_user: function (user_name) {
        this.clear_results();
        $input_field.val(user_name);
        $invite_button.removeAttr("disabled");
    },

    submit_form: function (ev) {
        if (
            search_results.length == 1 &&
            search_results[0].name == $input_field.val()
        ) {
            this.select_user(search_results[0].name);
            this.send_invite();
            this.clear_results();
        }
        return false;
    },

    clear_results: function () {
        last_search = "";
        $shake_results.hide().html("");
    },

    clear_input: function () {
        $input_field.val("");
        $invite_button.attr("disabled", "disabled");
    },

    send_invite: function () {
        if ($invite_button.disabled) {
            return false;
        } else {
            var url = $form.attr("action");
            var data = $form.serialize();
            $.post(
                url,
                data,
                () => {
                    this.data_sent();
                    return false;
                },
                "json",
            );
            return false;
        }
    },

    data_sent: function () {
        $title.html("Your invitation has been sent");
        this.clear_input();
        this.clear_results();
    },
};

export { InviteMember };
