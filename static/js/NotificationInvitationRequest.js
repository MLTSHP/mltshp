const NotificationInvitationRequest = {
    attachEvents: function ($root, updateFn) {
        // const $form = $root.find("form");
        const $form_approve_invitation = $root.find(".approve-invitation");
        const $form_decline_invitation = $root.find(".decline-invitation");

        function submit_approve_invitation(ev) {
            ev.preventDefault();
            submit_form($form_approve_invitation);
        }

        function submit_decline_invitation(ev) {
            ev.preventDefault();
            submit_form($form_decline_invitation);
        }

        function submit_form($form) {
            var url = $form.attr("action");
            var data = $form.serialize();
            $.post(url, data, (resp) => clear_notification(resp), "json");
        }

        function clear_notification(response) {
            if (response["status"] == "ok") {
                $root.remove();
                updateFn(response["count"]);
            }
        }

        $root.delegate(".approve-invitation", "submit", (ev) =>
            submit_approve_invitation(ev),
        );

        $root.delegate(".decline-invitation", "submit", (ev) =>
            submit_decline_invitation(ev),
        );
    },
};

export { NotificationInvitationRequest };
