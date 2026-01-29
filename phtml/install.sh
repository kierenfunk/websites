# if github action worker, do this:
mkdir -p "$HOME/.local/bin"
wget -O "$HOME/.local/bin/phtml" "https://github.com/kierenfunk/websites/phtml/phtml.py"
chmod +x "$HOME/.local/bin/phtml"
echo "$HOME/.local/bin" >> "$GITHUB_PATH"
# else
# install to /usr/local/bin?
