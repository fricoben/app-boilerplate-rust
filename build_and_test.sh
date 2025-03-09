# #!/bin/bash
# set -e

# echo "=== Building the application ==="
# git submodule update --init --recursive
# docker exec -it -u 0 app-boilerplate-rust-container bash -c 'cd ./ && cargo ledger build stax -- -Zunstable-options --out-dir build/stax/bin && mv build/stax/bin/app-boilerplate-rust build/stax/bin/app.elf && mv build/stax/bin/app-boilerplate-rust.apdu build/stax/bin/app.apdu'

# echo "=== Running the Safe TX tests ==="
# # Run the Safe TX tests using Docker run
# docker run --rm -it -v "$(pwd):/app" ghcr.io/ledgerhq/ledger-app-builder/ledger-app-dev-tools:latest pytest tests/test_safe_tx.py -v -s --device stax

echo "=== Running the Sign Safe TX tests ==="
# Run the Safe TX tests using Docker run
docker exec -it -u 0 app-boilerplate-rust-container bash -c ' [ -f ./tests//requirements.txt ] && pip install -r ./tests//requirements.txt' ; docker exec -it app-boilerplate-rust-container bash -c "pytest tests/test_sign_safe_tx.py -v -s --device stax --display"
docker exec -it -u 0 app-boilerplate-rust-container bash -c ' [ -f ./tests//requirements.txt ] && pip install -r ./tests//requirements.txt' ; docker exec -it app-boilerplate-rust-container bash -c "pytest tests/test_sign_cmd.py -v -s --device stax --display"