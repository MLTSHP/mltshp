/**
 * Functionality related to a user requesting an invitation to join a shake.
 * This module attaches an event handler to the "Join this shake" button, and
 * persists a request for invitation to the server for the shaken owner to sed.
 */

const RequestInvitation = {
    attachEvents: function ($root) {
        const $form = $root.find("form");

        // Per invocation functions that will close over the context dependent
        // variables defined above.
        async function submitRequest() {
            var url = $form.attr("action");
            var data = $form.serialize();
            $.post(url, data, () => processResponse());

            // Work in progress. Seems to be some difference in behaviour
            // between the two techniques.
            // const url = $form.attr("action");
            // const data = $form.serialize();
            // console.log(url, data);
            // await fetch(url, {
            //     method: "POST",
            //     body: new URLSearchParams(data),
            // });
            // processResponse();

            return false;
        }

        function processResponse() {
            $root.html("<span>Ok! Request sent.</span>");
        }

        // Attach any event handlers.
        $root.delegate("form", "submit", () => submitRequest());
    },
};

export { RequestInvitation };
