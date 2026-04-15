/**
 * Functionality for "Invite A New Member" form shown in the sidebar of a shake
 * the current user is an editor of. Lets the user type in a few characters, see
 * an autocompleted list of matching usernames to pick from, and finally sends
 * an invitation via the backend.
 */

// Invite Member widget for the Shake administrator.
const $mainModule = $("#shake-invite-member");
const $inputField = $mainModule.find(".input-text");
const $inviteButton = $mainModule.find(".invite-button");
const $shakeResults = $mainModule.find(".shake-results");
const $form = $mainModule.find("form");
const $title = $mainModule.find("h3");
let searchResults = [];
let lastSearch = "";

const InviteMember = {
    attachEvents: function () {
        $inputField.keyup((ev) => this.searchNames(ev));
        $form.submit((ev) => this.submitForm());
        $shakeResults.click((ev) => this.selectUser($(ev.target).text()));
        $inviteButton.click(() => {
            this.sendInvite();
            return false;
        });
    },

    searchNames: async function () {
        if ($inputField.val() == "") {
            this.clearResults();
            this.clearInput();
            return false;
        }

        // don't search again if field hasn't changed.
        if ($inputField.val() == lastSearch) {
            return false;
        }
        lastSearch = $inputField.val();

        const data = $form.serialize();
        const resp = await fetch("/account/quick_name_search", {
            method: "POST",
            body: new URLSearchParams(data),
        });
        const json = await resp.json();

        if ("users" in json) {
            this.updateResults(json["users"]);
        }
    },

    updateResults: function (users) {
        searchResults = users;
        if (searchResults.length == 0) {
            this.clearResults();
        } else {
            this.renderResults();
        }
    },

    renderResults: function () {
        $shakeResults.html("").show();
        for (let i = 0; i < searchResults.length; i++) {
            $shakeResults.append(
                `<li>
                    <img src="${searchResults[i].profile_image_url}"
                        width="24" height="24">
                    <span>${searchResults[i].name}</span>
                </li>`,
            );
        }
    },

    selectUser: function (userName) {
        this.clearResults();
        $inputField.val(userName);
        $inviteButton.removeAttr("disabled");
    },

    submitForm: function (ev) {
        if (
            searchResults.length == 1 &&
            searchResults[0].name == $inputField.val()
        ) {
            this.selectUser(searchResults[0].name);
            this.sendInvite();
            this.clearResults();
        }
        return false;
    },

    clearResults: function () {
        lastSearch = "";
        $shakeResults.hide().html("");
    },

    clearInput: function () {
        $inputField.val("");
        $inviteButton.attr("disabled", "disabled");
    },

    sendInvite: async function () {
        if ($inviteButton.disabled) {
            return false;
        } else {
            const url = $form.attr("action");
            const data = $form.serialize();

            await fetch(url, {
                method: "POST",
                body: new URLSearchParams(data),
            });

            this.dataSent();
            return false;
        }
    },

    dataSent: function () {
        $title.html("Your invitation has been sent");
        this.clearInput();
        this.clearResults();
    },
};

export { InviteMember };
