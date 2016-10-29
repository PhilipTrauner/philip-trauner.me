<img align="right" src="http://static.philip-trauner.me/touch-icon.png">
# philip-trauner.me
This is the code for my website. There's not much to see, really. 

## Install
```bash
git clone https://github.com/PhilipTrauner/philip-trauner.me.git
cd philip-trauner.me
pip3 install -r requirements.txt
git submodule init
git submodule update
git lfs install
git lfs pull
cd static/octicons
npm install && npm run build
```

## Run
```bash
python3 app.py
```

Upon first lauch a config file called `philip-trauner.me.cfg` is created. Edit it to suit your needs.  
By default there is no static content serving activated and a web server is required, switch `static_handler` to `True` and that is taken care of.

## Caveats
The GitHub integration is not really an integration at all because it works without authentication, which is good because I don't want to worry about access tokens every time I deploy this somewhere.
