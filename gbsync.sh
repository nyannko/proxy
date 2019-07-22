set -e
gitbook build
cd $HOME/github/proxy/
git co gh-pages 
cp -r $HOME/github/gitbooks/proxy/_book/* $HOME/github/proxy/
git add .
dt=$(date '+%d/%m/%Y,%H:%M')
comsg="$@" # get all params as commit msg
echo ${comsg}
if [[ $# -eq 0 ]]; then # if no commit msg, use the date
    git commit -m ${dt}
else 
    git commit -m "${comsg}"
fi
git push -u origin gh-pages
git co master