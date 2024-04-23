#!/bin/bash

SERVICE_NAME="hello"
REGION="europe-west9"

SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --platform managed --region $REGION --format "value(status.url)")

for ((i=1;i<=1000;i++))
  do curl -s $SERVICE_URL?who=$i > /dev/null
done