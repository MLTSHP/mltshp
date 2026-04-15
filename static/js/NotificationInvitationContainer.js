import { NotificationInvitationRequest } from "./NotificationInvitationRequest.js";

let onShakePage;
let $header;
let $body;

function update_count(count) {
    if (!onShakePage) {
        const requestText = count === 1 ? "request" : "requests";
        const html = `${count} ${requestText} to join a shake`;
        $header.html(html);
    } else {
        $header.html("Got it!");
    }
}

const NotificationInvitationContainer = {
    populate: function ($root) {
        $header = $root.find(".notification-block-hd");
        $body = $root.find(".notification-block-bd");
        onShakePage = $header.hasClass("on-shake-page");
        $root.find(".notification").each(function () {
            // Attach events to each invitation, passing the update_count
            // function as a callback for approval / disapproval clicks to
            // update the container header.
            NotificationInvitationRequest.attachEvents($(this), update_count);
        });
    },
};

export { NotificationInvitationContainer };
