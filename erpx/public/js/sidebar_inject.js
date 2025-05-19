// ERPX Sidebar Menu Injector
function injectSidebarMenu() {
    let sidebar = $(".layout-side-section");

    if (sidebar.length) {
        // Remove existing custom menu if it exists
        sidebar.find('div.navigation-header[data-custom="true"]').remove();
        sidebar.find('a[data-custom="true"]').remove();

        // Add a custom navigation header
        const navigationHeader = $('<div class="navigation-header" data-custom="true">Navigation</div>');
        sidebar.append(navigationHeader);

        // Add custom CSS for hover effects
        if (!$('#erpx-sidebar-styles').length) {
            $('head').append(`
                <style id="erpx-sidebar-styles">
                    .erpx-nav-item {
                        display: flex;
                        align-items: center;
                        text-decoration: none;
                        color: inherit;
                        padding: 10px 15px;
                        border: 1px solid #e0e0e0;
                        border-radius: 5px;
                        background-color: #f9f9f9;
                        width: 210px;
                        max-width: 210px;
                        margin: 3px 0;
                        transition: all 0.2s ease;
                    }
                    
                    .erpx-nav-item:hover {
                        font-weight: bold;
                        color: #009D4A;
                        background-color: #e0f7e9;
                        text-decoration: none;
                    }
                    
                    .erpx-nav-icon {
                        display: inline-flex;
                        align-items: center;
                        justify-content: center;
                        margin-right: 8px;
                        font-size: 24px;
                        width: 24px;
                        height: 24px;
                    }
                </style>
            `);
        }

        // Navigation items with icons
        const navItems = [
            { name: "Angebot", url: "/app/quotation", icon: "📄" },
            { name: "Auftrag", url: "/app/sales-order", icon: "📝" },
            { name: "Rechnung", url: "/app/sales-invoice", icon: "🧾" },
            { name: "Kunde", url: "/app/customer", icon: "👤" },
            { name: "Lieferschein", url: "/app/delivery-note", icon: "🚚" },
            { name: "Projekt (Kanban)", url: "/app/project/view/kanban/Project", icon: "📊" },
            { name: "Projekt (List)", url: "/app/project", icon: "📋" },
            { name: "Artikel", url: "/app/item", icon: "📦" },
            { name: "Artikelpreis", url: "/app/item-price", icon: "💲" },
            { name: "Brief", url: "/app/item/pdf%20brief", icon: "✉️" },
            { name: "Aufgabe", url: "/app/todo/view/calendar/default", icon: "✓" }
        ];

        // Add each navigation item
        navItems.forEach(item => {
            const navItem = $(`
                <a href="${item.url}" class="erpx-nav-item" data-custom="true">
                    <span class="erpx-nav-icon">${item.icon}</span>
                    <span>${item.name}</span>
                </a>
            `);
            
            sidebar.append(navItem);
        });
    } else {
        setTimeout(injectSidebarMenu, 500);
    }
}

// Start the sidebar injection
function startSidebarInjection() {
    injectSidebarMenu();
    
    // Set up a constant check every 2 seconds
    setInterval(function() {
        injectSidebarMenu();
    }, 2000);
}

// Wait until Frappe is fully loaded, then start the function
frappe.after_ajax(() => {
    startSidebarInjection();
});
