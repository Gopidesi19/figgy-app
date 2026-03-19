# Figgy - A Zomato/Swiggy Clone

This project is a clone of a food delivery service like Zomato or Swiggy, built with a microservices architecture.

## Architecture Overview

The system employs an event-driven, asynchronous microservices architecture to handle food order processing.

### Workflow:

1.  A **User** initiates an order via an **API Gateway**, which routes the request to the **User Service** (Flask on Cloud Run).
2.  The **User Service** publishes an `orders.place` event to a **Pub/Sub** topic.
3.  The **Order Processor** (a Cloud Run service configured for Pub/Sub Push) is triggered by the `orders.place` message. It validates the user and order data, creates the initial `pending` order in **Firestore**, and then publishes an `orders.created` event.
4.  The **Restaurant Service** (another Cloud Run service with Pub/Sub Push) consumes `orders.created` messages. It simulates assigning a restaurant and its decision to accept or reject the order. It updates the order status in Firestore and publishes either `orders.accepted` or `orders.rejected` events to dedicated Pub/Sub topics.
5.  Upon an `orders.accepted` event, the **Delivery Orchestrator** (an HTTP-triggered Cloud Function) is invoked. It simulates assigning a delivery agent, updates the order status to `out_for_delivery` in Firestore, and enqueues a **Cloud Task** to simulate the delivery duration.
6.  After a configured delay, the **Cloud Task** triggers the **Delivery Completion Service** (an HTTP-triggered Cloud Function). This function updates the order status to `delivered` in Firestore.
7.  Users can query the **User Service** to retrieve the latest status of their orders.

### Diagram:

```
[User] -> [API Gateway] -> [User Service (Cloud Run)]
                              | (Publishes order.place)
                              v
                      [Pub/Sub: orders.place]
                              | (Triggers via Push Subscription)
                              v
                 +-----------------------+
                 | Order Processor       |  Cloud Run
                 | - Validates request   |
                 | - Creates order in Firestore |
                 | - Publishes orders.created |
                 +-----------+-----------+
                             | (Publishes orders.created)
                             v
                     [Pub/Sub: orders.created]
                             | (Triggers via Push Subscription)
                             v
                 +-----------------------+
                 | Restaurant Service    |  Cloud Run
                 | - Assigns restaurant  |
                 | - Accepts/Rejects (updates Firestore) |
                 | - Publishes orders.accepted/rejected |
                 +-----------+-----------+
                             |
             accepts -> v          v <- rejects
      [Pub/Sub: orders.accepted]   [Pub/Sub: orders.rejected]
                             |
                             v (Invokes HTTP Endpoint)
               +-----------------------+
               | Delivery Orchestrator |  Cloud Function (HTTP)
               | - Assigns delivery agent |
               | - Updates status (Firestore) |
               | - Creates Cloud Task  |
               +-----------+-----------+
                             | (Enqueues Task)
                             v
                     [Cloud Tasks Queue]
                             |
                             v (Triggers after delay via HTTP)
    [Delivery Completion Service (HTTP Cloud Function)]
                             |
                             v (Updates DB)
                       [Firestore] (collections: users, orders, restaurants)
```

## Project Structure

```
figgy-project/
├── backend/
│   ├── user-service/
│   ├── order-processor/
│   ├── restaurant-service/
│   ├── delivery-orchestrator/
│   └── delivery-completion-service/
├── firestore/
│   ├── firestore.rules
│   └── sample-data.json
├── frontend/
└── infra/
```

## Deployment to Google Cloud Platform (GCP)

This guide provides step-by-step instructions to deploy the entire Figgy application to GCP.

### 1. Initial GCP Project Setup

Replace `YOUR_GCP_PROJECT_ID` and `YOUR_GCP_REGION` with your actual project ID and desired region (e.g., `us-central1`).

#### a. Set Your GCP Project

```bash
gcloud config set project YOUR_GCP_PROJECT_ID
```

#### b. Enable Required GCP APIs

Ensure the following GCP APIs are enabled in your project. This can be done via the GCP Console or using the `gcloud` CLI:

```bash
gcloud services enable run.googleapis.com
gcloud services enable pubsub.googleapis.com
gcloud services enable cloudfunctions.googleapis.com
gcloud services enable cloudtasks.googleapis.com
gcloud services enable firestore.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable servicenetworking.googleapis.com
gcloud services enable appengine.googleapis.com # Required for Cloud Tasks
gcloud services enable storage.googleapis.com # Required for Frontend deployment
```

### 2. Configure Firestore

#### a. Create Firestore Database

If you don't have a Firestore database set up, create one in Native mode (not Datastore mode). Choose your preferred region.

#### b. Deploy Firestore Security Rules

```bash
gcloud firestore deploy-rules firestore/firestore.rules
```

#### c. Import Sample Data (Optional)

You can manually add the data from `firestore/sample-data.json` via the GCP Console or write a script to import it.

### 3. Create Service Accounts and Grant Permissions

You will need dedicated service accounts for various components to interact securely. Replace `YOUR_GCP_PROJECT_ID` with your project ID.

#### a. Cloud Build Service Account

Cloud Build requires permissions to build, push images, and deploy services.

```bash
# Get your project number
PROJECT_NUMBER=$(gcloud projects describe YOUR_GCP_PROJECT_ID --format="value(projectNumber)")

# Grant necessary roles to the default Cloud Build service account
# For simplicity in development, you can grant roles/editor or roles/owner.
# For production, use more granular roles.
gcloud projects add-iam-policy-binding YOUR_GCP_PROJECT_ID \
  --member="serviceAccount:${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com" \
  --role="roles/editor"
  # More granular roles for Cloud Build:
  # roles/run.admin, roles/iam.serviceAccountUser, roles/artifactregistry.writer, roles/cloudfunctions.developer, roles/cloudtasks.admin, roles/pubsub.editor, roles/datastore.user, roles/storage.admin
```

#### b. Runtime Service Accounts for Microservices

Each microservice (Cloud Run, Cloud Functions) should ideally run with its own service account with the principle of least privilege.

**i. `app-runtime-sa` (for User Service, Order Processor, Restaurant Service)**

Permissions:
- Publish to Pub/Sub topics (`roles/pubsub.publisher`)
- Read/Write to Firestore (`roles/datastore.user`)
- Invoke Cloud Functions (if Cloud Run directly calls functions)

```bash
gcloud iam service-accounts create app-runtime-sa \
  --display-name "App Runtime Service Account"

gcloud projects add-iam-policy-binding YOUR_GCP_PROJECT_ID \
  --member="serviceAccount:app-runtime-sa@YOUR_GCP_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/pubsub.publisher"

gcloud projects add-iam-policy-binding YOUR_GCP_PROJECT_ID \
  --member="serviceAccount:app-runtime-sa@YOUR_GCP_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/datastore.user"
```

**ii. `delivery-orchestrator-sa` (for Delivery Orchestrator Cloud Function)**

Permissions:
- Read/Write to Firestore (`roles/datastore.user`)
- Enqueue Cloud Tasks (`roles/cloudtasks.enqueuer`)

```bash
gcloud iam service-accounts create delivery-orchestrator-sa \
  --display-name "Delivery Orchestrator Service Account"

gcloud projects add-iam-policy-binding YOUR_GCP_PROJECT_ID \
  --member="serviceAccount:delivery-orchestrator-sa@YOUR_GCP_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/datastore.user"

gcloud projects add-iam-policy-binding YOUR_GCP_PROJECT_ID \
  --member="serviceAccount:delivery-orchestrator-sa@YOUR_GCP_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/cloudtasks.enqueuer"
```

**iii. `delivery-completion-sa` (for Delivery Completion Service Cloud Function)**

Permissions:
- Read/Write to Firestore (`roles/datastore.user`)

```bash
gcloud iam service-accounts create delivery-completion-sa \
  --display-name "Delivery Completion Service Account"

gcloud projects add-iam-policy-binding YOUR_GCP_PROJECT_ID \
  --member="serviceAccount:delivery-completion-sa@YOUR_GCP_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/datastore.user"
```

### 4. Setup Pub/Sub Topics and Cloud Tasks Queue

#### a. Create Pub/Sub Topics

```bash
gcloud pubsub topics create orders-place
gcloud pubsub topics create orders-created
gcloud pubsub topics create orders-accepted
gcloud pubsub topics create orders-rejected
```

#### b. Create a Cloud Tasks Queue

```bash
gcloud tasks queues create delivery-queue --location=YOUR_GCP_REGION
```

### 5. Deploy Backend Microservices (Cloud Build CI/CD)

Each backend service has a `cloudbuild.yaml` file in its respective directory (`backend/<service-name>/cloudbuild.yaml`). These files define the steps to build a Docker image, push it to Artifact Registry, and deploy the service.

#### a. Setup Artifact Registry

If you don't have an Artifact Registry repository, create one:

```bash
gcloud artifacts repositories create figgy-docker \
  --repository-format=docker \
  --location=YOUR_GCP_REGION \
  --description="Docker repository for Figgy microservices"
```

#### b. Create Cloud Build Triggers for Each Service

For each service (User Service, Order Processor, Restaurant Service, Delivery Orchestrator, Delivery Completion Service):

1.  **Commit your code** to a Git repository (e.g., Cloud Source Repositories, GitHub, GitLab).
2.  Go to **Cloud Build** in the GCP Console -> **Triggers**.
3.  Click **CREATE TRIGGER**.
4.  Configure the trigger:
    *   **Name**: `figgy-<service-name>-ci-cd` (e.g., `figgy-user-service-ci-cd`).
    *   **Event**: `Push to a branch`.
    *   **Source**: Select your repository and the branch (e.g., `main` or `master`).
    *   **Build configuration**: Select `Cloud Build configuration file`.
    *   **Cloud Build file location**: Specify the path to your service's `cloudbuild.yaml` (e.g., `backend/user-service/cloudbuild.yaml`).
    *   **Substitutions (Optional)**: You might need to add `_GCP_REGION` with your region value if you don't hardcode it in `cloudbuild.yaml`.
5.  Create the trigger.

Once triggered (e.g., by pushing code), Cloud Build will automatically build, push, and deploy your services.
**After initial deployments, get the URLs for your Cloud Run services and Cloud Functions, as you'll need them for Pub/Sub subscriptions.**

#### c. Update `cloudbuild.yaml` files (if needed)

Ensure that all `cloudbuild.yaml` files are updated to reflect:
-   The correct `YOUR_GCP_REGION`.
-   The correct service account for deployment (`--service-account`).
-   For Cloud Run services, ensure they are deployed with `--allow-unauthenticated` if they are accessed directly or via API Gateway.

**Example `cloudbuild.yaml` for a Cloud Run Service (`user-service`):**

```yaml
# backend/user-service/cloudbuild.yaml
steps:
# Build the Docker image
- name: 'gcr.io/cloud-builders/docker'
  args: ['build', '-t', 'YOUR_GCP_REGION-docker.pkg.dev/$PROJECT_ID/figgy-docker/user-service:$COMMIT_SHA', '.']
  dir: 'backend/user-service'

# Push the Docker image to Artifact Registry
- name: 'gcr.io/cloud-builders/docker'
  args: ['push', 'YOUR_GCP_REGION-docker.pkg.dev/$PROJECT_ID/figgy-docker/user-service:$COMMIT_SHA']

# Deploy to Cloud Run
- name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
  entrypoint: gcloud
  args:
  - 'run'
  - 'deploy'
  - 'user-service'
  - '--image'
  - 'YOUR_GCP_REGION-docker.pkg.dev/$PROJECT_ID/figgy-docker/user-service:$COMMIT_SHA'
  - '--region'
  - 'YOUR_GCP_REGION'
  - '--platform'
  - 'managed'
  - '--allow-unauthenticated'
  - '--service-account'
  - 'app-runtime-sa@$PROJECT_ID.iam.gserviceaccount.com'
  # Set environment variables for config if needed
  # - '--set-env-vars=FIRESTORE_PROJECT_ID=$PROJECT_ID,PUBSUB_TOPIC_PLACE=orders-place'
images:
- 'YOUR_GCP_REGION-docker.pkg.dev/$PROJECT_ID/figgy-docker/user-service:$COMMIT_SHA'
```

**Example `cloudbuild.yaml` for a Cloud Function (`delivery-orchestrator`):**

```yaml
# backend/delivery-orchestrator/cloudbuild.yaml
steps:
- name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
  entrypoint: gcloud
  args:
  - 'functions'
  - 'deploy'
  - 'delivery-orchestrator' # Function name
  - '--region'
  - 'YOUR_GCP_REGION'
  - '--source'
  - 'backend/delivery-orchestrator' # Path to the function's source code relative to repo root
  - '--entry-point'
  - 'delivery_orchestrator' # Function entry point in your main.py
  - '--runtime'
  - 'python39' # Or python310, python311 etc.
  - '--trigger-http' # HTTP triggered function
  - '--service-account'
  - 'delivery-orchestrator-sa@$PROJECT_ID.iam.gserviceaccount.com'
  - '--memory'
  - '128MB'
  - '--timeout'
  - '60s'
  # Add environment variables if necessary
  # - '--set-env-vars'
  # - 'FIRESTORE_PROJECT_ID=$PROJECT_ID,CLOUD_TASKS_QUEUE=delivery-queue'
```

### 6. Configure Pub/Sub Subscriptions with Deployed Service URLs

Once your Cloud Run services and Cloud Functions are deployed and have generated URLs, you can create the Pub/Sub subscriptions.

```bash
# Get Cloud Run service URLs
USER_SERVICE_URL=$(gcloud run services describe user-service --platform managed --region YOUR_GCP_REGION --format "value(status.url)")
ORDER_PROCESSOR_URL=$(gcloud run services describe order-processor --platform managed --region YOUR_GCP_REGION --format "value(status.url)")
RESTAURANT_SERVICE_URL=$(gcloud run services describe restaurant-service --platform managed --region YOUR_GCP_REGION --format "value(status.url)")
DELIVERY_ORCHESTRATOR_URL=$(gcloud functions describe delivery-orchestrator --region YOUR_GCP_REGION --format "value(httpsTrigger.url)")
DELIVERY_COMPLETION_URL=$(gcloud functions describe delivery-completion-service --region YOUR_GCP_REGION --format "value(httpsTrigger.url)")


# Subscription for Order Processor (push to Cloud Run service)
gcloud pubsub subscriptions create order-processor-sub \
  --topic orders-place \
  --push-endpoint=${ORDER_PROCESSOR_URL} \
  --ack-deadline=30s \
  --service-account=app-runtime-sa@YOUR_GCP_PROJECT_ID.iam.gserviceaccount.com # Use SA with invoker role for Cloud Run push

# Subscription for Restaurant Service (push to Cloud Run service)
gcloud pubsub subscriptions create restaurant-service-sub \
  --topic orders-created \
  --push-endpoint=${RESTAURANT_SERVICE_URL} \
  --ack-deadline=30s \
  --service-account=app-runtime-sa@YOUR_GCP_PROJECT_ID.iam.gserviceaccount.com # Use SA with invoker role for Cloud Run push

# Subscription for Delivery Orchestrator (push to Cloud Function HTTP endpoint)
gcloud pubsub subscriptions create delivery-orchestrator-sub \
  --topic orders-accepted \
  --push-endpoint=${DELIVERY_ORCHESTRATOR_URL} \
  --ack-deadline=30s \
  --service-account=delivery-orchestrator-sa@YOUR_GCP_PROJECT_ID.iam.gserviceaccount.com # Use SA with invoker role for Cloud Function push
```
**Note:** Ensure the service accounts used for push subscriptions have the `roles/run.invoker` or `roles/cloudfunctions.invoker` role on the respective Cloud Run services or Cloud Functions.

### 7. Deploy Frontend Application

The frontend is a React application. You can deploy it to Google Cloud Storage and serve it via Firebase Hosting or directly via a Load Balancer with Cloud CDN. For simplicity, we'll outline a Cloud Storage + Firebase Hosting approach.

#### a. Build Frontend

```bash
cd frontend
npm install
npm run build
```
This will create a `build/` directory with static assets.

#### b. Deploy to Cloud Storage (Manual)

```bash
# Create a Cloud Storage bucket for your frontend (must be globally unique)
gsutil mb -p YOUR_GCP_PROJECT_ID -l YOUR_GCP_REGION gs://YOUR_FRONTEND_BUCKET_NAME

# Upload your build files
gsutil -m cp -r build/* gs://YOUR_FRONTEND_BUCKET_NAME/

# Make objects publicly readable
gsutil iam ch allUsers:objectViewer gs://YOUR_FRONTEND_BUCKET_NAME
```

#### c. Configure Firebase Hosting (Recommended for SPAs)

1.  **Install Firebase CLI**: `npm install -g firebase-tools`
2.  **Initialize Firebase in your project**:
    ```bash
    cd frontend
    firebase init hosting
    # Choose your GCP project
    # Set 'public' directory to 'build'
    # Configure as a single-page app (rewrite all URLs to /index.html)
    ```
3.  **Deploy**:
    ```bash
    firebase deploy --only hosting
    ```

**Note**: You'll need to update the `API_BASE_URL` in `frontend/src/config.js` to point to the URL of your deployed `user-service` Cloud Run instance. You can do this dynamically during CI/CD or before building the frontend.

### 8. API Gateway (Optional but Recommended for Production)

For a robust production setup, an API Gateway (e.g., Cloud Endpoints or Apigee) should be used in front of the User Service to handle authentication, routing, and rate limiting.

### 9. Local Development

Refer to the `How to Run` section below for instructions on running the application locally.

## How to Run Locally

### 1. Start Backend User Service

```bash
cd figgy-project/backend/user-service
pip install -r requirements.txt
python main.py
```
This will start the Flask server on `http://localhost:8080`.

### 2. Start Frontend Application

```bash
cd figgy-project/frontend
npm install
npm start
```
This will open the application in your web browser at `http://localhost:3000`.

### 3. Interact with the Local UI

*   Open `http://localhost:3000`.
*   Register and log in.
*   Browse restaurants, add items to cart, checkout, and check order status.
*   Note: The backend Pub/Sub, Firestore, and Cloud Tasks interactions are currently simulated with print statements in the local `main.py` files for simplicity.