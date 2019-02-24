# SVNRequest

## Visual web-tool to observe SVN-repositories and easily search through them.

*It simply lists svn-repository and generates static HTML and JSON web-files of this listing with ability of searching through file names. You can serve it with your web-server.*

### Requirements
- python3
- subversion

### Installing
1. Clone this repo.
2. Install dependencies with `pip3 install -r requirements.txt`

### Running
1. Set your web-server (nginx/apache/etc) to serve this `svnquest` directory.

2. Edit `config.yaml`: add svn repos you want to visualize. use `url` for repo url and `alias` to show it on the html page. 

Example:

```yaml
remotes:
  - url: http://svn.apache.org/repos/asf/spamassassin/trunk
    alias: Spam Assassin
  - url: http://svn.apache.org/repos/asf/falcon/trunk
    alias: Falcon
```
3. Run `python3 svnquest.py`. It will list and generate files with this listing. Then you can find generated files iniside `html/` and `remotes/` directories.

### Navigation

Navigate your browser to `<your.site/svnquest/html>`:

![Imgur](https://i.imgur.com/WQ0kymZ.png)

Choose repo and try to search something:

![Imgur](https://i.imgur.com/YhG3Emm.png)

You can create cron-task to regularly update repositories index.
