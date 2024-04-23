#!/bin/bash

SERVICE_NAME="sample-webservice"
REGION="europe-west9"

SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --platform managed --region $REGION --format "value(status.url)")

for ((i=1;i<=100;i++))
	do curl -s "$SERVICE_URL/fashionMNIST_MLP?epochs=10&batch_size=50" > /dev/null
done