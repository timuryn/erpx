console.log("🚀 Project heatmap override script loaded");

frappe.ui.form.on('Project', {
    refresh: function(frm) {
        setTimeout(function() {
            override_project_heatmap(frm);
        }, 2000);
    }
});

function override_project_heatmap(frm) {
    try {
        var $heatmap = frm.page.main.find('.heatmap');
        
        if ($heatmap.length > 0) {
            var $container = $heatmap.closest('.heatmap-container');
            if ($container.length > 0 && !$container.find('.heatmap-explanation').length) {
                $container.prepend(`
                    <div class="heatmap-explanation" style="text-align: center; margin-bottom: 15px; padding: 10px; background-color: #f8f9fa; border-radius: 6px; border-left: 4px solid #007bff;">
                        <h5 style="margin: 0 0 5px 0; color: #007bff;">📅 Erweiterte Aktivitäts-Heatmap</h5>
                        <p style="margin: 0; font-size: 13px; color: #666;">
                            <strong>Zeitraum:</strong> September 2024 - September 2025 (inkl. nächste 60 Tage)
                        </p>
                    </div>
                `);
            }
            
            $heatmap.html('');
            
            frappe.call({
                method: "erpx.overrides.activity.get_project_heatmap_data",
                args: {
                    project: frm.doc.name
                },
                callback: function(r) {
                    try {
                        if (r.message && $heatmap.length > 0) {
                            var heatmapData, activityDetails;
                            
                            if (r.message.heatmap_data) {
                                heatmapData = r.message.heatmap_data;
                                activityDetails = r.message.activity_details || {};
                            } else {
                                heatmapData = r.message;
                                activityDetails = {};
                            }
                            
                            new frappe.Chart($heatmap.get(0), {
                                type: "heatmap",
                                discreteDomains: 1,
                                countLabel: "Stunden",
                                radius: 3,
                                data: {
                                    dataPoints: heatmapData,
                                },
                            });
                            
                            setTimeout(function() {
                                fixMonthLabels($heatmap);
                                fixTooltips($heatmap);
                                
                                if (Object.keys(activityDetails).length > 0) {
                                    setupEnhancedTooltips($heatmap, activityDetails);
                                }
                            }, 1000);
                        }
                    } catch (e) {
                        console.log("❌ Error in callback:", e);
                    }
                }
            });
        }
    } catch (e) {
        console.log("❌ Error in override_project_heatmap:", e);
    }
}

function fixMonthLabels($heatmap) {
    try {
        var $svg = $heatmap.find('svg');
        if ($svg.length === 0) return;
        
        var $monthLabels = $svg.find('text.domain-name');
        var monthMap = {
            'JUL': 'SEP',  'AUG': 'OCT',  'SEP': 'NOV',  'OCT': 'DEC',
            'NOV': 'JAN',  'DEC': 'FEB',  'JAN': 'MAR',  'FEB': 'APR',
            'MAR': 'MAY',  'APR': 'JUN',  'MAY': 'JUL',  'JUN': 'AUG'
        };
        
        $monthLabels.each(function() {
            var $label = $(this);
            var currentText = $label.text().trim();
            if (monthMap[currentText]) {
                $label.text(monthMap[currentText]);
            }
        });
    } catch (e) {
        console.log("❌ Error fixing month labels:", e);
    }
}

function fixTooltips($heatmap) {
    try {
        var $svg = $heatmap.find('svg');
        if ($svg.length === 0) return;
        
        var $dayRects = $svg.find('rect.day[data-date]');
        
        $dayRects.each(function() {
            var $rect = $(this);
            var originalDate = $rect.attr('data-date');
            
            if (originalDate) {
                try {
                    var parts = originalDate.split('-');
                    var year = parseInt(parts[0]);
                    var month = parseInt(parts[1]) - 1;
                    var day = parseInt(parts[2]);
                    
                    var originalDateObj = new Date(year, month, day);
                    var newDateObj;
                    
                    if (year === 2024) {
                        newDateObj = new Date(year, month + 2, day);
                        if (newDateObj.getMonth() !== (month + 2) % 12) {
                            newDateObj = new Date(year + Math.floor((month + 2) / 12), (month + 2) % 12 + 1, 0);
                        }
                    } else if (year === 2025) {
                        if (month >= 7) {
                            newDateObj = new Date(originalDateObj);
                            newDateObj.setDate(newDateObj.getDate() - 1);
                        } else {
                            newDateObj = new Date(year, month + 2, day);
                            if (newDateObj.getMonth() !== (month + 2) % 12) {
                                newDateObj = new Date(year, month + 2 + 1, 0);
                            }
                        }
                    } else {
                        newDateObj = new Date(originalDateObj);
                    }
                    
                    var newYear = newDateObj.getFullYear();
                    var newMonth = String(newDateObj.getMonth() + 1).padStart(2, '0');
                    var newDay = String(newDateObj.getDate()).padStart(2, '0');
                    var newDateStr = `${newYear}-${newMonth}-${newDay}`;
                    
                    $rect.attr('data-date', newDateStr);
                } catch (e) {
                    // Silently continue on date processing errors
                }
            }
        });
    } catch (e) {
        console.log("❌ Error fixing tooltips:", e);
    }
}

function setupEnhancedTooltips($heatmap, activityDetails) {
    try {
        // Hide default tooltips
        if (!$('#heatmap-tooltip-override').length) {
            $('head').append(`
                <style id="heatmap-tooltip-override">
                    .chart-tooltip,
                    .tooltip,
                    .frappe-chart-tooltip {
                        display: none !important;
                    }
                </style>
            `);
        }
        
        var $svg = $heatmap.find('svg');
        if ($svg.length === 0) return;
        
        var $dayRects = $svg.find('rect.day[data-date]');
        
        // Clean up existing tooltips and handlers
        $('body').find('.custom-heatmap-tooltip').remove();
        $dayRects.off('mouseenter.custom mouseleave.custom');
        
        $dayRects.each(function(index) {
            var $rect = $(this);
            var date = $rect.attr('data-date');
            var value = parseFloat($rect.attr('data-value')) || 0;
            
            if (value > 0) {
                var chartStart = new Date('2024-07-08');
                var originalChartDate = new Date(chartStart);
                originalChartDate.setDate(chartStart.getDate() + index);
                var chartTimestamp = Math.floor(originalChartDate.getTime() / 1000);
                
                var details = activityDetails[chartTimestamp];
                var tooltipContent;
                
                if (details && details.activities && details.activities.length > 0) {
                    var niceDate = formatDateNice(date);
                    var activityLines = details.activities.map(function(activity) {
                        return `${activity.type} - ${activity.hours} Stunden`;
                    });
                    tooltipContent = activityLines.join('<br>') + `<br><small>am ${niceDate}</small>`;
                } else {
                    var niceDate = formatDateNice(date);
                    tooltipContent = `${value} Stunden am ${niceDate}`;
                }
                
                $rect.on('mouseenter.custom', function(e) {
                    showCustomTooltip(e, tooltipContent);
                });
                
                $rect.on('mouseleave.custom', function() {
                    hideCustomTooltip();
                });
                
                $rect.removeAttr('title');
            }
        });
    } catch (e) {
        console.log("❌ Error setting up enhanced tooltips:", e);
    }
}

function formatDateNice(dateStr) {
    try {
        var date = new Date(dateStr);
        var months = ['Jan', 'Feb', 'Mär', 'Apr', 'Mai', 'Jun',
                     'Jul', 'Aug', 'Sep', 'Okt', 'Nov', 'Dez'];
        return `${date.getDate()}. ${months[date.getMonth()]} ${date.getFullYear()}`;
    } catch (e) {
        return dateStr;
    }
}

function showCustomTooltip(event, content) {
    hideCustomTooltip();
    
    var tooltip = $(`
        <div class="custom-heatmap-tooltip" style="
            position: absolute;
            background: rgba(0, 0, 0, 0.8);
            color: white;
            padding: 8px 12px;
            border-radius: 4px;
            font-size: 12px;
            line-height: 1.4;
            z-index: 1000;
            pointer-events: none;
            max-width: 250px;
        ">${content}</div>
    `);
    
    $('body').append(tooltip);
    
    var x = event.pageX + 10;
    var y = event.pageY - 10;
    
    tooltip.css({
        left: x + 'px',
        top: y + 'px'
    });
}

function hideCustomTooltip() {
    $('.custom-heatmap-tooltip').remove();
}
