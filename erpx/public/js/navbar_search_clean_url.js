(function () {
    function clean_url_when_filter_applied() {
        const route = frappe.get_route();
        if (!route || route[0] !== "List") return;

        let attempts = 0;
        const check = setInterval(() => {
            attempts++;
            if (window.location.search) {
                clearInterval(check);
                window.history.replaceState(null, "", window.location.pathname);
            } else if (attempts > 40) {
                clearInterval(check);
            }
        }, 50);
    }

    if (frappe.router && typeof frappe.router.on === "function") {
        frappe.router.on("change", clean_url_when_filter_applied);
    } else {
        $(document).on("page-change", clean_url_when_filter_applied);
    }
})();
