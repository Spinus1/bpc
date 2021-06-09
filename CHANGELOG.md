**0.99.2**:

**New Features**:
* Configuration file changes :
	* adding new options --pr-set-auto-fetch and --pr-set-auto-push (pr_set_ignore_dirty_workarea is just for bpc developers)      
	* Adding isConfigOptionEnabled function: it returns false if config option is missing: so config file does not need to be updated
	* Update config version to v 2
* Autofetch: fetch for upstream modification before creating PR
* Autopush: push latest changes before opening PR
* Abort PR creation if local repo contains uncommitted changes

**Bugfixes**:
* Fix issue when bpc config url does not contain username, but git repo does
* Add repo name to title even when passing title with command line
* Force to use only true/false for boolean configuration parameter
	* Fixed some wrong usage of boolean config parameters
* Avoid to ask for server information twice when config file is empty
* Fix issue when config file was not existing
* Fix loglevel
* Fixing handling of pr_set_empty_description

**Other**:
* Adding Gplv3 license

**0.99.1**:
* Fix issue when config file was not present

**0.99.0**:
* Dev release

*Maintainer: Alessio Moscatello <alessio.moscatello@marelli.com>*
