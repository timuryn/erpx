// ERPX Sidebar Navigation Injector
frappe.provide('erpx');

erpx.SidebarInjector = class {
    constructor() {
        this.injected = false;
        this.isMenuHidden = localStorage.getItem('erpx-menu-hidden') === 'true';
        this.isAnimating = false;
        this.injectionTimeout = null;
        this.init();
    }

    init() {
        $(document).on('page-change', () => {
            if (!$('.erpx-nav-wrapper').length) {
                this.injected = false;
            }
            this.updateActiveState();
        });

        frappe.router.on('change', () => {
            if (!$('.erpx-nav-wrapper').length) {
                this.injected = false;
                this.scheduleInjection();
            } else {
                this.updateActiveState();
            }
        });

        $(window).on('resize', () => {
            this.injected = false;
            this.scheduleInjection();
        });

        this.scheduleInjection();
    }

    scheduleInjection() {
        if (this.isAnimating) return;

        if (this.injectionTimeout) {
            clearTimeout(this.injectionTimeout);
        }

        if (frappe.after_ajax) {
            frappe.after_ajax(() => {
                this.injectionTimeout = setTimeout(() => this.injectNavigation(), 300);
            });
        } else {
            this.injectionTimeout = setTimeout(() => this.injectNavigation(), 500);
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

        if (route[0] === 'Form') {
            if (route[1] && (route[1].startsWith('new-') || route[1] === 'new' || route[1].includes('/new-'))) {
                return true;
            }
            if (current_route_str.includes('/new-')) {
                return true;
            }
            if ($('input[data-fieldname="__unsaved"]').length > 0) {
                return true;
            }
            const titleText = $('.title-text').text().trim();
            if (titleText.startsWith('New ') || titleText === 'New') {
                return true;
            }
        }
        return false;
    }

    getResponsiveStyles() {
        const width = window.innerWidth;

        if (width >= 3840) {
            return { wrapperWidth: '450px', left: '40px', top: '750px', fontSize: '18px', iconSize: '24px', padding: '14px 20px', headerFontSize: '16px', headerPadding: '16px 20px', gap: '5px', borderRadius: '8px', collapsedSize: '48px', collapsedIcon: '26px' };
        } else if (width >= 2560) {
            return { wrapperWidth: '350px', left: '30px', top: '550px', fontSize: '16px', iconSize: '22px', padding: '12px 18px', headerFontSize: '14px', headerPadding: '14px 18px', gap: '4px', borderRadius: '7px', collapsedSize: '42px', collapsedIcon: '22px' };
        } else if (width >= 1920) {
            return { wrapperWidth: '250px', left: '25px', top: '450px', fontSize: '15px', iconSize: '20px', padding: '2px 5px', headerFontSize: '14px', headerPadding: '5px 16px', gap: '3px', borderRadius: '7px', collapsedSize: '36px', collapsedIcon: '20px' };
        } else if (width >= 1366) {
            return { wrapperWidth: '200px', left: '20px', top: '500px', fontSize: '14px', iconSize: '18px', padding: '2px 5px', headerFontSize: '13px', headerPadding: '5px 15px', gap: '3px', borderRadius: '6px', collapsedSize: '34px', collapsedIcon: '18px' };
        } else if (width >= 1024) {
            return { wrapperWidth: '250px', left: '15px', top: '500px', fontSize: '13px', iconSize: '16px', padding: '2px 5px', headerFontSize: '12px', headerPadding: '5px 12px', gap: '2px', borderRadius: '6px', collapsedSize: '32px', collapsedIcon: '17px' };
        } else {
            return { wrapperWidth: '210px', left: '10px', top: '450px', fontSize: '12px', iconSize: '14px', padding: '5px 5px', headerFontSize: '11px', headerPadding: '10px 10px', gap: '2px', borderRadius: '5px', collapsedSize: '30px', collapsedIcon: '16px' };
        }
    }

    // crossed-out eye (feather "eye-off"), inherits colour from the button
    getEyeOffIcon(size) {
        return `
            <svg xmlns="http://www.w3.org/2000/svg" width="${size}" height="${size}"
                 viewBox="0 0 24 24" fill="none" stroke="currentColor"
                 stroke-width="2" stroke-linecap="round" stroke-linejoin="round"
                 style="display:block !important; pointer-events:none !important;">
                <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"></path>
                <line x1="1" y1="1" x2="23" y2="23"></line>
            </svg>
        `;
    }

    getThemeStyle() {
        const isDark = document.documentElement.getAttribute('data-theme-mode') === 'dark' ||
                       document.documentElement.getAttribute('data-theme') === 'dark';
        return {
            bg: isDark ? '#1e1e1e' : '#ffffff',
            text: isDark ? '#c8c8c8' : '#333333',
            border: isDark ? '#383838' : '#d1d8dd',
            hover: isDark ? '#2a2a2a' : '#f4f5f6',
            active: isDark ? '#1a4466' : '#e8f4fd'
        };
    }

    updateActiveState() {
        const current_route = frappe.get_route_str();
        const style = this.getThemeStyle();

        const items = document.querySelectorAll('.erpx-nav-item');
        let found = false;

        items.forEach((element) => {
            const itemRoute = element.getAttribute('data-route');
            const normalizeRoute = (route) => route.toLowerCase().replace(/-/g, ' ');
            const isActive = normalizeRoute(current_route).includes(normalizeRoute(itemRoute));

            if (isActive && !found) {
                found = true;
                element.style.setProperty('color', '#009D4A', 'important');
                element.style.setProperty('border-color', '#009D4A', 'important');
                element.style.setProperty('background', style.active, 'important');
                element.style.setProperty('font-weight', '500', 'important');
                element.classList.add('active');

                document.querySelectorAll('.erpx-nav-item > span:last-child').forEach(dot => {
                    if (dot.style.width === '6px' || dot.style.width.includes('6px')) {
                        dot.remove();
                    }
                });

                const dot = document.createElement('span');
                dot.style.cssText = 'width: 6px !important; height: 6px !important; background: #009D4A !important; border-radius: 50% !important; margin-left: 8px !important; flex-shrink: 0 !important; display: inline-block !important;';
                element.appendChild(dot);
            } else {
                element.style.setProperty('color', style.text, 'important');
                element.style.setProperty('border-color', style.border, 'important');
                element.style.setProperty('background', style.bg, 'important');
                element.style.setProperty('font-weight', '400', 'important');
                element.classList.remove('active');
            }
        });
    }

    // ============================================================
    // Collapsed <-> expanded
    // Collapsed = the whole panel is gone, only a translucent
    // crossed-eye button remains where the menu used to sit.
    // ============================================================
    applyMenuState(animate) {
        const $wrapper = $('.erpx-nav-wrapper');
        if (!$wrapper.length) return;

        const wrapper = $wrapper[0];
        const panel = wrapper.querySelector('.erpx-nav-panel');
        const eye = wrapper.querySelector('.erpx-collapsed-toggle');
        const responsive = this.getResponsiveStyles();

        // keep the icon in step with the current breakpoint
        if (eye) {
            eye.style.setProperty('width', responsive.collapsedSize, 'important');
            eye.style.setProperty('height', responsive.collapsedSize, 'important');
            eye.innerHTML = this.getEyeOffIcon(parseInt(responsive.collapsedIcon));
        }

        if (this.isMenuHidden) {
            wrapper.style.setProperty('width', 'auto', 'important');
            wrapper.classList.add('erpx-collapsed');
            if (panel) panel.style.setProperty('display', 'none', 'important');
            if (eye) eye.style.setProperty('display', 'flex', 'important');
        } else {
            wrapper.style.setProperty('width', responsive.wrapperWidth, 'important');
            wrapper.classList.remove('erpx-collapsed');
            if (eye) eye.style.setProperty('display', 'none', 'important');
            if (panel) {
                panel.style.setProperty('display', 'block', 'important');
                if (animate) {
                    panel.style.setProperty('opacity', '0', 'important');
                    requestAnimationFrame(() => panel.style.setProperty('opacity', '1', 'important'));
                }
            }
        }

        this.isAnimating = false;
    }

    toggleMenu() {
        this.isMenuHidden = !this.isMenuHidden;
        localStorage.setItem('erpx-menu-hidden', this.isMenuHidden);
        this.applyMenuState(true);
    }

    injectNavigation() {
        if (this.injected || this.isAnimating) return;

        if (this.isNewDocument()) {
            $('.erpx-nav-wrapper').remove();
            return;
        }

        const sidebar = this.getSidebar();
        if (!sidebar) return;

        const existingWrapper = $('.erpx-nav-wrapper');
        if (existingWrapper.length) {
            this.injected = true;
            this.applyMenuState(false);
            this.updateActiveState();
            return;
        }

        this.injected = true;

        const current_route = frappe.get_route_str();
        const responsive = this.getResponsiveStyles();
        const style = this.getThemeStyle();

        const wrapper = $(`
            <div class="erpx-nav-wrapper" style="display: block !important; visibility: visible !important; opacity: 1 !important; position: fixed !important; left: ${responsive.left} !important; top: ${responsive.top} !important; width: ${responsive.wrapperWidth} !important; z-index: 100 !important; padding: 0 !important; margin: 0 !important;">
                <button class="erpx-collapsed-toggle" title="Schnellzugriff anzeigen"
                        style="display: none; align-items: center !important; justify-content: center !important; width: ${responsive.collapsedSize} !important; height: ${responsive.collapsedSize} !important; padding: 0 !important; margin: 0 !important; border: 1px solid ${style.border} !important; border-radius: 50% !important; background: ${style.bg} !important; color: ${style.text} !important; cursor: pointer !important; opacity: 0.5 !important; transition: opacity 0.2s ease, transform 0.2s ease !important;">
                    ${this.getEyeOffIcon(parseInt(responsive.collapsedIcon))}
                </button>
                <div class="erpx-nav-panel" style="display: block; transition: opacity 0.2s ease !important;">
                    <div class="erpx-nav-header" style="font-weight: 600 !important; padding: ${responsive.headerPadding} !important; margin-bottom: 10px !important; border-bottom: 2px solid ${style.border} !important; color: ${style.text} !important; font-size: ${responsive.headerFontSize} !important; text-transform: uppercase !important; letter-spacing: 0.5px !important; display: flex !important; align-items: center !important; justify-content: space-between !important; visibility: visible !important; background: ${style.bg} !important; border-radius: ${responsive.borderRadius} ${responsive.borderRadius} 0 0 !important;">
                        <span>🚀 Schnellzugriff</span>
                        <button class="erpx-toggle-menu" title="Schnellzugriff ausblenden"
                                style="background: none !important; border: none !important; color: ${style.text} !important; cursor: pointer !important; padding: 0 !important; margin: 0 !important; display: flex !important; align-items: center !important; justify-content: center !important; width: 20px !important; height: 20px !important; transition: transform 0.2s ease, opacity 0.2s ease !important; opacity: 0.65 !important; flex-shrink: 0 !important;">
                            ${this.getEyeOffIcon(Math.max(14, parseInt(responsive.headerFontSize)))}
                        </button>
                    </div>
                    <div class="erpx-nav-list" style="display: flex; flex-direction: column !important; gap: ${responsive.gap} !important; visibility: visible !important; background: ${style.bg} !important; padding: 0 0 10px 0 !important; border-radius: 0 0 ${responsive.borderRadius} ${responsive.borderRadius} !important; overflow-y: auto !important;"></div>
                </div>
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
            const normalizeRoute = (route) => route.toLowerCase().replace(/-/g, ' ');
            const isActive = normalizeRoute(current_route).includes(normalizeRoute(itemRoute));

            const link = $(`
                <a href="${item.url}" class="erpx-nav-item ${isActive ? 'active' : ''}" data-route="${itemRoute}" style="display: flex !important; align-items: center !important; padding: ${responsive.padding} !important; text-decoration: none !important; color: ${isActive ? '#009D4A' : style.text} !important; border: 1px solid ${isActive ? '#009D4A' : style.border} !important; border-radius: ${responsive.borderRadius} !important; background: ${isActive ? style.active : style.bg} !important; margin: 0 10px 2px 10px !important; transition: all 0.2s ease !important; font-size: ${responsive.fontSize} !important; cursor: pointer !important; visibility: visible !important; opacity: 1 !important; font-weight: ${isActive ? '500' : '400'} !important;">
                    <span class="erpx-nav-icon" style="margin-right: 10px !important; font-size: ${responsive.iconSize} !important; width: ${parseInt(responsive.iconSize) + 8}px !important; text-align: center !important; flex-shrink: 0 !important; display: inline-block !important;">${item.icon}</span>
                    <span style="flex: 1 !important; display: inline-block !important;">${item.name}</span>
                    ${isActive ? `<span style="width: 6px !important; height: 6px !important; background: #009D4A !important; border-radius: 50% !important; margin-left: 8px !important; flex-shrink: 0 !important; display: inline-block !important;"></span>` : ''}
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

        const self = this;
        wrapper.find('.erpx-toggle-menu, .erpx-collapsed-toggle').on('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            self.toggleMenu();
        });

        $('body').append(wrapper);

        $('#erpx-nav-styles').remove();
        $('head').append(`
            <style id="erpx-nav-styles">
                .erpx-nav-wrapper { display: block !important; visibility: visible !important; opacity: 1 !important; position: fixed !important; transition: width 0.2s ease !important; }
                .erpx-nav-list { display: flex; flex-direction: column !important; }
                .erpx-nav-item { position: relative !important; z-index: 1 !important; }

                /* collapsed state — translucent until you reach for it */
                .erpx-collapsed-toggle:hover { opacity: 1 !important; transform: scale(1.1) !important; border-color: #009D4A !important; color: #009D4A !important; }
                .erpx-collapsed-toggle:focus-visible { opacity: 1 !important; outline: 2px solid #009D4A !important; outline-offset: 2px !important; }
                .erpx-nav-wrapper.erpx-collapsed { box-shadow: none !important; filter: none !important; }

                .erpx-toggle-menu:hover { transform: scale(1.15) !important; opacity: 1 !important; color: #009D4A !important; }
                .erpx-nav-list::-webkit-scrollbar { width: ${parseInt(responsive.fontSize) > 15 ? '6px' : '4px'} !important; }
                .erpx-nav-list::-webkit-scrollbar-thumb { background: ${style.border} !important; border-radius: 2px !important; }
                .erpx-nav-list::-webkit-scrollbar-track { background: transparent !important; }
                @media (min-width: 3840px) { .erpx-nav-wrapper:not(.erpx-collapsed) { filter: drop-shadow(0 4px 12px rgba(0,0,0,0.15)); } .erpx-nav-item:hover { box-shadow: 0 4px 12px rgba(0,0,0,0.15); } }
                @media (min-width: 2560px) and (max-width: 3839px) { .erpx-nav-wrapper:not(.erpx-collapsed) { filter: drop-shadow(0 3px 10px rgba(0,0,0,0.12)); } .erpx-nav-item:hover { box-shadow: 0 3px 10px rgba(0,0,0,0.12); } }
                @media (min-width: 1920px) and (max-width: 2559px) { .erpx-nav-wrapper:not(.erpx-collapsed) { filter: drop-shadow(0 2px 8px rgba(0,0,0,0.1)); } }
                @media (max-width: 1024px) { .erpx-nav-wrapper { display: none !important; } }
            </style>
        `);

        this.applyMenuState(false);
        this.updateActiveState();
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
