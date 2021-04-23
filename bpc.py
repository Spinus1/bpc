#!/usr/bin/env python
import traceback
import os  
from os import path  
import sys    
import logging
import argparse
import stashy
import git
from git import Repo
import urllib
import json
from pathlib import Path
import click

from version import __version__


configFileFolder=str(Path.home())+os.path.sep+".bpc"
configFile=configFileFolder+os.path.sep+"config.json"
configData=None
currentServer=None
defaultEditor=None


def criticalError(msg: str):
    "Raise critical error and exit"
    logging.critical("Critical error: {}, exiting!".format(msg))
    sys.exit(1)

def handleStashyException(e):
    logging.error("Error creating PR: '{}'".format(e.data['errors'][0]['message']))


class repoInfo:
    """Hosts git repository details"""
    def __init__(self,repositoryProject,repositoryName,basepath,baseurl,branch,url):
        self.repositoryProject=repositoryProject
        self.repositoryName=repositoryName
        self.basepath=basepath
        self.baseurl=baseurl
        self.branch=branch
        self.url=url


def getLocalRepoInfo():
    "Retrieve git information from working directory"
    
    	#search the folder containing .git
    drive=os.path.splitdrive(os.getcwd())[0]
    logging.debug("Drive is {}".format(drive))

    while not path.exists(".git"):
        os.chdir("../")
        logging.debug("new dir "+ os.getcwd())
        curdir=os.getcwd().replace("\\","")
        if curdir== drive or "/"==curdir :
            break

    if not path.exists(".git"):
        criticalError("Please invoke bpc in folder containing git repository")

    logging.info("final dir "+ os.getcwd())

    repo = Repo(".")
    
    # Retrieve repo uri, then retrieve repo name and project
    # Bitbucket server URL are like:
    #       https://www.example.com:PORT/scm/PROJECT_KEY/REPO_NAME
    #       https://www.example.com:PORT/scm/PROJECT_KEY/REPO_NAME.git
    # But it can be deployed to different path:
    #       https://www.example.com:PORT/subpath/scm/PROJECT_KEY/REPO_NAME.git
    
    remotes=repo.remotes
    remote=remotes[0]
    o=urllib.parse.urlparse(remote.url)
    
    it=iter(o.path.split("/"))
    # get rid of first empty token
    next(it)
    token=next(it)
    basepath=""
    try:
        # Search for 'scm' in the URL
        try:
            while "scm" != token:
                basepath=basepath + "/" + token
                token=next(it)
        except StopIteration:
            pass
        
        repositoryProject=next(it)
        repositoryName=next(it)
        repositoryName=repositoryName.replace(".git","")
    except:
        logging.info("This repository seems not to be hosted in Bibucket Server: I cannot find 'scm' string on the URL '{}'".format(remote.url))
    
    baseurl=urllib.parse.urlunsplit([o.scheme,o.netloc,basepath,"",""])
    
    basepath=basepath.replace("/","")
    
    logging.info("Repository project name: {}".format(repositoryProject))
    logging.info("Repository name: {}".format(repositoryName))
    logging.info("Bitbucket basepath: {}".format(basepath))
    logging.info("Bitbucket baseurl: {}".format(baseurl))
    
    branch=repo.active_branch.name
    logging.info ("Current branch: {}".format(branch))

    return repoInfo(repositoryProject,repositoryName,basepath,baseurl,branch,remote.url)

def get_pr_description():
    MARKER = '#Insert PR comment above this line...(click without saving to avoid adding a comment)\n'
    message = click.edit('\n\n\n' + MARKER)
    if message is not None:
        return message.split(MARKER, 1)[0].rstrip('\n')

def do_connect(config):
    logging.debug("Connecting...{} {} ".format(config['baseurl'], config['username']))
    return stashy.connect(config['baseurl'], config['username'], config['token'])


def printHeader():
        "Print status header"
        logging.info(">> Using {} ".format(currentServer))


def printPRinfo(pr):
    logging.info (">> PR {} - {}".format(pr["id"],pr["title"]))
    logging.info ("\t{} > {}".format(pr['fromRef']['displayId'],pr['toRef']['displayId']))
    if "description" in pr:
        logging.info ("\tDescription: {} ".format(pr["description"]))
    else:
        logging.info ("\tDescription: empty")
    logging.info ("\tReviewers: " )

    
    it=iter(pr["reviewers"])
    for reviewer in it:
        logging.info ("\t\t{} ".format(reviewer["user"]["displayName"]))
        next(it,None)
    
def printProjectInfo(prj):
    logging.info ("\t{} ({})".format(prj["key"],prj["name"]))

def printBitbucketRepoInfo(repo):
    logging.info ("\t{}".format(repo['slug']))


def do_list(args):
    "Lists projects or repositories"
    initialize(args)
    printHeader()
    serverToUse=currentServer

    # Check wheter to use default server or provided one    
    if args.server:
        if args.server in configData['servers']:
            serverToUse=args.server
        else:
            logging.error("Server {} not found in bpc configuration, using default one {}".format(args.server,currentServer))

    remote=do_connect(configData['servers'][serverToUse])

    if args.project:
            logging.info("Listing repositories for project {}".format(args.project))
            repoList=""
            try :
                repoList=remote.projects[args.project].repos.list()
            except:
                logging.error("Project {} does not existing in server {}".format(args.project,configData['servers'][serverToUse]['shortcut']))

            for repo in repoList:
                printBitbucketRepoInfo(repo)
    else :
        logging.info("Listing Bitbucket projects")
        logging.info("\tkey (name)")
        for prj in remote.projects.list():
            printProjectInfo(prj)
        
    return


def do_pr(args): 
    """Manages Pull Requests"""
    logging.debug("do_pr...")

    initialize(args)
    
    printHeader()

    # Load info fro local git repository
    info=getLocalRepoInfo()
    
    if info.baseurl in configData['url-shortcut-map']:
        if configData['url-shortcut-map'][info.baseurl] in configData['servers']:
            config=configData['servers'][configData['url-shortcut-map'][info.baseurl]]
        else:
            criticalError("Server listed in url-shortcut-map, but not in servers, please report a bug...")

        # Use the same server of local git repository
        baseurl=config['baseurl']
        if info.baseurl != baseurl:
            criticalError("Bitbucket URL {} different {}".format(info.baseurl,baseurl))
        else :

            # Set PR default branch
            if args.set_default_branch:
                logging.info("Setting branch '{}' as default target branch for PR on repository {}".format(args.set_default_branch,info.repositoryName))
                repositorySetting=dict()
                if info.url in configData['repositories']:
                    repositorySetting=configData['repositories'][info.url]
                repositorySetting['pr_default_branch']=args.set_default_branch
                configData['repositories'][info.url]=repositorySetting
                writeConfig()
                sys.exit(0)
        

            remote=do_connect(config)
            
            # List already existing PRs
            if args.list:
                logging.info("\nListing PR for repository: {}".format(info.repositoryProject+"/"+info.repositoryName))

                try:
                   
                    res=remote.projects[info.repositoryProject].repos[info.repositoryName].pull_requests.list()
                    it=iter(res)
                    for pr in it:
                            printPRinfo(pr)
                            next(it,None)
                except stashy.errors.GenericException as e:
                    handleStashyException(e)

            # PR creation
            else:
                defaultTitle="Insert title"
                # Add repo name to PR title
                if 'true' == configData['common']['pr_set_repo_title']:
                    defaultTitle="[{}] - ".format(info.repositoryName) + defaultTitle

                if not args.title:
                    prTitle=click.edit(defaultTitle,defaultEditor)
                    if None == prTitle and "" != prTitle:
                        prTitle=defaultTitle
                else:
                    prTitle=args.title 
               
                prDescription=""
                
                if 'false' == configData['common']['pr_set_empty_description']:
                    prDescription=get_pr_description()
                
                # Retrieve default brach
                defaultBranch='master'
                if info.url in configData['repositories']:
                    repositorySetting=configData['repositories'][info.url]
                    if 'pr_default_branch' in repositorySetting:
                        defaultBranch=repositorySetting['pr_default_branch']
            
                
                prTargetBranch=input("Please provide target branch (default: {}): ".format(defaultBranch))
                
                if None == prTargetBranch or "" == prTargetBranch:
                    prTargetBranch=defaultBranch

                logging.info("PR recap:\n\tTitle: '{}'".format(prTitle))
                logging.info("\tDescription: '{}'".format(prDescription))
                logging.info("\tTarget branch:'{}'".format(prTargetBranch))

                try:
                    res=remote.projects[info.repositoryProject].repos[info.repositoryName].pull_requests.create(prTitle,info.branch,prTargetBranch,prDescription)
                    printPRinfo(res)
                except stashy.errors.GenericException as e:
                    handleStashyException(e)
    else:
        criticalError("No Bitbucket server configuration found for current repository\nPlease add it with command 'bpc config --server-base-url {} --server-shortcut {}'".format(info.baseurl,info.basepath))                
    return

def writeConfig():
    "Just dumps configuration data as Json text file"
    logging.info("Writing config file {}".format(configFile))
    try:
        if not os.path.exists(configFileFolder):
            os.makedirs(configFileFolder)
        with open(configFile, 'w+') as outfile:
            json.dump(configData, outfile,indent=4, sort_keys=True)
    except :
        logging.error("Error creating config file..")
        return None


def createConfig():
    """Create config file from scratch"""
    global configData
    common={"version":"1","pr_message": "true", "pr_message_commits": "false","default_server":"","pr_title_reponame":"true","pr_set_repo_title":"true","pr_set_empty_description":"true"}
    configData={"common":common,"servers":{},"url-shortcut-map":{},"repositories":{}}
    logging.info(configData)


def loadConfig(args):
    "Load configuration file"
    
    global currentServer
    global configData

    if not os.path.exists(configFile) or os.stat(configFile).st_size == 0:
        logging.info("Configuration file is empty, please add at least one Bitbucket server entry")
        createConfig()
        addServer(args)

    try:
        with open(configFile) as temp:
            configData = json.load(temp)
    except :
        logging.error("Configuration file '{}' is corrupted, please launch bcp with \"config\" command!".format(configFile))
    
    if configData['common']['default_server']:
        currentServer=configData['servers'][configData['common']['default_server']]
    else:
        logging.error("Missing default server")

    #set default server
    currentServer=configData['common']['default_server']

def do_config(args):
    "handle command line config option"
    logging.debug("do_config...")

    initialize(args)
    # List available server
    if args.list:
        logging.info("Server list: {}".format(configData["servers"])) 
    # Configure global options
    elif args.pr_set_repo_title or args.pr_set_empty_description: 
        if args.pr_set_repo_title:
            configData['common']['pr_set_repo_title']=args.pr_set_repo_title
        if args.pr_set_empty_description:
            configData['common']['pr_set_empty_description']=args.pr_set_empty_description
        writeConfig()
    # Add a new server
    else:
        addServer(args)

def addServer(args):
    """Add new Bitbucket server configuration"""
    global configData

    # Check if change of default server is requested
    if args.set_default_server:
        if args.set_default_server in configData['servers']:
            logging.info("Setting server {} as default one".format(args.set_default_server))
            configData['common']['default_server']=args.set_default_server
            writeConfig()
            sys.exit(0)
        else:
            criticalError("Cannot find server {} in bpc configuration".format(args.set_default_server))

    logging.info ("Configuring new Bitbucket server")

    # check if we are called from config subcommand
    if 'config'==args.subparser_name:
        configcall=True
    else:
        configcall=False

    if not configcall or not args.server_shortcut:
        shortcut=input("Bitbucket shortcut: ")
    else:
        shortcut=args.server_shortcut

    # remove trailing slash to avoid comparison problems 
    if not configcall or not args.server_base_url:
        baseurl=input("Bitbucket address: ").rstrip('/')
    else:
        baseurl=args.server_base_url

    if not configcall or not args.username:
        user=input("User name for Bitbucket:")
    else:
        user=args.username
   
    if not configcall or not args.token:
        token=input("Token used to acces Bitbucket:")
    else:
        token=args.token


    serverDetails={"shortcut":shortcut,"baseurl":baseurl,"username":user,"token":token}
    
    # Dictionary containing server details
    serverdict=configData["servers"]
    serverdict[shortcut]=serverDetails
    configData["servers"]=serverdict

    # Dictionary to map server baseurl to server shortcut 
    urlshortcutmap=configData["url-shortcut-map"]
    urlshortcutmap[baseurl]=shortcut
    configData["url-shortcut-map"]=urlshortcutmap    

    if not configData['common']['default_server'] :
        configData['common']['default_server']=shortcut

    writeConfig()




def initialize(args):
    # Set log level
    loglevel=logging.INFO
    if args.d:
        loglevel=logging.DEBUG
        logging.basicConfig(format='%(levelname)s: %(message)s', level=loglevel)
    else:
        logging.basicConfig(format='%(message)s', level=loglevel)

    loadConfig(args)

    
def main():
    global __version__

    # create top level parser
    parser = argparse.ArgumentParser(description="Bitbucker Server python client",epilog="Version: {}".format(__version__),allow_abbrev=True)
    parser.add_argument('-d',action='store_true',help='print debug logs')
    subparsers = parser.add_subparsers(title='subcommands', description='valid subcommands',help='sub-command help',dest='subparser_name')

    # create the parser for the "pr" command
    parser_pr = subparsers.add_parser('pr', help='manage Pull Request',aliases=['p'])
    parser_pr.add_argument('--list', action='store_true', help='List pull request')
    parser_pr.add_argument('--title', help='Pull Request title')
    parser_pr.add_argument('--description', help='Pull Request description')
    parser_pr.add_argument('--set-default-branch', help='Pull request default target branch for current git repository')
    parser_pr.set_defaults(func=do_pr)

    # create the parser for the "config" command
    parser_config = subparsers.add_parser('config', help='configure global bcp options: just invoke it and enter requested informations',aliases=['c'])
    parser_config.add_argument('--list', action='store_true', help='List already configured servers')
    parser_config.add_argument('--server-base-url', help='Bitbucket server basename, e.g.: www.example.com/myBitbucketInstance')
    parser_config.add_argument('--server-shortcut', help='Bitbucket shortcut, e.g.: myBitbucketInstance')
    parser_config.add_argument('--username', help='Username to access Bitbucket')
    parser_config.add_argument('--token', help='Token to access Bitbucket')
    parser_config.add_argument('--set-default-server', help='Set default server to query for projects/repositories')
    parser_config.add_argument('--pr-set-repo-title', help='Add repository name to Pull Request title')
    parser_config.add_argument('--pr-set-empty-description', help='Do not add any description to Pull Request')
    parser_config.set_defaults(func=do_config)

    # create the parser for the "remote" command
    parser_remote = subparsers.add_parser('remote', help='Show remote server information',aliases=['r'])
    parser_remote.add_argument('--server', help='Specify server to query for projects/repositories')
    parser_remote.add_argument('--project', help='List already configured servers')
    parser_remote.set_defaults(func=do_list)

    # Parse command line arguments
    arguments=parser.parse_args()
    # Invoke function associated with requested command
    if 'func' in arguments:
        arguments.func(arguments)
    else:
        parser.print_help(sys.stderr)
    


if __name__ == "__main__":
    main()
