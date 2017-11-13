======
README
======

View History 
============

This is an Odoo module which allows to keep a history of changes in the arch of a view. This will allow to keep a different versions of the views available, so it could be used to prototype, easily restore changes, etc... This could be specially useful for Odoo form and tree views, reports and websites.

Here are some keys to understand the way it works:

- In the ir.ui.view model, we have a boolean field (enable_history) which allow us to activate this functionality for a view (from the user interface).

- The create and write methods of ir.ui.view are extended, so they create new versions (ir.ui.view.version) with the changes on arch field when the enable_history flag is activated.

- Versions are listed in the ir.ui.view form view in a separate tab.

- The current_version field indicates which version is used for the standard actions (like retrieving the arch field when rendering a view). The read and render methods are extended with this purpose.

- When changes are made, those are not automatically “activated”, but store, lets say, as draft. To “activate” this changes, one needs to manually set the respective version as “current”. This could be done selection one version from the list of versions.

Notes:

- All changes are made over the latest version.

- Every time there is a change or a version is selected (except when selecting the latest version) a new version is created

- All changes are store using the complete arch field. We considered using other approach (like saving only the differences), but:

    - it makes the implementation more complex

    - could face performance issues (a lot of recursive calls to compute a view)

    - if the goal is to save space, it does not work well on all cases (when changing most of the content)

- We do not handle the case of changing of inherit views, i.e. if a ir.ui.view has enable_history activated, changes on inherited view are not detected.


