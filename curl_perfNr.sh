#!/bin/bash

SERVICE_NAME="sample-webservice"
REGION="europe-west3"

SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --platform managed --region $REGION --format "value(status.url)")

for ((i=1;i<=100;i++))
	do curl -s "$SERVICE_URL/perfectNr?howMany=4" > /dev/null
done