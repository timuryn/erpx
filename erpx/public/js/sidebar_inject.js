// ERPX Sidebar Menu Injector with Dark Mode Support
function injectSidebarMenu() {
    let sidebar = $(".layout-side-section");
    if (sidebar.length) {
        // Remove existing custom menu if it exists
        sidebar.find('div.navigation-header[data-custom="true"]').remove();
        sidebar.find('a[data-custom="true"]').remove();

        // Add a custom navigation header
        const navigationHeader = $('<div class="navigation-header" data-custom="true">Navigation</div>');
        sidebar.append(navigationHeader);

        // Multi-method dark mode detection for custom ERPNext apps
        function isDarkMode() {
            // Method 1: Check HTML data attributes (most reliable for newer ERPNext)
            const html = document.documentElement;
            const themeMode = html.getAttribute('data-theme-mode');
            const theme = html.getAttribute('data-theme');

            if (themeMode === 'dark' || theme === 'dark') {
                return true;
            }
            if (themeMode === 'light' || theme === 'light') {
                return false;
            }

        }

        // Update styles based on current mode
        function updateStyles() {
            const darkMode = isDarkMode();
            const styleId = 'erpx-sidebar-styles';

            // Remove existing styles
            $(`#${styleId}`).remove();

            // Define styles for both modes
            const lightModeStyles = `
                .erpx-nav-item {
                    display: flex;
                    align-items: center;
                    text-decoration: none;
                    color: #333333;
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
                    border-color: #009D4A;
                }
            `;

            const darkModeStyles = `
                .erpx-nav-item {
                    display: flex;
                    align-items: center;
                    text-decoration: none;
                    color: #e0e0e0;
                    padding: 10px 15px;
                    border: 1px solid #444444;
                    border-radius: 5px;
                    background-color: #2a2a2a;
                    width: 210px;
                    max-width: 210px;
                    margin: 3px 0;
                    transition: all 0.2s ease;
                }
                .erpx-nav-item:hover {
                    font-weight: bold;
                    color: #00ff5f;
                    background-color: #1a4a2a;
                    text-decoration: none;
                    border-color: #00ff5f;
                }
            `;

            const commonStyles = `
                .erpx-nav-icon {
                    display: inline-flex;
                    align-items: center;
                    justify-content: center;
                    margin-right: 8px;
                    font-size: 24px;
                    width: 24px;
                    height: 24px;
                }

                .navigation-header[data-custom="true"] {
                    color: ${darkMode ? '#e0e0e0' : '#333333'};
                    font-weight: bold;
                    margin-bottom: 8px;
                    padding: 5px 15px;
                }
            `;

            // Apply the appropriate styles
            const finalStyles = darkMode ? darkModeStyles + commonStyles : lightModeStyles + commonStyles;

            $('head').append(`<style id="${styleId}">${finalStyles}</style>`);
        }

        // Initial style application
        updateStyles();

        // Navigation items with icons
        const navItems = [
            { name: "Projekt", url: "/app/project", icon: "📋" },
            { name: "Angebot", url: "/app/quotation", icon: "📄" },
            { name: "Auftrag", url: "/app/sales-order", icon: "📝" },
            { name: "Lieferschein", url: "/app/delivery-note", icon: "🚚" },
            { name: "Rechnung", url: "/app/sales-invoice", icon: "🧾" },
            { name: "Kunde", url: "/app/customer", icon: "👤" },
            { name: "Artikel", url: "/app/item", icon: "📦" },
            { name: "Artikelpreis", url: "/app/item-price", icon: "€" },
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

        // Enhanced event handling for custom ERPNext apps
        // Monitor HTML attribute changes (primary method)
        const observer = new MutationObserver(function(mutations) {
            mutations.forEach(function(mutation) {
                if (mutation.type === 'attributes') {
                    const attrName = mutation.attributeName;
                    if (attrName === 'data-theme-mode' || attrName === 'data-theme' || attrName === 'class') {
                        updateStyles();
                    }
                }
            });
        });

        observer.observe(document.documentElement, {
            attributes: true,
            attributeFilter: ['data-theme-mode', 'data-theme', 'class']
        });

        // Also monitor body for theme classes
        observer.observe(document.body, {
            attributes: true,
            attributeFilter: ['class']
        });

        // Listen for frappe events (if available)
        if (frappe) {
            // General theme change events
            $(document).on('theme-change theme-updated user-settings-updated', updateStyles);

            // Listen for frappe ready event and user session updates
            $(document).on('app_ready', function() {
                setTimeout(updateStyles, 100); // Small delay to ensure theme is applied
            });
        }

        // System theme change detection (for Automatic mode)
        if (window.matchMedia) {
            window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', function(e) {
                // Only update if we can't determine the theme otherwise or if automatic
                const html = document.documentElement;
                const themeMode = html.getAttribute('data-theme-mode');
                const theme = html.getAttribute('data-theme');

                if (!themeMode && !theme) {
                    updateStyles();
                }
            });
        }

        // Periodic check as a backup (for custom apps that might not fire all events)
        let lastThemeCheck = null;
        setInterval(function() {
            const currentTheme = isDarkMode();
            if (currentTheme !== lastThemeCheck) {
                lastThemeCheck = currentTheme;
                updateStyles();
            }
        }, 5000); // Check every 5 seconds

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
