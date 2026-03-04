# EEA-AG V3.0 Project Plan

## Phase 1: Planning & Modular Architecture
- [ ] Read and analyze current `app.py`
- [ ] Design the modular directory structure
- [ ] Define database models and schema changes (statut_membre, audit log, OTP, etc.)
- [ ] Create implementation plan and review with user

## Phase 2: Core Application & Back-office (Module 1)
- [x] Setup Flask application factory and Blueprints
- [x] Initialize Database (SQLAlchemy) and migrate existing data
- [x] Implement Authentication & Roles (Admin, Gestion)
- [x] Implement Member Management (CRUD, new statuses)
- [x] Implement Advanced Dashboard (Stats, Datatable)
- [x] Implement Real-time Quorum Gauge
- [x] Implement Audit Log system
- [x] Implement Google Sheet Sync (Action 0)

## Phase 3: Members Portal / DMZ (Module 2)
- [x] Implement New Member Registration Form (Future member + Email)
- [x] Implement Secure Profile Modification (OTP validation, pending_modifications table)
- [x] Implement Annual Renewal Form
- [x] Implement Online Proxy Declaration (Max 2, AGO/AGE)

## Phase 4: On-site AG Management (Module 3)
- [x] Implement QR Code Generation and Emailing (Convocations)
- [x] Implement Assistance Kiosk `/kiosk`
- [x] Implement Scan Interface `/manager` (Barcode scanner, validation)
- [x] Implement On-site Proxy Validation (Pop-up for mandants)
- [x] Implement Real-time TV Display `/display`

## Phase 5: Automation & Archiving (Module 4)
- [x] Implement Annual Closure Script (August 31)
- [x] Implement Automatic Archiving (JSON format)
- [x] Implement Mailing Campaign (Mass email for renewal)
- [x] Create User Manual `/guide` inside Admin dashboard

## Phase 6: Global Dashboard & Routing Split (NEW)
- [x] Implement Top Navbar login in Portal for Admins
- [x] Display Admin buttons dynamically in Portal Index if logged in
- [x] Create `/admin/members` (Dedicated to Member CRUD, Sync, pending mods)
- [x] Create `/admin/ag` (Dedicated to AG Quorum, QR Codes Convocations, Display/Kiosk links)
- [x] Update `base.html` and navigation across all apps

## Phase 7: Real-time User Screen (Replacing Kiosk)
- [x] Remove Kiosk Blueprint and templates
- [x] Update `admin/ag.html` buttons to link to new User Screen
- [x] Create `/user_screen` route and UI in `scan.py`
- [x] Implement backend state (last scanned member)
- [x] Implement AJAX polling in User Screen to show member info in real time
- [x] Update Manager Scan interface to set the last scanned member
- [x] Implement 2-step manual validation for Receptionniste (+ cancel option)
- [x] Implement Real-time DOM updates for `/admin/ag` Dashboard

## Phase 8: Role Separation & User Management
- [x] Create User Management Interface (`/admin/users`)
- [x] Restrict `admin.members_dashboard` to Admin role only
- [x] Hide Admin cards in Portal Dashboard for Gestion role
- [x] Add Email field to Users DB model for password resets/management
- [x] Rename App to `EEA Manager` globally

## Phase 10: Security, Architecture & External Backups
- [x] Document Deployment Architecture (Mini-PC + Reverse Proxy/DMZ)
- [x] Create `/mentions-legales` route and public footer link
- [x] Implement Automated NAS Synchronizer (`/Volumes/AG/Members_List_Log/`)
- [x] Implement Automated GSheet Synchronizer (via `gspread`)
- [x] Write the step-by-step Setup Guide for NAS & Google Service Account

## Phase 11: Advanced Data Management & Archiving
- [x] Split NAS & GSheet logic (`_MEMBERS` and `_AG` variants)
- [x] Create manual export routes (`.db`, `_members.csv`, `_ag.csv`)
- [x] Add export buttons to `admin/members.html` and `admin/ag.html`
- [x] Add Archive Tabs to display past years from JSON backups in `admin/members.html`
- [x] Add visual quick-filters for "Non Renouvelés"

## Phase 12: Final Verification & Delivery
- [x] End-to-end testing
- [x] Walkthrough and documentation

## Phase 13: DB Restoration & Server Recap
- [x] Implement DB File Upload form in `admin/members.html`
- [x] Create `/admin/restore_db` route to handle the replacement securely
- [x] Write the `server_recap.md` documentation artifact
- [x] Provide architecture advice regarding the OVH subdomain DMZ

## Phase 14: Scheduled Backups & Enhanced Export Feedback
- [x] Implement Background Thread for Weekly Backups in `app/__init__.py`
- [x] Add DB copy support to NAS in `utils.py`
- [x] Update `export_db` and `export_csv` routes to save to `backups/manual/` and trigger NAS/GSheet sync
- [x] Add Information Popups (Modals) for Exports in `ag.html` and `members.html`

## Phase 15: Targeted Convocations Interface
- [x] Add `membres` object to `ag_dashboard` route in `admin.py`
- [x] Create Checkbox Form Modal in `ag.html` for Convocation selection
- [x] Create "Select All" / "Deselect All" button in JavaScript
- [x] Modify `send_convocations` route to only iterate over `request.form.getlist('selected_members')`
