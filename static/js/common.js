/**
 * Common utility functions.
 */

// http://stackoverflow.com/questions/1125292/how-to-move-cursor-to-end-of-contenteditable-entity
function setCaret(el) {
    const ctrl = el;
    const pos = ctrl.value.length;
    if (ctrl.setSelectionRange) {
        ctrl.focus();
        ctrl.setSelectionRange(pos, pos);
    } else if (ctrl.createTextRange) {
        var range = ctrl.createTextRange();
        range.collapse(true);
        range.moveEnd("character", pos);
        range.moveStart("character", pos);
        range.select();
    }
}

function toText(num, base) {
    return num == 1
        ? num + " " + "<span>" + base + "</span>"
        : num + " " + "<span>" + base + "s" + "</span>";
}

export { setCaret, toText };
