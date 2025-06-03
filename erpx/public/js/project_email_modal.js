// File: erpx/public/js/project.js

frappe.ui.form.on('Project', {
    refresh: function(frm) {
        // Function to add project link button to email modal
        function addProjectLinkToEmailModal() {
            // Use event delegation to handle dynamically created email buttons
            $(document).off('click.project-email').on('click.project-email', '.btn.btn-xs.btn-secondary.action-btn', function() {
                setTimeout(function() {
                    // Look for the email modal
                    var emailModal = $('.modal:visible').last();
                    if (emailModal.length && !emailModal.find('.project-link-btn').length) {
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
                }, 1000);
            });
        }
        
        // Function to add project link to email content
        function addProjectLinkToContent(frm, modal) {
            if (frm && frm.doc && frm.doc.name) {
                var projectName = frm.doc.name;
                var projectLink = `<br><br>Den Link zum entsprechenden Projekt finden Sie unten:<br><a href="http://192.168.178.180:8080/app/project/${projectName}">Klicken Sie hier, um das Projekt anzuzeigen</a>`;
                
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
