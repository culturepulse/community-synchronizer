# --batch to prevent interactive command
# --yes to assume "yes" for questions
gpg --quiet --batch --yes --decrypt --passphrase="$CREDENTIALS_PASSWORD" --output credentials.json credentials.json.gpg
