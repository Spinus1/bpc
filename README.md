# bpc
`bpc` Bitbucket Python Client is  simple python client for [Bitbucket Server](https://www.atlassian.com/it/software/bitbucket) that uses REST API through [Stashy library](https://github.com/cosmin/stashy)

## Dependencies
`bpc` is Python 3 based.
To install dependencies just launch:
* `pip install -r requirements.txt`

Or install them manually
```
pip install stashy
pip install gitpython
pip install click
```

*Note*: it is take for granted that your default Python installation is Python 3 if not just explicitly run `bpc` with Python 3: `python3 bpc`

# Usage
## Server configuration
`bpc` needs configuration for at least one Bitbucket server; to add new server configuration invoke command
```
bpc config
```
and provide required details:
* server-base-url: Bitbucket server web url e.g. "https://www.example.com/mybitbucketinstance"
	* this is not the git repository url, that is like https://www.example.com/mybitbucketinstance/scm
* server-shortcut: mnemonic name to ease server management in `bpc`
* usarname: user name to access Bitbucket server
* token: do not store plain password in `bpc` just use a personal access token
	* please refer to [upstream support page](https://confluence.atlassian.com/bitbucketserver/personal-access-tokens-939515499.html)

Non interactive way:
```
bpc config --server-base-url "https://www.example.com/mybitbucketinstance" --server-shortcut mybitbucketinstance --username myuser --token mytoken
```

The first server added to bpc will be used as default one; to change it invoke:
```
bpc config --set-default-server mybitbucketinstance
```
Note: default server is used only when querying for Bitbucket projects/repositories; the server configuration for managing Pull Request will be guess from local git repository

## Pull Request
To manage Pull Requests `bpc` shall be invoked in folder containing a git repository

### Creating PR
Invoke command:
```
bpc pr 
```
and provide required details:
* ...
* ...

Non interactive way:
```
bpc pr --title "PR title" --description "PR description"
```

### Additional settings
* A default target branch can be specified for each needed repository, invoke command:
	```
	bpc pr --set-default-branch myBranch
	```
* Repository name can be added to PR title: it can be enable disabled:
	```
	bpc config --pr-set-repo-title [true|false]
	```
* To enabled disable request for PR description, use the following command:
	```
	bpc config --pr-set-empty-description [true|false]
	```
 * To enable/disable fetch changes before opening PR, use the following command:
	```
	bpc config --pr-set-auto-fetch [true|false]
	```
	
* To enable/disable pushing changes to remote server before opening PR, use the following command:
	```
	bpc config --pr-set-auto-push [true|false]
	```

### Listing PRs
To list all the PR pending for a repository, just invoke command:
```
bpc pr --list 
```

## Listing projects and repositories
List all the projects in default Bitbucket server (*projects that the current user has access to*):
```
bpc list 
```

List all repositories on a specific Bitbucket project:
```
bpc list --project  PROJECT_NAME
```

## Select editor
bcp is using Click library to edit information, to change default editor in Linux you can edit file ~/.selected_editor

## Advanced tips
* Some command line options can be shortened when the resulting command is unambigous
* At your own risk, you can dig in `~/.bpc/config.json` to spot for features not yet officially released

# bpc development
## TODO
* Pretty print servers list
* Be able to add per repository default reviewers
* Select editor from bpc
* Clone repositories directly from bpc

## Debug configurations
You can retrieve some debug configurations is `.vscode/.launch.json`

## Dependency list generation
* Install  `pipreqs`
    * `pip install pipreqs` 
* just launch `pipreqs` to get requirements.txt list

# Generating executable
1. Install *cx-freeze* package with pip
2. Launch script `python setup.py build`

# Inspiration
[lab](https://github.com/zaquestion/lab/blob/master/README.md) for gitlab has given me the idea to implement this client, but is very far to have comparable features

