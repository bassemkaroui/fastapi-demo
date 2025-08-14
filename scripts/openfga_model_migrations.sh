#!/usr/bin/env bash

set -euo pipefail
set -x

STORE_NAME="$1"
STORE_FILE="$2"
MODEL_FILE="${OPENFGA_MODEL_FILE}"

STORE_ID=$(fga store list | jq -r --arg NAME "$STORE_NAME" '.stores[] | select(.name==$NAME) | .id')

# Chech if the store already has an authorization model
MODEL_COUNT=$(fga model list --store-id "$STORE_ID" | jq '.authorization_models // [] | length')

if [ "$MODEL_COUNT" -eq 0 ]; then
    EXISTING_HASH=""
else
    EXISTING_HASH=$(
        fga model transform \
            --file <(fga model get --store-id="$STORE_ID" --format fga) --output-format json | sha256sum | awk '{print $1}'
    )
fi

LOCAL_HASH=$(
    fga model transform --file "$MODEL_FILE" --output-format json | sha256sum | awk '{print $1}'
)

if [ "$LOCAL_HASH" != "$EXISTING_HASH" ]; then
    if [ -z "$EXISTING_HASH" ]; then
        echo "→ No authorization model found in store $STORE_NAME; importing from $STORE_FILE ..."
    else
        echo "→ Model changed (hash $EXISTING_HASH → $LOCAL_HASH); re-importing ..."
    fi

    fga store import --store-id "$STORE_ID" --file "$STORE_FILE"
    echo "✓ Imported authorization model and tuples into store $STORE_NAME (ID=$STORE_ID)."
else
    echo "✓ Authorization model in store $STORE_NAME is up-to-date; skipping import."
fi

# Test the authorization model
if [[ "$STORE_NAME" == *tests* ]]; then
    fga model test --tests "$STORE_FILE"
fi
