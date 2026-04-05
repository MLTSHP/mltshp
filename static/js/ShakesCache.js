var ShakesCache = {
    fetch: function () {
        if (this.result !== undefined) {
            return this.result;
        } else {
            return false;
        }
    },

    store: function (result) {
        this.result = result;
    },
};
