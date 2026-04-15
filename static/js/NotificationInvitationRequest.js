const NotificationInvitationRequest = {
    attachEvents: function ($root, updateCallbackFn) {
        const $formApproveInvitation = $root.find(".approve-invitation");
        const $formDeclineInvitation = $root.find(".decline-invitation");

        function submitApproveInvitation(ev) {
            ev.preventDefault();
            submitForm($formApproveInvitation);
        }

        function submitDeclineInvitation(ev) {
            ev.preventDefault();
            submitForm($formDeclineInvitation);
        }

        async function submitForm($form) {
            const url = $form.attr("action");
            const data = $form.serialize();
            const resp = await fetch(url, {
                method: "POST",
                body: new URLSearchParams(data),
            });
            const json = await resp.json();
            clearNotification(json);
        }

        function clearNotification(response) {
            if (response["status"] == "ok") {
                $root.remove();
                updateCallbackFn(response["count"]);
            }
        }

        $root.delegate(".approve-invitation", "submit", (ev) =>
            submitApproveInvitation(ev),
        );

        $root.delegate(".decline-invitation", "submit", (ev) =>
            submitDeclineInvitation(ev),
        );
    },
};

export { NotificationInvitationRequest };
