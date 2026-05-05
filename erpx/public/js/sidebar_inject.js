// ERPX Sidebar Navigation Injector
frappe.provide('erpx');

erpx.SidebarInjector = class {
    constructor() {
        this.injected = false;
        this.init();
    }

    init() {
        $(document).on('page-change', () => {
            this.injected = false;
            this.scheduleInjection();
        });

        frappe.router.on('change', () => {
            this.injected = false;
            this.scheduleInjection();
        });

        // Re-inject on window resize for responsive adjustments
        $(window).on('resize', () => {
            this.injected = false;
            this.scheduleInjection();
        });

        this.scheduleInjection();
    }

    scheduleInjection() {
        if (frappe.after_ajax) {
            frappe.after_ajax(() => {
                setTimeout(() => this.injectNavigation(), 300);
            });
        } else {
            setTimeout(() => this.injectNavigation(), 500);
        }
    }

    getSidebar() {
        const sidebars = $('.layout-side-section').filter(function() {
            const $this = $(this);
            return $this.width() > 0 && $this.css('display') !== 'none';
        });
        
        return sidebars.length ? sidebars.first() : null;
    }

	isNewDocument() {
		const route = frappe.get_route();
		const current_route_str = frappe.get_route_str();
		
		// Check if we're on a Form view
		if (route[0] === 'Form') {
			// Check if the document name contains "new-" prefix
			if (route[1] && (
				route[1].startsWith('new-') || 
				route[1] === 'new' ||
				route[1].includes('/new-')  // Handle cases like "sales-invoice/new-sales-invoice"
			)) {
				return true;
			}
			
			// Check URL path for new document pattern
			if (current_route_str.includes('/new-')) {
				return true;
			}
			
			// Check for the hidden input that exists on new documents
			if ($('input[data-fieldname="__unsaved"]').length > 0) {
				return true;
			}
			
			// Check if the form title contains "New" or "Draft"
			const titleText = $('.title-text').text().trim();
			if (titleText.startsWith('New ') || titleText === 'New') {
				return true;
			}
		}
		
		return false;
	}

    getResponsiveStyles() {
        const width = window.innerWidth;
        const height = window.innerHeight;
        
        // 4K and above (3840px+)
        if (width >= 3840) {
            return {
                wrapperWidth: '450px',
                left: '40px',
                top: '750px',
                fontSize: '18px',
                iconSize: '24px',
                padding: '14px 20px',
                headerFontSize: '16px',
                headerPadding: '16px 20px',
                gap: '5px',
                borderRadius: '8px',
            };
        }
        // 2K (2560px - 3839px)
        else if (width >= 2560) {
            return {
                wrapperWidth: '350px',
                left: '30px',
                top: '550px',
                fontSize: '16px',
                iconSize: '22px',
                padding: '12px 18px',
                headerFontSize: '14px',
                headerPadding: '14px 18px',
                gap: '4px',
                borderRadius: '7px',
            };
        }
        // HD/Full HD (1920px - 2559px)
        else if (width >= 1920) {
            return {
                wrapperWidth: '250px',
                left: '25px',
                top: '450px',
                fontSize: '15px',
                iconSize: '20px',
                padding: '2px 5px',
                headerFontSize: '14px',
                headerPadding: '5px 16px',
                gap: '3px',
                borderRadius: '7px',
            };
        }
        // HD Ready (1366px - 1919px)
        else if (width >= 1366) {
            return {
                wrapperWidth: '200px',
                left: '20px',
                top: '500px',
                fontSize: '14px',
                iconSize: '18px',
                padding: '2px 5px',
                headerFontSize: '13px',
                headerPadding: '5px 15px',
                gap: '3px',
                borderRadius: '6px',
            };
        }
        // Tablet/Laptop (1024px - 1365px)
        else if (width >= 1024) {
            return {
                wrapperWidth: '250px',
                left: '15px',
                top: '500px',
                fontSize: '13px',
                iconSize: '16px',
                padding: '2px 5px',
                headerFontSize: '12px',
                headerPadding: '5px 12px',
                gap: '2px',
                borderRadius: '6px',
            };
        }
        // Mobile/Tablet Portrait (< 1024px)
        else {
            return {
                wrapperWidth: '210px',
                left: '10px',
                top: '450px',
                fontSize: '12px',
                iconSize: '14px',
                padding: '5px 5px',
                headerFontSize: '11px',
                headerPadding: '10px 10px',
                gap: '2px',
                borderRadius: '5px',
            };
        }
    }

    injectNavigation() {
        if (this.injected) return;

        // Don't show on new document pages
        if (this.isNewDocument()) {
            $('.erpx-nav-wrapper').remove();
            return;
        }

        const sidebar = this.getSidebar();
        if (!sidebar) return;

        this.injected = true;
        $('.erpx-nav-wrapper').remove();

        const current_route = frappe.get_route_str();
        const responsive = this.getResponsiveStyles();
        const isDark = document.documentElement.getAttribute('data-theme-mode') === 'dark' ||
                      document.documentElement.getAttribute('data-theme') === 'dark';

        const style = {
            bg: isDark ? '#1e1e1e' : '#ffffff',
            text: isDark ? '#c8c8c8' : '#333333',
            border: isDark ? '#383838' : '#d1d8dd',
            hover: isDark ? '#2a2a2a' : '#f4f5f6',
            active: isDark ? '#1a4466' : '#e8f4fd'
        };

        const wrapper = $(`
            <div class="erpx-nav-wrapper" style="
                display: block !important;
                visibility: visible !important;
                opacity: 1 !important;
                position: fixed !important;
                left: ${responsive.left} !important;
                top: ${responsive.top} !important;
                width: ${responsive.wrapperWidth} !important;
                z-index: 100 !important;
                padding: 0 !important;
                margin: 0 !important;
            ">
                <div class="erpx-nav-header" style="
                    font-weight: 600 !important;
                    padding: ${responsive.headerPadding} !important;
                    margin-bottom: 10px !important;
                    border-bottom: 2px solid ${style.border} !important;
                    color: ${style.text} !important;
                    font-size: ${responsive.headerFontSize} !important;
                    text-transform: uppercase !important;
                    letter-spacing: 0.5px !important;
                    display: block !important;
                    visibility: visible !important;
                    background: ${style.bg} !important;
                    border-radius: ${responsive.borderRadius} ${responsive.borderRadius} 0 0 !important;
                ">
                    🚀 Schnellzugriff
                </div>
                <div class="erpx-nav-list" style="
                    display: flex !important;
                    flex-direction: column !important;
                    gap: ${responsive.gap} !important;
                    visibility: visible !important;
                    background: ${style.bg} !important;
                    padding: 0 0 10px 0 !important;
                    border-radius: 0 0 ${responsive.borderRadius} ${responsive.borderRadius} !important;
                    max-height: ${responsive.maxHeight} !important;
                    overflow-y: auto !important;
                "></div>
            </div>
        `);

        const items = [
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

        const navList = wrapper.find('.erpx-nav-list');

        items.forEach(item => {
            const itemRoute = item.url.replace('/app/', '');
            const isActive = current_route.includes(itemRoute);
            
            const link = $(`
                <a href="${item.url}" 
                   class="erpx-nav-item ${isActive ? 'active' : ''}"
                   data-route="${itemRoute}"
                   style="
                    display: flex !important;
                    align-items: center !important;
                    padding: ${responsive.padding} !important;
                    text-decoration: none !important;
                    color: ${isActive ? '#009D4A' : style.text} !important;
                    border: 1px solid ${isActive ? '#009D4A' : style.border} !important;
                    border-radius: ${responsive.borderRadius} !important;
                    background: ${isActive ? style.active : style.bg} !important;
                    margin: 0 10px 2px 10px !important;
                    transition: all 0.2s ease !important;
                    font-size: ${responsive.fontSize} !important;
                    cursor: pointer !important;
                    visibility: visible !important;
                    opacity: 1 !important;
                    font-weight: ${isActive ? '500' : '400'} !important;
                ">
                    <span class="erpx-nav-icon" style="
                        margin-right: 10px !important;
                        font-size: ${responsive.iconSize} !important;
                        width: ${parseInt(responsive.iconSize) + 8}px !important;
                        text-align: center !important;
                        flex-shrink: 0 !important;
                        display: inline-block !important;
                    ">${item.icon}</span>
                    <span style="
                        flex: 1 !important;
                        display: inline-block !important;
                    ">${item.name}</span>
                    ${isActive ? `
                        <span style="
                            width: 6px !important;
                            height: 6px !important;
                            background: #009D4A !important;
                            border-radius: 50% !important;
                            margin-left: 8px !important;
                            flex-shrink: 0 !important;
                            display: inline-block !important;
                        "></span>
                    ` : ''}
                </a>
            `);

            link.on('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                frappe.set_route(itemRoute);
            });

            link.on('mouseenter', function() {
                if (!$(this).hasClass('active')) {
                    $(this).css({
                        'background': style.hover,
                        'border-color': '#009D4A',
                        'transform': `translateX(${parseInt(responsive.fontSize) > 15 ? '5px' : '3px'})`
                    });
                }
            }).on('mouseleave', function() {
                if (!$(this).hasClass('active')) {
                    $(this).css({
                        'background': style.bg,
                        'border-color': style.border,
                        'transform': 'translateX(0)'
                    });
                }
            });

            navList.append(link);
        });

        $('body').append(wrapper);

        // Update existing styles if they exist, otherwise add new
        $('#erpx-nav-styles').remove();
        $('head').append(`
            <style id="erpx-nav-styles">
                .erpx-nav-wrapper {
                    display: block !important;
                    visibility: visible !important;
                    opacity: 1 !important;
                    position: fixed !important;
                    transition: all 0.3s ease !important;
                }
                
                .erpx-nav-list {
                    display: flex !important;
                    flex-direction: column !important;
                }
                
                .erpx-nav-item {
                    position: relative !important;
                    z-index: 1 !important;
                }
                
                .erpx-nav-list::-webkit-scrollbar {
                    width: ${parseInt(responsive.fontSize) > 15 ? '6px' : '4px'} !important;
                }
                
                .erpx-nav-list::-webkit-scrollbar-thumb {
                    background: ${style.border} !important;
                    border-radius: 2px !important;
                }
                
                .erpx-nav-list::-webkit-scrollbar-track {
                    background: transparent !important;
                }

                /* Screen-specific adjustments */
                @media (min-width: 3840px) {
                    .erpx-nav-wrapper {
                        filter: drop-shadow(0 4px 12px rgba(0,0,0,0.15));
                    }
                    .erpx-nav-item:hover {
                        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                    }
                }

                @media (min-width: 2560px) and (max-width: 3839px) {
                    .erpx-nav-wrapper {
                        filter: drop-shadow(0 3px 10px rgba(0,0,0,0.12));
                    }
                    .erpx-nav-item:hover {
                        box-shadow: 0 3px 10px rgba(0,0,0,0.12);
                    }
                }

                @media (min-width: 1920px) and (max-width: 2559px) {
                    .erpx-nav-wrapper {
                        filter: drop-shadow(0 2px 8px rgba(0,0,0,0.1));
                    }
                }

                @media (max-width: 1024px) {
                    .erpx-nav-wrapper {
                        display: none !important;
                    }
                }
            </style>
        `);
    }
}

$(function() {
    const init = () => {
        if (window.frappe?.boot && !window._erpxSidebarInjected) {
            window._erpxSidebarInjected = true;
            new erpx.SidebarInjector();
            return true;
        }
        return false;
    };

    if (!init()) {
        let attempts = 0;
        const interval = setInterval(() => {
            attempts++;
            if (init() || attempts > 50) {
                clearInterval(interval);
            }
        }, 200);
    }
});
