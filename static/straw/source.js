/** @preserve
Straw - a MLTSHP Bookmarklet.
Source: https://mltshp.com/static/straw/source.js
Bookmarklet URL: javascript:void((function(){var%20e=document.createElement('script');e.setAttribute('type','text/javascript');e.setAttribute('charset','UTF-8');e.setAttribute('src','https://mltshp.com/static/straw/compact.js?r='+Math.random()*99999999);document.body.appendChild(e)})());
*/
/*
 To compile, from project root:

java -jar ./tools/compiler.jar --js static/straw/source.js --js_output_file static/straw/compact.js
*/

(function (global) {
    "use strict";

    if (global.MLTSHPStraw !== undefined) {
        global.MLTSHPStraw.toggle();
        return;
    }

    var Event = (function () {
        var event_listener = !!global.document.addEventListener;

        return {
            bind: function (el, type, callback) {
                var handler = function (e) {
                    return callback.apply(el, arguments);
                };

                if (event_listener) {
                    el.addEventListener(type, handler, false);
                } else {
                    el.attachEvent("on" + type, handler);
                }
            },
        };
    })();

    var Proxy = function (callback, context) {
        return function () {
            callback.apply(context, arguments);
        };
    };

    var DOM = {
        style: function (el, property) {
            var y = null;
            if (el.currentStyle) {
                y = el.currentStyle[property];
            } else if (global.getComputedStyle) {
                y = global.document.defaultView
                    .getComputedStyle(el, null)
                    .getPropertyValue(property);
            }
            return y;
        },
    };

    var Sharedfile = function (category, asset, el) {
        this.category = category;
        this.asset = asset;
        this.el = el;
    };

    Sharedfile.prototype.append_root = global.document.body;

    Sharedfile.prototype.position = function () {
        var el = this.el,
            left = 0,
            top = 0;

        do {
            // Grab first relative container to use to append
            // our overlays.
            var style = DOM.style(el, "position");
            if (style == "relative") {
                this.append_root = el;
                break;
            }

            left += el.offsetLeft;
            top += el.offsetTop;
        } while ((el = el.offsetParent));

        return [left, top];
    };

    Sharedfile.prototype.hide = function () {
        if (this.view !== undefined) {
            this.view.style.display = "none";
        }
    };

    Sharedfile.prototype.show = function () {
        if (this.view !== undefined) {
            this.view.style.display = "block";
        }
    };

    Sharedfile.prototype.draw_overlay = function () {
        var position = this.position(),
            width = this.width(),
            height = this.height(),
            div = document.createElement("div"),
            append_root = this.append_root;

        div.className = "mltshp-sf-overlay";
        div.style.left = position[0] + "px";
        div.style.top = position[1] + "px";
        div.style.width = width - 4 + "px";
        div.style.height = height - 4 + "px";

        if (width > 300 && height > 100) {
            var left_margin = (width - 240) / 2,
                top_margin = (height - 45) / 2;
            html = '<span class="mltshp-sf-overlay-text" style="';
            html = html + "margin-top:" + top_margin + "px;";
            html = html + "margin-left:" + left_margin + "px;";
            html = html + '">Save on MLTSHP</span>';
            div.innerHTML = html;
        }

        append_root.appendChild(div);
        this.view = div;
        Event.bind(div, "click", Proxy(this.click_overlay, this));
    };

    Sharedfile.prototype.click_overlay = function (ev) {
        if (ev.stopPropagation) {
            ev.stopPropagation();
        } else {
            ev.cancelBubble = true;
        }

        left_location = screen.width / 2 - 450;
        top_location = screen.height / 2 - 300;
        var window_attributes =
            "width=850,height=650,menubar=yes,toolbar=yes,scrollbars=yes,resizable=yes,left=" +
            left_location +
            ",top=" +
            top_location +
            "screenX=" +
            left_location +
            ",screenY=" +
            top_location;
        global.open(
            "https://mltshp.com/tools/p?url=" +
                encodeURI(this.asset) +
                "&title=" +
                encodeURI(global.document.title) +
                "&source_url=" +
                encodeURI(global.location.href),
            "save_image",
            window_attributes,
        );
    };

    Sharedfile.prototype.height = function () {
        if (this._height === undefined) {
            this._height = this.el.offsetHeight;
        }
        return this._height;
    };

    Sharedfile.prototype.width = function () {
        if (this._width === undefined) {
            this._width = this.el.offsetWidth;
        }
        return this._width;
    };

    var AssetFinder = {
        _parse_query: function (query) {
            var split = query.split("&"),
                split_length = split.length,
                params = {};

            for (var i = 0; i < split_length; i++) {
                var param_value = split[i].split("=");
                params[param_value[0]] = param_value[1];
            }

            return params;
        },

        videos: function () {
            var embeds = document.getElementsByTagName("embed"),
                embeds_length = embeds.length,
                objects = document.getElementsByTagName("object"),
                objects_length = objects.length,
                found = [];

            for (var i = 0; i < embeds_length; i++) {
                var embed = embeds[i],
                    flashvars = embed.getAttribute("flashvars");
                if (flashvars) {
                    var params = this._parse_query(flashvars);
                    if (params["video_id"]) {
                        found.push({
                            el: embed,
                            url:
                                "http://www.youtube.com/watch?v=" +
                                params["mJ1CSeNlRA4"],
                        });
                    }
                }
            }

            for (var i = 0; i < objects_length; i++) {
                var object = objects[i];
                var data = object.getAttribute("data");
                if (data && data.indexOf("vimeocdn") > 0) {
                    var video_id = object
                        .getAttribute("id")
                        .replace("player", "")
                        .split("_")[0];
                    found.push({
                        el: object,
                        url: "http://vimeo.com/" + video_id,
                    });
                }
            }
            return found;
        },

        images: function () {
            var imgs = document.getElementsByTagName("img"),
                imgs_length = imgs.length,
                found = [];
            for (var i = 0; i < imgs_length; i++) {
                if (imgs[i].offsetWidth < 100 || imgs[i].offsetHeight < 100) {
                    continue;
                }
                found.push(imgs[i]);
            }
            return found;
        },
    };

    global.MLTSHPStraw = {
        found: [],

        init: function () {
            this.initiated = true;
            this.init_styles();
            this.find_assets();
            this.draw_overlays();
        },

        find_assets: function () {
            var images = AssetFinder.images(),
                images_length = images.length,
                videos = AssetFinder.videos(),
                videos_length = videos.length,
                found = [];

            for (var i = 0; i < images_length; i++) {
                found.push(new Sharedfile("image", images[i].src, images[i]));
            }

            //for (var i = 0; i < videos_length; i++) {
            //  found.push(new Sharedfile('video', videos[i].url, videos[i].el));
            //}

            this.found = found;
        },

        init_styles: function () {
            var style =
                "\
        .mltshp-sf-overlay {font-family: Helvetica,Arial,sans-serif;position: absolute; border: 4px solid #ff0080; text-align: center; cursor: pointer; z-index: 9999999; background-image:url('.'); }\
        .mltshp-sf-overlay-text {display: block; float: left; background-color: #ff0080; font-size: 24px; color: #fff; padding: 10px 20px; text-shadow: 3px 3px 0px #B5005A; \
        -webkit-border-radius: 5px; -moz-border-radius: 5px; border-radius: 5px; \
        -moz-box-shadow: 4px 4px 0px rgba(0, 0, 0, 0.3); -webkit-box-shadow: 4px 4px rgba(0, 0, 0, 0.3); box-shadow: 4px 4px 0px rgba(0, 0, 0, 0.3); }\
        .mltshp-sf-overlay:hover { border-color: #db008b} \
        .mltshp-sf-overlay:hover .mltshp-sf-overlay-text { background-color: #db008b; } \
      ";
            var style_el = document.createElement("style");
            style_el.setAttribute("type", "text/css");
            if (style_el.styleSheet !== undefined) {
                style_el.styleSheet.cssText = style; // IE
            } else {
                style_el.innerHTML = style;
            }
            global.document.body.appendChild(style_el);
        },

        draw_overlays: function () {
            for (var i = 0, length = this.found.length; i < length; i++) {
                this.found[i].draw_overlay();
            }
        },

        toggle: function () {
            if (!this.initiated) {
                this.find_assets();
                this.draw_overlays();
            } else {
                for (
                    var i = 0, found_length = this.found.length;
                    i < found_length;
                    i++
                ) {
                    this.found[i].hide();
                }
            }
            this.initiated = !this.initiated;
        },
    };
    MLTSHPStraw.init();
})(window);
