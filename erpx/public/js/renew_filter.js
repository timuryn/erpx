// Store the last visited route
let last_route = null;

// Override frappe.set_route to clean query parameters when navigating back to list views
const original_set_route = frappe.set_route;

frappe.set_route = function(...args) {
    // Get the current route before navigation
    const current_route = frappe.get_route_str();
    
    // Parse current route
    const current_parts = current_route.split('/').filter(p => p);
    
    // Check if current is a Form page (e.g., "Form/Project/2025-311")
    const is_form_page = current_parts[0] === 'Form' && current_parts.length >= 3;
    
    // Check if we're navigating to a doctype list (the target contains /app/doctype pattern)
    const is_navigating_to_list = args.length === 1 && 
                                   typeof args[0] === 'string' && 
                                   args[0].match(/^\/app\/[^\/]+$/);
    
    // If navigating from form back to list, mark for filter clearing
    if (is_form_page && is_navigating_to_list) {
        const current_doctype = current_parts[1];
        
        if (!frappe._clear_list_filters) {
            frappe._clear_list_filters = new Set();
        }
        frappe._clear_list_filters.add(current_doctype);
    }
    
    // Call the original set_route
    return original_set_route.apply(this, args);
};

// Function to clear list view filters
function clearListViewFilters(doctype) {
    setTimeout(() => {
        let cur_list = frappe.container.page?.list_view;
        
        if (cur_list && cur_list.doctype === doctype) {
            // Clear filter area
            if (cur_list.filter_area) {
                cur_list.filter_area.clear();
            }
            
            // Clear standard filters
            if (cur_list.standard_filters) {
                cur_list.standard_filters.forEach(filter => {
                    if (filter.set_value) {
                        filter.set_value('');
                    }
                });
            }
            
            // Clear filter inputs directly from DOM
            const $page = $(cur_list.page.wrapper);
            $page.find('.standard-filter-section input, .standard-filter-section select').val('');
            
            // Refresh the list
            cur_list.refresh();
        }
    }, 200);
}

// Handle browser back/forward button
window.addEventListener('popstate', function(e) {
    // Check if we have query parameters in the URL
    if (window.location.search && window.location.search.length > 0) {
        const route = frappe.get_route();
        
        // If we're on a list view
        if (route[0] === 'List' && route.length >= 2) {
            const doctype = route[1];
            
            // Remove query parameters from URL
            const clean_url = window.location.pathname;
            window.history.replaceState(null, '', clean_url);
            
            // Clear filters immediately
            clearListViewFilters(doctype);
        }
    }
});

// Hook into ListView to clear filters after it loads
frappe.router.on('change', () => {
    const new_route = frappe.get_route_str();
    
    // Check if we just loaded a List view that should have filters cleared
    const route_parts = new_route.split('/').filter(p => p);
    if (route_parts[0] === 'List' && route_parts.length >= 2) {
        const doctype = route_parts[1];
        
        if (frappe._clear_list_filters && frappe._clear_list_filters.has(doctype)) {
            // Clear filters
            clearListViewFilters(doctype);
            
            // Remove from the set
            frappe._clear_list_filters.delete(doctype);
        }
    }
    
    last_route = new_route;
});
