(function() {
    function initFilterRemoval() {
        // Check if frappe.session is available
        if (!frappe.session || !frappe.session.user) {
            setTimeout(initFilterRemoval, 100);
            return;
        }
        
        // Skip filter removal for this user
        if (frappe.session.user === "info@dippelwerbung.de") {
            return;
        }
        
        // Override frappe.set_route to clean query parameters when navigating back to list views
        const original_set_route = frappe.set_route;
        frappe.set_route = function(...args) {
            const current_route = frappe.get_route_str();
            const current_parts = current_route.split('/').filter(p => p);
            const is_form_page = current_parts[0] === 'Form' && current_parts.length >= 3;
            const is_navigating_to_list = args.length === 1 &&
                                           typeof args[0] === 'string' &&
                                           args[0].match(/^\/app\/[^\/]+$/);
            
            if (is_form_page && is_navigating_to_list) {
                const current_doctype = current_parts[1];
                if (!frappe._clear_list_filters) {
                    frappe._clear_list_filters = new Set();
                }
                frappe._clear_list_filters.add(current_doctype);
            }
            
            return original_set_route.apply(this, args);
        };
        
        // Function to clear list view filters
        function clearListViewFilters(doctype) {
            setTimeout(() => {
                let cur_list = frappe.container.page?.list_view;
                if (cur_list && cur_list.doctype === doctype) {
                    if (cur_list.filter_area) {
                        cur_list.filter_area.clear();
                    }
                    
                    if (cur_list.standard_filters) {
                        cur_list.standard_filters.forEach(filter => {
                            if (filter.set_value) {
                                filter.set_value('');
                            }
                        });
                    }
                    
                    const $page = $(cur_list.page.wrapper);
                    $page.find('.standard-filter-section input, .standard-filter-section select').val('');
                    cur_list.refresh();
                }
            }, 200);
        }
        
        // Handle browser back/forward button
        window.addEventListener('popstate', function(e) {
            if (window.location.search && window.location.search.length > 0) {
                const route = frappe.get_route();
                if (route[0] === 'List' && route.length >= 2) {
                    const doctype = route[1];
                    const clean_url = window.location.pathname;
                    window.history.replaceState(null, '', clean_url);
                    clearListViewFilters(doctype);
                }
            }
        });
        
        // Hook into ListView to clear filters after it loads
        frappe.router.on('change', () => {
            const new_route = frappe.get_route_str();
            const route_parts = new_route.split('/').filter(p => p);
            if (route_parts[0] === 'List' && route_parts.length >= 2) {
                const doctype = route_parts[1];
                if (frappe._clear_list_filters && frappe._clear_list_filters.has(doctype)) {
                    clearListViewFilters(doctype);
                    frappe._clear_list_filters.delete(doctype);
                }
            }
        });
    }
    
    initFilterRemoval();
})();
