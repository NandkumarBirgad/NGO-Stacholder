# TODO: Implement Enhanced Add New Stakeholder Form

## Tasks
- [x] Replace existing modal content in `template/stakeholders.html` with the new detailed form structure (including fields like city, address, notes, and updated layout).
- [x] Add CSS styles for new form classes (e.g., .form-container, .form-header, .form-row, .form-group, .form-actions, .btn, .cancel-btn, .create-btn) to `static/style.css`.
- [x] Update JavaScript in `static/script.js` to handle the new form's close functionality (define `closeForm()`), submit functionality, and ensure it matches the new fields.
- [x] Test the form appearance and functionality by running the app and clicking "Add New Stakeholder" (App is running on http://127.0.0.1:5000/stakeholders).
reatec# TODO: Implement Enhanced Add New Stakeholder Form
## Notes
- Ensure the form integrates with existing backend API (`/api/add_stakeholder`).
- The new form includes additional fields: city, joinedDate, address, notes.
- Form actions include Cancel and Create buttons.
- Implementation complete and tested successfully.

# TODO: Implement Add New Project Form

## Tasks
- [x] Replace the alert in `template/projects.html` with a modal containing the provided HTML form structure.
- [x] Add the form fields: projectName, description, category, status, startDate, endDate, budget, targetBeneficiaries, volunteersNeeded, location, projectManager.
- [x] Add JavaScript to handle form submission, sending data to `/api/add_project`.
- [x] Update the backend API in `app.py` to handle `/api/add_project` endpoint, inserting data into the event table.

## Tasks

## Notes
- Projects are stored in the `event` table in the database.
- The form includes validation for required fields (projectName, category).
- Form actions include Cancel and Create buttons.
- Implementation complete and tested successfully.

# TODO: Implement Add New Activity Form

## Tasks
- [x] Replace the alert in `template/activities.html` with a modal containing a detailed form structure for adding new activities.
- [x] Add the form fields: activityName, description, activityType, status, startDate, endDate, location, expectedAttendees, budget, volunteersNeeded, organizer, notes.
- [x] Add JavaScript to handle form submission, sending data to `/api/add_activity`.
- [x] Update the backend API in `app.py` to handle `/api/add_activity` endpoint, inserting data into the event table.
- [x] Update the activities table display to show existing activities from the database.
- [x] Test the form by running the app and clicking "+ New Activity" (App is running on http://127.0.0.1:5000/activities).

## Notes
- Activities are stored in the `event` table in the database.
- The form includes validation for required fields (activityName, activityType, startDate).
- Form actions include Cancel and Create buttons.
- Implementation complete and tested successfully.

# TODO: Implement Record New Donation Form

## Tasks
- [x] Replace the alert in `template/donations.html` with a modal containing the provided HTML form structure for recording donations.
- [x] Add the form fields: donorName, amount, date, paymentMethod, category, project, notes, recurring, taxReceipt.
- [x] Add JavaScript to handle form submission, sending data to `/api/add_donation`, and populate donor and project dropdowns.
- [x] Update the backend API in `app.py` to handle `/api/add_donation` endpoint, inserting data into the donation table.
- [x] Update the donations list display to show existing donations from the database.
- [x] Test the form by running the app and clicking "+ Record Donation" (App is running on http://127.0.0.1:5000/donations).

## Notes
- Donations are stored in the `donation` table in the database.
- The form includes validation for required fields (donorName, amount, date).
- Form actions include Cancel and Record buttons.
- Implementation complete and tested successfully.
- [x] Replace existing modal content in `template/stakeholders.html` with the new detailed form structure (including fields like city, address, notes, and updated layout).
- [x] Add CSS styles for new form classes (e.g., .form-container, .form-header, .form-row, .form-group, .form-actions, .btn, .cancel-btn, .create-btn) to `static/style.css`.
- [x] Update JavaScript in `static/script.js` to handle the new form's close functionality (define `closeForm()`), submit functionality, and ensure it matches the new fields.
- [x] Test the form appearance and functionality by running the app and clicking "Add New Stakeholder" (App is running on http://127.0.0.1:5000/stakeholders).

## Notes
- Ensure the form integrates with existing backend API (`/api/add_stakeholder`).
- The new form includes additional fields: city, joinedDate, address, notes.
- Form actions include Cancel and Create buttons.
- Implementation complete and tested successfully.

# TODO: Implement Add New Project Form

## Tasks
- [x] Replace the alert in `template/projects.html` with a modal containing the provided HTML form structure.
- [x] Add the form fields: projectName, description, category, status, startDate, endDate, budget, targetBeneficiaries, volunteersNeeded, location, projectManager.
- [x] Add JavaScript to handle form submission, sending data to `/api/add_project`.
- [x] Update the backend API in `app.py` to handle `/api/add_project` endpoint, inserting data into the event table.
- [x] Update the projects table display to show existing projects from the database.
- [x] Test the form by running the app and clicking "+ New Project" (App is running on http://127.0.0.1:5000/projects).

## Notes
- Projects are stored in the `event` table in the database.
- The form includes validation for required fields (projectName, category).
- Form actions include Cancel and Create buttons.
- Implementation complete and tested successfully.

# TODO: Implement Add New Activity Form

## Tasks
- [x] Replace the alert in `template/activities.html` with a modal containing a detailed form structure for adding new activities.
- [x] Add the form fields: activityName, description, activityType, status, startDate, endDate, location, expectedAttendees, budget, volunteersNeeded, organizer, notes.
- [x] Add JavaScript to handle form submission, sending data to `/api/add_activity`.
- [x] Update the backend API in `app.py` to handle `/api/add_activity` endpoint, inserting data into the event table.
- [x] Update the activities table display to show existing activities from the database.
- [x] Test the form by running the app and clicking "+ New Activity" (App is running on http://127.0.0.1:5000/activities).

## Notes
- Activities are stored in the `event` table in the database.
- The form includes validation for required fields (activityName, activityType, startDate).
- Form actions include Cancel and Create buttons.
- Implementation complete and tested successfully.
