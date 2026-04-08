const RequestInvitation = {
    attachEvents: function ($root) {
        const $form = $root.find("form");

        // Per invocation functions that will close over the context dependent
        // variables defined above.
        function submit_request() {
            var url = $form.attr("action");
            var data = $form.serialize();
            $.post(url, data, () => process_response());
            return false;
        }

        function process_response() {
            $root.html("<span>Ok! Request sent.</span>");
        }

        // Attach any event handlers.
        $root.delegate("form", "submit", () => submit_request());
    },
};

export { RequestInvitation };
