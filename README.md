<img align="right" src="http://static.philip-trauner.me/touch-icon.png"></img>
# philip-trauner.me
This is the code for my website. There's not much to see, really. 

## Install
```bash
git lfs install
git clone https://github.com/PhilipTrauner/philip-trauner.me.git
pip3 install pipenv
cd philip-trauner.me
pipenv install
npm install
npm run build
git lfs pull
```

## Run
```bash
pipenv shell
python3 app.py
```

Upon first lauch a config file called `philip-trauner.me.cfg` is created. Edit it to suit your needs.  
By default there is no static content serving activated and a web server is required, switch `static_handler` to `True` and that is taken care of.

## Caveats
The GitHub integration is not really an integration at all because it works without authentication, which is good because I don't want to worry about access tokens every time I deploy this somewhere.
