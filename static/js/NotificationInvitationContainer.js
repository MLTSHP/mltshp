import { NotificationInvitationRequest } from "./NotificationInvitationRequest.js";

let on_shake_page;
let $hd;
let $bd;

function update_count(count) {
    if (!on_shake_page) {
        var request_text = count == 1 ? " request" : " requests";
        var html = count + request_text + " to join a shake";
        $hd.html(html);
    } else {
        $hd.html("Got it!");
    }
}

const NotificationInvitationContainer = {
    populate: function ($root) {
        $hd = $root.find(".notification-block-hd");
        $bd = $root.find(".notification-block-bd");
        on_shake_page = $hd.hasClass("on-shake-page");
        $root.find(".notification").each(function () {
            // Attach events to each invitation, passing the update_count
            // function as a callback for approval / disapproval clicks to
            // update the container header.
            NotificationInvitationRequest.attachEvents($(this), update_count);
        });
    },
};

export { NotificationInvitationContainer };
