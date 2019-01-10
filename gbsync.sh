gitbook build
cd $HOME/github/proxy/
git co gh-pages 
cp -r $HOME/github/gitbooks/proxy/_book/* $HOME/github/proxy/
git add .
dt=`date '+%d/%m/%Y,%H:%M'`
git commit -m $dt
git push -u origin gh-pages
git co master