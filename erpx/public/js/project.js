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
                            <strong>Zeitraum:</strong> September 2024 - September 2025 (inkl. Timesheets & Google Calendar Events)
                        </p>
                    </div>
                `);
            }

            $heatmap.html('');

            frappe.call({
                method: "erpx.custom_scripts.activity.get_project_heatmap_data",
                args: {
                    project: frm.doc.name
                },
                callback: function(r) {
                    try {
                        console.log("📊 Heatmap data received:", r.message);
                        
                        if (r.message && $heatmap.length > 0) {
                            var heatmapData, activityDetails;

                            if (r.message.heatmap_data) {
                                heatmapData = r.message.heatmap_data;
                                activityDetails = r.message.activity_details || {};
                                
                                // DEBUG: Show non-empty activities
                                Object.keys(activityDetails).forEach(function(timestamp) {
                                    if (activityDetails[timestamp].activities.length > 0) {
                                        var date = new Date(parseInt(timestamp) * 1000);
                                        console.log(`🎯 Found activity at timestamp ${timestamp} (${date.toISOString().split('T')[0]}):`, activityDetails[timestamp]);
                                    }
                                });
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
        console.log("🔧 Setting up enhanced tooltips");
        
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

                console.log(`🔍 Processing day ${date} (index ${index}), chart timestamp: ${chartTimestamp}, value: ${value}`);
                
                // DEBUG: Check if there's activity data at any nearby timestamps
                var nearbyTimestamps = [];
                for (var i = -21; i <= 21; i++) {
                    var testTimestamp = chartTimestamp + (i * 86400); // Add/subtract days in seconds
                    if (activityDetails[testTimestamp] && activityDetails[testTimestamp].activities.length > 0) {
                        var testDate = new Date(testTimestamp * 1000);
                        nearbyTimestamps.push({
                            timestamp: testTimestamp,
                            offset: i,
                            date: testDate.toISOString().split('T')[0],
                            activities: activityDetails[testTimestamp].activities.length
                        });
                    }
                }
                if (nearbyTimestamps.length > 0) {
                    console.log(`🔍 Found nearby activities for ${date}:`, nearbyTimestamps);
                }
                
                var details = activityDetails[chartTimestamp];
                
                // TEMPORARY FIX: If no details found, try looking 20 days later (the exact offset we found)
                if (!details || details.activities.length === 0) {
                    var alternateTimestamp = chartTimestamp + (20 * 86400); // Add 20 days in seconds
                    if (activityDetails[alternateTimestamp] && activityDetails[alternateTimestamp].activities.length > 0) {
                        console.log(`🔧 Using alternate timestamp ${alternateTimestamp} instead of ${chartTimestamp}`);
                        details = activityDetails[alternateTimestamp];
                    }
                }
                
                console.log(`📋 Details for timestamp ${chartTimestamp}:`, details);
                
                var tooltipContent;

                if (details && details.activities && details.activities.length > 0) {
                    var niceDate = formatDateNice(date);
                    console.log(`✅ Found ${details.activities.length} activities for ${date}`);
                    
                    var activityLines = details.activities.map(function(activity) {
                        console.log("🔍 Processing activity:", activity);
                        
                        // Enhanced display for calendar events with full subject
                        if (activity.source === 'calendar') {
                            var fullSubject = activity.full_subject || activity.type;
                            // Remove emoji and clean up if needed
                            if (fullSubject.startsWith('📅 ')) {
                                fullSubject = fullSubject.substring(2);
                            }
                            console.log("📋 Calendar event full subject:", fullSubject);
                            return `📅 <strong>Event:</strong> ${fullSubject} - ${activity.hours} Stunden`;
                        } else {
                            return `${activity.type} - ${activity.hours} Stunden`;
                        }
                    });
                    tooltipContent = activityLines.join('<br>') + `<br><small><strong>Datum:</strong> ${niceDate}</small>`;
                } else {
                    console.log(`❌ No activities found for ${date}, using fallback`);
                    var niceDate = formatDateNice(date);
                    tooltipContent = `${value} Stunden am ${niceDate}`;
                }

                console.log("💬 Final tooltip content:", tooltipContent);

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
            background: rgba(0, 0, 0, 0.9);
            color: white;
            padding: 12px 16px;
            border-radius: 6px;
            font-size: 13px;
            line-height: 1.5;
            z-index: 1000;
            pointer-events: none;
            max-width: 350px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            border: 1px solid rgba(255,255,255,0.1);
        ">${content}</div>
    `);

    $('body').append(tooltip);

    var x = event.pageX + 15;
    var y = event.pageY - 10;

    // Prevent tooltip from going off screen
    var tooltipWidth = tooltip.outerWidth();
    var tooltipHeight = tooltip.outerHeight();
    var windowWidth = $(window).width();
    var windowHeight = $(window).height();

    if (x + tooltipWidth > windowWidth) {
        x = event.pageX - tooltipWidth - 15;
    }
    if (y + tooltipHeight > windowHeight) {
        y = event.pageY - tooltipHeight - 10;
    }

    tooltip.css({
        left: x + 'px',
        top: y + 'px'
    });
}

function hideCustomTooltip() {
    $('.custom-heatmap-tooltip').remove();
}

// Email functionality (unchanged)
frappe.ui.form.on('Project', {
    refresh: function(frm) {
        // Variable to track if new email button was clicked
        let isNewEmail = false;

        // Function to add project link button to email modal
        function addProjectLinkToEmailModal() {
            // Use event delegation to handle dynamically created email buttons
            $(document).off('click.project-email').on('click.project-email', '.btn.btn-xs.btn-secondary.action-btn', function() {
                // Check if this is the "Neue E-Mail" button
                const buttonText = $(this).text().trim();
                isNewEmail = buttonText === 'Neue E-Mail';

                setTimeout(function() {
                    // Look for the email modal
                    var emailModal = $('.modal:visible').last();
                    if (emailModal.length) {
                        // Handle subject line for new emails
                        if (isNewEmail) {
                            setNewEmailSubject(frm, emailModal);
                        }

                        // Add project link button if not already present
                        if (!emailModal.find('.project-link-btn').length) {
                            addProjectLinkButton(frm, emailModal);
                        }
                    }
                }, 1000);
            });

            // Handle reply button clicks
            $(document).off('click.project-reply').on('click.project-reply', 'a.action-btn.reply', function() {
                isNewEmail = false; // This is a reply

                setTimeout(function() {
                    // Look for the email modal
                    var emailModal = $('.modal:visible').last();
                    if (emailModal.length) {
                        // Handle subject line for replies
                        setReplyEmailSubject(frm, emailModal);

                        // Add project link button if not already present
                        if (!emailModal.find('.project-link-btn').length) {
                            addProjectLinkButton(frm, emailModal);
                        }
                    }
                }, 1000);
            });
        }

        // Function to set subject for new emails
        function setNewEmailSubject(frm, modal) {
            if (frm && frm.doc && frm.doc.name && frm.doc.project_name) {
                var projectName = frm.doc.project_name;
                var projectId = frm.doc.name;
                var newSubject = `${projectName} (${projectId})`;

                // Try to find the subject field
                var subjectField = modal.find('input[data-fieldname="subject"]');
                if (subjectField.length) {
                    // Clear any existing subject and set the new one
                    subjectField.val(newSubject);
                    // Trigger change event to ensure it's properly registered
                    subjectField.trigger('change');
                } else {
                    // Alternative selector for subject field
                    var subjectInput = modal.find('.frappe-control[data-fieldname="subject"] input');
                    if (subjectInput.length) {
                        subjectInput.val(newSubject);
                        subjectInput.trigger('change');
                    }
                }
            }
        }

        // Function to set subject for reply emails
        function setReplyEmailSubject(frm, modal) {
            if (frm && frm.doc && frm.doc.name && frm.doc.project_name) {
                var projectName = frm.doc.project_name;
                var projectId = frm.doc.name;
                var baseSubject = `${projectName} (${projectId})`;

                // Try to find the subject field
                var subjectField = modal.find('input[data-fieldname="subject"]');
                if (subjectField.length) {
                    var currentSubject = subjectField.val();
                    // Only add Re: if it doesn't already exist
                    if (currentSubject && !currentSubject.startsWith('Re:')) {
                        subjectField.val(`Re: ${currentSubject}`);
                    } else if (!currentSubject) {
                        // If no subject, use the base subject with Re:
                        subjectField.val(`Re: ${baseSubject}`);
                    }
                    // Trigger change event to ensure it's properly registered
                    subjectField.trigger('change');
                } else {
                    // Alternative selector for subject field
                    var subjectInput = modal.find('.frappe-control[data-fieldname="subject"] input');
                    if (subjectInput.length) {
                        var currentSubject = subjectInput.val();
                        if (currentSubject && !currentSubject.startsWith('Re:')) {
                            subjectInput.val(`Re: ${currentSubject}`);
                        } else if (!currentSubject) {
                            subjectInput.val(`Re: ${baseSubject}`);
                        }
                        subjectInput.trigger('change');
                    }
                }
            }
        }

        // Function to add project link button to email modal
        function addProjectLinkButton(frm, emailModal) {
            // Find the signature button area
            var signatureBtn = emailModal.find('button[data-fieldname="add_signature"]');

            if (signatureBtn.length) {
                // Create project link button
                var projectLinkBtn = $(`
                    <button type="button" class="btn btn-sm btn-default project-link-btn" style="margin-left: 10px;">
                        <i class="fa fa-link"></i> Projektlink hinzufügen
                    </button>
                `);

                // Add click handler
                projectLinkBtn.on('click', function() {
                    addProjectLinkToContent(frm, emailModal);
                });

                // Insert button after signature button
                signatureBtn.after(projectLinkBtn);
            } else {
                // Fallback: add button to form actions area
                var formActions = emailModal.find('.form-actions');
                if (formActions.length) {
                    var projectLinkBtn = $(`
                        <button type="button" class="btn btn-sm btn-default project-link-btn" style="margin-right: 10px;">
                            <i class="fa fa-link"></i> Projektlink hinzufügen
                        </button>
                    `);

                    projectLinkBtn.on('click', function() {
                        addProjectLinkToContent(frm, emailModal);
                    });

                    formActions.prepend(projectLinkBtn);
                }
            }
        }

        // Function to add project link to email content
        function addProjectLinkToContent(frm, modal) {
            if (frm && frm.doc && frm.doc.name) {
                var projectName = frm.doc.name;
                var projectLink = `<br><br>Den Link zum entsprechenden Projekt finden Sie unten:<br><a href="https://chow-ruling-closely.ngrok-free.app/app/project/${projectName}">Klicken Sie hier, um das Projekt anzuzeigen</a>`;

                // Try to find the content editor
                var contentEditor = modal.find('.frappe-control[data-fieldname="content"] .ql-editor');

                if (contentEditor.length) {
                    // Quill editor found
                    var currentContent = contentEditor.html();
                    contentEditor.html(currentContent + projectLink);
                } else {
                    // Try to find textarea fallback
                    var contentTextarea = modal.find('textarea[data-fieldname="content"]');
                    if (contentTextarea.length) {
                        var currentContent = contentTextarea.val();
                        contentTextarea.val(currentContent + projectLink);
                    } else {
                        frappe.msgprint('Could not find email content editor');
                    }
                }
            } else {
                frappe.msgprint('No project data available');
            }
        }

        // Initialize the email modal handler
        addProjectLinkToEmailModal();
    }
});
