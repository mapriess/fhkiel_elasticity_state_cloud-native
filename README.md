# Overview
This example is based upon [Google Codelabs](https://codelabs.developers.google.com) demonstrating 

A. the instance autoscaling in [Google Cloud Run](https://cloud.google.com/run) and

B. a statefull and stateless web service.

The code creates a basic web service responding to simple HTTP GET and POST requests via different routes.

# About Google Cloud run
[Google Cloud Run](https://cloud.google.com/run) is a managed compute platform that enables you to run stateless containers that are invocable via HTTP requests. It is built on the Knative open-source project, enabling portability of your workloads across platforms. Cloud Run is serverless: it abstracts away all infrastructure management, so you can focus on what matters most — building great applications.

# I. Demonstration of elasticity and instance autoscaling

## a. Setup
Steps in a nutshell to perform before deploying a basic web service on Google Cloud Run (for full details please refer to https://codelabs.developers.google.com/codelabs/cloud-run-hello-python3?hl=en#1)

1. Sign-in to the Google Cloud Console and create a new project or reuse an existing one.

2. Start Cloud Shell

3. Run the following command in the Cloud Shell to confirm that you are authenticated: 

```
gcloud auth list
```

4. Set project to work with gcloud:
```
gcloud config set project <PROJECT_ID>
```

This should output:
![](./src/output1.png)

5. Confirm:

```
gcloud config list project
```

This should output:
![](./src/output2.png)

6. [Cloud Build](https://cloud.google.com/build) automatically builds a container image from your source code and pushes it to [Artifact Registry](https://cloud.google.com/artifact-registry). Artifact Registry manages your container image.

For this to work we need to enable the Artifact Registry, Cloud Build, and Cloud Run APIs.

```
gcloud services enable \
  artifactregistry.googleapis.com \
  cloudbuild.googleapis.com \
  run.googleapis.com
```

## b. Write application
- Create working directory `sample-webservice` 
- Create main file `main.py` or use the one from this GitHub repo
- Create `requirements.txt`for python libraries
- Create `Procfile`neccessary for Cloud Run to specify how the application will be served:
`web: gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 main:app`

## c. Deployment

Deploy the application to Cloud Run:
```
gcloud run deploy $SERVICE_NAME \
  --source $WORKDIR \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated
```

where 
- `SERVICE_NAME` could be anything, e.g., the name of our working directory `sample-webservice`
- `REGION` is set, either for specific usage, to e.g., `REGION="europe-west3"` or as a default region `gcloud config set run/region $REGION` 
- `WORKDIR` is the path to the directory containing application files. 

Note when using Redis memorystore via the simplified Cloud Run integrations, this feature is only supported in certain regions (see below, section IIa).

A successfull deployment should output:
![](./src/output3.png)

`gcloud run deploy` firstly creates a Artifact Registry Docker repository named `cloud-run-source-deploy` in the specified region in order to store the built container. 

It then automatically builds a container image from the specified source code (option `--source`) and pushes the image to the created Artifact Registry repository.

The service will be available via the displayed service URL. You can also get the service URL with this command:
```
SERVICE_URL=$( \
  gcloud run services describe $SERVICE_NAME \
  --platform managed \
  --region $REGION \
  --format "value(status.url)" \
)
```

## d. Test the service
Just apply simple GET request opening service URL or via curl: 
```
curl $SERVICE_URL
``` 
or
```
curl $SERVICE_URL?who=007
```

This should output:
![](./src/output4.png)

## e. Demonstrating the instance autoscaling in Google Cloud Run
a. We increase the max number of instances for the deployed service to a higher number.

Note that if using more demanding functions such as the deep learning example (classifying fashion MNIST data) memory might hast to be increased, here 2048MB are required in order to be able to train for ten epochs.
```
gcloud run services update $SERVICE_NAME \
--region $REGION \
--max-instances 10
--memory 2048Mi
```

b. You can check the updated setting of the service:
```
gcloud run services describe $SERVICE_NAME \
--region $REGION \
--format export
```

or by looking at the web interface of the deployed service in Google Cloud Run, section "YAML"
![](./src/output5.png)
![](./src/output6.png)

c. Simulate a higher load through several user requests by submitting responses via one of the provided curl scripts, e.g., simulating that 20 users use the web service to calculate the first four perfect numbers 100 times one after another.
```
for ((i=1;i<=200;i++)); do ./curl_simpleGET.sh & done
```
```
for ((i=1;i<=20;i++)); do ./curl_perfNr.sh & done
```
```
for ((i=1;i<=20;i++)); do ./curl_fashionMNIST_MLP.sh & done
```
![](./src/output8.png)

d. Observe the behavior of the provided ressources at the Cloud Run dashboard of the deployed service under section "METRICS", here specifically look at "Container instance count".

You should observe an increase in the number of instances over execution of the above requests:
![](./src/output9.png)
![](./src/output11.png)

# II. Demonstration of stateless webservice
Components in a cloud-native architecture should be designed to be stateless. 

If the state should be available throughout requests, an application independant cache - such as Redis in-memory database - to store and retrieve user state should be used instead of using the local memory or database of the instance serving the application. 
Here, a simple shopping cart list, which can be populated with items and be retrieved using simple POST and GET requests is used for demonstration purposes.

## a. Setup in Google Cloud Run
You can access Redis from a service running on Cloud Run through a managed Redis service like Google Cloud Memorystore

You can use the [Cloud Run integrations](https://cloud.google.com/run/docs/integrate/redis-memorystore) feature for a simplified way to connect to a new Redis instance. Note the Cloud Run integrations is [only supported in certain regions](https://cloud.google.com/run/docs/locations#integrations).

Otherwise follow the steps described [here](https://cloud.google.com/memorystore/docs/redis/connect-redis-instance-cloud-run) to connect to a Redis instance from a Cloud Run service.

The following curl commands can be used to submit a POST and GET request to test the webservice.

## b. Accessing the exemplary (statefull) webservice using local memory
```
curl -X POST $SERVICE_URL/add_to_cart_SF -H 'Content-Type: application/json' -d '{"item": "Shirt"}'
```
```
curl -X POST $SERVICE_URL/add_to_cart_SF -H 'Content-Type: application/json' -d @shopping.json 
```
```
curl $SERVICE_URL/get_cart_SF
```

## c. Accessing the exemplary (stateless) webservice using redis in-memory database
```
curl -X POST $SERVICE_URL/add_to_cart_SL -H 'Content-Type: application/json' -d '{"item": "Shirt"}'
```
```
curl -X POST $SERVICE_URL/add_to_cart_SL -H 'Content-Type: application/json' -d @shopping.json 
```
```
curl $SERVICE_URL/get_cart_SL
```

# III. Clean up
You can delete your repository or delete your Cloud project to avoid incurring charge.

To delete your container image repository:
```
gcloud artifacts repositories delete cloud-run-source-deploy \
  --location $REGION
```

To delete your Cloud Run service:
```
gcloud run services delete $SERVICE_NAME \
  --platform managed \
  --region $REGION
```

Alternatively, you can delete your Google Cloud project which stops billing for all the resources used within that project.

```
PROJECT_ID=$(gcloud config get-value core/project)
gcloud projects delete $PROJECT_ID
```