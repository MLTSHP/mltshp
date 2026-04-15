/**
 * Functionality associated with the new post panel that pops up on any page
 * allowing the user to post a new image or video to one of their shakes.
 *
 * Takes care of adding event listeners to the new post button, as well as to
 * the shake dropdowns on both the image and video sides of the dialog. The new
 * post dropdown slides in from the top of the screen.
 */
let $newPostPanel;
let $newPostPanelInner;
let $newPostButton;
let $saveVideoForm;
let $saveVideoFormButton;
let $postVideoForm;
let $postVideoFormButton;
let $uploadImageInput;
let $linkToVideo;
let $videoShakeId;
let $shakeSelector;

function removeEvents() {
    $saveVideoFormButton.unbind();
    $postVideoFormButton.unbind();
    $shakeSelector.unbind();
    $linkToVideo.unbind();
}

function initDom() {
    $newPostPanel = $("#new-post-panel");
    $newPostPanelInner = $("#new-post-panel .new-post-panel--inner");
    $newPostButton = $("#new-post-button");
    // upload image
    $uploadImageInput = $("#upload-image-input");
    // link to video
    $linkToVideo = $("#link-to-video");
    $videoShakeId = $("#video-shake-id");
    // video preview screen
    $saveVideoForm = $("#new-post-panel .save-video-form");
    $saveVideoFormButton = $("#new-post-panel .save-video-form .btn");
    $postVideoForm = $("#new-post-panel .post-video-form");
    $postVideoFormButton = $("#new-post-panel .post-video-form .btn");
    // shake selector
    $shakeSelector = $(".shake-selector");
}

function initEvents() {
    // The events that are inside the panel that we want to initialize
    // when the panel loads.  These are the events that are subject
    // to change depending on content that is loaded.

    // Video upload step 1.
    // Called when user clicks "video" link and takes them to a new form where
    // they can enter the video url.
    $linkToVideo.click(function () {
        NewPostPanel.loadPostVideo();
        return false;
    });

    // Video upload step 2.
    // Called when the user clicks "Go get it!" button which takes the user to a
    // new form containing a preview of the video.
    $saveVideoFormButton.click(function (e) {
        NewPostPanel.submitSaveVideo();
        return false;
    });

    // Video upload step 3.
    // Called when the user clicks "Yes! Post it please!" which uploads the
    // video via submitPostVideo().
    $postVideoFormButton.click(function (e) {
        NewPostPanel.submitPostVideo();
        return false;
    });

    // Uploads the image file upon selection by the file upload dialog.
    $uploadImageInput.change(function () {
        $(this).closest("form").submit();
    });

    $shakeSelector.click(NewPostPanel.toggleShakeSelector);
    $shakeSelector.find("ul a").click(NewPostPanel.chooseShake);
}

const NewPostPanel = {
    attachEvents: function () {
        initDom();

        $newPostButton.click(function () {
            NewPostPanel.loadNewPost();
            return false;
        });

        // We don't want click event on panel to bubble up to body
        // since a click to body closes the panel.
        $newPostPanel.click(function (ev) {
            ev.stopPropagation();
        });
    },

    toggleShakeSelector: function (ev) {
        $(this).toggleClass("is-active").find("ul").toggle();
        ev.stopPropagation();
        ev.preventDefault();
    },

    // Sets the text of the shake to the chosen one and
    // sets a hidden input field with the proper shake id.
    chooseShake: function () {
        const $shakeSelector = $(this).parents(".shake-selector");
        const $selectedShake = $shakeSelector.find(".green");
        const $selectedShakeInput = $shakeSelector.find("input");
        const name = $(this).html();
        const id = $(this)
            .attr("id")
            .replace(/[^0-9]+/, "");
        $selectedShake.html(name);
        $selectedShakeInput.val(id);
    },

    // Renders step 1 of image / video upload process - shake choice and file
    // type.
    loadNewPost: async function () {
        var url = "/tools/new-post";
        const resp = await fetch(url);

        this.refreshPanel(await resp.text());
        this.expandPanel();
        return false;
    },

    // Renders step 2 of the video upload process - entering the url.
    loadPostVideo: async function () {
        let shakeSuffix = "";
        if ($videoShakeId.length > 0) {
            shakeSuffix = "?shake_id=" + $videoShakeId.val();
        }
        const url = `/tools/save-video${shakeSuffix}`;

        const resp = await fetch(url);
        this.refreshPanel(await resp.text());
        this.expandPanel();
    },

    expandPanel: function () {
        $newPostPanel.slideDown();
        var that = this;
        $("body").one("click", $.proxy(this.close_panel, this));
        // we want to hide anything with a video since we can't
        // overlap things like youtube embeds, which is an iframe
        // that has an absolutely positioned flash element inside.
        $(".the-image iframe").each(function () {
            $(this).parent().css("height", $(this).height());
            $(this).parent().css("width", $(this).width());
            $(this).hide();
        });
    },

    close_panel: function () {
        $newPostPanel.hide();
        removeEvents();
        // show the videos again.
        $(".the-image iframe").show();
    },

    // Renders step 3 of the video upload process - previewing the video.
    submitSaveVideo: async function () {
        const url = $saveVideoForm.attr("action");
        const data = $saveVideoForm.serialize();

        const resp = await fetch(`${url}?${new URLSearchParams(data)}`);
        this.refreshPanel(await resp.text());
    },

    // Final step of video upload - submitting the post details to the server.
    submitPostVideo: async function () {
        const url = $postVideoForm.attr("action");
        const data = $postVideoForm.serialize();
        $postVideoFormButton.unbind("click").find("span").html("Posting...");

        const resp = await fetch(url, {
            method: "POST",
            body: new URLSearchParams(data),
        });
        const json = await resp.json();

        // Redirect to the new post permalink page.
        document.location =
            document.location.protocol +
            `//${document.location.host}${json["path"]}`;
    },

    refreshPanel: function (html) {
        $newPostPanelInner.html(html);
        removeEvents();
        initDom();
        initEvents();
    },
};

export { NewPostPanel };
